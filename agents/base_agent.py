from abc import ABC, abstractmethod
from typing import List
from langchain.schema import BaseMessage
from langchain.chat_models import init_chat_model


class BaseAgent(ABC):
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        model_provider: str = "google-genai",
        temperature: float = 0.0,
    ):
        """Base Framework for all agents

        Args:
            model_name (str): name of the model used
            model_provider (str): name of the provider
            temperature (float, optional): adjust the level of creativity. Defaults to 0.
        """
        self.llm = init_chat_model(
            model=model_name,
            model_provider=model_provider,
            temperature=temperature,
        )

    @abstractmethod
    def safe_invoke(self, *args, **kwargs):
        """
        Args:
            Method for safe invoking.
        """
        pass

    @abstractmethod
    def run(self, *args, **kwargs):
        """
        Method for agent to execute the task.
        """
        pass
