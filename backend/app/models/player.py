"""
玩家模型定义

定义游戏中玩家的数据结构和状态管理
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RoleType(str, Enum):
    """
    角色类型枚举
    
    定义游戏中所有可用角色
    """
    WEREWOLF = "werewolf"    # 狼人
    SEER = "seer"            # 预言家
    WITCH = "witch"          # 女巫
    HUNTER = "hunter"        # 猎人
    VILLAGER = "villager"    # 平民


class PlayerStatus(str, Enum):
    """
    玩家状态枚举
    
    定义玩家在游戏中的存活状态
    """
    ALIVE = "alive"          # 存活
    DEAD = "dead"            # 死亡
    POISONED = "poisoned"    # 被毒死（猎人不可开枪）


class Player(BaseModel):
    """
    玩家数据模型
    
    Attributes:
        id: 玩家唯一标识（1-7）
        name: 玩家显示名称
        role: 玩家角色类型
        status: 玩家当前状态
        is_human: 是否为真实玩家
        has_voted: 当前回合是否已投票
        vote_target: 投票目标玩家ID
    """
    id: int = Field(..., ge=1, le=7, description="玩家编号")
    name: str = Field(..., description="玩家名称")
    role: Optional[RoleType] = Field(None, description="角色类型")
    status: PlayerStatus = Field(default=PlayerStatus.ALIVE, description="玩家状态")
    is_human: bool = Field(default=False, description="是否为真实玩家")
    has_voted: bool = Field(default=False, description="是否已投票")
    vote_target: Optional[int] = Field(None, description="投票目标")
    
    def is_alive(self) -> bool:
        """检查玩家是否存活"""
        return self.status == PlayerStatus.ALIVE
    
    def is_werewolf(self) -> bool:
        """检查玩家是否为狼人"""
        return self.role == RoleType.WEREWOLF
    
    def is_good(self) -> bool:
        """检查玩家是否为好人阵营"""
        return self.role != RoleType.WEREWOLF
    
    def kill(self, by_poison: bool = False) -> None:
        """
        击杀玩家
        
        Args:
            by_poison: 是否被女巫毒死
        """
        if by_poison:
            self.status = PlayerStatus.POISONED
        else:
            self.status = PlayerStatus.DEAD
    
    def reset_vote(self) -> None:
        """重置投票状态"""
        self.has_voted = False
        self.vote_target = None


class WitchSkills(BaseModel):
    """
    女巫技能状态
    
    Attributes:
        has_antidote: 是否还有解药
        has_poison: 是否还有毒药
    """
    has_antidote: bool = Field(default=True, description="解药剩余")
    has_poison: bool = Field(default=True, description="毒药剩余")
    
    def use_antidote(self) -> bool:
        """使用解药，返回是否成功"""
        if self.has_antidote:
            self.has_antidote = False
            return True
        return False
    
    def use_poison(self) -> bool:
        """使用毒药，返回是否成功"""
        if self.has_poison:
            self.has_poison = False
            return True
        return False
