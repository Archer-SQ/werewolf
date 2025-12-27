/**
 * 游戏类型定义
 * 
 * 定义与后端交互的所有数据结构
 */

/** 角色类型 */
export type RoleType = 'werewolf' | 'seer' | 'witch' | 'hunter' | 'villager';

/** 游戏阶段 */
export type GamePhase = 
  | 'waiting'
  | 'night'
  | 'night_wolf'
  | 'night_seer'
  | 'night_witch'
  | 'day'
  | 'day_discuss'
  | 'day_vote'
  | 'hunter_shoot'
  | 'game_over';

/** 游戏结果 */
export type GameResult = 'wolves_win' | 'villagers_win' | 'ongoing';

/** 玩家状态 */
export type PlayerStatus = 'alive' | 'dead' | 'poisoned';

/** 玩家信息 */
export interface Player {
  id: number;
  name: string;
  role?: RoleType;
  roleName?: string;
  status: PlayerStatus;
  isHuman: boolean;
  isAlive: boolean;
}

/** 发言记录 */
export interface SpeechRecord {
  playerId: number;
  playerName: string;
  content: string;
  round: number;
  phase: GamePhase;
}

/** 投票详情 */
export interface VoteDetail {
  targetId: number;
  votes: number;
}

/** 游戏状态 */
export interface GameState {
  gameId: string;
  players: Player[];
  phase: GamePhase;
  round: number;
  currentSpeaker: number | null;
  humanPlayerId: number | null;
  result: GameResult;
}

/** WebSocket 消息类型 */
export type MessageType = 
  | 'game_created'
  | 'role_assigned'
  | 'game_started'
  | 'phase_change'
  | 'action_required'
  | 'speaker_turn'
  | 'player_speech'
  | 'night_result'
  | 'vote_result'
  | 'seer_result'
  | 'hunter_shoot_result'
  | 'game_over'
  | 'pong'
  | 'night_action_change'
  | 'announcement'
  | 'thinking_start'
  | 'player_voted'
  | 'reset_vote';

/** WebSocket 消息 */
export interface WSMessage {
  type: MessageType;
  data: Record<string, unknown>;
}

/** 操作类型 */
export type ActionType = 
  | 'wolf_kill'
  | 'seer_check'
  | 'witch_action'
  | 'speak'
  | 'vote'
  | 'hunter_shoot'
  | 'wait'
  | 'confirm_result';

/** 操作请求 */
export interface ActionRequired {
  action: ActionType;
  message: string;
  validTargets?: number[];
  timeLimit?: number;
  wolfTarget?: number;
  canSave?: boolean;
  hasAntidote?: boolean;
  hasPoison?: boolean;
  validPoisonTargets?: number[];
  teammates?: number[];
  result_data?: {
    target_name: string;
    is_good: boolean;
  };
}

/** 角色中文名映射 */
export const ROLE_NAMES: Record<RoleType, string> = {
  werewolf: '狼人',
  seer: '预言家',
  witch: '女巫',
  hunter: '猎人',
  villager: '平民'
};

/** 角色描述映射 */
export const ROLE_DESCRIPTIONS: Record<RoleType, string> = {
  werewolf: '夜晚可以选择杀死一名玩家',
  seer: '夜晚可以查验一名玩家的身份',
  witch: '拥有一瓶解药和一瓶毒药',
  hunter: '死亡时可以开枪带走一名玩家',
  villager: '没有特殊技能，依靠推理投票'
};
