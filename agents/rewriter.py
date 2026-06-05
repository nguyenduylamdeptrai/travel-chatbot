from dotenv import load_dotenv

load_dotenv(override=True)

from prompt import REWRITER_PROMPT, REWRITE_REFLECTOR_PROMPT


import time
import google.api_core.exceptions
from agents.base_agent import BaseAgent
from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.schema import AIMessage, HumanMessage
import json


class Rewriter(BaseAgent):
    def __init__(self, model_name: str, model_provider: str, temperature=0.0):
        super().__init__(model_name=model_name, model_provider=model_provider)
        self.tools = []

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", REWRITER_PROMPT),
                MessagesPlaceholder(variable_name="chat_history"),
                MessagesPlaceholder(variable_name="question"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        prompt_reflector = ChatPromptTemplate.from_messages(
            [
                ("system", REWRITE_REFLECTOR_PROMPT),
                MessagesPlaceholder(variable_name="chat_history"),
                MessagesPlaceholder(variable_name="question"),
                MessagesPlaceholder(variable_name="rewrite_result"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        # Create agent from prompt template
        Agent_calling = create_tool_calling_agent(
            self.llm, tools=self.tools, prompt=prompt
        )

        Reflector_agent_calling = create_tool_calling_agent(
            self.llm, tools=self.tools, prompt=prompt_reflector
        )

        self.RewriteExecutor = AgentExecutor(
            agent=Agent_calling,
            tools=self.tools,
            verbose=False,
            handle_parsing_errors=True,
        )

        self.RewriteReflectExecutor = AgentExecutor(
            agent=Reflector_agent_calling,
            tools=self.tools,
            verbose=False,
            handle_parsing_errors=True,
        )

    def safe_invoke(self, input, retries=5, delay=2):
        for i in range(retries):
            try:
                return self.RewriteExecutor.invoke(input)
            except google.api_core.exceptions.ServiceUnavailable as e:
                print(f"[Retry {i+1}] Model overloaded. Waiting {delay}s...")
                time.sleep(delay)
        raise Exception("Model vẫn quá tải sau nhiều lần thử lại.")

    def safe_reflect_invoke(self, input, retries=5, delay=2):
        for i in range(retries):
            result = ""
            try:
                result = self.RewriteReflectExecutor.invoke(input)["output"]
                try:
                    result = result.strip()
                    # Bỏ ```json và ``` nếu có
                    if result.startswith("```json"):
                        result = result[len("```json") :].strip()
                    if result.endswith("```"):
                        result = result[:-3].strip()
                    result = json.loads(result)
                    return result
                except Exception as e:
                    print("Lỗi khi parse output từ reflector, xem lại phản hồi:")
                    return {
                        "verdict": "FAIL",
                        "feedback": "Do reflector phản hồi không đúng định dạng, không phải do Rewriter.",
                    }
            except google.api_core.exceptions.ServiceUnavailable as e:
                print(f"[Retry {i+1}] Model overloaded. Waiting {delay}s...")
                time.sleep(delay)
        raise Exception("Model vẫn quá tải sau nhiều lần thử lại.")

    def run(
        self, input: str, chat_history: list = None, max_iterations: int = 5
    ) -> str:

        print("=" * 50 + " REWRITER " + "=" * 50)

        feedback = None
        chat_history = chat_history or []

        for i in range(max_iterations):
            print(f"\nRewrite vòng {i+1}:")

            # Rewrite, truyền cả feedback nếu có
            input_message = [HumanMessage(content=input)]
            if feedback:
                input_message.append(
                    HumanMessage(content=f"Phản hồi từ người đánh giá: {feedback}")
                )

            response = self.safe_invoke(
                {"question": input_message, "chat_history": chat_history}
            )
            rewrite_text = response["output"]
            print(f"Câu rewrite: {rewrite_text}")

            # Reflect
            reflect_result = self.safe_reflect_invoke(
                {
                    "chat_history": chat_history,
                    "question": [HumanMessage(content=input)],
                    "rewrite_result": [AIMessage(content=rewrite_text)],
                }
            )

            verdict = reflect_result.get("verdict", "").upper()
            feedback = reflect_result.get("feedback", "")

            print(f"Reflector đánh giá: {verdict}")
            if verdict == "PASS":
                print("Câu hỏi đã được viết lại ổn.")
                return rewrite_text
            else:
                print(f"Feedback: {feedback}")

        print("Đã vượt quá số lần rewrite mà vẫn chưa đạt yêu cầu.")
        return rewrite_text


def main():
    rewritter = Rewriter("gemini-2.5-flash", "google-genai")

    chat_history = [
        HumanMessage(content="Tớ định đi Đà Lạt hoặc Sapa dịp Tết."),
        AIMessage(content="Cả hai nơi đều đẹp, nhưng Sapa có thể lạnh hơn."),
    ]
    query = "Vậy nếu Đà Lạt đông quá thì sao?"

    response = rewritter.run(query, chat_history=chat_history)
    print(response)


if __name__ == "__main__":
    main()
