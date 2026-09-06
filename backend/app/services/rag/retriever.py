import time
import jieba
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models import RagQueryLog
from app.services.rag.embedder import embed_texts

def tokenize(content: str) -> str:
    return " ".join(w.strip() for w in jieba.cut_for_search(content) if w.strip())

async def hybrid_search(db: AsyncSession, query: str, *, top_k: int | None = None, user_id: int | None = None) -> list[dict]:
    start = time.monotonic(); top_k = top_k or settings.RAG_TOP_K; n = settings.RAG_CANDIDATES
    vec_rows = []
    try:
        [qvec] = await embed_texts([query])
        res = await db.execute(text("""
            SELECT id, document_id, content, embedding <=> CAST(:qvec AS vector) AS dist
            FROM kb_chunks WHERE embedding IS NOT NULL ORDER BY dist LIMIT :n"""),
            {"qvec": str(qvec), "n": n})
        vec_rows = res.fetchall()
    except Exception: pass
    fts_rows = []
    tokens = tokenize(query)
    if tokens:
        res = await db.execute(text("""
            SELECT id, document_id, content, ts_rank(to_tsvector('simple', content_tokens), plainto_tsquery('simple', :q)) AS rank
            FROM kb_chunks WHERE to_tsvector('simple', content_tokens) @@ plainto_tsquery('simple', :q)
            ORDER BY rank DESC LIMIT :n"""),
            {"q": tokens, "n": n})
        fts_rows = res.fetchall()
    k = settings.RAG_RRF_K
    fused: dict[int, dict] = {}
    for rank, row in enumerate(vec_rows, start=1):
        fused.setdefault(row.id, {"chunk_id": row.id, "document_id": row.document_id, "content": row.content, "score": 0.0})
        fused[row.id]["score"] += 1.0 / (k + rank)
    for rank, row in enumerate(fts_rows, start=1):
        fused.setdefault(row.id, {"chunk_id": row.id, "document_id": row.document_id, "content": row.content, "score": 0.0})
        fused[row.id]["score"] += 1.0 / (k + rank)
    results = sorted(fused.values(), key=lambda x: x["score"], reverse=True)[:top_k]
    db.add(RagQueryLog(user_id=user_id, query=query[:1000], chunk_ids=[r["chunk_id"] for r in results],
                       latency_ms=int((time.monotonic() - start) * 1000)))
    await db.commit()
    return results

def build_context(results: list[dict], max_chars: int = 2400) -> str:
    parts, total = [], 0
    for i, r in enumerate(results, 1):
        piece = f"[参考{i}] {r['content']}"
        if total + len(piece) > max_chars: break
        parts.append(piece); total += len(piece)
    return "\n\n".join(parts)
