from datetime import date, datetime, time, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import require_roles
from app.db.session import get_db
from app.models import LlmCallLog, RagQueryLog, Role, User
from app.schemas import LlmLogOut, StatsOut

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/llm-logs", response_model=list[LlmLogOut])
async def llm_logs(limit: int = 100, scene: str | None = None, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.admin))):
    stmt = select(LlmCallLog).order_by(LlmCallLog.id.desc()).limit(min(limit, 500))
    if scene: stmt = stmt.where(LlmCallLog.scene == scene)
    return list((await db.execute(stmt)).scalars())

@router.get("/rag-logs")
async def rag_logs(limit: int = 100, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.admin))):
    return [{"id": r.id, "user_id": r.user_id, "query": r.query, "chunk_ids": r.chunk_ids, "latency_ms": r.latency_ms,
        "created_at": r.created_at.isoformat()} for r in (await db.execute(select(RagQueryLog).order_by(RagQueryLog.id.desc()).limit(min(limit, 500)))).scalars()]

@router.get("/stats", response_model=StatsOut)
async def stats(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.admin))):
    total = await db.scalar(select(func.count(LlmCallLog.id))) or 0
    ok = await db.scalar(select(func.count()).where(LlmCallLog.status == "ok")) or 0
    err = await db.scalar(select(func.count()).where(LlmCallLog.status == "error")) or 0
    fb = await db.scalar(select(func.count()).where(LlmCallLog.status == "fallback")) or 0
    tokens = await db.scalar(select(func.coalesce(func.sum(LlmCallLog.prompt_tokens + LlmCallLog.completion_tokens), 0))) or 0
    avg_latency = await db.scalar(select(func.coalesce(func.avg(LlmCallLog.latency_ms), 0)).where(LlmCallLog.status.in_(["ok", "fallback"]))) or 0
    today_start = datetime.combine(date.today(), time.min).replace(tzinfo=timezone.utc)
    today = await db.scalar(select(func.count()).where(LlmCallLog.created_at >= today_start)) or 0
    scenes = (await db.execute(select(LlmCallLog.scene, func.count()).group_by(LlmCallLog.scene))).all()
    return StatsOut(total_calls=total, ok_calls=ok, error_calls=err, fallback_calls=fb, total_tokens=int(tokens),
        avg_latency_ms=round(float(avg_latency), 1), today_calls=today, scene_breakdown={s: c for s, c in scenes})
