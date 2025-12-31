/**
 * 游戏常量配置
 * 
 * 定义前端使用的常量
 */

/** 
 * 动态获取后端服务地址
 * 生产环境：使用相对路径，由 Nginx 转发
 * 开发环境：尝试连接本地后端
 */
const getBaseUrl = () => {
    if (import.meta.env.PROD) {
        // 生产环境使用当前域名/IP，不带端口（默认80/443），由 Nginx 处理 /api 前缀
        return '';  
    }
    // 本地开发环境
    const hostname = window.location.hostname;
    return `http://${hostname}:8000`;
};

const getWsUrl = () => {
    if (import.meta.env.PROD) {
        // 生产环境使用 wss:// (如果是 https) 或 ws://
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//${window.location.host}/ws`;
    }
    // 本地开发环境
    const hostname = window.location.hostname;
    return `ws://${hostname}:8000/ws`;
};

/** 后端服务地址 */
export const API_BASE_URL = getBaseUrl();

/** WebSocket 地址 */
export const WS_URL = getWsUrl();

/** 发言时间限制（秒） */
export const SPEECH_TIME_LIMIT = 30;

/** 玩家总数 */
export const PLAYER_COUNT = 7;

/** 角色颜色 */
export const ROLE_COLORS: Record<string, string> = {
    werewolf: '#ff4d4f',
    seer: '#722ed1',
    witch: '#13c2c2',
    hunter: '#fa8c16',
    villager: '#52c41a',
    unknown: '#8c8c8c'
};

/** 阶段名称 */
export const PHASE_NAMES: Record<string, string> = {
    waiting: '等待开始',
    night: '夜晚',
    night_wolf: '狼人行动',
    night_seer: '预言家查验',
    night_witch: '女巫行动',
    day: '天亮了',
    day_announce: '天亮了',
    day_discuss: '白天讨论',
    day_vote: '投票阶段',
    last_words: '遗言阶段',
    hunter_shoot: '猎人开枪',
    game_over: '游戏结束'
};
