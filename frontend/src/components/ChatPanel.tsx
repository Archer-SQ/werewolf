/**
 * 发言面板组件
 * 
 * 仅显示发言记录，移除系统消息标签页
 */
import { useState, useRef, useEffect } from 'react';
import { SpeechRecord } from '../types/game';
import './ChatPanel.css';

interface ChatPanelProps {
    /** 发言记录列表 */
    speeches: SpeechRecord[];
    /** 当前发言者 ID */
    currentSpeaker: number | null;
    /** 是否是真实玩家发言 */
    isHumanTurn: boolean;
    /** 真实玩家 ID */
    humanPlayerId: number | null;
    /** 发言回调 */
    onSpeak?: (content: string) => void;
}

/**
 * 发言面板组件
 */
export function ChatPanel({
    speeches,
    currentSpeaker,
    isHumanTurn,
    humanPlayerId,
    onSpeak
}: ChatPanelProps) {
    const [inputValue, setInputValue] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // 自动滚动到底部
    useEffect(() => {
        // 使用 setTimeout 确保 DOM 更新后再滚动
        setTimeout(() => {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
    }, [speeches]);

    const handleSubmit = () => {
        if (inputValue.trim() && onSpeak) {
            onSpeak(inputValue.trim());
            setInputValue('');
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <div className="chat-panel-container card-glass">
            <div className="panel-header">
                <h3>💬 游戏发言</h3>
                <span className="speech-count">{speeches.length} 条记录</span>
            </div>

            <div className="panel-content">
                <div className="message-list chat-list">
                    {speeches.length === 0 ? (
                        <div className="empty-tip">等待游戏开始发言...</div>
                    ) : (
                        speeches.map((msg, index) => (
                            <div
                                key={index}
                                className={`speech-item ${msg.playerId === humanPlayerId ? 'own' : ''} animate-slide-in`}
                            >
                                <div className="speech-avatar">
                                    <span className="avatar-num">{msg.playerId}</span>
                                </div>
                                <div className="speech-bubble">
                                    <div className="speech-name">{msg.playerId}号 {msg.playerName}</div>
                                    <div className="speech-content-box">
                                        {msg.content}
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* 底部保留位置，用于输入框或状态条 */}
            <div className={`input-area-wrapper ${isHumanTurn ? 'highlight' : ''}`}>
                {isHumanTurn ? (
                    <div className="human-input-area animate-slide-up">
                        <div className="input-header">
                            <span className="input-label">轮到你发言了</span>
                        </div>
                        <div className="input-box">
                            <input
                                type="text"
                                className="chat-input-field"
                                placeholder="请输入你的发言..."
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyPress={handleKeyPress}
                                autoFocus
                            />
                            <button
                                className="send-button"
                                onClick={handleSubmit}
                                disabled={!inputValue.trim()}
                            >
                                发送
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="status-bar">
                        {currentSpeaker && (!speeches.length || speeches[speeches.length - 1].playerId !== currentSpeaker) ? (
                            <>
                                <span className="status-icon pulse-icon">🎤</span>
                                <span className="status-text highlight-text">{currentSpeaker}号玩家正在发言...</span>
                            </>
                        ) : (
                            <span className="status-text">
                                {currentSpeaker ? `${currentSpeaker}号玩家发言结束` : '非发言阶段'}
                            </span>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
