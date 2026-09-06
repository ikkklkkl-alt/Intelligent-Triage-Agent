import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import require_roles
from app.db.session import get_db
from app.models import Role, TriageMessage, TriageSession, User
from app.schemas import TriageMessageIn, TriageSessionOut
from app.services.triage import run_triage_turn

router = APIRouter(prefix="/triage", tags=["triage"])

@router.get("/sessions", response_model=list[TriageSessionOut])
async def list_sessions(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.patient))):
    return list((await db.execute(select(TriageSession).where(TriageSession.patient_id == user.id)
        .order_by(TriageSession.id.desc()))).scalars())

@router.post("/sessions", response_model=TriageSessionOut)
async def create_session(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.patient))):
    session = TriageSession(patient_id=user.id); db.add(session); await db.commit(); await db.refresh(session); return session

@router.get("/sessions/{session_id}", response_model=TriageSessionOut)
async def get_session(session_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.patient))):
    session = await db.get(TriageSession, session_id)
    if not session or session.patient_id != user.id: raise HTTPException(404, "会话不存在")
    return session

@router.get("/sessions/{session_id}/messages")
async def list_messages(session_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.patient))):
    session = await db.get(TriageSession, session_id)
    if not session or session.patient_id != user.id: raise HTTPException(404, "会话不存在")
    return [{"role": m.role, "content": m.content} for m in (await db.execute(select(TriageMessage)
        .where(TriageMessage.session_id == session_id).order_by(TriageMessage.id))).scalars()]

@router.post("/sessions/{session_id}/messages")
async def send_message(session_id: int, data: TriageMessageIn, db: AsyncSession = Depends(get_db),
                       user: User = Depends(require_roles(Role.patient))):
    session = await db.get(TriageSession, session_id)
    if not session or session.patient_id != user.id: raise HTTPException(404, "会话不存在")
    async def gen():
        async for event in run_triage_turn(db, session, data.content, user.id):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
