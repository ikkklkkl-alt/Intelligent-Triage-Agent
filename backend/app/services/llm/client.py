"""统一 LLM 服务层：Token 预算控制、调用日志、超时重试、多供应商降级链、SSE 流式。"""
import asyncio, json, time
from collections.abc import AsyncGenerator
from dataclasses import dataclass
import httpx
from app.core.config import settings
from app.db.session import async_session_factory, get_sync_db
from app.models import LlmCallLog
from app.services.llm.budget import check_budget, consume_budget

class LlmError(Exception): pass
class BudgetExceeded(LlmError): pass

@dataclass
class Provider:
    base_url: str; api_key: str; model: str

@dataclass
class LlmResult:
    content: str; model: str; prompt_tokens: int = 0; completion_tokens: int = 0; fallback_used: bool = False

def _providers() -> list[Provider]:
    chain = [Provider(settings.LLM_BASE_URL, settings.LLM_API_KEY, settings.LLM_MODEL)]
    if settings.LLM_FALLBACK_API_KEY:
        chain.append(Provider(settings.LLM_FALLBACK_BASE_URL, settings.LLM_FALLBACK_API_KEY, settings.LLM_FALLBACK_MODEL))
    return chain

def _payload(p: Provider, messages: list[dict], json_mode: bool, stream: bool, temperature: float) -> dict:
    body: dict = {"model": p.model, "messages": messages, "temperature": temperature, "stream": stream}
    if json_mode: body["response_format"] = {"type": "json_object"}
    if stream: body["stream_options"] = {"include_usage": True}
    return body

async def _log(user_id, scene, model, pt, ct, latency_ms, status, error=None):
    try:
        async with async_session_factory() as db:
            db.add(LlmCallLog(user_id=user_id, scene=scene, model=model, prompt_tokens=pt,
                completion_tokens=ct, latency_ms=latency_ms, status=status, error=(error or "")[:2000] or None))
            await db.commit()
    except Exception: pass

async def chat(messages: list[dict], *, scene: str, user_id: int | None = None,
               json_mode: bool = False, temperature: float = 0.3) -> LlmResult:
    if user_id is not None:
        ok, _ = await check_budget(user_id)
        if not ok:
            await _log(user_id, scene, "-", 0, 0, 0, "blocked", "daily token budget exceeded")
            raise BudgetExceeded("今日 AI 使用额度已用完，请明天再试")
    last_err = None
    for idx, p in enumerate(_providers()):
        for attempt in range(settings.LLM_MAX_RETRIES + 1):
            start = time.monotonic()
            try:
                async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
                    resp = await client.post(f"{p.base_url.rstrip('/')}/chat/completions",
                        headers={"Authorization": f"Bearer {p.api_key}"}, json=_payload(p, messages, json_mode, False, temperature))
                    resp.raise_for_status(); data = resp.json()
                latency = int((time.monotonic() - start) * 1000)
                usage = data.get("usage") or {}
                result = LlmResult(content=data["choices"][0]["message"]["content"], model=p.model,
                    prompt_tokens=usage.get("prompt_tokens", 0), completion_tokens=usage.get("completion_tokens", 0), fallback_used=idx > 0)
                if user_id is not None: await consume_budget(user_id, result.prompt_tokens + result.completion_tokens)
                await _log(user_id, scene, p.model, result.prompt_tokens, result.completion_tokens, latency, "fallback" if idx > 0 else "ok")
                return result
            except Exception as e:
                last_err = e
                await _log(user_id, scene, p.model, 0, 0, int((time.monotonic() - start) * 1000), "error", repr(e))
                if attempt < settings.LLM_MAX_RETRIES: await asyncio.sleep(0.5 * (attempt + 1))
    raise LlmError(f"所有 LLM 供应商均调用失败: {last_err!r}")

async def stream_chat(messages: list[dict], *, scene: str, user_id: int | None = None,
                      temperature: float = 0.5) -> AsyncGenerator[str, None]:
    if user_id is not None:
        ok, _ = await check_budget(user_id)
        if not ok: raise BudgetExceeded("今日 AI 使用额度已用完，请明天再试")
    last_err = None
    for idx, p in enumerate(_providers()):
        start = time.monotonic(); emitted = False; pt = ct = 0
        try:
            async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
                async with client.stream("POST", f"{p.base_url.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {p.api_key}"}, json=_payload(p, messages, False, True, temperature)) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.startswith("data:"): continue
                        chunk = line[5:].strip()
                        if chunk == "[DONE]": break
                        obj = json.loads(chunk)
                        if obj.get("usage"): pt = obj["usage"].get("prompt_tokens", 0); ct = obj["usage"].get("completion_tokens", 0)
                        choices = obj.get("choices") or []
                        if choices:
                            delta = choices[0].get("delta", {}).get("content")
                            if delta: emitted = True; yield delta
            latency = int((time.monotonic() - start) * 1000)
            if user_id is not None: await consume_budget(user_id, pt + ct)
            await _log(user_id, scene, p.model, pt, ct, latency, "fallback" if idx > 0 else "ok")
            return
        except Exception as e:
            last_err = e
            await _log(user_id, scene, p.model, pt, ct, int((time.monotonic() - start) * 1000), "error", repr(e))
            if emitted: raise LlmError(f"流式输出中断: {e!r}") from e
    raise LlmError(f"所有 LLM 供应商均调用失败: {last_err!r}")

def chat_sync(messages, *, scene, user_id=None, json_mode=False, temperature=0.3) -> LlmResult:
    last_err = None
    for idx, p in enumerate(_providers()):
        for attempt in range(settings.LLM_MAX_RETRIES + 1):
            start = time.monotonic()
            try:
                with httpx.Client(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
                    resp = client.post(f"{p.base_url.rstrip('/')}/chat/completions",
                        headers={"Authorization": f"Bearer {p.api_key}"}, json=_payload(p, messages, json_mode, False, temperature))
                    resp.raise_for_status(); data = resp.json()
                usage = data.get("usage") or {}
                _log_sync(user_id, scene, p.model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0),
                    int((time.monotonic() - start) * 1000), "fallback" if idx > 0 else "ok")
                return LlmResult(content=data["choices"][0]["message"]["content"], model=p.model,
                    prompt_tokens=usage.get("prompt_tokens", 0), completion_tokens=usage.get("completion_tokens", 0), fallback_used=idx > 0)
            except Exception as e:
                last_err = e
                _log_sync(user_id, scene, p.model, 0, 0, int((time.monotonic() - start) * 1000), "error", repr(e))
                if attempt < settings.LLM_MAX_RETRIES: time.sleep(0.5 * (attempt + 1))
    raise LlmError(f"所有 LLM 供应商均调用失败: {last_err!r}")

def _log_sync(user_id, scene, model, pt, ct, latency_ms, status, error=None):
    try:
        db = get_sync_db()
        try:
            db.add(LlmCallLog(user_id=user_id, scene=scene, model=model, prompt_tokens=pt,
                completion_tokens=ct, latency_ms=latency_ms, status=status, error=(error or "")[:2000] or None))
            db.commit()
        finally: db.close()
    except Exception: pass
