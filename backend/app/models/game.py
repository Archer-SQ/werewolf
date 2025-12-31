"""
游戏状态模型定义

管理整体游戏状态和回合信息
"""
from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from .player import Player, RoleType, WitchSkills


class GamePhase(str, Enum):
    """
    游戏阶段枚举
    
    定义游戏的各个阶段
    """
    WAITING = "waiting"          # 等待开始
    NIGHT = "night"              # 夜晚
    NIGHT_WOLF = "night_wolf"    # 狼人行动
    NIGHT_SEER = "night_seer"    # 预言家行动
    NIGHT_WITCH = "night_witch"  # 女巫行动
    DAY = "day"                  # 白天
    DAY_DISCUSS = "day_discuss"  # 白天讨论
    DAY_VOTE = "day_vote"        # 白天投票
    LAST_WORDS = "last_words"    # 发表遗言
    HUNTER_SHOOT = "hunter_shoot"  # 猎人开枪
    GAME_OVER = "game_over"      # 游戏结束


class GameResult(str, Enum):
    """游戏结果"""
    WOLVES_WIN = "wolves_win"    # 狼人胜利
    VILLAGERS_WIN = "villagers_win"  # 好人胜利
    ONGOING = "ongoing"          # 游戏进行中


class SpeechRecord(BaseModel):
    """
    发言记录
    
    Attributes:
        player_id: 发言玩家ID
        content: 发言内容
        round: 发言回合
        phase: 发言阶段
    """
    player_id: int
    player_name: str
    content: str
    round: int
    phase: GamePhase


class NightAction(BaseModel):
    """
    夜晚行动记录
    
    用于记录夜晚各角色的行动
    """
    wolf_target: Optional[int] = None      # 狼人杀人目标
    seer_target: Optional[int] = None      # 预言家查验目标
    seer_result: Optional[bool] = None     # 查验结果（True=好人）
    witch_save: bool = False               # 女巫是否救人
    witch_poison_target: Optional[int] = None  # 女巫毒人目标


class GameState(BaseModel):
    """
    游戏状态模型
    
    管理整个游戏的状态信息
    
    Attributes:
        game_id: 游戏唯一标识
        players: 玩家列表
        phase: 当前游戏阶段
        round: 当前回合数
        current_speaker: 当前发言玩家ID
        speech_records: 历史发言记录
        night_action: 当前夜晚行动
        witch_skills: 女巫技能状态
        result: 游戏结果
    """
    game_id: str = Field(..., description="游戏ID")
    players: List[Player] = Field(default_factory=list, description="玩家列表")
    phase: GamePhase = Field(default=GamePhase.WAITING, description="当前阶段")
    round: int = Field(default=0, description="当前回合")
    current_speaker: Optional[int] = Field(None, description="当前发言者")
    speech_records: List[SpeechRecord] = Field(default_factory=list, description="发言记录")
    night_action: Optional[NightAction] = Field(None, description="夜晚行动")
    witch_skills: WitchSkills = Field(default_factory=WitchSkills, description="女巫技能")
    checked_players: List[int] = Field(default_factory=list, description="预言家已查验玩家ID列表")
    votes: Dict[int, int] = Field(default_factory=dict, description="当前投票情况")
    result: GameResult = Field(default=GameResult.ONGOING, description="游戏结果")
    human_player_id: Optional[int] = Field(None, description="真实玩家ID")
    
    def get_player(self, player_id: int) -> Optional[Player]:
        """根据ID获取玩家"""
        for player in self.players:
            if player.id == player_id:
                return player
        return None
    
    def get_alive_players(self) -> List[Player]:
        """获取所有存活玩家"""
        return [p for p in self.players if p.is_alive()]
    
    def get_alive_wolves(self) -> List[Player]:
        """获取存活的狼人"""
        return [p for p in self.get_alive_players() if p.is_werewolf()]
    
    def get_alive_villagers(self) -> List[Player]:
        """获取存活的好人"""
        return [p for p in self.get_alive_players() if p.is_good()]
    
    def get_player_by_role(self, role: RoleType) -> List[Player]:
        """根据角色获取玩家列表"""
        return [p for p in self.players if p.role == role]
    
    def add_speech(self, player_id: int, content: str) -> None:
        """添加发言记录"""
        player = self.get_player(player_id)
        if player:
            record = SpeechRecord(
                player_id=player_id,
                player_name=player.name,
                content=content,
                round=self.round,
                phase=self.phase
            )
            self.speech_records.append(record)
    
    def get_round_speeches(self, round_num: Optional[int] = None) -> List[SpeechRecord]:
        """获取指定回合的发言记录"""
        target_round = round_num if round_num is not None else self.round
        return [s for s in self.speech_records if s.round == target_round]
    
    def check_game_over(self) -> GameResult:
        """
        检查游戏是否结束
        
        Returns:
            GameResult: 游戏结果
        """
        alive_wolves = len(self.get_alive_wolves())
        alive_villagers = len(self.get_alive_villagers())
        
        # 狼人全部死亡，好人胜利
        if alive_wolves == 0:
            self.result = GameResult.VILLAGERS_WIN
            return GameResult.VILLAGERS_WIN
        
        # 狼人数量 >= 好人数量
        if alive_wolves >= alive_villagers:
            # 特殊情况：如果当前是猎人开枪阶段，且猎人刚死还未开枪
            # 此时即使人数相等，游戏也不应该结束，因为猎人可能带走狼人
            if self.phase == GamePhase.HUNTER_SHOOT:
                # 再次确认是否有猎人死亡且未开枪（这里简化逻辑，只要是 HUNTER_SHOOT 阶段就不判负）
                # 严格来说应该检查具体的猎人状态，但 Phase 已经是 HUNTER_SHOOT 说明正在等待开枪
                return GameResult.ONGOING
                
            self.result = GameResult.WOLVES_WIN
            return GameResult.WOLVES_WIN
        
        return GameResult.ONGOING
