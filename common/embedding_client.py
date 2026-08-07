from langchain_openai import OpenAIEmbeddings

from settings import get_settings

settings = get_settings()

class EmbeddingClient():

    def __init__(self, model: str = ""):
        self._embedding = OpenAIEmbeddings(
            model= model or settings.embedding_model,
            base_url=settings.base_url,
            api_key=settings.api_key,
            check_embedding_ctx_length=False
        )

    def get_size(self, text:str) -> int:
        return len(self.embed_text(text))
        return len(self._embedding.embed_query(text))

    def embed_query(self, text:str)-> list:
        return self._embedding.embed_query(text)

    def embed_documents(self, text:list[str])-> list[float]:
        return self._embedding.embed_documents(text)

    def get_model_name(self) -> str:
        return self._embedding.model