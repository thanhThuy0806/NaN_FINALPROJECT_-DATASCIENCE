from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from llama_index.embeddings.ollama import OllamaEmbedding
from chromadb import Documents, Embeddings, EmbeddingFunction
from chromadb.utils.embedding_functions import register_embedding_function



class InsertRequest(BaseModel):
    name: str
    genres: List[str]=None
    description: str=None 
    rank: int=Field(ge=1)
    tag_list: List[str]


class RetrieveRequest(BaseModel):
    name: str
    genres: List[str] | None
    description: str | None 
    top_k: Optional[int]=Field(default=5, ge=1, le=10)
    top_tag: Optional[int]=Field(default=5, ge=1)
    top_genre: Optional[int]=Field(default=2, ge=1, le=5)


class RetrieveResponse(BaseModel):
    tag_list: List[str] | None
    genres_list: List[str] | None


@register_embedding_function
class CustomEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model: OllamaEmbedding):
        self.model = model
        self.model_name = model.model_name

    def __call__(self, input: Documents) -> Embeddings:
        documents = self.model.get_text_embedding_batch(input)
        return documents

    @staticmethod
    def name() -> str:
        return "custom-ef"

    @staticmethod
    def build_from_config(config: Dict[str, Any]) -> "EmbeddingFunction":
        reconstructed_model = OllamaEmbedding(model_name=config['model_name'])
        return CustomEmbeddingFunction(reconstructed_model)
    
    def get_config(self) -> Dict[str, Any]:
        return {"model_name": self.model_name}

    def _embed_query(self, input: Documents):
        return self.__call__(input)        





