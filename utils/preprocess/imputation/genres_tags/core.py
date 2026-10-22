import chromadb
from utils.preprocess.imputation.genres_tags.model import embed_func



client = chromadb.HttpClient(host="localhost", port=8000)

collection = client.get_or_create_collection(
    name="steam-games-collection",
    embedding_function=embed_func
)






