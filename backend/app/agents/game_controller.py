"""
游戏控制器

协调游戏引擎和 AI Agents 的交互
"""
import asyncio
from typing import Dict, List, Optional, Callable, Any
import random
from ..models.player import Player, RoleType
from ..models.game import GameState, GamePhase, GameResult
from ..game.engine import GameEngine
from ..game.roles import WerewolfAction, SeerAction, WitchAction, HunterAction, RoleAction
from .player_agent import PlayerAgent


class GameController:
    """
    游戏控制器
    
    管理游戏流程，协调真实玩家和 AI 玩家的交互
    """
    
    def __init__(self, message_callback: Optional[Callable[[dict], Any]] = None):
        """
        初始化游戏控制器
        
        Args:
            message_callback: 消息回调函数，用于向客户端发送消息
        """
        self.engine = GameEngine()
        self.agents: Dict[int, PlayerAgent] = {}
        self.message_callback = message_callback
        self.is_running = True  # 游戏运行状态标记
    
    async def send_message(self, msg_type: str, data: dict) -> None:
        """发送消息给客户端"""
        if not self.is_running:
            return

        if self.message_callback:
            message = {"type": msg_type, "data": data}
            try:
                # 统一处理同步和异步回调
                result = self.message_callback(message)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                # 捕获发送消息时的异常（如 WebSocket 断开），防止游戏逻辑崩溃
                print(f"发送消息失败 (type={msg_type}): {e}")
                # 如果发送消息失败，通常意味着连接断开，停止游戏逻辑以避免无效计算和日志刷屏
                self.is_running = False
                print("GameController: 检测到连接断开，停止游戏循环")
    
    async def create_game(self, player_name: str = "玩家") -> GameState:
        """
        创建新游戏
        
        Args:
            player_name: 真实玩家的名称
            
        Returns:
            GameState: 游戏状态
        """
        game_state = self.engine.create_game(player_name)
        
        await self.send_message("game_created", {
            "game_id": game_state.game_id,
            "players": [
                {"id": p.id, "name": p.name, "is_human": p.is_human}
                for p in game_state.players
            ]
        })
        
        return game_state
    
    async def start_game(self) -> GameState:
        """
        开始游戏
        
        分配角色并初始化 AI Agents
        """
        print("GameController.start_game: 开始")
        try:
            game_state = self.engine.start_game()
            print("GameController.start_game: 引擎启动成功")
            
            # 为 AI 玩家创建 Agent
            for player in game_state.players:
                if not player.is_human:
                    self.agents[player.id] = PlayerAgent(player)
            print(f"GameController.start_game: 创建了 {len(self.agents)} 个 AI Agents")
            
            # 通知玩家角色
            human_player = self.engine.get_human_player()
            if human_player:
                # 如果是狼人，获取队友信息
                teammates = []
                if human_player.role == RoleType.WEREWOLF:
                    teammates = [p.id for p in game_state.players if p.role == RoleType.WEREWOLF and p.id != human_player.id]

                await self.send_message("role_assigned", {
                    "player_id": human_player.id,
                    "role": human_player.role.value if human_player.role else None,
                    "role_name": RoleAction.get_role_name(human_player.role) if human_player.role else "未知",
                    "role_description": RoleAction.get_role_description(human_player.role) if human_player.role else "",
                    "teammates": teammates
                })
            print("GameController.start_game: 角色分配消息已发送")
            
            await self.send_message("game_started", {
                "round": game_state.round,
                "phase": game_state.phase.value
            })
            print("GameController.start_game: game_started 消息已发送")
            
            # 等待玩家确认角色，不再自动进入夜晚
            print("GameController.start_game: 等待玩家确认角色...")
            # await self._run_night_phase() # 移至 handle_action
            
            return game_state
        except Exception as e:
            print(f"GameController.start_game 异常: {e}")
            import traceback
            traceback.print_exc()
            raise e
    
    async def _run_night_phase(self) -> None:
        """执行夜晚阶段"""
        await self.send_message("phase_change", {
            "phase": "night",
            "message": "入夜了..."
        })
        
        # 播报：天黑请闭眼
        await self.send_message("announcement", {
            "content": "天黑请闭眼"
        })
        # 广播具体的夜晚行动提示 (重置为通用提示)
        await self.send_message("night_action_change", {
            "action": None,
            "message": "天黑请闭眼"
        })
        await asyncio.sleep(4)  # 等待动画
        
        # 启动夜晚流程链：狼人 -> 预言家 -> 女巫 -> 天亮
        # 使用 create_task 避免阻塞
        asyncio.create_task(self._wolf_action())
    
    async def _wolf_action(self) -> None:
        """狼人行动阶段"""
        # 播报：狼人正在行动
        await self.send_message("announcement", {
            "content": "狼人正在行动"
        })
        await self.send_message("phase_change", {
            "phase": "night_wolf",
            "message": "狼人行动"
        })
        # 广播具体的夜晚行动提示，方便前端全屏遮罩更新文字
        await self.send_message("night_action_change", {
            "action": "wolf_kill",
            "message": "狼人正在行动"
        })
        await asyncio.sleep(3)

        self.engine.enter_wolf_phase()
        
        game_state = self.engine.game_state
        if not game_state:
            return
            
        wolves = [p for p in game_state.get_alive_players() if p.role == RoleType.WEREWOLF]
        if not wolves:
            # 没有存活狼人，随机等待一会儿模拟
            await asyncio.sleep(random.uniform(1, 2))
            await self.send_message("announcement", {
                "content": "狼人请闭眼"
            })
            await asyncio.sleep(1)
            # 直接进入下一阶段
            # 使用 create_task 避免阻塞
            asyncio.create_task(self._seer_action())
            return
            
        valid_targets = WerewolfAction.get_valid_targets(game_state)
        human_player = self.engine.get_human_player()
        
        # 检查是否有真实玩家是狼人
        human_wolf = next((p for p in wolves if p.is_human), None)
        
        if human_wolf:
            # 真实玩家狼人，保持原有等待逻辑
            teammates = [p.id for p in wolves if p.id != human_wolf.id]
            # 更新前端提示：您的回合
            await self.send_message("night_action_change", {
                "action": "wolf_kill",
                "message": "请选择击杀目标"
            })
            await self.send_message("action_required", {
                "action": "wolf_kill",
                "message": "狼人请选择击杀目标",
                "valid_targets": valid_targets,
                "teammates": teammates
            })
            # 等待真实玩家操作，中断流程
            return
        else:
            # AI 狼人，加速处理
            # 简单策略：第一个 AI 狼人做决定
            ai_wolf = None
            for wolf in wolves:
                if wolf.id in self.agents:
                    ai_wolf = self.agents[wolf.id]
                    break
            
            if ai_wolf:
                # 更新前端提示：狼人正在行动
                await self.send_message("night_action_change", {
                    "action": "wolf_kill",
                    "message": "狼人正在行动"
                })
                target = await ai_wolf.generate_wolf_kill(game_state, valid_targets)
                WerewolfAction.kill(game_state, target)
            
            # AI 完成操作，快速进入下一阶段
            await asyncio.sleep(1.5) # 缩短模拟时间
            await self.send_message("announcement", {
                "content": "狼人请闭眼"
            })
            await asyncio.sleep(1)
            # 使用 create_task 避免阻塞
            asyncio.create_task(self._seer_action())
    
    async def _seer_action(self) -> None:
        """预言家行动阶段"""
        # 播报：预言家正在行动
        await self.send_message("announcement", {
            "content": "预言家正在行动"
        })
        await self.send_message("phase_change", {
            "phase": "night_seer",
            "message": "预言家查验"
        })
        # 广播具体的夜晚行动提示
        await self.send_message("night_action_change", {
            "action": "seer_check",
            "message": "预言家正在行动"
        })
        await asyncio.sleep(3)

        game_state = self.engine.game_state
        if not game_state:
            return
        
        self.engine.enter_seer_phase()
        
        # 获取存活的预言家
        seers = [p for p in game_state.get_alive_players() if p.role == RoleType.SEER]
        if not seers:
             # 没有存活预言家，随机等待一会儿模拟
            await asyncio.sleep(random.uniform(1.5, 3.0))
            await self.send_message("announcement", {
                "content": "预言家请闭眼"
            })
            await asyncio.sleep(2)
            # 进入下一阶段
            # 使用 create_task 避免阻塞
            asyncio.create_task(self._witch_action())
            return
        
        seer = seers[0]
        valid_targets = SeerAction.get_valid_targets(game_state, seer.id)
        human_player = self.engine.get_human_player()
        
        if seer.is_human and human_player:
            # 真实玩家预言家
            # 更新前端提示：您的回合
            await self.send_message("night_action_change", {
                "action": "seer_check",
                "message": "请选择查验目标"
            })
            await self.send_message("action_required", {
                "action": "seer_check",
                "message": "选择要查验的玩家",
                "valid_targets": valid_targets
            })
            # 等待操作，中断流程
            return
        elif seer.id in self.agents:
            # AI 预言家
            # 更新前端提示
            await self.send_message("night_action_change", {
                "action": "seer_check",
                "message": "预言家正在行动"
            })
            agent = self.agents[seer.id]
            target = await agent.generate_seer_check(game_state, valid_targets)
            result = SeerAction.check(game_state, target)
            
            if result is not None:
                target_player = game_state.get_player(target)
                info = f"{target_player.name}是{'好人' if result else '狼人'}"
                agent.add_known_info(info)
            
            # AI 完成操作，进入下一阶段
            await asyncio.sleep(2)
            await self.send_message("announcement", {
                "content": "预言家请闭眼"
            })
            await asyncio.sleep(2)
            # 使用 create_task 避免阻塞
            asyncio.create_task(self._witch_action())
    
    async def _witch_action(self) -> None:
        """女巫行动阶段"""
        # 播报：女巫正在行动
        await self.send_message("announcement", {
            "content": "女巫正在行动"
        })
        await self.send_message("phase_change", {
            "phase": "night_witch",
            "message": "女巫行动"
        })
        # 广播具体的夜晚行动提示
        await self.send_message("night_action_change", {
            "action": "witch_action",
            "message": "女巫正在行动"
        })
        await asyncio.sleep(3)

        game_state = self.engine.game_state
        if not game_state:
            return
        
        self.engine.enter_witch_phase()
        
        # 获取存活的女巫
        witches = [p for p in game_state.get_alive_players() if p.role == RoleType.WITCH]
        if not witches:
            # 没有存活女巫，随机等待一会儿模拟
            await asyncio.sleep(random.uniform(1.5, 3.0))
            await self.send_message("announcement", {
                "content": "女巫请闭眼..."
            })
            await asyncio.sleep(2)
            # 进入下一阶段
            # 使用 create_task 避免阻塞
            asyncio.create_task(self._enter_day())
            return
        
        witch = witches[0]
        can_save = WitchAction.can_save(game_state)
        can_poison = game_state.witch_skills.has_poison
        valid_targets = WitchAction.get_valid_poison_targets(game_state, witch.id)
        human_player = self.engine.get_human_player()
        
        if witch.is_human and human_player:
            # 真实玩家女巫
            # 更新前端提示：您的回合
            await self.send_message("night_action_change", {
                "action": "witch_action",
                "message": "请选择行动"
            })
            wolf_target = game_state.night_action.wolf_target if game_state.night_action else None
            
            await self.send_message("action_required", {
                "action": "witch_action",
                "message": "女巫请选择行动",
                "valid_targets": valid_targets,
                "can_save": can_save,
                "has_antidote": game_state.witch_skills.has_antidote,
                "has_poison": game_state.witch_skills.has_poison,
                "can_poison": can_poison, # 保留以防万一
                "night_kill": False, # 简化处理，不再传递方法引用
                "wolf_target": wolf_target
            })
            # 等待操作
            return
        elif witch.id in self.agents:
            # AI 女巫
            # 更新前端提示
            await self.send_message("night_action_change", {
                "action": "witch_action",
                "message": "女巫正在行动"
            })
            agent = self.agents[witch.id]
            wolf_target = game_state.night_action.wolf_target if game_state.night_action else None
            save, poison_target = await agent.generate_witch_action(
                game_state, wolf_target, valid_targets
            )
            
            if save:
                WitchAction.save(game_state)
            if poison_target:
                WitchAction.poison(game_state, poison_target)
            
            # AI 完成操作，进入下一阶段
            await asyncio.sleep(2)
            await self.send_message("announcement", {
                "content": "女巫请闭眼"
            })
            await asyncio.sleep(2)
            await self._enter_day()
    
    async def _enter_day(self) -> None:
        """进入白天"""
        # 播报：天亮了
        await self.send_message("announcement", {
            "content": "天亮了"
        })
        # 广播具体的夜晚行动提示 (天亮了，清除)
        await self.send_message("night_action_change", {
            "action": None,
            "message": "天亮了"
        })
        await self.send_message("phase_change", {
            "phase": "day_announce",
            "message": "天亮了"
        })
        await asyncio.sleep(3)

        game_state, messages = self.engine.enter_day()
        
        # 记录原本应该进入的阶段，以便遗言后恢复
        original_phase = game_state.phase
        
        # 发送夜晚结算信息
        if messages:
            await self.send_message("night_result", {
                "messages": messages,
                "dead_announcement": "昨晚的死亡公告" if messages else "昨晚是平安夜",
                "players": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "is_human": p.is_human,
                        "is_alive": p.is_alive(),
                        "death_reason": p.death_reason
                    }
                    for p in game_state.players
                ]
            })
            
            # 播报死亡信息
            died_names = [msg.split(" ")[0] for msg in messages if "死亡" in msg]
            if died_names:
                 await asyncio.sleep(2)
                 await self.send_message("announcement", {
                    "content": f"昨晚 {', '.join(died_names)} 倒牌了"
                })
                 await asyncio.sleep(4)
                 
                 # 首夜死亡有遗言
                 if game_state.round == 1:
                     dead_players = [p for p in game_state.players if p.name in died_names and not p.is_alive()]
                     for player in dead_players:
                         await self._handle_last_words(player.id)
                     
                     # 显式标记首夜遗言结束，避免重复触发
                     self._first_night_last_words_done = True
                     
                     # 清除 action_required，防止前端残留输入框
                     await self.send_message("action_required", {})
                     
                     await asyncio.sleep(1)
                     
                     # 恢复原本的阶段
                     game_state.phase = original_phase
                     
                     # 如果是进入讨论阶段，需要发送 phase_change 通知前端
                     if original_phase == GamePhase.DAY_DISCUSS:
                         # 恢复当前发言者，防止因 _handle_last_words 修改 current_speaker 导致第一个玩家被跳过
                         if self.engine.speaking_order:
                             game_state.current_speaker = self.engine.speaking_order[self.engine.current_speaker_index]
                             
                         # 显式切换阶段，确保前端状态更新
                         await self.send_message("phase_change", {
                            "phase": "day_discuss",
                            "message": "白天讨论阶段开始，请按顺序发言"
                        })
                     
                     # 不在这里调用 _run_discussion，让代码继续向下执行，经过游戏结束检查后统一调用
                     print("DEBUG: _enter_day ready to continue to _run_discussion")
                 else:
                     # 非首夜，不处理遗言，直接继续流程
                     pass
            else:
                 await asyncio.sleep(2)
                 await self.send_message("announcement", {
                    "content": "昨晚是平安夜"
                })
                 await asyncio.sleep(3)
                 
                 # 无人死亡，直接进入白天
                 pass
        else:
            await self.send_message("night_result", {
                "messages": ["昨晚是平安夜，没有人死亡"],
                "dead_announcement": "平安夜"
            })
            
            await asyncio.sleep(2)
            await self.send_message("announcement", {
                "content": "昨晚是平安夜"
            })
            await asyncio.sleep(3)
        
        # 检查游戏是否结束
        if game_state.phase == GamePhase.GAME_OVER:
            await self._game_over()
            return
        
        # 检查是否需要猎人开枪
        if game_state.phase == GamePhase.HUNTER_SHOOT:
            await self._hunter_shoot()
            return
        
        # 检查是否所有人都死亡（防止死循环）
        alive_count = len(game_state.get_alive_players())
        if alive_count <= 0:
             print("GameController._enter_day: 所有玩家已死亡，强制结束游戏")
             game_state.result = GameResult.WOLVES_WIN # 或者是平局，这里简化
             game_state.phase = GamePhase.GAME_OVER
             await self._game_over()
             return
             
        # 进入白天讨论
        # 使用 create_task 避免阻塞
        if game_state.phase == GamePhase.DAY_DISCUSS:
            print("DEBUG: _enter_day calling _run_discussion")
            asyncio.create_task(self._run_discussion())
        else:
            print(f"DEBUG: _enter_day phase is {game_state.phase}, skipping _run_discussion")
    
    async def _run_discussion(self, resume: bool = False) -> None:
        """
        运行白天讨论阶段
        
        Args:
            resume: 是否是恢复之前的讨论（例如真实玩家发言后）
        """
        print(f"DEBUG: _run_discussion started, resume={resume}")
        game_state = self.engine.game_state
        if not game_state:
            return
        
        # 只有在非恢复模式下才发送阶段变更通知
        if not resume:
            # 再次确认 phase，防止状态被覆盖
            if game_state.phase != GamePhase.DAY_DISCUSS:
                game_state.phase = GamePhase.DAY_DISCUSS
                
            await self.send_message("phase_change", {
                "phase": "day_discuss",
                "message": "白天讨论阶段开始，请按顺序发言"
            })
            
            # 确保 current_speaker 正确
            if self.engine.speaking_order and game_state.current_speaker not in self.engine.speaking_order:
                 # 如果当前发言者不在发言队列中（可能是死者），强制重置为第一个存活玩家
                 if self.engine.speaking_order:
                     game_state.current_speaker = self.engine.speaking_order[0]
                     self.engine.current_speaker_index = 0
                     print(f"DEBUG: _run_discussion reset current_speaker to {game_state.current_speaker}")
        
        # 检查是否所有人都死亡（防止死循环）
        alive_count = len(game_state.get_alive_players())
        if alive_count <= 0:
             print("GameController._run_discussion: 所有玩家已死亡，跳过讨论")
             await self._run_vote()
             return

        # 按顺序发言
        while game_state.current_speaker is not None:
            speaker_id = game_state.current_speaker
            speaker = game_state.get_player(speaker_id)
            
            if not speaker or not speaker.is_alive():
                self.engine.next_speaker()
                continue
            
            await self.send_message("speaker_turn", {
                "speaker_id": speaker_id,
                "speaker_name": speaker.name,
                "is_human": speaker.is_human,
                "time_limit": 30
            })
            
            if speaker.is_human:
                # 等待真实玩家发言
                await self.send_message("action_required", {
                    "action": "speak",
                    "message": "请发言（30秒）",
                    "time_limit": 30
                })
                # 真实玩家的发言通过 WebSocket 接收，会调用 handle_speech
                break  # 等待玩家输入
            else:
                # AI 发言
                if speaker_id in self.agents:
                    # 广播：开始思考
                    await self.send_message("thinking_start", {
                        "player_id": speaker_id,
                        "action": "speak"
                    })
                    
                    # 模拟思考时间（已禁用 LLM 思考，加一点延迟更自然）
                    await asyncio.sleep(random.uniform(1.0, 2.0))
                    
                    speech = await self.agents[speaker_id].generate_speech(game_state)
                    game_state.add_speech(speaker_id, speech)
                    
                    # 确保发送的 player_speech 包含当前的 round 信息
                    # 这样前端才能正确检测轮次变化
                    await self.send_message("player_speech", {
                        "speaker_id": speaker_id,
                        "speaker_name": speaker.name,
                        "content": speech,
                        "round": game_state.round
                    })
                
                # 切换到下一个发言者
                next_speaker = self.engine.next_speaker()
                
                # 增加延迟，确保前端有足够时间处理上一条 player_speech 消息
                # 防止 speaker_turn 消息过快覆盖 player_speech
                await asyncio.sleep(1)
                
                if next_speaker is None:
                    # 发言结束，等待真实玩家点击"开始投票"按钮
                    # 不再自动调用 _run_vote()
                    # 发送一个 action_required 消息给前端，要求显示开始投票按钮
                    human_player = self.engine.get_human_player()
                    if human_player and human_player.is_alive():
                        await self.send_message("action_required", {
                            "action": "start_vote",
                            "message": "发言结束，请点击开始投票"
                        })
                    else:
                        # 如果玩家已死，直接进入投票
                        await asyncio.sleep(2)
                        asyncio.create_task(self._run_vote())
                    return  # 必须 return，结束当前循环任务
                
                # 如果还有下一个发言者，继续循环
                # 注意：这里不需要 create_task，因为 while 循环会处理下一个
                continue

    async def handle_start_vote(self) -> None:
        """处理开始投票请求"""
        # 只有在发言阶段结束且等待投票时才处理
        # 广播投票阶段开始，并正式启动投票流程
        await self._run_vote()

    async def handle_speech(self, content: str) -> None:
        """
        处理真实玩家发言
        
        Args:
            content: 发言内容
        """
        game_state = self.engine.game_state
        if not game_state or not game_state.current_speaker:
            return
        
        speaker_id = game_state.current_speaker
        speaker = game_state.get_player(speaker_id)
        
        if speaker and speaker.is_human:
            game_state.add_speech(speaker_id, content)
            
            await self.send_message("player_speech", {
                "speaker_id": speaker_id,
                "speaker_name": speaker.name,
                "content": content,
                "round": game_state.round,
                "phase": game_state.phase.value # 显式传递当前阶段
            })
            
            # 如果正在等待遗言，触发事件并返回
            if hasattr(self, '_waiting_for_speech') and self._waiting_for_speech:
                await asyncio.sleep(0.5)  # 短暂延迟，确保前端先收到 player_speech
                self._waiting_for_speech.set()
                return

            # 切换到下一个发言者
            next_speaker = self.engine.next_speaker()
            
            # 添加短暂延迟，确保前端有足够时间处理上一条消息
            # 特别是当连续两个 AI 发言时，这个延迟有助于防止前端状态竞争
            await asyncio.sleep(1)
            
            if next_speaker is None:
                # 发言结束，等待真实玩家点击"开始投票"按钮
                # 发送 action_required 消息
                human_player = self.engine.get_human_player()
                if human_player and human_player.is_alive():
                    await self.send_message("action_required", {
                        "action": "start_vote",
                        "message": "发言结束，请点击开始投票"
                    })
                else:
                    await asyncio.sleep(2)
                    asyncio.create_task(self._run_vote())
            else:
                # 继续讨论 - 这里的逻辑需要修正
                # 因为 handle_speech 是在 WebSocket 线程中调用的，
                # 而 _run_discussion 的 while 循环已经因为 break 而退出了（等待真实玩家输入时）
                # 所以这里必须重新启动 _run_discussion 来继续后续的 AI 发言
                # 传入 resume=True 以避免重复发送 phase_change 消息
                asyncio.create_task(self._run_discussion(resume=True))
    
    async def _run_vote(self) -> None:
        """运行投票阶段"""
        game_state = self.engine.game_state
        if not game_state:
            return
        
        await self.send_message("phase_change", {
            "phase": "day_vote",
            "message": "投票阶段开始"
        })
        
        # 清除上一轮的投票状态
        await self.send_message("reset_vote", {})
        
        human_player = self.engine.get_human_player()
        
        # 创建投票任务列表
        voting_tasks = []
        
        # AI 玩家投票任务
        for player in game_state.get_alive_players():
            if not player.is_human and player.id in self.agents:
                # 广播：AI 正在投票思考
                await self.send_message("thinking_start", {
                    "player_id": player.id,
                    "action": "vote"
                })
                # 创建 AI 投票任务
                voting_tasks.append(asyncio.create_task(self._ai_vote_task(player.id)))
        
        # 请求真实玩家投票（如果存活）
        if human_player and human_player.is_alive():
            valid_targets = [p.id for p in game_state.get_alive_players() if p.id != human_player.id]
            await self.send_message("action_required", {
                "action": "vote",
                "message": "请选择要投票的玩家",
                "valid_targets": valid_targets
            })
        
        # 等待所有 AI 投票完成
        if voting_tasks:
            try:
                # 增加超时，防止无限等待
                await asyncio.wait_for(asyncio.gather(*voting_tasks), timeout=30.0)
            except asyncio.TimeoutError:
                print("AI voting timed out!")
                # 超时后强制结算，未投票的 AI 随机投票
                for player in game_state.get_alive_players():
                    if player.id not in game_state.votes:
                         valid_targets = [p.id for p in game_state.get_alive_players()]
                         if valid_targets:
                             target = random.choice(valid_targets)
                             self.engine.record_vote(player.id, target)
                             await self.send_message("player_voted", {"player_id": player.id})
            except Exception as e:
                print(f"Error in AI voting tasks: {e}")
            
        # 检查是否所有存活玩家都已投票
        # 如果真实玩家还没投，这里会继续等待 handle_vote 的触发
        # 但我们需要一种机制来等待所有票齐
        
        # 简单策略：轮询检查投票是否完成
        # 注意：这里会阻塞直到所有票收集完毕，所以必须使用 asyncio.sleep 释放控制权
        while not self.engine.is_vote_finished():
            await asyncio.sleep(0.5)
            
        # 使用 create_task 避免阻塞 WebSocket 循环
        asyncio.create_task(self._resolve_vote())

    async def _ai_vote_task(self, player_id: int) -> None:
        """AI 玩家投票任务"""
        game_state = self.engine.game_state
        if not game_state or player_id not in self.agents:
            return
            
        try:
            # 模拟思考时间
            await asyncio.sleep(random.uniform(2.0, 5.0))
            
            target = await self.agents[player_id].generate_vote(game_state)
            self.engine.record_vote(player_id, target)
            
            # 广播：AI 已投票
            await self.send_message("player_voted", {
                "player_id": player_id
            })
        except Exception as e:
            print(f"AI vote failed for player {player_id}: {e}")
            # 异常处理：随机投票，防止流程卡死
            valid_targets = [p.id for p in game_state.get_alive_players()]
            if valid_targets:
                target = random.choice(valid_targets)
                self.engine.record_vote(player_id, target)
                await self.send_message("player_voted", {
                    "player_id": player_id
                })

    async def handle_vote(self, target_id: int) -> None:
        """
        处理真实玩家投票
        
        Args:
            target_id: 被投票玩家ID
        """
        game_state = self.engine.game_state
        if not game_state:
            return
        
        human_player = self.engine.get_human_player()
        if human_player:
            self.engine.record_vote(human_player.id, target_id)
            # 广播：真实玩家已投票
            await self.send_message("player_voted", {
                "player_id": human_player.id
            })
            
            # 通知前端等待其他玩家
            await self.send_message("action_required", {
                "action": "wait",
                "message": "等待其他玩家投票..."
            })
        
        # 不需要在这里调用 _resolve_vote，_run_vote 中的循环会处理

    
    async def _resolve_vote(self) -> None:
        """结算投票"""
        try:
            executed_id, vote_count = self.engine.resolve_vote()
            game_state = self.engine.game_state
            
            if not game_state:
                return
            
            # 发送投票结果
            vote_details = [
                {"target_id": tid, "votes": count}
                for tid, count in vote_count.items()
            ]
            
            # 立即检查游戏是否结束（基于投票后的状态）
            result = game_state.check_game_over()
            print(f"DEBUG: Vote resolved. Executed: {executed_id}. check_game_over result: {result}")
            
            if executed_id:
                executed = game_state.get_player(executed_id)
                await self.send_message("vote_result", {
                    "executed_id": executed_id,
                    "executed_name": executed.name if executed else "未知",
                    "vote_details": vote_details,
                    "is_tie": False
                })
                
                # 播报处决结果
                await self.send_message("announcement", {
                    "content": f"{executed.name} 被公投出局"
                })
                await asyncio.sleep(4)
            else:
                await self.send_message("vote_result", {
                    "executed_id": None,
                    "executed_name": None,
                    "vote_details": vote_details,
                    "is_tie": True,
                    "message": "平票，直接进入夜晚"
                })
                
                # 播报平票
                await self.send_message("announcement", {
                    "content": "平票，无人出局"
                })
                await asyncio.sleep(3)
                
                # 2. 如果游戏结束，直接结算，跳过遗言和后续
            if result != GameResult.ONGOING:
                print("DEBUG: Game Over triggered in _resolve_vote, calling _game_over")
                game_state.phase = GamePhase.GAME_OVER
                await self._game_over()
                return

            # 3. 游戏未结束，处理遗言
            if executed_id:
                # 发表遗言
                await self._handle_last_words(executed_id)
                
                # 检查是否是猎人，如果是，直接进入猎人开枪环节，不显示"进入夜晚"按钮
                executed = game_state.get_player(executed_id)
                if executed and executed.role == RoleType.HUNTER:
                     # 播报猎人发动技能
                     await self.send_message("announcement", {
                        "content": "猎人发动技能"
                     })
                     await asyncio.sleep(2)
                     
                     game_state.phase = GamePhase.HUNTER_SHOOT
                     # 使用 create_task 避免阻塞
                     # 标记触发来源为投票阶段
                     asyncio.create_task(self._hunter_shoot(is_day_vote=True))
                     return
                
                # 非猎人，正常等待进入夜晚
                await self.send_message("action_required", {
                    "action": "enter_night",
                    "message": "遗言结束，请点击进入夜晚"
                })
                self._waiting_for_night_start = asyncio.Event()
                await self._waiting_for_night_start.wait()
                self._waiting_for_night_start = None
            
            # 只有在游戏未结束且非猎人开枪阶段才进入夜晚
            if game_state.phase != GamePhase.HUNTER_SHOOT:
                # 进入夜晚
                print("DEBUG: Entering night phase from _resolve_vote")
                self.engine.after_vote()
                # 使用 create_task 避免阻塞
                asyncio.create_task(self._run_night_phase())
        except Exception as e:
            print(f"ERROR in _resolve_vote: {e}")
            import traceback
            traceback.print_exc()
    
    async def _handle_last_words(self, player_id: int) -> None:
        """
        处理发表遗言环节
        
        Args:
            player_id: 发表遗言的玩家ID
        """
        game_state = self.engine.game_state
        if not game_state:
            return
            
        player = game_state.get_player(player_id)
        if not player:
            return
            
        # 切换游戏阶段到遗言阶段
        # 这很重要，因为：
        # 1. 前端会根据 phase_change 清除之前的 action_required (如"等待投票")
        # 2. 前端收到 player_speech 时会记录当前的 phase，用于显示"遗言"标签
        game_state.phase = GamePhase.LAST_WORDS
        # 设置当前发言者，确保 handle_speech 能正确处理遗言
        game_state.current_speaker = player_id
        await self.send_message("phase_change", {
            "phase": "last_words",
            "message": "请发表遗言"
        })
            
        # 广播：请发表遗言
        await self.send_message("announcement", {
            "content": f"请 {player.name} 发表遗言"
        })
        await asyncio.sleep(2)
        
        await self.send_message("speaker_turn", {
            "speaker_id": player_id,
            "speaker_name": player.name,
            "is_human": player.is_human,
            "time_limit": 30,
            "is_last_words": True
        })
        
        if player.is_human:
            await self.send_message("action_required", {
                "action": "speak",
                "message": "请发表遗言（30秒）",
                "time_limit": 30
            })
            
            # 使用 Event 等待玩家遗言，或超时
            self._waiting_for_speech = asyncio.Event()
            try:
                # 等待 35 秒（比前端 30 秒稍长）
                await asyncio.wait_for(self._waiting_for_speech.wait(), timeout=35.0)
            except asyncio.TimeoutError:
                # 超时未发言，自动跳过
                pass
            finally:
                self._waiting_for_speech = None
                
        else:
            # AI 发表遗言
            if player_id in self.agents:
                await self.send_message("thinking_start", {
                    "player_id": player_id,
                    "action": "speak"
                })
                await asyncio.sleep(random.uniform(1.0, 2.0))
                
                # 使用 generate_speech 生成遗言
                speech = await self.agents[player_id].generate_speech(game_state, is_last_words=True)
                
                await self.send_message("player_speech", {
                    "speaker_id": player_id,
                    "speaker_name": player.name,
                    "content": speech,
                    "round": game_state.round,
                    "phase": "last_words" # 显式传递阶段
                })
                await asyncio.sleep(2)

    async def _hunter_shoot(self, is_day_vote: bool = False) -> None:
        """
        猎人开枪阶段
        
        Args:
            is_day_vote: 是否是在白天投票阶段触发的（决定开枪后的流程流转）
        """
        game_state = self.engine.game_state
        if not game_state:
            return
        
        # 记录触发来源，供 handle_hunter_shoot 使用
        self._hunter_trigger_source = "day_vote" if is_day_vote else "night_death"
        
        # 找到刚死亡的猎人
        hunters = [p for p in game_state.players 
                   if p.role == RoleType.HUNTER and not p.is_alive()]
        
        if not hunters:
            return
        
        hunter = hunters[-1]  # 最后死亡的猎人
        valid_targets = HunterAction.get_valid_targets(game_state, hunter.id)
        
        if hunter.is_human:
            await self.send_message("action_required", {
                "action": "hunter_shoot",
                "message": "你死亡了，请选择开枪目标",
                "valid_targets": valid_targets
            })
        elif hunter.id in self.agents:
            target = await self.agents[hunter.id].generate_hunter_shoot(game_state, valid_targets)
            HunterAction.shoot(game_state, hunter.id, target)
            
            target_player = game_state.get_player(target)
            await self.send_message("hunter_shoot_result", {
                "hunter_id": hunter.id,
                "target_id": target,
                "target_name": target_player.name if target_player else "未知"
            })
            
            # 检查游戏结束
            result = game_state.check_game_over()
            if result != GameResult.ONGOING:
                await self._game_over()
            else:
                # 继续之前的流程
                trigger_source = getattr(self, '_hunter_trigger_source', 'night_death')
                
                if trigger_source == 'day_vote':
                    self.engine.after_vote()
                    asyncio.create_task(self._run_night_phase())
                else:
                    if game_state.phase == GamePhase.HUNTER_SHOOT:
                        game_state.phase = GamePhase.DAY_DISCUSS
                        self.engine.setup_speaking_order()
                        await self._run_discussion()
    
    async def handle_hunter_shoot(self, target_id: int) -> None:
        """处理真实玩家猎人开枪"""
        game_state = self.engine.game_state
        if not game_state:
            return
        
        human_player = self.engine.get_human_player()
        if human_player and human_player.role == RoleType.HUNTER:
            HunterAction.shoot(game_state, human_player.id, target_id)
            
            target = game_state.get_player(target_id)
            await self.send_message("hunter_shoot_result", {
                "hunter_id": human_player.id,
                "target_id": target_id,
                "target_name": target.name if target else "未知"
            })
            
            # 检查游戏结束
            # 强制重新检查状态，确保数据最新
            alive_wolves = len(game_state.get_alive_wolves())
            alive_villagers = len(game_state.get_alive_villagers())
            print(f"DEBUG: Hunter shoot resolved. Executed: {target_id}. Wolves: {alive_wolves}, Villagers: {alive_villagers}")
            
            result = game_state.check_game_over()
            print(f"DEBUG: check_game_over result: {result}")
            
            if result != GameResult.ONGOING:
                print("DEBUG: Game Over triggered in handle_hunter_shoot")
                game_state.phase = GamePhase.GAME_OVER
                await self._game_over()
            else:
                # 继续之前的流程
                # 根据触发来源决定后续流程
                trigger_source = getattr(self, '_hunter_trigger_source', 'night_death')
                
                if trigger_source == 'day_vote':
                    # 如果是白天投票死的，开完枪直接进入夜晚
                    print("DEBUG: Hunter shot after day vote, entering night phase")
                    self.engine.after_vote()
                    asyncio.create_task(self._run_night_phase())
                else:
                    # 如果是夜晚死的，开完枪继续白天讨论
                    print("DEBUG: Hunter shot after night death, continuing day discussion")
                    game_state.phase = GamePhase.DAY_DISCUSS
                    self.engine.setup_speaking_order()
                    await self._run_discussion()
    
    async def handle_action(self, action: str, data: dict) -> None:
        """
        处理玩家操作
        
        Args:
            action: 操作类型
            data: 操作数据
        """
        if action == "role_confirmed":
            print("GameController.handle_action: 玩家已确认角色，开始夜晚流程")
            await self._run_night_phase()

        elif action == "wolf_kill":
            target_id = data.get("target_id")
            if target_id and self.engine.game_state:
                WerewolfAction.kill(self.engine.game_state, target_id)
                
                # 播报：狼人请闭眼
                await self.send_message("announcement", {
                    "content": "狼人请闭眼..."
                })
                await asyncio.sleep(2)
                
                await self._seer_action()
        
        elif action == "seer_check":
            target_id = data.get("target_id")
            if target_id and self.engine.game_state:
                result = SeerAction.check(self.engine.game_state, target_id)
                target = self.engine.game_state.get_player(target_id)
                
                # 发送查验结果
                await self.send_message("seer_result", {
                    "target_id": target_id,
                    "target_name": target.name if target else "未知",
                    "is_good": result
                })
                
                # 等待几秒让前端展示动画
                await asyncio.sleep(4)
                
                # 播报：预言家请闭眼
                await self.send_message("announcement", {
                    "content": "预言家请闭眼..."
                })
                await asyncio.sleep(2)
                
                # 使用 create_task 避免阻塞
                asyncio.create_task(self._witch_action())
        
        elif action == "confirm_result":
             # 废弃，不再需要手动确认
             pass
        
        elif action == "witch_action":
            save = data.get("save", False)
            poison_target = data.get("poison_target")
            
            if self.engine.game_state:
                saved = False
                if save:
                    saved = WitchAction.save(self.engine.game_state)
                
                # 只有未救人时才能使用毒药（不可同一晚双药）
                if poison_target and not saved:
                    WitchAction.poison(self.engine.game_state, poison_target)
                
                # 播报：女巫请闭眼
                await self.send_message("announcement", {
                    "content": "女巫请闭眼..."
                })
                await asyncio.sleep(2)
                
                # 使用 create_task 避免阻塞
                asyncio.create_task(self._enter_day())
        
        elif action == "speak":
            content = data.get("content", "")
            await self.handle_speech(content)
        
        elif action == "start_vote":
            # 真实玩家触发开始投票
            # 使用 create_task 避免阻塞
            asyncio.create_task(self.handle_start_vote())
        
        elif action == "vote":
            target_id = data.get("target_id")
            if target_id is not None:
                await self.handle_vote(target_id)
        
        elif action == "enter_night":
            if hasattr(self, '_waiting_for_night_start') and self._waiting_for_night_start:
                self._waiting_for_night_start.set()

        elif action == "enter_day":
            if hasattr(self, '_waiting_for_day_start') and self._waiting_for_day_start:
                self._waiting_for_day_start.set()
        
        elif action == "hunter_shoot":
            target_id = data.get("target_id")
            if target_id:
                await self.handle_hunter_shoot(target_id)
    
    async def _game_over(self) -> None:
        """游戏结束"""
        print("DEBUG: _game_over called")
        game_state = self.engine.game_state
        if not game_state:
            print("DEBUG: _game_over failed - no game state")
            return
        
        try:
            # 揭示所有玩家角色
            roles = [
                {
                    "id": p.id,
                    "name": p.name,
                    "role": p.role.value if p.role else None,
                    "role_name": RoleAction.get_role_name(p.role) if p.role else "未知",
                    "is_alive": p.is_alive(),
                    "death_reason": p.death_reason
                }
                for p in game_state.players
            ]
            
            await self.send_message("game_over", {
                "result": game_state.result.value,
                "winner": "狼人" if game_state.result == GameResult.WOLVES_WIN else "好人",
                "roles": roles,
                "message": self.engine.get_game_status_message()
            })
            
            # 播报游戏结束
            winner_text = "狼人胜利" if game_state.result == GameResult.WOLVES_WIN else "好人胜利"
            await self.send_message("announcement", {
                "content": f"游戏结束 - {winner_text}"
            })
        except Exception as e:
            print(f"ERROR in _game_over: {e}")
            import traceback
            traceback.print_exc()
