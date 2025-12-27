/**
 * Toast 通知组件
 * 
 * 用于展示系统消息弹窗
 */
import { useEffect, useState } from 'react';
import './Toast.css';

export interface ToastMessage {
    id: number;
    content: string;
    type?: 'info' | 'success' | 'warning' | 'error';
}

interface ToastContainerProps {
    messages: ToastMessage[];
    onRemove: (id: number) => void;
}

export function ToastContainer({ messages, onRemove }: ToastContainerProps) {
    return (
        <div className="toast-container">
            {messages.map((msg) => (
                <Toast key={msg.id} message={msg} onRemove={onRemove} />
            ))}
        </div>
    );
}

function Toast({ message, onRemove }: { message: ToastMessage; onRemove: (id: number) => void }) {
    const [exiting, setExiting] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => {
            setExiting(true);
            setTimeout(() => onRemove(message.id), 300); // Wait for animation
        }, 3000); // 3秒后自动消失

        return () => clearTimeout(timer);
    }, [message.id, onRemove]);

    return (
        <div className={`toast-item ${message.type || 'info'} ${exiting ? 'exit' : ''}`}>
            <span className="toast-icon">📢</span>
            <span className="toast-content">{message.content}</span>
        </div>
    );
}
