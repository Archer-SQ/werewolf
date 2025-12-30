/**
 * WebSocket Hook
 * 
 * 管理与后端的 WebSocket 连接
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { WSMessage } from '../types/game';
import { WS_URL } from '../utils/constants';

interface UseWebSocketReturn {
    /** 连接状态 */
    isConnected: boolean;
    /** 最后接收的消息 */
    lastMessage: WSMessage | null;
    /** 发送消息 */
    sendMessage: (type: string, data?: Record<string, unknown>) => void;
    /** 连接 */
    connect: () => void;
    /** 断开连接 */
    disconnect: () => void;
}

/**
 * WebSocket 连接 Hook
 * 
 * @returns WebSocket 操作接口
 */
export function useWebSocket(): UseWebSocketReturn & { messageQueue: WSMessage[], clearQueue: () => void } {
    const [isConnected, setIsConnected] = useState(false);
    const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
    // 使用消息队列来解决高并发下的消息丢失问题
    const [messageQueue, setMessageQueue] = useState<WSMessage[]>([]);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

    /**
     * 清空消息队列
     */
    const clearQueue = useCallback(() => {
        setMessageQueue([]);
    }, []);

    /**
     * 发送消息
     */
    const sendMessage = useCallback((type: string, data: Record<string, unknown> = {}) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type, data }));
        } else {
            console.warn('WebSocket 未连接，无法发送消息');
        }
    }, []);

    /**
     * 启动心跳
     */
    const startHeartbeat = useCallback(() => {
        if (pingIntervalRef.current) {
            clearInterval(pingIntervalRef.current);
        }
        
        pingIntervalRef.current = setInterval(() => {
            sendMessage('ping');
        }, 30000); // 每30秒发送一次心跳
    }, [sendMessage]);

    /**
     * 停止心跳
     */
    const stopHeartbeat = useCallback(() => {
        if (pingIntervalRef.current) {
            clearInterval(pingIntervalRef.current);
            pingIntervalRef.current = null;
        }
    }, []);

    /**
     * 建立 WebSocket 连接
     */
    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            return;
        }

        try {
            const ws = new WebSocket(WS_URL);

            ws.onopen = () => {
                console.log('WebSocket 已连接');
                setIsConnected(true);
                startHeartbeat();
            };

            ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data) as WSMessage;
                    if (message.type === 'pong') {
                        // 收到心跳响应，这里可以做更多处理，比如重置超时检测
                        return;
                    }
                    setLastMessage(message);
                    setMessageQueue(prev => [...prev, message]);
                } catch (e) {
                    console.error('消息解析失败:', e);
                }
            };

            ws.onclose = () => {
                console.log('WebSocket 已断开');
                setIsConnected(false);
                stopHeartbeat();

                // 5秒后尝试重连
                reconnectTimeoutRef.current = setTimeout(() => {
                    connect();
                }, 5000);
            };

            ws.onerror = (error) => {
                console.error('WebSocket 错误:', error);
            };

            wsRef.current = ws;
        } catch (error) {
            console.error('WebSocket 连接失败:', error);
        }
    }, [startHeartbeat, stopHeartbeat]);

    /**
     * 断开 WebSocket 连接
     */
    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        stopHeartbeat();

        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }

        setIsConnected(false);
    }, [stopHeartbeat]);

    // 组件卸载时断开连接
    useEffect(() => {
        return () => {
            disconnect();
        };
    }, [disconnect]);

    return {
        isConnected,
        lastMessage,
        sendMessage,
        connect,
        disconnect,
        messageQueue,
        clearQueue
    };
}
