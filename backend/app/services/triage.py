"""智能分诊工作流：审核 -> RAG -> 多轮上下文 -> 流式输出 -> 结构化结论 -> 规则兜底。"""
import json, re
from collections.abc import AsyncGenerator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models import Department, TriageMessage, TriageSession, TriageStatus
from app.schemas import TriageResult
from app.services.llm import client as llm
from app.services.llm.moderation import check_input
from app.services.llm.prompts import TRIAGE_FALLBACK_DEFAULT, TRIAGE_FALLBACK_RULES, TRIAGE_OFF_TOPIC_REPLY, OFF_TOPIC_PATTERNS, TRIAGE_SYSTEM
from app.services.rag.retriever import build_context, hybrid_search

RESULT_RE = re.compile(r"<TRIAGE_RESULT>(.*?)</TRIAGE_RESULT>", re.S)
MAX_HISTORY = 12

def rule_based_triage(text: str, departments: list[str]) -> TriageResult:
    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, text, re.I):
            return TriageResult(department="未分诊", urgency="low", advice=TRIAGE_OFF_TOPIC_REPLY, degraded=True)
    for pattern, dept in TRIAGE_FALLBACK_RULES:
        if re.search(pattern, text) and dept in departments:
            return TriageResult(department=dept, urgency="medium", advice=f"根据症状关键词建议挂 {dept}，具体以医生面诊为准。", degraded=True)
    fallback = TRIAGE_FALLBACK_DEFAULT if TRIAGE_FALLBACK_DEFAULT in departments else departments[0]
    return TriageResult(department=fallback, urgency="medium", advice="暂时无法智能判断科室，建议先挂全科/门诊由医生分诊。", degraded=True)

def parse_result(full_text: str) -> TriageResult | None:
    m = RESULT_RE.search(full_text)
    if not m: return None
    try:
        data = json.loads(m.group(1)); data.setdefault("degraded", False)
        return TriageResult(**data)
    except Exception: return None

async def run_triage_turn(db: AsyncSession, session: TriageSession, user_text: str, user_id: int) -> AsyncGenerator[dict, None]:
    ok, block_msg = check_input(user_text)
    if not ok:
        db.add(TriageMessage(session_id=session.id, role="user", content=user_text))
        db.add(TriageMessage(session_id=session.id, role="assistant", content=block_msg))
        await db.commit(); yield {"type": "delta", "content": block_msg}; yield {"type": "done"}; return
    departments = list((await db.execute(select(Department.name))).scalars())
    history = list((await db.execute(select(TriageMessage).where(TriageMessage.session_id == session.id)
        .order_by(TriageMessage.id.desc()).limit(MAX_HISTORY))).scalars())[::-1]
    rag_results = await hybrid_search(db, user_text, user_id=user_id)
    system = TRIAGE_SYSTEM.format(app_name=settings.APP_NAME, departments="、".join(departments), context=build_context(rag_results) or "（无）")
    messages = [{"role": "system", "content": system}]
    messages += [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": user_text})
    db.add(TriageMessage(session_id=session.id, role="user", content=user_text)); await db.commit()
    full = ""
    try:
        async for delta in llm.stream_chat(messages, scene="triage", user_id=user_id):
            full += delta; yield {"type": "delta", "content": delta}
    except llm.BudgetExceeded as e:
        yield {"type": "error", "message": str(e)}; return
    except llm.LlmError:
        result = rule_based_triage(user_text, departments)
        session.result_json = result.model_dump(); session.status = TriageStatus.completed
        reply = f"（AI 服务暂时不可用，已启用规则分诊）建议科室：{result.department}。{result.advice}"
        db.add(TriageMessage(session_id=session.id, role="assistant", content=reply)); await db.commit()
        yield {"type": "delta", "content": reply}; yield {"type": "result", "result": result.model_dump()}; yield {"type": "done"}; return
    result = parse_result(full)
    visible_text = RESULT_RE.sub("", full).strip()
    db.add(TriageMessage(session_id=session.id, role="assistant", content=visible_text or full))
    if result:
        session.result_json = result.model_dump(); session.status = TriageStatus.completed
        await db.commit(); yield {"type": "result", "result": result.model_dump()}
    else: await db.commit()
    yield {"type": "done"}
