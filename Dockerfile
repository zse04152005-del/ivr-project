# ── Stage 1: 构建 React 前端 ──────────────────────────────────────────────
FROM node:20-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build
# 构建产物在 /backend/static（vite.config.js 配置的 outDir）

# ── Stage 2: Python 后端 ──────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# 安装依赖（单独一层，利用缓存）
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./

# 从 Stage 1 复制构建好的前端静态文件
COPY --from=frontend-build /backend/static ./static

EXPOSE 8000

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
