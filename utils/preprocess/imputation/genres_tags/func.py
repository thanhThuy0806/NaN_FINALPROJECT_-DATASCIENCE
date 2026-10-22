from typing import List
from collections import Counter
from utils.preprocess.imputation.genres_tags.schemas import InsertRequest, RetrieveRequest, RetrieveResponse
from utils.preprocess.imputation.genres_tags.core import collection



def insert_tag_batch(requests: List[InsertRequest]) -> None:
    texts = []
    ids = []
    metadatas = []

    for req in requests:
        # Construct the text block
        text = '\n'.join([req.name, ','.join(req.genres), req.description])
        texts.append(text)
        ids.append('id_' + str(req.rank))
        
        # Serialize list to string for ChromaDB
        metadatas.append({"tags": ','.join(req.tag_list), "genres": ','.join(req.genres)})

    # Insert the entire batch in one network call
    collection.add(
        documents=texts,
        metadatas=metadatas,
        ids=ids,
    )


def retrieve_tag_list(request: RetrieveRequest) -> RetrieveResponse:
    text = '\n'.join([request.name, ','.join(request.genres), request.description])
    
    data = collection.query(
        query_texts=[text],
        n_results=request.top_k
    )

    # Iterate over the retrieved neighbors to compile the tags
    aggregated_tags = []
    aggregated_genres = []

    for metadata_dict in data['metadatas'][0]:
        # Split the string back into a list and append
        tags = metadata_dict['tags'].split(',')
        genres = metadata_dict['genres'].split(',')

        aggregated_tags.extend(tags)
        aggregated_genres.extend(genres)

    tags_count = Counter(aggregated_tags)
    genres_count = Counter(aggregated_genres)

    top_tag_tuples = tags_count.most_common(request.top_tag)
    top_genre_tuples = genres_count.most_common(request.top_genre)

    unique_tags = [tag for tag, _ in top_tag_tuples]
    unique_genres = [genre for genre, _ in top_genre_tuples]

    return RetrieveResponse(tag_list=unique_tags,
                            genres_list=unique_genres)






