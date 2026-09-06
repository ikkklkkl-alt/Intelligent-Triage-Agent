from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import require_roles
from app.db.session import get_db
from app.models import KbChunk, KbDocument, Role, User
from app.schemas import KbDocumentIn, KbDocumentOut
from app.services.rag.retriever import hybrid_search
from app.tasks.kb_tasks import ingest_document

router = APIRouter(prefix="/kb", tags=["kb"])

@router.post("/documents", response_model=KbDocumentOut)
async def create_document(data: KbDocumentIn, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.admin))):
    doc = KbDocument(title=data.title, source=data.source, content=data.content); db.add(doc); await db.commit(); await db.refresh(doc)
    ingest_document.delay(doc.id); return doc

@router.get("/documents", response_model=list[KbDocumentOut])
async def list_documents(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.admin))):
    return list((await db.execute(select(KbDocument).order_by(KbDocument.id.desc()))).scalars())

@router.post("/documents/{doc_id}/reingest", response_model=KbDocumentOut)
async def reingest(doc_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.admin))):
    doc = await db.get(KbDocument, doc_id)
    if not doc: raise HTTPException(404, "文档不存在")
    ingest_document.delay(doc.id); return doc

@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.admin))):
    doc = await db.get(KbDocument, doc_id)
    if not doc: raise HTTPException(404, "文档不存在")
    await db.execute(delete(KbChunk).where(KbChunk.document_id == doc_id)); await db.delete(doc); await db.commit()
    return {"message": "已删除"}

@router.get("/search")
async def search(q: str, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.admin))):
    return await hybrid_search(db, q, user_id=user.id)
