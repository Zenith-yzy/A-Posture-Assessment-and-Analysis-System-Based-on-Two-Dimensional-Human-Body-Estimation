from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.api.posture import router as posture_router

app = FastAPI(
    title="Posture Detection API",
    version="1.0.0"
)

# 包含 API 路由
app.include_router(posture_router, prefix="/posture")

# 配置静态文件服务
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")