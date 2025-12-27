/**
 * 游戏大厅组件
 * 
 * 游戏入口页面，显示游戏标题和开始按钮
 */
import { useState } from 'react';
import './GameLobby.css';

interface GameLobbyProps {
    /** 连接状态 */
    isConnected: boolean;
    /** 游戏是否已创建 */
    gameCreated: boolean;
    /** 连接服务器 */
    onConnect: () => void;
    /** 创建游戏 */
    onCreateGame: (playerName: string) => void;
    /** 开始游戏 */
    onStartGame: () => void;
}

/**
 * 游戏大厅组件
 */
export function GameLobby({
    isConnected,
    gameCreated,
    onConnect,
    onCreateGame,
    onStartGame
}: GameLobbyProps) {
    const [playerName, setPlayerName] = useState('玩家');
    const [isStarting, setIsStarting] = useState(false);

    const handleConnect = () => {
        onConnect();
    };

    const handleCreateGame = () => {
        if (playerName.trim()) {
            onCreateGame(playerName.trim());
        }
    };

    const handleStartGame = () => {
        setIsStarting(true);
        onStartGame();
        // 设置一个超时，如果5秒后通过props传入的状态还没变，重置按钮（可选，防止永久loading）
        setTimeout(() => setIsStarting(false), 5000);
    };

    return (
        <div className="lobby-container">
            {/* 背景动效 */}
            <div className="lobby-bg">
                <div className="aurora aurora-1"></div>
                <div className="aurora aurora-2"></div>
                <div className="aurora aurora-3"></div>
            </div>

            {/* 主内容 */}
            <div className="lobby-content animate-fade-in">
                {/* 标题 */}
                <div className="lobby-header">
                    <h1 className="lobby-title">
                        <span className="title-text">暗夜狼人杀</span>
                    </h1>
                    <p className="lobby-subtitle">
                        与 AI 共战的智能狼人杀体验
                    </p>
                </div>

                {/* 游戏卡片 */}
                <div className="lobby-card card card-glass">
                    {!isConnected ? (
                        <div className="lobby-step">
                            <div className="step-icon">🔌</div>
                            <h3>连接游戏服务器</h3>
                            <p>点击下方按钮连接到游戏服务器</p>
                            <button
                                className="btn btn-primary lobby-btn"
                                onClick={handleConnect}
                            >
                                连接服务器
                            </button>
                        </div>
                    ) : !gameCreated ? (
                        <div className="lobby-step">
                            <div className="step-icon">🎮</div>
                            <h3>设置你的名字</h3>
                            <div className="name-input-wrapper">
                                <input
                                    type="text"
                                    className="input name-input"
                                    placeholder="输入你的游戏名"
                                    value={playerName}
                                    onChange={(e) => setPlayerName(e.target.value)}
                                    maxLength={10}
                                />
                            </div>
                            <button
                                className="btn btn-primary lobby-btn"
                                onClick={handleCreateGame}
                                disabled={!playerName.trim()}
                            >
                                创建游戏
                            </button>
                        </div>
                    ) : (
                        <div className="lobby-step">
                            <div className="step-icon">✨</div>
                            <h3>准备就绪</h3>
                            <p>游戏房间已创建，点击开始游戏</p>
                            <button
                                className="btn btn-primary lobby-btn shiny-btn"
                                onClick={handleStartGame}
                                disabled={isStarting}
                            >
                                {isStarting ? '正在启动...' : '开始游戏'}
                            </button>
                        </div>
                    )}
                </div>

                {/* 游戏规则 */}
                <div className="lobby-rules card">
                    <h3>📜 游戏规则</h3>
                    <div className="rules-grid">
                        <div className="rule-item">
                            <span className="rule-icon">👥</span>
                            <span>7人局：1真实玩家 + 6 AI</span>
                        </div>
                        <div className="rule-item">
                            <span className="rule-icon">🐺</span>
                            <span>2狼人 + 1预言家 + 1女巫 + 1猎人 + 2平民</span>
                        </div>
                        <div className="rule-item">
                            <span className="rule-icon">⏱️</span>
                            <span>发言时间：每人30秒</span>
                        </div>
                        <div className="rule-item">
                            <span className="rule-icon">🎯</span>
                            <span>平票直接进入夜晚</span>
                        </div>
                    </div>
                </div>

                {/* 连接状态 */}
                <div className="connection-status">
                    <span className={`status-dot ${isConnected ? 'connected' : ''}`}></span>
                    <span>{isConnected ? '已连接' : '未连接'}</span>
                </div>
            </div>
        </div>
    );
}
