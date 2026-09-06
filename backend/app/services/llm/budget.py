from datetime import date
import redis.asyncio as aioredis
from app.core.config import settings

_redis: aioredis.Redis | None = None

def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis

def _key(user_id: int) -> str:
    return f"llm:budget:{user_id}:{date.today().isoformat()}"

async def check_budget(user_id: int) -> tuple[bool, int]:
    try:
        used = int(await get_redis().get(_key(user_id)) or 0)
    except Exception:
        return True, 0
    return used < settings.LLM_DAILY_TOKEN_BUDGET, used

async def consume_budget(user_id: int, tokens: int) -> None:
    try:
        r = get_redis(); key = _key(user_id)
        await r.incrby(key, tokens); await r.expire(key, 60 * 60 * 26)
    except Exception:
        pass
