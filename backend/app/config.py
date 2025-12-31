"""
暗夜狼人杀后端配置模块

管理环境变量和应用配置
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """应用配置类"""
    
    # 模型 API 配置
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/api/v1")
    QWEN_MODEL_NAME: str = os.getenv("QWEN_MODEL_NAME", "glm-4.7")
    
    # 服务器配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # 游戏配置
    PLAYER_COUNT: int = 7  # 总玩家数（1真实 + 6 AI）
    SPEECH_TIME_LIMIT: int = 30  # 发言时间限制（秒）
    
    # 角色配置
    ROLE_CONFIG: dict = {
        "werewolf": 2,      # 狼人
        "seer": 1,          # 预言家
        "witch": 1,         # 女巫
        "hunter": 1,        # 猎人
        "villager": 2       # 平民
    }
    
    @classmethod
    def validate(cls) -> bool:
        """
        验证必要配置是否存在
        
        Returns:
            bool: 配置是否有效
        """
        if not cls.DASHSCOPE_API_KEY:
            print("警告: DASHSCOPE_API_KEY 未配置")
            return False
        return True


config = Config()
