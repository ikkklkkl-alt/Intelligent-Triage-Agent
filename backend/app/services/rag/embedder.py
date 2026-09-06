import httpx
from app.core.config import settings

class EmbeddingError(Exception): pass

def _url(): return f"{settings.EMBEDDING_BASE_URL.rstrip('/')}/embeddings"
def _headers(): return {"Authorization": f"Bearer {settings.EMBEDDING_API_KEY}"}

async def embed_texts(texts: list[str]) -> list[list[float]]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(_url(), headers=_headers(), json={"model": settings.EMBEDDING_MODEL, "input": texts})
        resp.raise_for_status(); data = resp.json()["data"]
    return [item["embedding"] for item in sorted(data, key=lambda x: x["index"])]

def embed_texts_sync(texts: list[str], batch_size: int = 10) -> list[list[float]]:
    out = []
    with httpx.Client(timeout=60) as client:
        for i in range(0, len(texts), batch_size):
            resp = client.post(_url(), headers=_headers(), json={"model": settings.EMBEDDING_MODEL, "input": texts[i:i+batch_size]})
            resp.raise_for_status(); data = resp.json()["data"]
            out.extend(item["embedding"] for item in sorted(data, key=lambda x: x["index"]))
    return out
