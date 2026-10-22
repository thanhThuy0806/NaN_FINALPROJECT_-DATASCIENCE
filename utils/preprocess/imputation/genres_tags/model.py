from llama_index.embeddings.ollama import OllamaEmbedding
from utils.preprocess.imputation.genres_tags.schemas import CustomEmbeddingFunction


embed_model = OllamaEmbedding(
    model_name="nomic-embed-text-v2-moe",
    base_url="http://localhost:11434"
)


embed_func = CustomEmbeddingFunction(model=embed_model)






