# 暗夜狼人杀

一个基于 AI 的 Web 狼人杀游戏，1 名真实玩家与 6 名 AI 玩家进行游戏。

## 技术栈

- **后端**: Python 3.8+ / FastAPI / WebSocket
- **AI**: 通义千问 (DashScope API)
- **前端**: React / TypeScript / Vite

## 游戏规则

- **角色配置**: 2狼人 + 1预言家 + 1女巫 + 1猎人 + 2平民
- **女巫技能**: 毒药和解药可同一晚使用
- **猎人规则**: 被毒死可开枪
- **平票处理**: 直接进入夜晚
- **发言规则**: 按顺序发言，每人最多30秒

## 快速开始

### 1. 配置 API Key

```bash
cd backend
cp .env.example .env
# 编辑 .env 文件，填入你的通义千问 API Key
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 4. 开始游戏

打开浏览器访问 `http://localhost:5173`

## 目录结构

```
werewolf-game/
├── backend/            # 后端服务
│   ├── app/
│   │   ├── agents/     # AI Agent 系统
│   │   ├── game/       # 游戏核心逻辑
│   │   ├── models/     # 数据模型
│   │   └── websocket/  # WebSocket 处理
│   └── requirements.txt
├── frontend/           # 前端应用
│   ├── src/
│   │   ├── components/ # UI 组件
│   │   ├── hooks/      # React Hooks
│   │   ├── types/      # TypeScript 类型
│   │   └── utils/      # 工具常量
│   └── package.json
└── README.md
```

## License

MIT
