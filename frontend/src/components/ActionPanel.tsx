/**
 * 操作面板组件
 * 
 * 显示玩家可执行的操作（投票、技能使用等）
 */
import { useState, useEffect } from 'react';
import { Player, ActionRequired, RoleType } from '../types/game';
import './ActionPanel.css';

interface ActionPanelProps {
    /** 需要执行的操作 */
    action: ActionRequired;
    /** 玩家列表 */
    players: Player[];
    /** 真实玩家角色 */
    humanRole: RoleType | null;
    /** 女巫的狼人目标 */
    wolfTarget?: number;
    /** 执行操作回调 */
    onAction: (action: string, data: Record<string, unknown>) => void;
}

/**
 * 操作面板组件
 */
export function ActionPanel({
    action,
    players,
    // humanRole, // 保留参数但暂不使用
    wolfTarget,
    onAction
}: ActionPanelProps) {
    const [selectedTarget, setSelectedTarget] = useState<number | null>(null);
    const [witchChoice, setWitchChoice] = useState<'save' | 'poison' | 'pass' | null>(null);
    const [speechContent, setSpeechContent] = useState('');
    const [timeLeft, setTimeLeft] = useState(30);

    // 倒计时逻辑
    useEffect(() => {
        if (action.action === 'speak' && action.timeLimit) {
            setTimeLeft(action.timeLimit);
            const timer = setInterval(() => {
                setTimeLeft((prev) => {
                    if (prev <= 1) {
                        clearInterval(timer);
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);
            return () => clearInterval(timer);
        }
    }, [action]);

    const validTargets = action.validTargets || [];
    const selectablePlayers = players.filter(p => validTargets.includes(p.id));

    const handleConfirm = () => {
        switch (action.action) {
            case 'wolf_kill':
                if (selectedTarget) {
                    onAction('wolf_kill', { target_id: selectedTarget });
                }
                break;
            case 'seer_check':
                if (selectedTarget) {
                    onAction('seer_check', { target_id: selectedTarget });
                    setHasConfirmedCheck(true);
                }
                break;
            case 'witch_action':
                if (witchChoice === 'save') {
                    onAction('witch_action', { save: true, poison_target: null });
                } else if (witchChoice === 'poison' && selectedTarget) {
                    onAction('witch_action', { save: false, poison_target: selectedTarget });
                } else {
                    onAction('witch_action', { save: false, poison_target: null });
                }
                break;
            case 'vote':
                if (selectedTarget) {
                    onAction('vote', { target_id: selectedTarget });
                }
                break;
            case 'hunter_shoot':
                if (selectedTarget) {
                    onAction('hunter_shoot', { target_id: selectedTarget });
                }

                break;
            case 'speak':
                onAction('speak', { content: speechContent });
                break;
        }
    };

    // 预言家查验结果状态
    const [checkResult, setCheckResult] = useState<{targetId: number, isGood: boolean} | null>(null);
    // 是否已确认查验（用于隐藏确认按钮）
    const [hasConfirmedCheck, setHasConfirmedCheck] = useState(false);
    
    // 监听 WebSocket 消息获取查验结果
    useEffect(() => {
        const handleSeerResult = (event: Event) => {
            const customEvent = event as CustomEvent;
            setCheckResult({
                targetId: customEvent.detail.target_id,
                isGood: customEvent.detail.is_good
            });
            
            // 3秒后清除结果
            setTimeout(() => {
                setCheckResult(null);
                // 这里不重置 hasConfirmedCheck，等待后端推动阶段变化
            }, 3000);
        };
        
        window.addEventListener('seer_result', handleSeerResult);
        return () => window.removeEventListener('seer_result', handleSeerResult);
    }, []);

    // 当 action 变化时（例如进入新回合），重置 hasConfirmedCheck
    useEffect(() => {
        setHasConfirmedCheck(false);
    }, [action]);

    // 动作标题
    const getActionTitle = () => {
        switch (action.action) {
            case 'wolf_kill': return '🐺 狼人杀人';
            case 'seer_check': return '🔮 预言家查验';
            case 'witch_action': return '🧪 女巫行动';
            case 'vote': return '🗳️ 投票';
            case 'hunter_shoot': return '🔫 猎人开枪';
            case 'speak': return '🗣️ 请发言';
            case 'wait': return '⏳ 等待中';
            default: return '操作';
        }
    };

    const getTargetPlayer = (id: number) => players.find(p => p.id === id);

    // 等待状态显示
    if (action.action === 'wait') {
        return (
            <div className="action-panel card animate-scale-in waiting">
                <div className="wait-content">
                    <div className="loading-spinner"></div>
                    <div className="wait-text">
                        <h3>{getActionTitle()}</h3>
                        <p>{action.message}</p>
                    </div>
                </div>
            </div>
        );
    }

    // 确认结果状态（如预言家查验结果）
    // 已废弃，通过翻转卡片实现
    if (action.action === 'confirm_result') {
        return null;
    }

    return (
        <div className="action-panel card animate-scale-in">
            {/* 标题 */}
            <div className="action-header">
                <h3>{getActionTitle()}</h3>
            </div>

            {/* 操作提示 */}
            <p className="action-message">{action.message}</p>

            {/* 女巫特殊操作 */}
            {action.action === 'witch_action' && (
                <>
                    {/* 给女巫的特别提示 */}
                    <div className="night-alert">
                        <h4>🌙 今夜情况</h4>
                        {action.hasAntidote && wolfTarget ? (
                            <p className="alert-content">
                                狼人袭击了 <span className="highlight-target">{getTargetPlayer(wolfTarget)?.name}</span> ({wolfTarget}号)
                            </p>
                        ) : (
                            <p className="alert-content safe">
                                今夜平安，无人死亡 (或你已用过解药)
                            </p>
                        )}
                    </div>

                    <div className="witch-actions">
                        {/* 解药选项 */}
                        {action.canSave && action.hasAntidote && wolfTarget && (
                            <div className="witch-option">
                                <div className="option-info">
                                    <span className="option-icon">💊</span>
                                    <div>
                                        <span className="option-title">使用解药</span>
                                        <span className="option-desc">
                                            救活 {getTargetPlayer(wolfTarget)?.name}（{wolfTarget}号）
                                        </span>
                                    </div>
                                </div>
                                <button
                                    className={`btn ${witchChoice === 'save' ? 'btn-primary' : 'btn-secondary'}`}
                                    onClick={() => {
                                        setWitchChoice('save');
                                        setSelectedTarget(null);
                                        // 救人直接执行，不需要确认
                                        onAction('witch_action', { save: true, poison_target: null });
                                    }}
                                >
                                    救人
                                </button>
                            </div>
                        )}

                        {/* 毒药选项 */}
                        {action.hasPoison && (!action.canSave || witchChoice !== 'save') && (
                            <div className="witch-option">
                                <div className="option-info">
                                    <span className="option-icon">☠️</span>
                                    <div>
                                        <span className="option-title">使用毒药</span>
                                        <span className="option-desc">选择一名玩家毒死</span>
                                    </div>
                                </div>
                                <button
                                    className={`btn ${witchChoice === 'poison' ? 'btn-primary' : 'btn-secondary'}`}
                                    onClick={() => setWitchChoice('poison')}
                                >
                                    毒人
                                </button>
                            </div>
                        )}

                        {/* 跳过选项 */}
                        <div className="witch-option">
                            <div className="option-info">
                                <span className="option-icon">⏭️</span>
                                <div>
                                    <span className="option-title">不使用药水</span>
                                    <span className="option-desc">跳过本回合</span>
                                </div>
                            </div>
                            <button
                                className={`btn ${witchChoice === 'pass' ? 'btn-primary' : 'btn-secondary'}`}
                                onClick={() => {
                                    setWitchChoice('pass');
                                    setSelectedTarget(null);
                                    // 直接触发操作，不需要再点确认
                                    onAction('witch_action', { save: false, poison_target: null });
                                }}
                            >
                                跳过
                            </button>
                        </div>
                    </div>
                </>
            )}

            {/* 目标选择列表 */}
            {(action.action !== 'witch_action' || witchChoice === 'poison') && (
                <div className="target-list">
                    {/* 移除重复的标题 "选择目标"，因为上下文已经很明确 */}
                    {/* <h4>选择目标</h4> */}
                    <div className="targets-grid">
                        {selectablePlayers.map(player => {
                            // 如果是预言家查验且已出结果，且该玩家是查验对象
                            const isChecked = action.action === 'seer_check' && checkResult?.targetId === player.id;
                            const isGood = checkResult?.isGood;

                            return (
                                <button
                                    key={player.id}
                                    className={`target-btn ${selectedTarget === player.id ? 'selected' : ''} ${isChecked ? 'checked' : ''}`}
                                    onClick={() => setSelectedTarget(player.id)}
                                    disabled={isChecked}
                                >
                                    {isChecked ? (
                                        <div className="target-result animate-flip-in">
                                            <div className="result-icon">{isGood ? '😇' : '🐺'}</div>
                                            <span className="result-text">{isGood ? '好人' : '狼人'}</span>
                                        </div>
                                    ) : (
                                        <>
                                            <div className="target-avatar">
                                                {player.id}
                                            </div>
                                            <span className="target-name">{player.name}</span>
                                            {action.teammates?.includes(player.id) && (
                                                <span className="teammate-badge">队友</span>
                                            )}
                                        </>
                                    )}
                                </button>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* 狼人队友提示 */}
            {action.action === 'wolf_kill' && action.teammates && action.teammates.length > 0 && (
                <div className="teammates-hint">
                    <span className="hint-icon">🐺</span>
                    你的狼人队友：{action.teammates.map(id => `${id}号`).join('、')}
                </div>
            )}

            {/* 发言输入框 */}
            {action.action === 'speak' && (
                <div className="speech-input-area">
                    <div className="timer-display" style={{
                        color: timeLeft < 10 ? 'var(--color-danger)' : 'var(--color-text-primary)',
                        fontWeight: 'bold',
                        marginBottom: '10px',
                        textAlign: 'center'
                    }}>
                        ⏱️ 剩余时间: {timeLeft}秒
                    </div>
                    <textarea
                        className="speech-textarea"
                        value={speechContent}
                        onChange={(e) => setSpeechContent(e.target.value)}
                        placeholder="请输入发言内容..."
                        maxLength={200}
                        style={{
                            width: '100%',
                            minHeight: '100px',
                            padding: '12px',
                            borderRadius: '8px',
                            border: '1px solid var(--color-border)',
                            background: 'rgba(0, 0, 0, 0.2)',
                            color: 'var(--color-text-primary)',
                            resize: 'vertical',
                            marginBottom: '16px'
                        }}
                    />
                </div>
            )}

            {/* 确认按钮 */}
            {/* 只在需要确认操作时显示按钮 */}
            {/* 女巫阶段：只有选择了"毒人"才显示确认按钮，"救人"和"跳过"直接触发 */}
            {/* 预言家阶段：如果已确认查验，则隐藏按钮 */}
            {/* 其他阶段：始终显示确认按钮 */}
            {(action.action !== 'witch_action' || witchChoice === 'poison') && 
             !(action.action === 'seer_check' && hasConfirmedCheck) && (
                <div className="action-footer">
                    <button
                        className="btn btn-primary confirm-btn"
                        onClick={handleConfirm}
                        disabled={
                            // 女巫毒人时，必须选了目标
                            (action.action === 'witch_action' && witchChoice === 'poison' && !selectedTarget) ||
                            // 其他操作（除了发言），必须选了目标
                            (action.action !== 'witch_action' && action.action !== 'speak' && !selectedTarget) ||
                            // 发言时，内容不能为空
                            (action.action === 'speak' && !speechContent.trim())
                        }
                    >
                        {action.action === 'speak' ? '结束发言' : '确认'}
                    </button>
                </div>
            )}
        </div>
    );
}
