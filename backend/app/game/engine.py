"""
游戏引擎

管理游戏流程和状态转换
"""
import random
import uuid
from typing import List, Dict, Optional, Tuple
from ..models.player import Player, RoleType, PlayerStatus, WitchSkills
from ..models.game import GameState, GamePhase, GameResult, NightAction
from ..config import config


class GameEngine:
    """
    游戏引擎类
    
    负责管理整个游戏的生命周期，包括：
    - 游戏初始化和角色分配
    - 阶段切换和流程控制
    - 行动验证和执行
    - 胜负判定
    """
    
    def __init__(self):
        """初始化游戏引擎"""
        self.game_state: Optional[GameState] = None
        self.speaking_order: List[int] = []  # 发言顺序
        self.current_speaker_index: int = 0
    
    def create_game(self, player_name: str = "玩家") -> GameState:
        """
        创建新游戏
        
        Args:
            player_name: 真实玩家的名称
            
        Returns:
            GameState: 游戏状态
        """
        game_id = str(uuid.uuid4())
        
        # 创建7名玩家
        players = []
        # 随机决定真实玩家的位置 (1-7)
        human_position = random.randint(1, 7)
        
        for i in range(1, 8):
            is_human = (i == human_position)
            name = player_name if is_human else f"玩家{i}"
            players.append(Player(id=i, name=name, is_human=is_human))
            
        self.game_state = GameState(
            game_id=game_id,
            players=players,
            human_player_id=human_position,
            witch_skills=WitchSkills(has_antidote=True, has_poison=True)
        )
        
        return self.game_state
    
    def assign_roles(self) -> Dict[int, RoleType]:
        """
        分配角色
        
        按照配置随机分配角色给所有玩家
        
        Returns:
            Dict[int, RoleType]: 玩家ID到角色的映射
        """
        if not self.game_state:
            raise ValueError("游戏未初始化")
        
        # 根据配置生成角色列表
        roles: List[RoleType] = []
        for role, count in config.ROLE_CONFIG.items():
            roles.extend([RoleType(role)] * count)
        
        # 随机打乱
        random.shuffle(roles)
        
        # 分配给玩家
        role_assignment = {}
        for i, player in enumerate(self.game_state.players):
            player.role = roles[i]
            role_assignment[player.id] = roles[i]
        
        return role_assignment
    
    def start_game(self) -> GameState:
        """
        开始游戏
        
        分配角色并进入第一个夜晚
        
        Returns:
            GameState: 更新后的游戏状态
        """
        if not self.game_state:
            raise ValueError("游戏未初始化")
        
        # 分配角色
        self.assign_roles()
        
        # 进入第一个夜晚
        self.game_state.round = 1
        self.game_state.phase = GamePhase.NIGHT
        self.game_state.night_action = NightAction()
        
        return self.game_state
    
    def enter_night(self) -> GameState:
        """进入夜晚阶段"""
        if not self.game_state:
            raise ValueError("游戏未初始化")
        
        self.game_state.round += 1
        self.game_state.phase = GamePhase.NIGHT
        self.game_state.night_action = NightAction()
        
        return self.game_state
    
    def enter_wolf_phase(self) -> GameState:
        """进入狼人行动阶段"""
        if not self.game_state:
            raise ValueError("游戏未初始化")
        
        self.game_state.phase = GamePhase.NIGHT_WOLF
        return self.game_state
    
    def enter_seer_phase(self) -> GameState:
        """进入预言家行动阶段"""
        if not self.game_state:
            raise ValueError("游戏未初始化")
        
        self.game_state.phase = GamePhase.NIGHT_SEER
        return self.game_state
    
    def night_kill(self, player_id: int) -> bool:
        """
        夜晚杀人（女巫毒药使用时调用）
        
        这个方法主要用于给 GameController 调用，
        实际上女巫毒人应该通过 WitchAction.poison 调用
        """
        if not self.game_state:
            return False
            
        player = self.game_state.get_player(player_id)
        if player and player.is_alive():
            # 这里只是为了给前端传递信息，实际状态修改在 resolve_night 中
            # 但为了兼容 GameController 中的调用，这里返回 True
            return True
        return False

    def enter_witch_phase(self) -> GameState:
        """进入女巫行动阶段"""
        if not self.game_state:
            raise ValueError("游戏未初始化")
        
        self.game_state.phase = GamePhase.NIGHT_WITCH
        return self.game_state
    
    def resolve_night(self) -> Tuple[List[int], List[str]]:
        """
        结算夜晚
        
        根据夜晚行动确定死亡玩家
        
        Returns:
            Tuple[List[int], List[str]]: (死亡玩家ID列表, 死亡信息列表)
        """
        if not self.game_state or not self.game_state.night_action:
            return [], []
        
        dead_players: List[int] = []
        messages: List[str] = []
        night_action = self.game_state.night_action
        
        # 处理狼人杀人
        wolf_target = night_action.wolf_target
        if wolf_target:
            # 检查女巫是否救人
            if not night_action.witch_save:
                player = self.game_state.get_player(wolf_target)
                if player:
                    player.kill()
                    dead_players.append(wolf_target)
                    messages.append(f"{player.name} 昨晚死亡")
        
        # 处理女巫毒人
        poison_target = night_action.witch_poison_target
        if poison_target:
            player = self.game_state.get_player(poison_target)
            if player:
                player.kill(by_poison=True)
                dead_players.append(poison_target)
                messages.append(f"{player.name} 昨晚死亡")
        
        # 清空夜晚行动
        self.game_state.night_action = None
        
        return dead_players, messages
    
    def enter_day(self) -> Tuple[GameState, List[str]]:
        """
        进入白天阶段
        
        结算夜晚结果，检查游戏是否结束
        
        Returns:
            Tuple[GameState, List[str]]: (游戏状态, 夜晚结算消息)
        """
        if not self.game_state:
            raise ValueError("游戏未初始化")
        
        # 结算夜晚
        dead_players, messages = self.resolve_night()
        
        # 检查游戏是否结束
        result = self.game_state.check_game_over()
        if result != GameResult.ONGOING:
            self.game_state.phase = GamePhase.GAME_OVER
            return self.game_state, messages
        
        # 检查猎人是否需要开枪
        for pid in dead_players:
            player = self.game_state.get_player(pid)
            if player and player.role == RoleType.HUNTER:
                self.game_state.phase = GamePhase.HUNTER_SHOOT
                return self.game_state, messages
        
        # 进入白天讨论
        self.game_state.phase = GamePhase.DAY_DISCUSS
        self.setup_speaking_order()
        
        return self.game_state, messages
    
    def setup_speaking_order(self) -> None:
        """设置发言顺序"""
        if not self.game_state:
            return
        
        # 获取存活玩家
        alive_players = self.game_state.get_alive_players()
        # 确保顺序是 ID 升序，不要随机
        self.speaking_order = sorted([p.id for p in alive_players])
        self.current_speaker_index = 0
        
        if self.speaking_order:
            self.game_state.current_speaker = self.speaking_order[0]
        else:
            self.game_state.current_speaker = None
            self.game_state.phase = GamePhase.DAY_VOTE
    
    def next_speaker(self) -> Optional[int]:
        """
        切换到下一个发言者
        
        Returns:
            Optional[int]: 下一个发言者ID，如果没有则返回None
        """
        if not self.game_state:
            return None
        
        # 简单递增索引
        self.current_speaker_index += 1
        
        # 边界检查
        if self.current_speaker_index >= len(self.speaking_order):
            # 发言结束，进入投票阶段
            self.game_state.current_speaker = None
            self.game_state.phase = GamePhase.DAY_VOTE
            return None
            
        # 获取下一个发言者 ID
        # 因为 setup_speaking_order 时已经过滤了存活玩家，且顺序是固定的
        # 所以理论上只要索引不越界，取出来的就是有效的存活玩家ID
        # (除非在白天发言过程中有人突然暴毙，这在标准狼人杀中不常见，若有则需额外处理)
        next_id = self.speaking_order[self.current_speaker_index]
        self.game_state.current_speaker = next_id
        return next_id
    
    def record_vote(self, player_id: int, target_id: int) -> None:
        """记录投票"""
        if self.game_state:
            self.game_state.votes[player_id] = target_id

    def is_vote_finished(self) -> bool:
        """检查投票是否完成"""
        if not self.game_state:
            return False
        
        alive_players = self.game_state.get_alive_players()
        # 检查是否所有存活玩家都已在 votes 字典中
        for player in alive_players:
            if player.id not in self.game_state.votes:
                return False
        return True

    def resolve_vote(self) -> Tuple[Optional[int], Dict[int, int]]:
        """
        结算投票
        
        Returns:
            Tuple[Optional[int], Dict[int, int]]: (被处决玩家ID或None表示平票, 投票统计)
        """
        if not self.game_state:
            return None, {}
        
        # 统计票数
        # 使用 self.game_state.votes 而不是 player.vote_target，因为 vote_target 是历史遗留字段
        vote_count: Dict[int, int] = {}
        for player_id, target_id in self.game_state.votes.items():
            vote_count[target_id] = vote_count.get(target_id, 0) + 1
        
        if not vote_count:
            return None, {}
        
        # 找出最高票数
        max_votes = max(vote_count.values())
        top_voted = [pid for pid, votes in vote_count.items() if votes == max_votes]
        
        # 重置所有玩家投票状态（包括清空 votes 字典）
        self.game_state.votes.clear()
        for player in self.game_state.players:
            player.reset_vote()
        
        # 平票直接进入夜晚
        if len(top_voted) > 1:
            return None, vote_count
        
        # 处决得票最高者
        executed_id = top_voted[0]
        executed = self.game_state.get_player(executed_id)
        if executed:
            executed.kill(reason="被公投出局")
        
        return executed_id, vote_count
    
    def after_vote(self) -> GameState:
        """
        投票后处理
        
        检查猎人开枪和游戏结束
        
        Returns:
            GameState: 更新后的游戏状态
        """
        if not self.game_state:
            raise ValueError("游戏未初始化")
        
        # 检查游戏是否结束
        result = self.game_state.check_game_over()
        if result != GameResult.ONGOING:
            self.game_state.phase = GamePhase.GAME_OVER
            return self.game_state
        
        # 进入夜晚
        self.enter_night()
        return self.game_state
    
    def get_human_player(self) -> Optional[Player]:
        """获取真实玩家"""
        if not self.game_state:
            return None
        return self.game_state.get_player(self.game_state.human_player_id or 0)
    
    def get_game_status_message(self) -> str:
        """获取当前游戏状态消息"""
        if not self.game_state:
            return "游戏未开始"
        
        phase_messages = {
            GamePhase.WAITING: "等待游戏开始",
            GamePhase.NIGHT: "夜晚降临，请闭眼",
            GamePhase.NIGHT_WOLF: "狼人请睁眼，选择击杀目标",
            GamePhase.NIGHT_SEER: "预言家请睁眼，选择查验目标",
            GamePhase.NIGHT_WITCH: "女巫请睁眼",
            GamePhase.DAY: "天亮了",
            GamePhase.DAY_DISCUSS: "白天讨论阶段",
            GamePhase.DAY_VOTE: "投票阶段",
            GamePhase.HUNTER_SHOOT: "猎人请选择开枪目标",
            GamePhase.GAME_OVER: self._get_game_over_message()
        }
        
        return phase_messages.get(self.game_state.phase, "未知阶段")
    
    def _get_game_over_message(self) -> str:
        """获取游戏结束消息"""
        if not self.game_state:
            return "游戏结束"
        
        if self.game_state.result == GameResult.WOLVES_WIN:
            return "游戏结束！狼人获胜！"
        elif self.game_state.result == GameResult.VILLAGERS_WIN:
            return "游戏结束！好人获胜！"
        return "游戏结束"
