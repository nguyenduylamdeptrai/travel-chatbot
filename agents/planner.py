from dotenv import load_dotenv

load_dotenv(override=True)
import time
import google.api_core.exceptions
from agents.base_agent import BaseAgent
from prompt import PLANNER_PROMPT
from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.schema import AIMessage, HumanMessage
import json
from langchain.schema import BaseMessage
from typing import List
from collections import defaultdict, deque
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.api_tracker import create_callback

# KHÔNG DÙNG TRONG PIPELINE


class Planner(BaseAgent):
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
                ("system", PLANNER_PROMPT),
                MessagesPlaceholder(variable_name="chat_history"),
                MessagesPlaceholder(variable_name="question"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        # Create agent from prompt template
        Agent_calling = create_tool_calling_agent(
            self.llm, tools=self.tools, prompt=prompt
        )

        self.PlanExecutor = AgentExecutor(
            agent=Agent_calling,
            tools=self.tools,
            verbose=False,
            handle_parsing_errors=True,
        )

    def safe_invoke(self, input, retries=5, delay=2):
        for i in range(retries):
            try:
                return self.PlanExecutor.invoke(input, config={"callbacks": [self.callback]})
            except google.api_core.exceptions.ServiceUnavailable as e:
                print(f"[Retry {i+1}] Model overloaded. Waiting {delay}s...")
                time.sleep(delay)
        raise Exception("Model vẫn quá tải sau nhiều lần thử lại.")

    def run(self, query: str, chat_history: List[BaseMessage]):
        print("=" * 50 + " PLANNER " + "=" * 50)

        response = self.safe_invoke(
            {"question": [HumanMessage(content=query)], "chat_history": chat_history}
        )
        try:
            result = response["output"].strip()

            # Bỏ ```json và ``` nếu có
            if result.startswith("```json"):
                result = result[len("```json") :].strip()
            if result.endswith("```"):
                result = result[:-3].strip()
            tasks = json.loads(result)
            sorted_tasks = self.topological_sort(tasks)
            return sorted_tasks
        except Exception as e:
            print("Lỗi parse JSON:", e)
            return [
                {"id": "task_1", "description": response["output"], "depends_on": []}
            ]

    def topological_sort(self, tasks: List[dict]) -> List[dict]:
        """
        Sắp xếp các task theo thứ tự topo dựa vào trường depends_on.

        Args:
            tasks (List[dict]): Danh sách các task với trường depends_on.

        Returns:
            List[dict]: Danh sách các task đã được sắp xếp theo thứ tự topo.
        """
        # Xây dựng đồ thị phụ thuộc
        graph = defaultdict(list)
        in_degree = defaultdict(int)

        for task in tasks:
            task_id = task["id"]
            depends_on = task["depends_on"]

            for dependency in depends_on:
                graph[dependency].append(task_id)
                in_degree[task_id] += 1

            if task_id not in in_degree:
                in_degree[task_id] = 0

        # Tìm các node không có phụ thuộc (in_degree = 0)
        queue = deque([task["id"] for task in tasks if in_degree[task["id"]] == 0])
        sorted_tasks = []
        task_map = {task["id"]: task for task in tasks}

        # Thực hiện sắp xếp topo
        while queue:
            current = queue.popleft()
            sorted_tasks.append(task_map[current])

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Kiểm tra nếu có chu trình
        if len(sorted_tasks) != len(tasks):
            return tasks
        return sorted_tasks


def main():
    planner = Planner("gemini-2.5-flash", "google-genai")
    chat_history = [
        HumanMessage(content="Xin chào"),
        AIMessage(content="Xin chào, bạn muốn làm gì hôm nay?"),
    ]
    query = "Các địa điểm đi du lịch hay ho ở miền Bắc?"
    response = planner.run(query=query, chat_history=chat_history)
    print(response)


if __name__ == "__main__":
    main()
