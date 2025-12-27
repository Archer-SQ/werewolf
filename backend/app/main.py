"""
暗夜狼人杀后端服务入口

FastAPI 应用配置和路由定义
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .websocket.handler import WebSocketHandler
from .config import config

# 创建 FastAPI 应用
app = FastAPI(
    title="暗夜狼人杀",
    description="一个基于 AI 的狼人杀游戏后端服务",
    version="1.0.0"
)

# 配置跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """健康检查接口"""
    return {
        "name": "暗夜狼人杀",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/api/config")
async def get_config():
    """获取游戏配置"""
    return {
        "player_count": config.PLAYER_COUNT,
        "speech_time_limit": config.SPEECH_TIME_LIMIT,
        "role_config": config.ROLE_CONFIG
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 游戏连接端点
    
    客户端通过此端点建立实时通信
    """
    handler = WebSocketHandler(websocket)
    
    try:
        await handler.handle_connection()
    except WebSocketDisconnect:
        print("客户端断开连接")
    except Exception as e:
        print(f"WebSocket 异常: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True
    )
