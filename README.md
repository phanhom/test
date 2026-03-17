# 合金弹头风格小游戏

横版射击游戏，支持闯关、地图、皮肤、开房间多人联机、更大 Lobby、NPC 大模型对话。

## 配置 (config.json)

复制 `config.example.json` 为 `config.json`，按需修改：

```json
{
  "lobby": { "width": 1024, "height": 640, "max_players": 8 },
  "game": { "width": 800, "height": 500 },
  "npc": {
    "enabled": true,
    "llm": {
      "api_key": "sk-xxx",
      "model": "gpt-4o-mini",
      "base_url": "https://api.openai.com/v1"
    },
    "list": [{ "id": "npc_1", "name": "教官", "role": "军事教官", "prompt": "...", "x": 120, "y": 380 }]
  }
}
```

- **lobby**: 大厅尺寸、最大玩家数
- **npc**: 启用后，大厅中可点击 NPC 对话，对接大模型 (OpenAI 兼容 API)

## 项目结构

```
test/
├── config.json           # 本地配置 (勿提交)
├── config.example.json   # 配置模板
├── core/                 # 核心
│   └── config_loader.py
├── npc/                  # NPC 与大模型
│   ├── llm_client.py
│   └── npc_entity.py
├── game/                 # 游戏核心
│   ├── constants.py      # 常量配置
│   ├── entities.py       # 玩家、敌人、子弹
│   ├── skins.py          # 皮肤定义
│   ├── maps.py           # 地图系统
│   ├── levels.py         # 关卡配置
│   └── game_logic.py     # 游戏主逻辑
├── network/              # 网络模块
│   ├── protocol.py       # 消息协议
│   ├── room_server.py    # 房间服务器
│   └── room_client.py    # 房间客户端
├── ui/                   # 界面
│   ├── menu.py           # 主菜单
│   └── lobby.py          # 房间大厅
├── main.py               # 入口
├── requirements.txt
└── README.md
```

## 安装与运行

```bash
pip install -r requirements.txt
python main.py
```

## 地图机制

每关对应不同地图，共 5 种：

| 地图 | 特点 |
|------|------|
| 训练场 | 平坦地面 |
| 沙漠前线 | 沙漠色调，多层平台 |
| 工厂废墟 | 工业风，平台 |
| 雪地要塞 | 雪景，平台 |
| 丛林基地 | 丛林绿，平台 |

## 开房间多人

1. **主机**：创建房间 → 进入大厅 → 显示房间码和 IP → 等待玩家 → 按 Enter 开始
2. **客户端**：加入房间（输入 IP）→ 进入大厅 → 按 R 准备 → 等待主机开始
3. 支持最多 4 人在大厅，当前游戏最多 2 人联机

## 广场大厅

- 可走动广场：WASD / 方向键 移动、跳跃
- 平台、地面，多人可见彼此位置
- 走近 NPC 点击对话

## 四季系统

- 春 / 夏 / 秋 / 冬 自动循环
- 不同季节：天空、地面、落叶/花瓣等视觉效果
- `config.json` 中 `seasons.cycle_seconds` 控制切换间隔

## 商店系统

- 广场中点击「商店」打开军需商店
- 使用金币购买皮肤（默认皮肤免费）
- 金币来源：游戏得分，每 100 分 = 1 金币
- 存档：`save_data.json` 保存金币与已购皮肤

## NPC 系统

- 广场中可点击的 NPC（教官、军医等）
- 点击 NPC 打开对话框，输入后按 Enter，NPC 通过大模型回复
- 在 `config.json` 中配置 `npc.llm.api_key` 及 `npc.list`

## 聊天系统

- **大厅**：点击下方输入框，输入后按 Enter 发送
- **游戏中**：联机时同样可点击输入框聊天
- 消息实时同步给房间内所有玩家

## 操作

- **P1**：WASD 移动，J 射击
- **P2**：方向键移动，K 射击
- **R**：大厅中切换准备状态
- **ESC**：暂停

## 关卡

- 共 5 关，难度递增
- 每关消灭指定数量敌人后进入下一关
- 每关使用不同地图
