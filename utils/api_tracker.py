from typing import Dict
from collections import defaultdict
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
import threading

# Thread-safe usage store per conversation
_usage: Dict[str, Dict[str, int]] = defaultdict(
    lambda: {"api_calls": 0, "prompt_tokens": 0, "completion_tokens": 0}
)
_lock = threading.Lock()


def increment_api_call(conversation_id: str):
    with _lock:
        _usage[conversation_id]["api_calls"] += 1


class GeminiUsageCallback(BaseCallbackHandler):
    """Callback to track Gemini API usage per conversation."""

    def __init__(self, conversation_id: str):
        super().__init__()
        self.conversation_id = conversation_id

    def on_llm_start(self, serialized, prompts, **kwargs):
        increment_api_call(self.conversation_id)

    def on_llm_end(self, response: LLMResult, **kwargs):
        with _lock:
            if response and hasattr(response, "llm_output") and response.llm_output:
                usage = response.llm_output.get("token_usage", {})
                _usage[self.conversation_id]["prompt_tokens"] += usage.get(
                    "prompt_tokens", 0
                )
                _usage[self.conversation_id]["completion_tokens"] += usage.get(
                    "completion_tokens", 0
                )


def create_callback(conversation_id: str) -> GeminiUsageCallback:
    return GeminiUsageCallback(conversation_id or "default")


def get_usage(conversation_id: str) -> Dict[str, int]:
    with _lock:
        return _usage[conversation_id].copy()

