"""检验报告 AI 解读（Celery 同步上下文执行）。"""
import json, re
from sqlalchemy import select, text as sql
from sqlalchemy.orm import Session
from app.models import AIStatus, LabOrder, LabReport, RagQueryLog
from app.services.llm import client as llm
from app.services.llm.prompts import REPORT_SYSTEM
from app.services.rag.retriever import tokenize

def _search_sync(db: Session, query: str, top_k: int = 4) -> list[dict]:
    rows = []; tokens = tokenize(query)
    if tokens:
        rows = db.execute(sql("""SELECT id, content FROM kb_chunks
            WHERE to_tsvector('simple', content_tokens) @@ plainto_tsquery('simple', :q)
            ORDER BY ts_rank(to_tsvector('simple', content_tokens), plainto_tsquery('simple', :q)) DESC LIMIT :n"""),
            {"q": tokens, "n": top_k}).fetchall()
    if not rows:
        try:
            from app.services.rag.embedder import embed_texts_sync
            [qvec] = embed_texts_sync([query])
            rows = db.execute(sql("""SELECT id, content FROM kb_chunks WHERE embedding IS NOT NULL
                ORDER BY embedding <=> CAST(:v AS vector) LIMIT :n"""), {"v": str(qvec), "n": top_k}).fetchall()
        except Exception: rows = []
    return [{"chunk_id": r.id, "content": r.content} for r in rows]

def rule_based_summary(raw_text: str) -> str:
    abnormal = [ln.strip() for ln in raw_text.splitlines() if re.search(r"[↑↓]|偏高|偏低|阳性|异常", ln)]
    body = ("检测到以下指标可能异常：\n- " + "\n- ".join(abnormal[:10])) if abnormal else "未从报告文本中识别到明显异常标记。"
    return json.dumps({"summary": body, "abnormal": [], "advice": "请携带报告咨询您的主诊医生。",
        "warning": "AI 解读服务暂不可用，以上为规则摘要，仅供参考。"}, ensure_ascii=False)

def interpret_report(db: Session, report_id: int) -> None:
    report = db.get(LabReport, report_id)
    if not report: return
    report.ai_status = AIStatus.processing; db.commit()
    order = db.get(LabOrder, report.lab_order_id)
    query = f"{order.item_name if order else ''} 检验指标解读 {report.raw_text[:200]}"
    chunks = _search_sync(db, query)
    context = "\n\n".join(f"[参考{i}] {c['content']}" for i, c in enumerate(chunks, 1)) or "（无）"
    db.add(RagQueryLog(user_id=None, query=query[:1000], chunk_ids=[c["chunk_id"] for c in chunks]))
    messages = [{"role": "system", "content": REPORT_SYSTEM.format(context=context)},
        {"role": "user", "content": f"检验项目：{order.item_name if order else '未知'}\n报告内容：\n{report.raw_text}"}]
    try:
        result = llm.chat_sync(messages, scene="report", json_mode=True)
        json.loads(result.content)
        report.ai_summary = result.content; report.ai_degraded = False; report.ai_status = AIStatus.done
    except Exception:
        report.ai_summary = rule_based_summary(report.raw_text); report.ai_degraded = True; report.ai_status = AIStatus.failed
    db.commit()
