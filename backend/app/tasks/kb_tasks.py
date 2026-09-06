from app.db.session import get_sync_db
from app.models import DocStatus, KbChunk, KbDocument
from app.services.rag.chunker import split_text
from app.services.rag.retriever import tokenize
from app.tasks.celery_app import celery_app

@celery_app.task(name="kb.ingest", bind=True, max_retries=2, default_retry_delay=10)
def ingest_document(self, document_id: int) -> str:
    db = get_sync_db()
    try:
        doc = db.get(KbDocument, document_id)
        if not doc: return "not_found"
        doc.status = DocStatus.processing; db.commit()
        db.query(KbChunk).filter(KbChunk.document_id == doc.id).delete()
        pieces = split_text(doc.content)
        try:
            from app.services.rag.embedder import embed_texts_sync
            embeddings = embed_texts_sync(pieces)
        except Exception:
            embeddings = [None] * len(pieces)
        for i, piece in enumerate(pieces):
            db.add(KbChunk(document_id=doc.id, seq=i, content=piece, content_tokens=tokenize(piece), embedding=embeddings[i]))
        doc.chunk_count = len(pieces); doc.status = DocStatus.ready; doc.error = None; db.commit()
        return f"ok:{len(pieces)}"
    except Exception as e:
        db.rollback(); doc = db.get(KbDocument, document_id)
        if doc: doc.status = DocStatus.failed; doc.error = repr(e)[:1000]; db.commit()
        raise self.retry(exc=e)
    finally: db.close()
