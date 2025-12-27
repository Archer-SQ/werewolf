/**
 * 游戏流程公告遮罩
 * 
 * 用于展示 "天黑请闭眼"、"狼人请睁眼" 等过场动画
 */
import { useEffect, useState } from 'react';
import './AnnouncementOverlay.css';

interface AnnouncementOverlayProps {
    /** 阶段名称，如 "狼人请睁眼" */
    message: string | null;
    /** 回合数 */
    round: number;
    /** 是否强制显示（只要是夜晚就显示） */
    forceVisible?: boolean;
    /** 
     * 覆盖显示模式 
     * - 'auto': 自动消失 (默认)
     * - 'persistent': 持续显示，直到 message 变空或 forceVisible 为 false
     */
    mode?: 'auto' | 'persistent';
    /** 完成回调（仅 auto 模式有效） */
    onComplete?: () => void;
    /** 是否有玩家需要行动 */
    hasAction?: boolean;
    /** 子元素（如操作面板） */
    children?: React.ReactNode;
    /** 连接状态 */
    isConnected?: boolean;
}

export function AnnouncementOverlay({ 
    message, 
    round, 
    forceVisible = false,
    mode = 'auto',
    onComplete, 
    hasAction = false,
    children,
    isConnected = true
}: AnnouncementOverlayProps) {
    const [visible, setVisible] = useState(false);
    
    // 控制显示逻辑
    useEffect(() => {
        // 如果断开连接，强制显示
        if (!isConnected) {
            setVisible(true);
            return;
        }

        // 如果强制显示，直接设为可见
        if (forceVisible) {
            setVisible(true);
            return;
        }

        if (message) {
            setVisible(true);
            
            if (mode === 'auto') {
                // 自动消失模式：3秒后淡出
                const timer = setTimeout(() => {
                    setVisible(false);
                    setTimeout(() => onComplete?.(), 500);
                }, 3000);
                return () => clearTimeout(timer);
            }
        } else {
             // 如果没有消息且不强制显示，则隐藏
             setVisible(false);
        }
    }, [message, mode, onComplete, forceVisible, isConnected]);

    // 如果不可见，直接返回 null
    if (!visible) return null;

    return (
        <div className={`announcement-overlay ${visible ? 'visible' : ''} ${hasAction ? 'with-action' : ''}`}>
            {/* 星空背景 */}
            <div className="stars-bg">
                <div className="star star-1"></div>
                <div className="star star-2"></div>
                <div className="star star-3"></div>
                <div className="star star-4"></div>
                <div className="star star-5"></div>
            </div>
            
            <div className="announcement-content">
                {/* 月亮图标 */}
                <div className="moon-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                    </svg>
                </div>
                
                <h2 className="announcement-text">
                    {!isConnected ? "连接已断开" : (message || "天黑请闭眼")}
                </h2>
                <div className="phase-subtitle">
                    {!isConnected ? "请刷新页面重连" : `NIGHT ${round}`}
                </div>
                
                {/* 嵌入的操作面板 (ActionPanel) */}
                {isConnected && children && <div className="overlay-action-container animate-scale-in">{children}</div>}
            </div>
        </div>
    );
}
