from typing import List
from dotenv import load_dotenv

load_dotenv(override=True)

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "utils")))

from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.schema import AIMessage, HumanMessage
from prompt import RESPONDER_PROMPT
from tools.search_travel_info import search_travel_info
from tools.get_weather import get_weather
from tools.web_search import web_search
from tools.traveloka_api import search_hotels, search_planes, search_coaches
from tools.shopeefood_api import search_food
from tools.ticketbox_events import search_events_api

import time
import google.api_core.exceptions
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.api_tracker import create_callback


class Responder:
    def __init__(
        self,
        model_name: str,
        model_provider: str,
        temperature=0.0,
        conversation_id: str = None,
    ):
        """Create responder agent

        Args:
            model_name (str): name of the model used
            model_provider (str): name of the provider
            temperature (float, optional): adjust the level of creativity. Defaults to 0.
        """
        self.conversation_id = conversation_id or "default"
        self.callback = create_callback(self.conversation_id)
        self.llm_model = init_chat_model(
            model_name,
            model_provider=model_provider,
            temperature=temperature,
            callbacks=[self.callback],
        )

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", RESPONDER_PROMPT),
                MessagesPlaceholder(variable_name="question"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        self.tools = [
            search_travel_info,
            get_weather,
            web_search,
            search_hotels,
            search_planes,
            search_coaches,
            search_food,
            search_events_api,
        ]

        # Create agent from prompt template
        Agent_calling = create_tool_calling_agent(
            self.llm_model, tools=self.tools, prompt=prompt
        )

        self.TravelExecutor = AgentExecutor(
            agent=Agent_calling,
            tools=self.tools,
            verbose=False,
            handle_parsing_errors=True,
        )

    def safe_invoke(self, inputs, retries=5, delay=2):
        for i in range(retries):
            try:
                return self.TravelExecutor.invoke(inputs, config={"callbacks": [self.callback]})
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
                    # Lần retry cuối cùng thất bại
                    raise Exception(
                        f"Quota API Google Gemini đã hết. "
                        f"Free tier giới hạn 15 requests/phút. "
                        f"Vui lòng đợi {retry_delay:.0f} giây hoặc nâng cấp API key. "
                        f"Chi tiết: {error_msg[:200]}"
                    )
            except Exception as e:
                if i < retries - 1:
                    print(f"[Retry {i+1}/{retries}] Lỗi không mong đợi: {type(e).__name__}. Waiting {delay}s...")
                    time.sleep(delay)
                else:
                    raise
        
        raise Exception("Model vẫn quá tải hoặc gặp lỗi sau nhiều lần thử lại.")

    def run(self, query, depends_on_results=None):
        print("=" * 50 + " RESPONDER " + "=" * 50)

        required_keys = {"id", "description", "depends_on"}
        if not isinstance(query, dict):
            raise ValueError("Input 'query' phải là một dictionary.")
        if not required_keys.issubset(query.keys()):
            missing = required_keys - set(query.keys())
            raise ValueError(f"Thiếu trường trong input: {', '.join(missing)}")

        # Trích xuất câu hỏi cốt lõi
        user_request = query["description"]

        context = ""
        if depends_on_results:
            context = "\n".join([f"Task phụ thuộc: {r}" for r in depends_on_results])

        response = self.safe_invoke(
            {"question": [HumanMessage(content=context + "\n" + user_request)]}
        )

        agent_text_response = response.get(
            "output", "Xin lỗi, đã có lỗi xảy ra và tôi không thể tạo phản hồi."
        )

        final_output = {
            "id": query["id"],
            "description": query["description"],
            "depends_on": query["depends_on"],
            "response": agent_text_response.strip(),
        }

        return final_output


def main():
    responder = Responder("gemini-2.5-flash", "google-genai")
    query = {
        "id": "task_1",
        "description": "Các di tích lịch sử ở Hà Nội",
        "depends_on": [],
    }

    rsp = responder.run(query=query)
    print(rsp)


if __name__ == "__main__":
    main()
