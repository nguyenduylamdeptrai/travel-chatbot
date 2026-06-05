from dotenv import load_dotenv

load_dotenv(override=True)
import time
import google.api_core.exceptions
from agents.base_agent import BaseAgent
from prompt import SYNTHESIZER_PROMPT
from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.schema import AIMessage, HumanMessage
import json
from langchain.schema import BaseMessage
from typing import List
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.api_tracker import create_callback


class Synthesizer(BaseAgent):
    def __init__(self, model_name: str, model_provider: str, temperature=0.0, conversation_id: str = None):
        super().__init__(model_name=model_name, model_provider=model_provider)
        self.conversation_id = conversation_id or "default"
        self.callback = create_callback(self.conversation_id)
        # Override LLM with callback
        self.llm = init_chat_model(
            model=model_name,
            model_provider=model_provider,
            temperature=temperature,
            callbacks=[self.callback],
        )
        self.tools = []

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYNTHESIZER_PROMPT),
                MessagesPlaceholder(variable_name="question"),
                MessagesPlaceholder(variable_name="tasks_list"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        # Create agent from prompt template
        Agent_calling = create_tool_calling_agent(
            self.llm, tools=self.tools, prompt=prompt
        )

        self.SynthesizeExecutor = AgentExecutor(
            agent=Agent_calling,
            tools=self.tools,
            verbose=False,
            handle_parsing_errors=True,
        )

    def safe_invoke(self, input, retries=5, delay=2):
        for i in range(retries):
            try:
                return self.SynthesizeExecutor.invoke(input, config={"callbacks": [self.callback]})
            except google.api_core.exceptions.ServiceUnavailable as e:
                print(f"[Retry {i+1}] Model overloaded. Waiting {delay}s...")
                time.sleep(delay)
        raise Exception("Model vẫn quá tải sau nhiều lần thử lại.")

    def run(self, question: str, completed_tasks: list[dict]) -> str:
        """
        Tổng hợp kết quả từ các task đã hoàn thành để trả lời câu hỏi gốc.

        Args:
            question: Câu hỏi gốc của người dùng.
            completed_tasks: List các dictionary, mỗi dict là một task đã hoàn thành.

        Returns:
            Câu trả lời cuối cùng đã được tổng hợp.
        """
        print("=" * 50 + " SYNTHESIZER " + "=" * 50)

        formatted_tasks = "Dưới đây là kết quả của các tác vụ con đã được thực hiện để trả lời câu hỏi:\n\n"
        for task in completed_tasks:
            formatted_tasks += f"--- START TASK ---\n"
            formatted_tasks += f"ID Task: {task.get('id', 'N/A')}\n"
            depends_on = task.get("depends_on")
            if depends_on:
                formatted_tasks += f"Phụ thuộc vào Task: {', '.join(depends_on)}\n"
            formatted_tasks += f"Mô tả Task: {task.get('description', 'N/A')}\n"
            response_str = json.dumps(
                task.get("response", "Không có kết quả"), indent=2, ensure_ascii=False
            )
            formatted_tasks += f"Kết quả Task:\n{response_str}\n"
            formatted_tasks += f"--- END TASK ---\n\n"

        input_data = {
            "question": [
                HumanMessage(content=f'Câu hỏi gốc cần trả lời là: "{question}"')
            ],
            "tasks_list": [HumanMessage(content=formatted_tasks)],
        }

        result = self.safe_invoke(input_data)

        return result.get(
            "output", "Rất tiếc, tôi không thể tổng hợp được câu trả lời."
        )


if __name__ == "__main__":
    synthesizer_agent = Synthesizer(
        model_name="gemini-2.5-flash", model_provider="google-genai", temperature=0.1
    )

    question = "Giá cổ phiếu Tesla hôm nay?"
    tasks = [
        {
            "id": "task_1",
            "description": "Tìm giá cổ phiếu hiện tại của Tesla (TSLA).",
            "depends_on": [],
            "response": "Tôi xin lỗi, tôi không thể cung cấp thông tin về giá cổ phiếu. Tôi chỉ có thể cung cấp thông tin liên quan đến du lịch.",
        },
    ]

    print(f"Câu hỏi gốc: {question}")
    print("Dữ liệu đầu vào (kết quả các subtask):")
    print(json.dumps(tasks, indent=2, ensure_ascii=False))

    final_answer = synthesizer_agent.run(
        original_question=question, completed_tasks=tasks
    )

    print("\n--- Câu trả lời tổng hợp cuối cùng ---")
    print(final_answer)
    print("=" * 60)
