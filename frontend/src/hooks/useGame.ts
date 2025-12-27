/**
 * 游戏状态 Hook
 * 
 * 管理游戏整体状态
 */
import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from './useWebSocket';
import {
    Player,
    GamePhase,
    GameResult,
    SpeechRecord,
    ActionRequired,
    RoleType
} from '../types/game';

interface GameData {
    /** 游戏 ID */
    gameId: string | null;
    /** 玩家列表 */
    players: Player[];
    /** 当前阶段 */
    phase: GamePhase;
    /** 当前回合 */
    round: number;
    /** 当前发言者 */
    currentSpeaker: number | null;
    /** 真实玩家 ID */
    humanPlayerId: number | null;
    /** 真实玩家角色 */
    humanRole: RoleType | null;
    /** 真实玩家角色名 */
    humanRoleName: string;
    /** 角色描述 */
    roleDescription: string;
    /** 游戏结果 */
    result: GameResult;
    /** 发言记录 */
    speeches: SpeechRecord[];
    /** 系统消息 */
    systemMessages: string[];
    /** 当前需要的操作 */
    actionRequired: ActionRequired | null;
    /** 夜晚结果消息 */
    nightMessages: string[];
    /** 是否游戏进行中 */
    isGameRunning: boolean;
    /** 是否已确认角色（用于控制 UI 流程） */
    hasConfirmedRole: boolean;
    /** 当前公告 */
    announcement?: string | null;
    /** 正在思考的玩家 ID */
    thinkingPlayerId?: number | null;
    /** 正在投票思考的玩家 ID */
    votingThinkingPlayerIds?: number[];
    /** 已投票的玩家 ID 列表 */
    votedPlayerIds?: number[];
    /** 夜晚当前行动提示语 */
    nightActionMessage?: string | null;
    /** 狼人队友 ID 列表 */
    teammates?: number[];
}

interface UseGameReturn extends GameData {
    /** 连接状态 */
    isConnected: boolean;
    /** 创建游戏 */
    createGame: (playerName: string) => void;
    /** 开始游戏 */
    startGame: () => void;
    /** 执行操作 */
    performAction: (action: string, data: Record<string, unknown>) => void;
    /** 连接服务器 */
    connect: () => void;
    /** 重置游戏 */
    resetGame: () => void;
    /** 清除公告 */
    clearAnnouncement: () => void;
    /** 确认角色 */
    confirmRole: () => void;
}

/**
 * 游戏状态管理 Hook
 */
export function useGame(): UseGameReturn {
    const { isConnected, lastMessage, sendMessage, connect } = useWebSocket();

    const [gameData, setGameData] = useState<GameData>({
        gameId: null,
        players: [],
        phase: 'waiting',
        round: 0,
        currentSpeaker: null,
        humanPlayerId: null,
        humanRole: null,
        humanRoleName: '',
        roleDescription: '',
        result: 'ongoing',
        speeches: [],
        systemMessages: [],
        actionRequired: null,
        nightMessages: [],
        isGameRunning: false,
        hasConfirmedRole: false,
        thinkingPlayerId: null,
        votingThinkingPlayerIds: [],
        votedPlayerIds: [],
        nightActionMessage: null,
        announcement: null,
        teammates: []
    });

    /**
     * 确认角色
     */
    const confirmRole = useCallback(() => {
        setGameData(prev => ({
            ...prev,
            hasConfirmedRole: true
        }));
        // 通知后端开始游戏
        sendMessage('action', { action: 'role_confirmed', data: {} });
    }, [sendMessage]);

    /**
     * 清除公告
     */
    const clearAnnouncement = useCallback(() => {
        setGameData(prev => ({
            ...prev,
            announcement: null
        }));
    }, []);

    /**
     * 处理 WebSocket 消息
     */
    useEffect(() => {
        if (!lastMessage) return;

        const { type, data } = lastMessage;

        switch (type) {
            case 'announcement':
                // 如果是"请闭眼"类的公告，说明当前阶段结束，清除操作面板
                if (data.content && (data.content as string).includes('请闭眼')) {
                    setGameData(prev => ({
                        ...prev,
                        announcement: data.content as string,
                        actionRequired: null // 强制清除操作面板
                    }));
                } else {
                    setGameData(prev => ({
                        ...prev,
                        announcement: data.content as string
                    }));
                }
                break;

            case 'reset_vote':
                // 重置投票状态：所有存活玩家进入投票思考状态，已投票列表清空
                setGameData(prev => ({
                    ...prev,
                    votedPlayerIds: [],
                    votingThinkingPlayerIds: prev.players
                        .filter(p => p.status === 'alive' && p.isAlive) // 确保只选存活玩家
                        .map(p => p.id) 
                }));
                break;

            case 'game_created':
                setGameData(prev => ({
                    ...prev,
                    gameId: data.game_id as string,
                    players: (data.players as Array<{ id: number; name: string; is_human: boolean }>).map(p => ({
                        id: Number(p.id),
                        name: p.name,
                        isHuman: p.is_human,
                        status: 'alive' as const,
                        isAlive: true
                    })),
                    systemMessages: [...prev.systemMessages, '游戏房间已创建']
                }));
                break;

            case 'role_assigned':
                setGameData(prev => ({
                    ...prev,
                    humanPlayerId: Number(data.player_id),
                    humanRole: data.role as RoleType,
                    humanRoleName: data.role_name as string,
                    roleDescription: data.role_description as string,
                    isGameRunning: true, // 确保收到角色分配也能进入游戏
                    systemMessages: [...prev.systemMessages, `你的身份是：${data.role_name}`],
                    teammates: data.teammates ? (data.teammates as unknown[]).map(id => Number(id)) : []
                }));
                break;

            case 'game_started':
                setGameData(prev => ({
                    ...prev,
                    round: data.round as number,
                    phase: data.phase as GamePhase,
                    isGameRunning: true,
                    systemMessages: [...prev.systemMessages, '游戏开始！']
                }));
                break;

            case 'phase_change':
                setGameData(prev => ({
                    ...prev,
                    phase: data.phase as GamePhase,
                    isGameRunning: true, // 容错：确保进入游戏
                    systemMessages: [...prev.systemMessages, data.message as string],
                    actionRequired: null,
                    currentSpeaker: null, // 切换阶段时清除发言者状态
                    votedPlayerIds: [], // 切换阶段清除投票状态
                    votingThinkingPlayerIds: [] // 切换阶段清除投票思考状态，具体的初始化由 reset_vote 消息处理
                }));
                break;

            case 'action_required':
                setGameData(prev => ({
                    ...prev,
                    // 如果是女巫行动，强制清除之前的预言家查验结果面板（如果还在）
                    // 虽然 actionRequired 会被覆盖，但显式处理更清晰
                    actionRequired: {
                        action: data.action as ActionRequired['action'],
                        message: data.message as string,
                        validTargets: (data.valid_targets as unknown[] | undefined)?.map(id => Number(id)),
                        timeLimit: data.time_limit as number | undefined,
                        wolfTarget: data.wolf_target ? Number(data.wolf_target) : undefined,
                        canSave: data.can_save as boolean | undefined,
                        hasAntidote: data.has_antidote as boolean | undefined,
                        hasPoison: data.has_poison as boolean | undefined,
                        validPoisonTargets: (data.valid_poison_targets as unknown[] | undefined)?.map(id => Number(id)),
                        teammates: (data.teammates as unknown[] | undefined)?.map(id => Number(id))
                    }
                }));
                break;

            case 'speaker_turn':
                setGameData(prev => ({
                    ...prev,
                    currentSpeaker: Number(data.speaker_id),
                    systemMessages: [...prev.systemMessages,
                    `${data.speaker_name} (${data.speaker_id}号) 开始发言`
                    ]
                }));
                break;

            case 'thinking_start': {
                const isVoting = data.action === 'vote';
                const playerId = Number(data.player_id);
                
                if (isVoting) {
                    // 投票思考状态已在 reset_vote 中统一初始化，这里不需要额外操作
                    // 或者如果需要精确控制，可以确认该 ID 在列表中
                    return;
                }

                setGameData(prev => ({
                    ...prev,
                    thinkingPlayerId: playerId
                }));
                break;
            }

            case 'player_voted':
                setGameData(prev => {
                    const votedId = Number(data.player_id);
                    // 确保不重复添加
                    if (prev.votedPlayerIds?.includes(votedId)) {
                        return prev;
                    }
                    console.log(`Player ${votedId} voted. Updating state.`);
                    return {
                        ...prev,
                        votingThinkingPlayerIds: (prev.votingThinkingPlayerIds || []).filter(id => id !== votedId), // 移除思考状态
                        votedPlayerIds: [...(prev.votedPlayerIds || []), votedId]
                    };
                });
                break;

            case 'night_action_change':
                setGameData(prev => ({
                    ...prev,
                    nightActionMessage: data.message as string
                }));
                break;

            case 'player_speech':
                setGameData(prev => ({
                    ...prev,
                    thinkingPlayerId: null, // 发言时清除思考状态
                    // 确保不重复添加相同的发言（基于内容和发言者）
                    speeches: prev.speeches.some(s => 
                        s.playerId === Number(data.speaker_id) && 
                        s.content === (data.content as string)
                    ) ? prev.speeches : [...prev.speeches, {
                        playerId: Number(data.speaker_id),
                        playerName: data.speaker_name as string,
                        content: data.content as string,
                        round: prev.round,
                        phase: prev.phase
                    }],
                    actionRequired: prev.actionRequired?.action === 'speak' ? null : prev.actionRequired
                }));
                break;

            case 'night_result':
                setGameData(prev => ({
                    ...prev,
                    nightMessages: data.messages as string[],
                    systemMessages: [...prev.systemMessages, ...(data.messages as string[])],
                    // 同步玩家状态（如死亡）
                    players: data.players 
                        ? (data.players as Array<{ id: number; name: string; is_human: boolean; is_alive: boolean }>).map(p => ({
                            id: Number(p.id),
                            name: p.name,
                            isHuman: p.is_human,
                            status: p.is_alive ? 'alive' as const : 'dead' as const,
                            isAlive: p.is_alive,
                            role: prev.players.find(old => old.id === Number(p.id))?.role, // 保留已知角色
                            roleName: prev.players.find(old => old.id === Number(p.id))?.roleName // 保留已知角色名
                        }))
                        : prev.players
                }));
                break;

            case 'vote_result':
                {
                    const executedId = Number(data.executed_id);
                    const msg = data.is_tie
                        ? '平票，直接进入夜晚'
                        : `${data.executed_name} 被投票出局`;
                    setGameData(prev => ({
                        ...prev,
                        systemMessages: [...prev.systemMessages, msg],
                        players: prev.players.map(p =>
                            p.id === executedId
                                ? { ...p, status: 'dead' as const, isAlive: false }
                                : p
                        )
                    }));
                }
                break;

            case 'seer_result':
                {
                    const resultText = data.is_good ? '好人' : '狼人';
                    setGameData(prev => ({
                        ...prev,
                        systemMessages: [...prev.systemMessages,
                        `查验结果：${data.target_name} 是 ${resultText}`
                        ]
                    }));
                    // 触发自定义事件通知 ActionPanel
                    window.dispatchEvent(new CustomEvent('seer_result', { detail: data }));
                }
                break;

            case 'hunter_shoot_result':
                {
                    const targetId = Number(data.target_id);
                    setGameData(prev => ({
                        ...prev,
                        systemMessages: [...prev.systemMessages,
                        `猎人带走了 ${data.target_name}`
                        ],
                        players: prev.players.map(p =>
                            p.id === targetId
                                ? { ...p, status: 'dead' as const, isAlive: false }
                                : p
                        )
                    }));
                }
                break;

            case 'game_over':
                setGameData(prev => ({
                    ...prev,
                    phase: 'game_over',
                    result: data.result as GameResult,
                    isGameRunning: true, // 保持为 true 以显示游戏结束面板
                    players: (data.roles as Array<{
                        id: number;
                        name: string;
                        role: RoleType;
                        role_name: string;
                        is_alive: boolean;
                    }>).map(r => ({
                        id: Number(r.id),
                        name: r.name,
                        role: r.role,
                        roleName: r.role_name,
                        status: r.is_alive ? 'alive' as const : 'dead' as const,
                        isAlive: r.is_alive,
                        isHuman: prev.players.find(p => p.id === Number(r.id))?.isHuman || false
                    })),
                    systemMessages: [...prev.systemMessages, data.message as string]
                }));
                break;
        }
    }, [lastMessage]);

    /**
     * 创建游戏
     */
    const createGame = useCallback((playerName: string) => {
        sendMessage('create_game', { player_name: playerName });
    }, [sendMessage]);

    /**
     * 开始游戏
     */
    const startGame = useCallback(() => {
        sendMessage('start_game');
    }, [sendMessage]);

    /**
     * 执行操作
     */
    const performAction = useCallback((action: string, data: Record<string, unknown>) => {
        sendMessage('action', { action, data });
        
        // 对于预言家查验，不要立即清除 actionRequired
        // 因为我们需要保留 ActionPanel 来显示查验结果（翻转动画）
        // 只有当收到新的状态更新（如进入下一阶段）时，ActionPanel 才会自然消失
        if (action !== 'seer_check') {
            setGameData(prev => ({
                ...prev,
                actionRequired: null
            }));
        }
    }, [sendMessage]);

    /**
     * 重置游戏状态（保留连接）
     */
    const resetGame = useCallback(() => {
        setGameData({
            gameId: null,
            players: [],
            phase: 'waiting',
            round: 0,
            currentSpeaker: null,
            humanPlayerId: null,
            humanRole: null,
            humanRoleName: '',
            roleDescription: '',
            result: 'ongoing',
            speeches: [],
            systemMessages: [],
            actionRequired: null,
            nightMessages: [],
            isGameRunning: false,
            hasConfirmedRole: false,
            thinkingPlayerId: null,
            votingThinkingPlayerIds: [],
            votedPlayerIds: [],
            nightActionMessage: null,
            announcement: null
        });
    }, []);

    return {
        ...gameData,
        isConnected,
        createGame,
        startGame,
        performAction,
        connect,
        resetGame,
        clearAnnouncement,
        confirmRole
    };
}
