from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, AIMessage
from settings import settings, get_settings
from langsmith import traceable

settings = get_settings()

class LLMClient:

    def __init__(
            self,
            model: str =  "google/gemma-4-e4b",
            temperature: float = 0.5,
    ) -> None:
        self._llm  =  ChatOpenAI(
            model = model or settings.default_model,
            base_url = settings.base_url,
            api_key = settings.api_key,
            temperature = temperature
        )
    @traceable(
        name="LLMClient.chat",
        run_type="chain",
    )
    def chat(self, messages: list[dict[str, Any]]) -> str:
        response: AIMessage = self._llm.invoke(
            messages,
            config={
                "run_name": "chat-model-invoke",
                "metadata": {
                    "model_name": self._model_name,
                    "client": "LLMClient",
                },
                "tags": ["chat", "llm-client"],
            },
        )

        return str(response.content)

    def get_model_name(self) -> str:
        return self._llm.model_name



