/**
 * 角色选择/抽卡组件
 * 
 * 游戏开始前让用户体验抽卡过程，增强代入感
 */
import { useState, useEffect } from 'react';
import { RoleType, ROLE_NAMES } from '../types/game';
import { ROLE_COLORS } from '../utils/constants';
import './RoleSelection.css';

interface RoleSelectionProps {
    /** 实际分配到的角色 */
    assignedRole: RoleType;
    /** 角色描述 */
    roleDescription: string;
    /** 完成选择的回调 */
    onConfirm: () => void;
}

/**
 * 角色选择组件
 */
export function RoleSelection({ assignedRole, roleDescription, onConfirm }: RoleSelectionProps) {
    // 状态管理
    const [isRevealed, setIsRevealed] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
    const [cards, setCards] = useState<Array<{ id: number; delay: number }>>([]);
    const [centerOffset, setCenterOffset] = useState({ x: 0, y: 0 });
    
    // 简单的移动端检测
    const isMobile = typeof window !== 'undefined' && window.innerWidth <= 900;

    // 初始化卡片
    useEffect(() => {
        // 生成 7 张卡片（对应 7 人局）
        const newCards = Array.from({ length: 7 }, (_, i) => ({
            id: i,
            delay: i * 0.1 // 依次进场动画延迟
        }));
        setCards(newCards);
    }, []);

    /**
     * 处理卡片点击
     */
    const handleCardClick = (index: number, e: React.MouseEvent<HTMLDivElement>) => {
        if (selectedIndex !== null) return; // 已选择，防止重复点击
        
        // 计算移动到中心的偏移量
        const rect = e.currentTarget.getBoundingClientRect();
        const centerX = window.innerWidth / 2;
        const centerY = window.innerHeight / 2;
        const cardX = rect.left + rect.width / 2;
        const cardY = rect.top + rect.height / 2;
        
        setCenterOffset({
            x: centerX - cardX,
            y: centerY - cardY
        });

        setSelectedIndex(index);
        
        // 延迟翻转，配合动画
        setTimeout(() => {
            setIsRevealed(true);
        }, 600);
    };

    /**
     * 获取角色图标
     */
    const getRoleIcon = (role: RoleType) => {
        switch (role) {
            case 'werewolf': return '🐺';
            case 'seer': return '🔮';
            case 'witch': return '🧪';
            case 'hunter': return '🔫';
            case 'villager': return '🧑‍🌾';
            default: return '❓';
        }
    };

    return (
        <div className="role-selection-overlay">
            <div className="role-selection-container">
                <h2 className="role-selection-title">
                    {isRevealed ? '你的身份是...' : '请选择一张命运卡牌'}
                </h2>

                <div className="cards-container">
                    {cards.map((card, index) => {
                        // 计算每个卡片的状态类名
                        let wrapperClass = 'role-card-wrapper';
                        const isSelected = selectedIndex === index;
                        
                        if (isSelected) {
                            wrapperClass += ' selected';
                            if (isRevealed) wrapperClass += ' revealed';
                            // 移除 flipped 类，改用内联样式控制翻转
                        } else if (selectedIndex !== null) {
                            wrapperClass += ' fading';
                        }

                        // 动态样式
                        let wrapperStyle: React.CSSProperties = {
                            animationDelay: `${card.delay}s`
                        };

                        if (isSelected) {
                            // PC端使用 JS 计算的 transform 动画
                            // 移动端通过 CSS fixed 定位处理，不应用这里的 transform
                            if (!isMobile) {
                                wrapperStyle = {
                                    ...wrapperStyle,
                                    transform: `translate(${centerOffset.x}px, ${centerOffset.y}px) scale(1.5) ${isRevealed ? 'rotateY(180deg)' : ''}`,
                                    zIndex: 1000
                                };
                            } else {
                                // 移动端只设置 zIndex，动画交给 CSS
                                wrapperStyle = {
                                    ...wrapperStyle,
                                    zIndex: 2000
                                };
                            }
                        }

                        return (
                            <div 
                                key={card.id}
                                className={wrapperClass}
                                style={wrapperStyle}
                                onClick={(e) => handleCardClick(index, e)}
                            >
                                <div className="role-card card-back">
                                    <div className="card-pattern">
                                        <span className="card-logo">🐺</span>
                                    </div>
                                </div>
                                
                                <div 
                                    className="role-card card-front"
                                    style={{ '--role-color': ROLE_COLORS[assignedRole] } as React.CSSProperties}
                                >
                                    <div className="role-icon">{getRoleIcon(assignedRole)}</div>
                                    <div className="role-info">
                                        <div className="role-name">{ROLE_NAMES[assignedRole]}</div>
                                        <p className="role-desc">{roleDescription}</p>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>

                {isRevealed && (
                    <button 
                        className="role-confirm-btn visible"
                        onClick={onConfirm}
                    >
                        进入暗夜
                    </button>
                )}
            </div>
        </div>
    );
}
