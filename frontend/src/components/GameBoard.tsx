/**
 * 游戏主界面组件
 * 
 * 游戏进行中的主界面，包含玩家列表、发言区、操作区
 */
import { useState, useEffect, useRef } from 'react';
import { Player, SpeechRecord, ActionRequired, GamePhase, RoleType, ROLE_NAMES } from '../types/game';
import { PHASE_NAMES } from '../utils/constants';
import { PlayerCard } from './PlayerCard';
import { ChatPanel } from './ChatPanel';
import { ActionPanel } from './ActionPanel';
import { ToastContainer, ToastMessage } from './Toast';
import { AnnouncementOverlay } from './AnnouncementOverlay';
import './GameBoard.css';

interface GameBoardProps {
    /** 玩家列表 */
    players: Player[];
    /** 当前阶段 */
    phase: GamePhase;
    /** 当前回合 */
    round: number;
    /** 当前发言者 */
    currentSpeaker: number | null;
    /** 正在思考的玩家 */
    thinkingPlayerId?: number | null;
    /** 正在投票思考的玩家列表 */
    votingThinkingPlayerIds?: number[];
    /** 已投票的玩家列表 */
    votedPlayerIds?: number[];
    /** 夜晚当前行动提示语 */
    nightActionMessage?: string | null;
    /** 真实玩家 ID */
    humanPlayerId: number | null;
    /** 真实玩家角色 */
    humanRole: RoleType | null;
    /** 角色名称 */
    humanRoleName: string;
    /** 角色描述 */
    roleDescription: string;
    /** 发言记录 */
    speeches: SpeechRecord[];
    /** 系统消息 */
    systemMessages: string[];
    /** 需要的操作 */
    actionRequired: ActionRequired | null;
    /** 游戏结果 */
    gameResult: 'wolves_win' | 'villagers_win' | 'ongoing';
    /** 发言回调 */
    onSpeak: (content: string) => void;
    /** 操作回调 */
    onAction: (action: string, data: Record<string, unknown>) => void;
    /** 当前公告 */
    announcement?: string | null;
    /** 清除公告回调 */
    onClearAnnouncement?: () => void;
    /** 重置游戏回调 */
    onResetGame?: () => void;
    /** 返回首页回调 */
    onBackToHome?: () => void;
    /** 连接状态 */
    isConnected: boolean;
    /** 狼人队友列表 */
    teammates?: number[];
}

/**
 * 游戏主界面组件
 */
export function GameBoard({
    players,
    phase,
    round,
    currentSpeaker,
    thinkingPlayerId,
    // votingThinkingPlayerIds, // 暂不使用后端传递的投票思考状态，改为前端根据阶段判断
    votedPlayerIds,
    nightActionMessage,
    humanPlayerId,
    humanRole,
    humanRoleName,
    roleDescription,
    speeches,
    systemMessages,
    actionRequired,
    gameResult,
    onSpeak,
    onAction,
    announcement,
    onClearAnnouncement,
    onResetGame,
    onBackToHome,
    isConnected,
    teammates
}: GameBoardProps) {
    const isNight = phase.startsWith('night');
    const humanPlayer = players.find(p => p.id === humanPlayerId);
    const isHumanTurn = actionRequired?.action === 'speak';

    // Toast 状态管理
    const [toasts, setToasts] = useState<ToastMessage[]>([]);
    const lastMsgCountRef = useRef(0);

    // 监听系统消息变化，生成 Toast
    useEffect(() => {
        if (systemMessages.length > lastMsgCountRef.current) {
            const newMessages = systemMessages.slice(lastMsgCountRef.current);
            // 只保留最新的一条消息
            if (newMessages.length > 0) {
                const latestMsg = newMessages[newMessages.length - 1];
                setToasts([{
                    id: Date.now(),
                    content: latestMsg,
                    type: 'info' as const
                }]);
            }
            lastMsgCountRef.current = systemMessages.length;
        }
    }, [systemMessages]);

    const removeToast = (id: number) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    };

    return (
        <div className={`game-board ${isNight ? 'theme-night' : 'theme-day'}`}>
            {/* 系统消息弹窗 */}
            <ToastContainer messages={toasts} onRemove={removeToast} />

            {/* 游戏流程遮罩（替代弹窗） */}
            <AnnouncementOverlay
                message={
                    isNight ? (announcement || nightActionMessage || '天黑请闭眼') : null
                }
                round={round}
                forceVisible={isNight} // 只要是夜晚就强制显示
                mode={isNight ? 'persistent' : 'auto'} // 夜晚模式下持续显示
                hasAction={!!actionRequired}
                onComplete={onClearAnnouncement}
                isConnected={isConnected}
            >
                {/* 如果是夜晚且需要行动，将 ActionPanel 嵌入到遮罩中 */}
                {isNight && actionRequired && actionRequired.action !== 'speak' && (
                    <ActionPanel
                        action={actionRequired}
                        players={players}
                        humanRole={humanRole}
                        wolfTarget={actionRequired.wolfTarget}
                        onAction={onAction}
                    />
                )}
            </AnnouncementOverlay>

            {/* 顶部状态栏 */}
            <header className="game-header">
                <div className="header-left">
                    <span className="round-badge">第 {round} 轮</span>
                    <span className={`phase-badge ${isNight ? 'night' : 'day'}`}>
                        {isNight ? '🌙' : '☀️'} {PHASE_NAMES[phase] || phase}
                    </span>
                </div>
                <div className="header-center">
                    <h1 className="game-title">暗夜狼人杀</h1>
                </div>
                <div className="header-right">
                    {humanRole && (
                        <div className="my-role">
                            <span className="role-label">你的身份</span>
                            <span className="role-name">{humanRoleName}</span>
                        </div>
                    )}
                </div>
            </header>

            {/* 主内容区 */}
            <main className="game-main">
                {/* 左侧：玩家列表 */}
                <aside className="players-panel">
                    <div className="panel-header">
                        <h3>👥 玩家列表</h3>
                        <span className="alive-count">
                            存活: {players.filter(p => p.isAlive).length}/{players.length}
                        </span>
                    </div>
                    <div className="players-list">
                        {players.map(player => (
                            <PlayerCard
                                key={player.id}
                                player={player}
                                isThinking={thinkingPlayerId === player.id}
                                isVotingThinking={
                                    phase === 'day_vote' && 
                                    player.isAlive && 
                                    !votedPlayerIds?.includes(player.id)
                                }
                                hasVoted={votedPlayerIds?.includes(player.id)}
                                showRole={gameResult !== 'ongoing' || (player.isHuman && humanPlayer?.role !== undefined) || !player.isAlive}
                                isTeammate={teammates?.includes(player.id)}
                            />
                        ))}
                    </div>

                    {/* 角色说明 */}
                    {humanRole && roleDescription && (
                        <div className="role-description card">
                            <h4>{humanRoleName} 技能说明</h4>
                            <p>{roleDescription}</p>
                        </div>
                    )}
                </aside>

                {/* 中间：发言区/操作区 */}
                <section className="center-panel">
                    {/* 游戏结束 */}
                    {gameResult !== 'ongoing' ? (
                        <div className="game-over-panel animate-scale-in">
                            <div className="game-over-content">
                                <h2 className="game-over-title">
                                    {gameResult === 'wolves_win' ? '🐺 狼人胜利！' : '👥 好人胜利！'}
                                </h2>
                                <p className="game-over-desc">
                                    {gameResult === 'wolves_win'
                                        ? '狼人成功消灭了村民，夜幕永远笼罩这片土地...'
                                        : '村民们齐心协力，将所有狼人驱逐出村！'}
                                </p>
                                <div className="final-roles">
                                    <h4>角色揭晓</h4>
                                    <div className="roles-grid">
                                        {players.map(player => (
                                            <div key={player.id} className={`role-reveal ${player.isAlive ? '' : 'dead'}`}>
                                                <span className="reveal-number">{player.id}号</span>
                                                <span className="reveal-name">{player.name}</span>
                                                <span
                                                    className="reveal-role"
                                                    style={{ color: player.role ? `var(--color-${player.role})` : undefined }}
                                                >
                                                    {player.roleName || ROLE_NAMES[player.role as RoleType] || '???'}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                <div className="game-over-actions">
                                    <button 
                                        className="btn btn-primary restart-btn"
                                        onClick={onResetGame}
                                    >
                                        再来一局
                                    </button>
                                    <button 
                                        className="btn btn-secondary home-btn"
                                        onClick={onBackToHome}
                                    >
                                        回到首页
                                    </button>
                                </div>
                            </div>
                        </div>
                    ) : actionRequired && actionRequired.action !== 'speak' && actionRequired.action !== 'start_vote' && !isNight ? (
                        /* 白天操作面板（如投票） */
                        <ActionPanel
                            action={actionRequired}
                            players={players}
                            humanRole={humanRole}
                            wolfTarget={actionRequired.wolfTarget}
                            onAction={onAction}
                        />
                    ) : (
                        /* 发言面板 (或夜晚空状态，因为夜晚操作在 Overlay 中) */
                        <ChatPanel
                            speeches={speeches}
                            currentSpeaker={currentSpeaker}
                            isHumanTurn={isHumanTurn}
                            humanPlayerId={humanPlayerId}
                            onSpeak={onSpeak}
                            onStartVote={() => onAction('start_vote', {})}
                            isStartVoteRequired={actionRequired?.action === 'start_vote'}
                        />
                    )}
                </section>
            </main>
        </div>
    );
}
