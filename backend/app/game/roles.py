"""
角色系统定义

定义各角色的技能和行为
"""
from typing import List, Optional, TYPE_CHECKING
from ..models.player import Player, RoleType, PlayerStatus

if TYPE_CHECKING:
    from ..models.game import GameState


class RoleAction:
    """
    角色行动基类
    
    定义所有角色的通用接口
    """
    
    @staticmethod
    def get_role_name(role: RoleType) -> str:
        """
        获取角色中文名称
        
        Args:
            role: 角色类型
            
        Returns:
            str: 角色中文名
        """
        role_names = {
            RoleType.WEREWOLF: "狼人",
            RoleType.SEER: "预言家",
            RoleType.WITCH: "女巫",
            RoleType.HUNTER: "猎人",
            RoleType.VILLAGER: "平民"
        }
        return role_names.get(role, "未知")
    
    @staticmethod
    def get_role_description(role: RoleType) -> str:
        """
        获取角色描述
        
        Args:
            role: 角色类型
            
        Returns:
            str: 角色描述文字
        """
        descriptions = {
            RoleType.WEREWOLF: "你是狼人，夜晚可以选择杀死一名玩家。与队友狼人一起消灭所有好人即可获胜。",
            RoleType.SEER: "你是预言家，夜晚可以查验一名玩家的身份，知晓其是否为狼人。",
            RoleType.WITCH: "你是女巫，拥有一瓶解药和一瓶毒药。解药可救活被狼人杀死的玩家，毒药可毒死一名玩家。两瓶药不可在同一晚使用。",
            RoleType.HUNTER: "你是猎人，死亡时（被毒死除外）可以开枪带走一名玩家。",
            RoleType.VILLAGER: "你是平民，没有特殊技能，但你的分析和投票对好人阵营至关重要。"
        }
        return descriptions.get(role, "")


class WerewolfAction:
    """狼人行动处理"""
    
    @staticmethod
    def kill(game_state: "GameState", target_id: int) -> bool:
        """
        狼人杀人
        
        Args:
            game_state: 游戏状态
            target_id: 目标玩家ID
            
        Returns:
            bool: 是否成功
        """
        target = game_state.get_player(target_id)
        if target and target.is_alive():
            if game_state.night_action:
                game_state.night_action.wolf_target = target_id
            return True
        return False
    
    @staticmethod
    def get_valid_targets(game_state: "GameState") -> List[int]:
        """获取可杀目标列表（所有存活玩家，包括队友和自己）"""
        return [p.id for p in game_state.get_alive_players()]


class SeerAction:
    """预言家行动处理"""
    
    @staticmethod
    def check(game_state: "GameState", target_id: int) -> Optional[bool]:
        """
        预言家查验
        
        Args:
            game_state: 游戏状态
            target_id: 查验目标ID
            
        Returns:
            Optional[bool]: True=好人, False=狼人, None=查验失败
        """
        target = game_state.get_player(target_id)
        if target and target.is_alive():
            result = target.is_good()
            if game_state.night_action:
                game_state.night_action.seer_target = target_id
                game_state.night_action.seer_result = result
            return result
        return None
    
    @staticmethod
    def get_valid_targets(game_state: "GameState", seer_id: int) -> List[int]:
        """获取可查验目标列表（存活的其他玩家）"""
        return [p.id for p in game_state.get_alive_players() if p.id != seer_id]


class WitchAction:
    """女巫行动处理"""
    
    @staticmethod
    def save(game_state: "GameState") -> bool:
        """
        使用解药救人
        
        Args:
            game_state: 游戏状态
            
        Returns:
            bool: 是否成功
        """
        if game_state.witch_skills.use_antidote():
            if game_state.night_action:
                game_state.night_action.witch_save = True
            return True
        return False
    
    @staticmethod
    def poison(game_state: "GameState", target_id: int) -> bool:
        """
        使用毒药毒人
        
        Args:
            game_state: 游戏状态
            target_id: 目标玩家ID
            
        Returns:
            bool: 是否成功
        """
        target = game_state.get_player(target_id)
        if target and target.is_alive() and game_state.witch_skills.use_poison():
            if game_state.night_action:
                game_state.night_action.witch_poison_target = target_id
            return True
        return False
    
    @staticmethod
    def get_valid_poison_targets(game_state: "GameState", witch_id: int) -> List[int]:
        """获取可毒杀目标列表"""
        return [p.id for p in game_state.get_alive_players() if p.id != witch_id]
    
    @staticmethod
    def can_save(game_state: "GameState") -> bool:
        """检查是否可以救人"""
        # 如果是首夜，女巫可以自救（这里简化规则，假设始终不能自救，除非配置允许）
        # 只要有解药，且狼人有目标，就可以救
        
        # 调试日志
        print(f"DEBUG: can_save check - has_antidote: {game_state.witch_skills.has_antidote}")
        if game_state.night_action:
             print(f"DEBUG: can_save check - wolf_target: {game_state.night_action.wolf_target}")
        else:
             print("DEBUG: can_save check - night_action is None")

        return (
            game_state.witch_skills.has_antidote and
            game_state.night_action is not None and
            game_state.night_action.wolf_target is not None
        )


class HunterAction:
    """猎人行动处理"""
    
    @staticmethod
    def shoot(game_state: "GameState", hunter_id: int, target_id: int) -> bool:
        """
        猎人开枪
        
        Args:
            game_state: 游戏状态
            hunter_id: 猎人ID
            target_id: 目标玩家ID
            
        Returns:
            bool: 是否成功
        """
        hunter = game_state.get_player(hunter_id)
        target = game_state.get_player(target_id)
        
        # 猎人必须是刚死亡状态，目标必须存活
        if (hunter and target and 
            hunter.role == RoleType.HUNTER and
            hunter.status in [PlayerStatus.DEAD, PlayerStatus.POISONED] and
            target.is_alive()):
            target.kill()
            return True
        return False
    
    @staticmethod
    def can_shoot(player: Player) -> bool:
        """
        检查猎人是否可以开枪
        
        被毒死的猎人也可以开枪
        """
        return (
            player.role == RoleType.HUNTER and
            player.status in [PlayerStatus.DEAD, PlayerStatus.POISONED]
        )
    
    @staticmethod
    def get_valid_targets(game_state: "GameState", hunter_id: int) -> List[int]:
        """获取可射击目标列表"""
        return [p.id for p in game_state.get_alive_players() if p.id != hunter_id]
