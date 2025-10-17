import openai

from . import config

client = openai.OpenAI(api_key=config.OPENAI_API_KEY)


def embed(texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(
        model=config.EMBEDDING_MODEL,
        input=texts
    )
    # return a list of results, each one with .embedding:
    # {data: [{embedding: [1,2,3...]}, {embedding: [1,2,3...]}, {embedding: [1,2,3...]}]}
    return [item.embedding for item in response.data]
