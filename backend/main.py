"""FastAPI 入口文件"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import patients, tasks, appointments
from routers import callbacks, stats, twilio_webhook

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logging.info("数据库初始化完成")
    yield


# 创建应用
app = FastAPI(
    title="老年人体检预约 IVR 自动外呼系统",
    description="自动拨打电话，通过按键交互完成体检预约登记",
    version="1.0.0",
    lifespan=lifespan,
)

# 允许前端跨域访问，暴露自定义响应头
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)

# 注册路由
app.include_router(patients.router)
app.include_router(tasks.router)
app.include_router(appointments.router)
app.include_router(callbacks.router)
app.include_router(stats.router)
app.include_router(twilio_webhook.router)


@app.get("/", tags=["系统"])
def root():
    return {
        "system": "老年人体检预约 IVR 自动外呼系统",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
