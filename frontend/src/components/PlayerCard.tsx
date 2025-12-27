/**
 * 玩家卡片组件
 * 
 * 显示单个玩家的状态信息
 */
import { Player, ROLE_NAMES, RoleType } from '../types/game';
import { ROLE_COLORS } from '../utils/constants';
import './PlayerCard.css';

interface PlayerCardProps {
    /** 玩家信息 */
    player: Player;
    /** 是否正在发言 */
    isSpeaking?: boolean;
    /** 是否正在思考 */
    isThinking?: boolean;
    /** 是否可选中 */
    isSelectable?: boolean;
    /** 是否已选中 */
    isSelected?: boolean;
    /** 是否显示角色 */
    showRole?: boolean;
    /** 是否有新的发言内容（用于控制状态显示） */
    hasNewSpeech?: boolean;
    /** 是否正在投票思考 */
    isVotingThinking?: boolean;
    /** 是否已投票 */
    hasVoted?: boolean;
    /** 是否是队友 */
    isTeammate?: boolean;
    /** 点击回调 */
    onClick?: () => void;
}

/**
 * 玩家卡片组件
 */
export function PlayerCard({
    player,
    isSpeaking = false,
    isThinking = false,
    isSelectable = false,
    isSelected = false,
    showRole = false,
    isVotingThinking = false,
    hasVoted = false,
    isTeammate = false,
    onClick
}: PlayerCardProps) {
    // 状态显示逻辑优化
    // isThinking: 显示 "思考中..."
    // isSpeaking: 显示 "发言中..."
    
    const roleColor = player.role
        ? ROLE_COLORS[player.role]
        : ROLE_COLORS.unknown;

    const roleName = player.role
        ? ROLE_NAMES[player.role as RoleType]
        : (player.roleName || '???');

    const cardClasses = [
        'player-card',
        player.isAlive ? 'alive' : 'dead',
        isSpeaking ? 'speaking' : '',
        isSelectable ? 'selectable' : '',
        isSelected ? 'selected' : '',
        player.isHuman ? 'human' : 'ai'
    ].filter(Boolean).join(' ');

    return (
        <div
            className={cardClasses}
            onClick={isSelectable ? onClick : undefined}
            style={{ '--role-color': roleColor } as React.CSSProperties}
        >
            {/* 发言光晕 */}
            {isSpeaking && <div className="speaking-glow"></div>}

            {/* 头像区域 */}
            <div className="player-avatar">
                <div className="avatar-circle">
                    <span className="avatar-number">{player.id}</span>
                </div>
                {player.isHuman && <div className="human-badge">你</div>}
                {isTeammate && !player.isHuman && <div className="teammate-badge">队友</div>}
            </div>

            {/* 玩家信息 */}
            <div className="player-info">
                <span className="player-name">{player.name}</span>
                {showRole && (
                    <span className="player-role" style={{ color: roleColor }}>
                        {roleName}
                    </span>
                )}
            </div>

            {/* 状态指示 */}
            <div className="player-status">
                {!player.isAlive && (
                    <div className="status-dead-overlay">
                         <span className="dead-mark">出局</span>
                    </div>
                )}
                {/* 投票中状态 */}
                {isVotingThinking && !hasVoted && (
                    <div className="status-badge thinking">
                        <span className="text">投票中</span>
                        <span className="dot"></span>
                        <span className="dot"></span>
                        <span className="dot"></span>
                    </div>
                )}
                {hasVoted && (
                    <div className="status-badge voted">
                        <span className="icon">✅</span>
                        <span className="text">已投票</span>
                    </div>
                )}
                {/* 思考中状态：最低优先级，仅在非投票、非已投票时显示 */}
                {isThinking && !isVotingThinking && !hasVoted && (
                    <div className="status-badge thinking">
                        <span className="text">思考中</span>
                        <span className="dot"></span>
                        <span className="dot"></span>
                        <span className="dot"></span>
                    </div>
                )}
            </div>

            {/* 选中效果 */}
            {isSelected && <div className="selected-indicator">✓</div>}
        </div>
    );
}
