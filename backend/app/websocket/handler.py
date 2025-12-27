"""
WebSocket 消息处理器

处理客户端 WebSocket 连接和消息
"""
import json
import asyncio
from typing import Optional, Callable, Any
from fastapi import WebSocket
from ..agents.game_controller import GameController


class WebSocketHandler:
    """
    WebSocket 处理器
    
    管理 WebSocket 连接和消息通信
    """
    
    def __init__(self, websocket: WebSocket):
        """
        初始化 WebSocket 处理器
        
        Args:
            websocket: FastAPI WebSocket 连接
        """
        self.websocket = websocket
        self.game_controller: Optional[GameController] = None
    
    async def send_message(self, message: dict) -> None:
        """
        发送消息给客户端
        
        Args:
            message: 消息数据
        """
        # FastAPI/Starlette 的 websocket.send_json 会自动处理序列化
        await self.websocket.send_json(message)
    
    async def handle_connection(self) -> None:
        """处理 WebSocket 连接"""
        await self.websocket.accept()
        
        # 创建游戏控制器，设置消息回调
        self.game_controller = GameController(
            message_callback=self.send_message
        )
        
        try:
            while True:
                # 接收客户端消息
                data = await self.websocket.receive_text()
                message = json.loads(data)
                
                await self.handle_message(message)
                
        except Exception as e:
            print(f"WebSocket 错误: {e}")
        finally:
            print("WebSocket 连接关闭")
    
    async def handle_message(self, message: dict) -> None:
        """
        处理客户端消息
        
        Args:
            message: 消息数据
        """
        msg_type = message.get("type")
        data = message.get("data", {})
        
        if not self.game_controller:
            return
        
        if msg_type == "create_game":
            # 创建游戏
            player_name = data.get("player_name", "玩家")
            await self.game_controller.create_game(player_name)
        
        elif msg_type == "start_game":
            # 开始游戏
            print("收到 start_game 请求")
            # 使用 create_task 异步执行 start_game，避免阻塞 WebSocket 接收循环
            asyncio.create_task(self.game_controller.start_game())
            print("start_game 任务已启动")
        
        elif msg_type == "action":
            # 玩家操作
            action = data.get("action")
            action_data = data.get("data", {})
            await self.game_controller.handle_action(action, action_data)
        
        elif msg_type == "ping":
            # 心跳检测
            await self.send_message({"type": "pong"})
