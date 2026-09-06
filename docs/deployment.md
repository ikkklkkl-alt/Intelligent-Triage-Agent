# IMCS 智能医疗预约诊疗系统 — 部署与排障指南

> 本文档覆盖从零开始搭建 IMCS 开发/测试环境，以及生产环境加固的完整流程。

---

## 1. 环境要求

### 1.1 基础依赖

| 组件 | 最低版本 | 说明 |
|------|----------|------|
| Docker | 24.0+ | 含 BuildKit，`docker buildx` 可选 |
| Docker Compose | v2.20+ | 使用 `docker compose`（非 `docker-compose`） |
| Git | 2.30+ | 克隆仓库 |

如选择手动部署（不使用 Docker），还需要：

| 组件 | 版本 |
|------|------|
| Python | 3.11+ |
| PostgreSQL | 15+，需启用 `pgvector` 扩展 |
| Redis | 7.0+ |
| Node.js | 18+（前端构建） |

### 1.2 API Key 申请

系统依赖以下外部服务，部署前须准备对应的 Key：

| 服务 | 用途 | 申请地址 | 环境变量 |
|------|------|----------|----------|
| DeepSeek | 主 LLM（对话、分诊、报告解读） | https://platform.deepseek.com | `DEEPSEEK_API_KEY` |
| 通义千问（Qwen） | LLM 降级备用 | https://dashscope.console.aliyun.com | `DASHSCOPE_API_KEY` |
| Embedding 服务 | 知识库文档向量化（可选，不配置则走 TF-IDF 降级） | 同 DeepSeek 或自建 | `EMBEDDING_API_KEY` |

> **安全提示**：API Key 仅存放在 `.env` 文件中，禁止提交到 Git 仓库。`.env.example` 中的值均为占位符。

---

## 2. 快速启动（Docker Compose）

```bash
# 1. 克隆项目
git clone https://github.com/your-org/imcs.git
cd imcs

# 2. 创建环境配置
cp .env.example .env
# 编辑 .env，填入上一节申请的 API Key
vi .env

# 3. 一键启动
docker compose up -d

# 4. 检查服务状态
docker compose ps

# 5. 访问
# 前端：  http://localhost:8080
# API 文档：http://localhost:8010/api/docs
# Flower（Celery 监控）：http://localhost:5555
```

`docker compose up` 会依次拉起以下容器：

| 服务名 | 镜像 | 端口 | 职责 |
|--------|------|------|------|
| `db` | pgvector/pgvector:pg15 | 5432 | PostgreSQL + pgvector |
| `redis` | redis:7-alpine | 6379 | 缓存、消息队列、Token 预算计数 |
| `backend` | 自建 | 8000 | FastAPI 应用 |
| `celery-worker` | 同 backend | — | 异步任务处理 |
| `celery-beat` | 同 backend | — | 定时任务调度 |
| `frontend` | node:18 + nginx | 3000 | 前端 SPA |
| `flower` | mher/flower | 5555 | Celery 任务监控面板 |

首次启动时，`backend` 服务会自动执行 Alembic 数据库迁移，无需手动建表。

---

## 3. 手动部署（非 Docker）

适合已有基础设施或需要调试底层服务的场景。

### 3.1 数据库准备

```bash
# 安装 pgvector 扩展
sudo apt install postgresql-15-pgvector  # Ubuntu
# 或
CREATE EXTENSION IF NOT EXISTS vector;   -- PostgreSQL 内

# 创建数据库和用户
sudo -u postgres psql
CREATE USER imcs WITH PASSWORD 'your_password';
CREATE DATABASE imcs_db OWNER imcs;
\q
```

### 3.2 后端启动

```bash
cd backend

# 创建虚拟环境
python3.11 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
vi .env

# 数据库迁移
alembic upgrade head

# 启动 API 服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 启动 Celery Worker（另开终端）
celery -A app.core.celery_app worker --loglevel=info --concurrency=4

# 启动 Celery Beat 定时调度（另开终端）
celery -A app.core.celery_app beat --loglevel=info
```

### 3.3 前端构建

```bash
cd frontend
npm install
npm run build
# 产物在 dist/ 目录，配置 nginx 或其他静态服务器指向该目录
```

### 3.4 Redis

```bash
# macOS
brew install redis && brew services start redis

# Ubuntu
sudo apt install redis-server && sudo systemctl start redis

# 验证连接
redis-cli ping  # 应返回 PONG
```

---

## 4. 常见问题排查

### 4.1 数据库连接失败

**症状**：启动报错 `ConnectionRefusedError` 或 `could not connect to server`

```
排查步骤：
1. 确认 PostgreSQL 服务运行中
   systemctl status postgresql  # Linux
   brew services list           # macOS

2. 检查 .env 中的 DATABASE_URL 格式
   正确格式：postgresql+asyncpg://user:password@host:5432/db_name
   常见错误：漏写 +asyncpg、端口号不对、密码含特殊字符未 URL 编码

3. 检查 pg_hba.conf 是否允许对应 IP 段连接
   # Docker 环境下常见：容器网络与宿主机 PostgreSQL 不通
   # 解决：将 host 改为 host.docker.internal 或使用 Docker 网络

4. 确认 pgvector 扩展已安装
   psql -d imcs_db -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

### 4.2 Celery Worker 不启动

**症状**：`celery worker` 命令卡住或报 `ConnectionError`

```
排查步骤：
1. 确认 Redis 可达
   redis-cli -h $REDIS_HOST -p $REDIS_PORT ping

2. 检查 CELERY_BROKER_URL 配置
   格式：redis://host:port/0
   注意：Docker 内部使用服务名 redis，外部使用 localhost

3. 检查模块导入错误
   celery -A app.core.celery_app worker --loglevel=debug
   # debug 模式会输出完整堆栈

4. Worker 数量受限
   # Docker 默认无 CPU 限制，手动部署时 --concurrency 不要超过 CPU 核心数
   celery worker --concurrency=$(nproc)
```

### 4.3 LLM 调用超时

**症状**：分诊或报告解读长时间无响应，日志中出现 `TimeoutError` 或 `APITimeoutError`

```
排查步骤：
1. 检查 API Key 是否有效
   curl https://api.deepseek.com/v1/models \
     -H "Authorization: Bearer $DEEPSEEK_API_KEY"
   # 应返回模型列表，401 表示 Key 无效

2. 检查网络连通性（Docker 环境中容器能否访问外网）
   docker compose exec backend curl -s https://api.deepseek.com

3. 调整超时配置（.env）
   LLM_REQUEST_TIMEOUT=60      # 单次请求超时（秒）
   LLM_MAX_RETRIES=3           # 最大重试次数

4. 观察降级是否生效
   # 系统配置了 DeepSeek → Qwen 的降级链
   # 日志中出现 "Falling back to Qwen" 说明降级正常工作
   # 如果所有供应商都超时，系统会返回兜底回复并记录告警
```

### 4.4 Embedding 服务不可用时的降级行为

系统设计了两层降级，确保知识库检索不会因 Embedding 服务挂掉而完全不可用：

| 优先级 | 策略 | 触发条件 | 检索质量 |
|--------|------|----------|----------|
| 1 | 向量检索 + 全文检索混合 | Embedding 服务正常 | 最优 |
| 2 | 仅全文检索（BM25 + jieba 分词） | Embedding 服务不可用 | 良好，语义匹配能力下降 |
| 3 | 返回通用模板回复 | 全文检索也无结果 | 基础兜底 |

降级过程对调用方透明，API 响应格式不变，仅在 `meta.degraded=true` 字段中标识。

---

## 5. 生产环境加固建议

### 5.1 HTTPS

```nginx
# nginx.conf 片段
server {
    listen 443 ssl http2;
    server_name imcs.your-hospital.com;

    ssl_certificate     /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    # 反向代理到后端
    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 前端静态资源
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # SSE 流式端点需要特殊配置
    location /api/triage/stream {
        proxy_pass http://backend:8000/triage/stream;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }
}
```

### 5.2 密码策略

```python
# 在 .env 中配置
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_DIGIT=true
PASSWORD_REQUIRE_SPECIAL=true

# 数据库密码、Redis 密码务必使用强随机字符串
# 生成方法：
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 5.3 速率限制

```python
# 后端已内置基于 Redis 的速率限制中间件
# 在 .env 中调整（单位：次/分钟）
RATE_LIMIT_ANONYMOUS=30        # 匿名用户
RATE_LIMIT_AUTHENTICATED=120   # 已登录用户
RATE_LIMIT_LLM_PER_USER=10    # 每用户每分钟 LLM 调用次数

# LLM 调用限制尤其重要——防止滥用 API Key 导致费用失控
```

### 5.4 日志持久化

```yaml
# docker-compose.yml 中为 backend 和 celery-worker 添加日志驱动
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
  celery-worker:
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
```

生产环境建议接入 ELK（Elasticsearch + Logstash + Kibana）或 Loki + Grafana：

```yaml
# 使用 Loki 日志驱动
logging:
  driver: loki
  options:
    loki-url: "http://loki:3100/loki/api/v1/push"
    labels: "service"
```

关键日志点：
- LLM 调用日志：请求/响应 token 数、耗时、供应商、降级触发
- 分诊会话日志：用户输入摘要、分诊结果、置信度
- 异步任务日志：任务 ID、开始/结束时间、成功/失败状态

---

## 附录：环境变量速查

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `DATABASE_URL` | 是 | — | PostgreSQL 连接串 |
| `REDIS_URL` | 是 | `redis://localhost:6379/0` | Redis 连接串 |
| `DEEPSEEK_API_KEY` | 是 | — | DeepSeek API Key |
| `DASHSCOPE_API_KEY` | 否 | — | Qwen 降级备用 Key |
| `EMBEDDING_API_KEY` | 否 | — | Embedding 服务 Key，不填则降级 |
| `LLM_REQUEST_TIMEOUT` | 否 | `60` | LLM 请求超时（秒） |
| `LLM_MAX_RETRIES` | 否 | `3` | LLM 最大重试次数 |
| `LLM_DAILY_BUDGET_TOKENS` | 否 | `1000000` | 每日 Token 预算上限 |
| `SECRET_KEY` | 是 | — | JWT 签名密钥 |
| `CORS_ORIGINS` | 否 | `http://localhost:3000` | 允许的前端源 |
| `ENVIRONMENT` | 否 | `development` | `development` / `production` |
