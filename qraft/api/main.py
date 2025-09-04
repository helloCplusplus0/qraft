import os
from typing import Dict, Any

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from qraft.utils.config import load_config
from qraft.api.routes import router as api_router


def create_app() -> FastAPI:
    """创建FastAPI应用
    
    Returns:
        FastAPI应用实例
    """
    # 加载API配置
    config_path = os.environ.get("QRAFT_CONFIG_DIR", "./configs")
    api_config = load_config(os.path.join(config_path, "api.yaml"))
    
    # 创建应用
    app = FastAPI(
        title="Qraft API",
        description="Qraft7.0 数据流驱动自动化模式探索平台 API",
        version="0.1.0",
        debug=api_config.get("debug", False)
    )
    
    # 配置CORS
    cors_config = api_config.get("cors", {})
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_config.get("allow_origins", ["*"]),
        allow_credentials=cors_config.get("allow_credentials", True),
        allow_methods=cors_config.get("allow_methods", ["*"]),
        allow_headers=cors_config.get("allow_headers", ["*"])
    )
    
    # 注册路由
    app.include_router(api_router, prefix="/api")
    
    # 添加健康检查
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}
    
    # 添加版本信息
    @app.get("/version")
    async def version():
        return {"version": "0.1.0"}
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    # 加载API配置
    config_path = os.environ.get("QRAFT_CONFIG_DIR", "./configs")
    api_config = load_config(os.path.join(config_path, "api.yaml"))
    
    host = api_config.get("host", "0.0.0.0")
    port = api_config.get("port", 8000)
    
    uvicorn.run("qraft.api.main:app", host=host, port=port, reload=True)