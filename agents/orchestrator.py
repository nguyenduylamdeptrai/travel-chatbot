from typing import List, Literal
from dotenv import load_dotenv

load_dotenv(override=True)

from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate
from langchain.schema import AIMessage, HumanMessage, BaseMessage
from langchain.schema.messages import get_buffer_string

from pydantic import BaseModel, Field
import time
import google.api_core.exceptions
import json

from agents.planner import Planner
from agents.responder import Responder
from agents.response_synthesizer import Synthesizer
from prompt import ORCHESTRATOR_PROMPT

from langchain.memory import ConversationSummaryBufferMemory
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.api_tracker import create_callback, get_usage


class ValidationResult(BaseModel):
    """Schema để đánh giá câu trả lời."""

    is_sufficient: Literal["yes", "no"] = Field(
        description="Trả lời 'yes' nếu câu trả lời đầy đủ và 'no' nếu không."
    )
    feedback: str = Field(
        description="Phản hồi chi tiết nếu câu trả lời không đủ tốt, giải thích tại sao và cần cải thiện những gì."
    )


class Orchestrator:
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        model_provider: str = "google-genai",
        temperature=0.0,
        max_tokens: int = 4000,
        conversation_id: str = None,
    ):
        """Create orchestrator agent"""
        self.conversation_id = conversation_id or "default"
        self.callback = create_callback(self.conversation_id)
        self.llm_model = init_chat_model(
            model_name,
            model_provider=model_provider,
            temperature=temperature,
            callbacks=[self.callback],
        )

        structured_llm = self.llm_model.with_structured_output(ValidationResult)

        validation_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", ORCHESTRATOR_PROMPT),
                ("human", "Câu hỏi gốc của người dùng: \n```{question}```"),
                ("ai", "Đây là câu trả lời đã được tạo ra: \n```{answer}```"),
                ("human", "Dựa vào câu hỏi và câu trả lời, hãy đánh giá câu trả lời."),
            ]
        )

        self.validation_chain = validation_prompt | structured_llm

        # Manual managing memory
        # self.max_tokens = max_tokens
        # self.total_tokens = 0
        # self.chat_history: List[BaseMessage] = []

        # Manage memory by summarizing...
        self.memory = ConversationSummaryBufferMemory(
            llm=self.llm_model,
            max_token_limit=max_tokens,
            return_messages=True,
            memory_key="chat_history",
            input_key="input",
        )

        self.planner = Planner(
            model_name=model_name,
            model_provider=model_provider,
            temperature=temperature,
            conversation_id=self.conversation_id,
        )
        self.responder = Responder(
            model_name=model_name,
            model_provider=model_provider,
            temperature=temperature,
            conversation_id=self.conversation_id,
        )
        self.synthesizer = Synthesizer(
            model_name=model_name,
            model_provider=model_provider,
            temperature=temperature,
            conversation_id=self.conversation_id,
        )

    def update_total_tokens(self):
        self.total_tokens = self.llm_model.get_num_tokens(
            get_buffer_string(self.chat_history)
        )

    def trim_history_to_fit(self):
        while self.total_tokens > self.max_tokens and len(self.chat_history) > 1:
            self.chat_history.pop(0)
            self.update_total_tokens()

    def safe_invoke_validator(self, question: str, answer: str, retries=5, delay=1):
        for i in range(retries):
            try:
                start_time = time.time()
                response = self.validation_chain.invoke(
                    {"question": question, "answer": answer}
                )
                duration = time.time() - start_time
                print("-" * 60)
                print(
                    f"Validation Result: is_sufficient='{response.is_sufficient}', feedback='{response.feedback}'"
                )
                print(f"[TIMING][Orchestrator.validator] latency={duration:.2f}s")
                return response
            except google.api_core.exceptions.ServiceUnavailable as e:
                print(f"[Retry {i+1}/{retries}] Model overloaded. Waiting {delay}s...")
                time.sleep(delay)
            except google.api_core.exceptions.ResourceExhausted as e:
                # Xử lý quota/rate limit error
                error_msg = str(e)
                retry_delay = delay
                
                # Thử trích xuất retry delay từ error message
                if "retry_delay" in error_msg or "Please retry in" in error_msg:
                    import re
                    match = re.search(r'Please retry in ([\d.]+)s', error_msg)
                    if match:
                        retry_delay = max(float(match.group(1)), delay)
                
                if i < retries - 1:
                    print(f"[Retry {i+1}/{retries}] Quota/rate limit exceeded. Waiting {retry_delay:.1f}s...")
                    print(f"Lỗi: Bạn đã vượt quá quota API. Free tier giới hạn 15 requests/phút.")
                    time.sleep(retry_delay)
                else:
                    # Không retry nữa, trả về validation result với feedback
                    print(f"Quota API đã hết sau {retries} lần thử. Trả về kết quả validation.")
                    return ValidationResult(
                        is_sufficient="no",
                        feedback=f"Không thể xác thực câu trả lời do quota API đã hết. "
                                f"Free tier giới hạn 15 requests/phút. Vui lòng đợi {retry_delay:.0f} giây."
                    )
            except Exception as e:
                print(f"Lỗi không mong muốn trong quá trình xác thực: {e}")
                return ValidationResult(
                    is_sufficient="no",
                    feedback=f"Lỗi hệ thống trong quá trình xác thực: {e}",
                )

        raise Exception("Model vẫn quá tải hoặc gặp lỗi sau nhiều lần thử lại.")

    def run(self, question: str):
        """Execute the agent"""
        print("=" * 50 + " ORCHESTRATOR " + "=" * 50)

        # Manual managing memory
        # self.chat_history.append(HumanMessage(content=question))
        # self.update_total_tokens()
        # self.trim_history_to_fit()

        # Manage memory by summarizing...
        chat_history = self.memory.chat_memory.messages
        print(f"\nCurrent History ({len(chat_history)} messages):")
        print(get_buffer_string(chat_history))
        # =====

        print("\n[1] Planning tasks...")
        plan_start = time.time()
        tasks = self.planner.run(query=question, chat_history=chat_history)
        plan_duration = time.time() - plan_start
        print(f"[TIMING][Orchestrator.planner] latency={plan_duration:.2f}s")
        print(f"  -> Plan: {tasks}")

        final_answer = ""

        for attempt in range(3):
            print(f"\n--- ATTENTION {attempt + 1} ---")

            print("[3] Responding to tasks...")
            responses = []
            responses_dict = {}
            for i, task in enumerate(tasks):
                print(f"  - Executing task {i+1}/{len(tasks)}: {task}")
                depends_on_results = [
                    responses_dict[dep_id]
                    for dep_id in task.get("depends_on", [])
                    if dep_id in responses_dict
                ]
                resp_start = time.time()
                response = self.responder.run(
                    task, depends_on_results=depends_on_results
                )
                resp_duration = time.time() - resp_start
                print(
                    f"[TIMING][Orchestrator.responder] task_id={task.get('id', i)} "
                    f"latency={resp_duration:.2f}s"
                )
                responses.append(response)
                responses_dict[task["id"]] = response["response"]

            print("\n[4] Synthesizing final answer...")
            synth_start = time.time()
            final_answer = self.synthesizer.run(question, responses)
            synth_duration = time.time() - synth_start
            print(f"[TIMING][Orchestrator.synthesizer] latency={synth_duration:.2f}s")
            print("  -> Synthesized Answer (candidate):")
            print(final_answer)

            print("\n[5] Validating the answer...")
            validation_result = self.safe_invoke_validator(
                question=question, answer=final_answer, retries=1
            )

            if validation_result and validation_result.is_sufficient == "yes":
                print("\n[SUCCESS] Answer is sufficient.")
                # Manual:
                # ai_msg = AIMessage(content=final_answer)
                # self.chat_history.append(ai_msg)
                # =====
                # Summarizing:
                self.memory.save_context({"input": question}, {"output": final_answer})
                # =====
                return final_answer
            else:
                feedback = (
                    validation_result.feedback
                    if validation_result
                    else "Không nhận được phản hồi."
                )
                print(f"\n[REPLAN] Attempt {attempt + 1} failed. Feedback: {feedback}")

                if attempt < 1:
                    print("\nRe-planning based on feedback...")
                    replan_prompt = f"""Một nỗ lực trước đó để trả lời câu hỏi này đã thất bại. Đây là câu trả lời đã được tạo ra và phản hồi về nó:
    Câu trả lời thất bại: "{final_answer}"
    Phản hồi: "{feedback}"

    Dựa trên phản hồi này, hãy tạo ra một kế hoạch MỚI và TỐT HƠN. Tránh những sai lầm của kế hoạch trước. Kế hoạch của bạn phải giải quyết được những thiếu sót đã được chỉ ra trong phần phản hồi."""
                    tasks = self.planner.run(
                        # Manual:
                        # query=replan_prompt, chat_history=self.chat_history
                        # =====
                        # Summarizing:
                        query=replan_prompt,
                        chat_history=chat_history,
                        # =====
                    )
                    print(f"  -> New Plan: {tasks}")

        print(
            f"\n[FAILURE] Không thể tạo ra câu trả lời đủ tốt sau {attempt+1} lần thử. Trả lại kết quả cuối cùng."
        )

        # Manual:
        # ai_msg = AIMessage(content=final_answer)
        # self.chat_history.append(ai_msg)
        # self.update_total_tokens()
        # =====
        # Summarizing:
        self.memory.save_context({"input": question}, {"output": final_answer})
        # =====
        return final_answer


if __name__ == "__main__":
    master = Orchestrator()
    question = (
        "Lên kế hoạch đi Đà Nẵng 2 ngày 1 đêm với ngân sách 10 triệu, đi từ Hà Nội"
    )
    answer = master.run(question)
    print("\n" + "=" * 40 + " FINAL ANSWER " + "=" * 40)
    print(answer)
