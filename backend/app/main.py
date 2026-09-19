from contextlib import asynccontextmanager
from datetime import date
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import Base, engine
import app.models  # noqa: F401

logger = logging.getLogger("imcs")

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    if settings.SEED_ON_STARTUP:
        from app.db.seed import seed
        await seed()
    # LLM API Key 检查
    from app.services.llm.client import is_llm_configured
    if not is_llm_configured():
        logger.warning("⚠️  LLM_API_KEY 未配置，智能分诊将使用规则模式（非 AI）。"
                        "请在 .env 中设置 LLM_API_KEY 以启用 AI 分诊。")
    else:
        logger.info("✅ LLM API Key 已配置，AI 分诊已启用。")
    yield

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Authorization", "Content-Type"])
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "today": str(date.today())}
