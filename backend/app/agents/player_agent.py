"""
AI 玩家 Agent

使用通义千问实现 AI 玩家的智能对话和决策
"""
from openai import AsyncOpenAI
from dashscope import Generation
import dashscope
from typing import List, Optional, Tuple
import asyncio
import json
import random
from ..models.player import Player, RoleType
from ..models.game import GameState, GameResult
from ..game.roles import RoleAction, WitchAction
from ..config import config
from .prompts import (
    SYSTEM_PROMPT_TEMPLATE, 
    SPEECH_PROMPT_TEMPLATE, 
    VOTE_PROMPT_TEMPLATE,
    WOLF_KILL_PROMPT_TEMPLATE,
    SEER_CHECK_PROMPT_TEMPLATE,
    WITCH_ACTION_PROMPT_TEMPLATE,
    HUNTER_SHOOT_PROMPT_TEMPLATE
)

# 辅助函数：格式化玩家列表
def format_player_list(players: List[dict]) -> str:
    """格式化玩家列表为字符串"""
    if not players:
        return "无"
    return ", ".join([f"{p['name']}（{p['id']}号）" for p in players])

# 辅助函数：格式化发言记录
def format_speeches(speeches: List[dict]) -> str:
    """格式化发言记录为字符串"""
    if not speeches:
        return "暂无发言"
    return "\n".join([f"{s['player_name']}（{s['player_id']}号）: {s['content']}" for s in speeches])

# 辅助函数：在线程中运行 DashScope 调用
def run_dashscope(model, messages, api_key):
    dashscope.base_http_api_url = config.LLM_BASE_URL
    return Generation.call(
        api_key=api_key,
        model=model,
        messages=messages,
        result_format="message",
        enable_thinking=False
    )

class PlayerAgent:
    """
    AI 玩家 Agent
    
    每个 AI 玩家对应一个 Agent 实例，负责生成发言和做出决策
    """
    
    is_llm_enabled = True  # 类级别熔断机制：如果 API 报错，所有 Agent 禁用 LLM
    
    def __init__(self, player: Player):
        """
        初始化 AI 玩家 Agent
        
        Args:
            player: 玩家对象
        """
        self.player = player
        self.known_info: List[str] = []  # 已知信息（预言家查验结果等）
    
    def _build_system_prompt(self, game_state: GameState) -> str:
        """
        构建系统提示词
        """
        alive_players = [
            {"id": p.id, "name": p.name}
            for p in game_state.get_alive_players()
        ]
        dead_players = [
            {"id": p.id, "name": p.name}
            for p in game_state.players
            if not p.is_alive()
        ]
        
        # 狼人队友信息
        teammate_info = ""
        if self.player.role == RoleType.WEREWOLF:
            teammates = [
                f"{p.name}（{p.id}号）"
                for p in game_state.players
                if p.role == RoleType.WEREWOLF and p.id != self.player.id
            ]
            if teammates:
                teammate_info = f"你的狼人队友是：{', '.join(teammates)}。你们需要配合。"
            else:
                teammate_info = "你的狼人队友已死亡，你是孤狼。"
        
        return SYSTEM_PROMPT_TEMPLATE.format(
            role_name=RoleAction.get_role_name(self.player.role) if self.player.role else "未知",
            player_name=self.player.name,
            player_id=self.player.id,
            role_description=RoleAction.get_role_description(self.player.role) if self.player.role else "",
            round=game_state.round,
            alive_players=format_player_list(alive_players),
            dead_players=format_player_list(dead_players) if dead_players else "暂无",
            teammate_info=teammate_info
        )
    
    async def _call_llm(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        异步调用 LLM API (使用 DashScope SDK)
        
        Returns:
            Optional[str]: LLM 响应，如果失败返回 None
        """
        # 暂时移除熔断判断，强制重试
        # if not PlayerAgent.is_llm_enabled:
        #    print(f"PlayerAgent {self.player.id}: LLM 已熔断，使用 Mock 响应 (当前配置模型: {config.QWEN_MODEL_NAME})")
        #    return None

        print(f"PlayerAgent {self.player.id}: 开始调用 LLM (模型: {config.QWEN_MODEL_NAME})...")
        try:
            # 简单的重试机制
            max_retries = 2
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    # 在线程中运行同步的 DashScope SDK 调用，避免阻塞 asyncio 循环
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                    
                    response = await asyncio.to_thread(
                        run_dashscope,
                        model=config.QWEN_MODEL_NAME,
                        messages=messages,
                        api_key=config.DASHSCOPE_API_KEY
                    )

                    if response.status_code == 200:
                        # 记录思考过程（如果模型支持）
                        message = response.output.choices[0].message
                        # 只有在启用思考时才尝试获取 reasoning_content
                        # if hasattr(message, "reasoning_content") and message.reasoning_content:
                        #    print(f"\n[{self.player.name} 的思考]:\n{message.reasoning_content}\n" + "-"*30)
                        
                        content = message.content
                        if content:
                            print(f"PlayerAgent {self.player.id}: LLM 调用成功")
                            # 成功一次就重置熔断状态
                            PlayerAgent.is_llm_enabled = True
                            return content.strip()
                        else:
                             print(f"PlayerAgent {self.player.id}: API 返回内容为空，重试中...")
                    else:
                        print(f"PlayerAgent {self.player.id}: API 调用失败 Code: {response.code}, Message: {response.message}")
                        raise Exception(f"DashScope Error: {response.message}")

                except Exception as e:
                    print(f"PlayerAgent {self.player.id}: 第 {attempt + 1} 次调用失败: {e}")
                    last_exception = e
                    await asyncio.sleep(1) # 简单的避退
            
            # 如果重试都失败了
            if last_exception:
                raise last_exception
            
            return None

        except Exception as e:
            error_msg = str(e)
            print(f"PlayerAgent {self.player.id}: LLM 调用异常: {error_msg}")
            
            # 关键错误触发熔断
            critical_errors = ["Authentication", "401", "403", "Arrearage", "Access denied", "400", "insufficient_quota"]
            # 暂时不自动熔断，允许用户修复 key 后继续重试
            # if any(err in error_msg for err in critical_errors):
            #      print(f"PlayerAgent {self.player.id}: 检测到关键 API 错误 ({error_msg})，全局启用熔断机制，后续将切换为 Mock 模式。")
            #      PlayerAgent.is_llm_enabled = False
                 
            return None
    
    def _get_mock_speech(self) -> str:
        """获取 Mock 发言"""
        speeches = [
            "我觉得我们需要仔细分析一下局势。",
            "目前信息还比较少，先听听其他人怎么说。",
            "大家发言都很谨慎啊。",
            "我也没什么特别要说的，过。",
            "如果是狼人请不要装好人。",
            "预言家出来带队吧。",
            "我是好人，全场唯一真好人。",
            "这局很有意思。",
        ]
        import random
        return random.choice(speeches)

    async def generate_speech(self, game_state: GameState) -> str:
        """生成发言内容"""
        system_prompt = self._build_system_prompt(game_state)
        
        # 获取本轮之前的发言
        round_speeches = game_state.get_round_speeches()
        previous_speeches = [
            {
                "player_id": s.player_id,
                "player_name": s.player_name,
                "content": s.content
            }
            for s in round_speeches
            if s.player_id != self.player.id
        ]
        
        # 构建情况分析
        situation = self._analyze_situation(game_state)
        
        user_prompt = SPEECH_PROMPT_TEMPLATE.format(
            previous_speeches=format_speeches(previous_speeches),
            situation_analysis=situation,
            role_name=RoleAction.get_role_name(self.player.role) if self.player.role else "玩家"
        )
        
        response = await self._call_llm(system_prompt, user_prompt)
        if response:
            return response
        return self._get_mock_speech()
    
    async def generate_vote(self, game_state: GameState) -> int:
        """生成投票决策"""
        system_prompt = self._build_system_prompt(game_state)
        
        round_speeches = game_state.get_round_speeches()
        speeches = [
            {
                "player_id": s.player_id,
                "player_name": s.player_name,
                "content": s.content
            }
            for s in round_speeches
        ]
        
        alive_players = [
            {"id": p.id, "name": p.name}
            for p in game_state.get_alive_players()
            if p.id != self.player.id
        ]
        
        user_prompt = VOTE_PROMPT_TEMPLATE.format(
            round_speeches=format_speeches(speeches),
            alive_players=format_player_list(alive_players)
        )
        
        response = await self._call_llm(system_prompt, user_prompt)
        
        target_id = None
        if response:
            try:
                target_id = int(response.strip())
                if not any(p.id == target_id for p in game_state.get_alive_players()):
                    target_id = None
            except ValueError:
                pass
        
        if target_id is None:
            import random
            valid_targets = [p.id for p in game_state.get_alive_players() if p.id != self.player.id]
            target_id = random.choice(valid_targets) if valid_targets else self.player.id
            
        return target_id
    
    async def generate_wolf_kill(self, game_state: GameState, valid_targets: List[int]) -> int:
        """生成狼人杀人决策"""
        system_prompt = self._build_system_prompt(game_state)
        
        targets = [
            {"id": p.id, "name": p.name}
            for p in game_state.players
            if p.id in valid_targets
        ]
        
        user_prompt = WOLF_KILL_PROMPT_TEMPLATE.format(
            valid_targets=format_player_list(targets)
        )
        
        response = await self._call_llm(system_prompt, user_prompt)
        
        target_id = None
        if response:
            try:
                target_id = int(response.strip())
                if target_id not in valid_targets:
                    target_id = None
            except ValueError:
                pass
        
        if target_id is None:
            import random
            # 优先刀预言家（如果能猜到）或随机
            # 这里简单随机
            target_id = random.choice(valid_targets)
            
        return target_id
    
    async def generate_seer_check(self, game_state: GameState, valid_targets: List[int]) -> int:
        """生成预言家查验决策"""
        system_prompt = self._build_system_prompt(game_state)
        
        targets = [
            {"id": p.id, "name": p.name}
            for p in game_state.players
            if p.id in valid_targets
        ]
        
        known_info = "\n".join(self.known_info) if self.known_info else "暂无已知信息"
        
        user_prompt = SEER_CHECK_PROMPT_TEMPLATE.format(
            valid_targets=format_player_list(targets),
            known_info=known_info
        )
        
        response = await self._call_llm(system_prompt, user_prompt)
        
        target_id = None
        if response:
            try:
                target_id = int(response.strip())
                if target_id not in valid_targets:
                    target_id = None
            except ValueError:
                pass
        
        if target_id is None:
            import random
            # 优先查没查过的人
            target_id = random.choice(valid_targets)
            
        return target_id
    
    def add_known_info(self, info: str) -> None:
        """添加已知信息"""
        self.known_info.append(info)
    
    async def generate_witch_action(
        self,
        game_state: GameState,
        wolf_target: Optional[int],
        valid_poison_targets: List[int]
    ) -> Tuple[bool, Optional[int]]:
        """生成女巫行动决策"""
        system_prompt = self._build_system_prompt(game_state)
        
        antidote_status = "可用" if game_state.witch_skills.has_antidote else "已使用"
        poison_status = "可用" if game_state.witch_skills.has_poison else "已使用"
        
        if wolf_target and game_state.witch_skills.has_antidote:
            target_player = game_state.get_player(wolf_target)
            night_info = f"今晚{target_player.name}（{wolf_target}号）被狼人杀死，你可以使用解药救他。"
        else:
            night_info = "今晚没有人需要救助。" if not wolf_target else "你已经没有解药了。"
        
        targets = [
            {"id": p.id, "name": p.name}
            for p in game_state.players
            if p.id in valid_poison_targets
        ]
        
        user_prompt = WITCH_ACTION_PROMPT_TEMPLATE.format(
            antidote_status=antidote_status,
            poison_status=poison_status,
            night_info=night_info,
            valid_poison_targets=format_player_list(targets)
        )
        
        response = None
        llm_resp = await self._call_llm(system_prompt, user_prompt)
        if llm_resp:
            response = llm_resp.upper().strip()
        
        if response:
            if response == "SAVE" and game_state.witch_skills.has_antidote and wolf_target:
                return (True, None)
            elif response.startswith("POISON") and game_state.witch_skills.has_poison:
                try:
                    parts = response.split()
                    if len(parts) >= 2:
                        poison_target = int(parts[1])
                        if poison_target in valid_poison_targets:
                            return (False, poison_target)
                except (ValueError, IndexError):
                    pass
        
        # Mock 逻辑：如果有解药且有人死，50%概率救；不毒人
        if wolf_target and game_state.witch_skills.has_antidote:
            import random
            if random.random() > 0.5:
                return (True, None)
        
        return (False, None)
    
    async def generate_hunter_shoot(self, game_state: GameState, valid_targets: List[int]) -> int:
        """生成猎人开枪决策"""
        system_prompt = self._build_system_prompt(game_state)
        
        targets = [
            {"id": p.id, "name": p.name}
            for p in game_state.players
            if p.id in valid_targets
        ]
        
        situation = self._analyze_situation(game_state)
        
        user_prompt = HUNTER_SHOOT_PROMPT_TEMPLATE.format(
            valid_targets=format_player_list(targets),
            situation_analysis=situation
        )
        
        response = await self._call_llm(system_prompt, user_prompt)
        
        if not response:
             print(f"PlayerAgent {self.player.id}: LLM 调用失败，使用 Mock 决策")

        target_id = None
        if response:
            try:
                target_id = int(response.strip())
                if target_id not in valid_targets:
                    target_id = None
            except ValueError:
                pass
        
        if target_id is None:
            import random
            target_id = random.choice(valid_targets)
            
        return target_id
    
    def _analyze_situation(self, game_state: GameState) -> str:
        """分析场上局势"""
        alive_count = len(game_state.get_alive_players())
        dead_count = len(game_state.players) - alive_count
        
        analysis = f"当前第{game_state.round}轮，存活{alive_count}人，死亡{dead_count}人。"
        
        if self.known_info:
            analysis += " 你已知的信息：" + "；".join(self.known_info[-3:])
        
        return analysis
