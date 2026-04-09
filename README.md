w# Lollipop MCP Plugin

AI 控制遊戲 bot 的 Claude Code 插件。自然語言操作掛機、買賣、傳送、組隊。

## 安裝

### 本地路徑安裝
```bash
claude --plugin-dir /path/to/dist
```

首次啟動會自動：
1. 建立 Python venv + 安裝依賴
2. 啟動 MCP server
3. 載入 14 個操作 skills
4. 詢問連線設定（Tailscale key 或直連 IP）

### 連線模式

**多台模式（Tailscale）**— 填 tailscale_key + server_url + card_id

**單台模式（直連）**— 只填 direct_ip

## Skills（14 個）

| Skill | 功能 |
|-------|------|
| mcp-rules | 操作強制規範（每次操作前必讀） |
| buy-from-npc | NPC 商店購買 |
| warehouse | 倉庫存取 |
| teleport | 傳送系統（卷軸/NPC/祝福） |
| fleet-ops | 艦隊多機管理 |
| use-item | 使用物品 |
| ui-popup | UI 彈窗處理 |
| combat-setup | 戰鬥掛機設定 |
| supply-system | 自動補給 |
| protect-system | 保護系統（死亡/逃跑） |
| loot-system | 撿物系統 |
| party-system | 組隊系統 |
| navigation | 導航/移動 |
| character-manage | 角色管理/狀態/設定 |
| skill-script | Skill 腳本（自動化流程） |
| low-level-ops | 低階操作（UI/GLFW/HTTP） |

## 自然語言操作範例

```
"煎餅狗子去海音城"
"買10瓶治癒藥水"
"存500金幣到血盟倉庫"
"所有角色停止掛機"
"設定掛機範圍20格，只打哥布林"
"HP低於30%就逃跑"
"全隊跟著我"
```

## 檔案說明

```
dist/
├── .claude-plugin/plugin.json   # 插件定義
├── mcp_hub.py                   # MCP 伺服器（117 個 tool）
├── requirements.txt             # Python 依賴
├── setup.sh                     # 自動環境設定
├── CLAUDE.md                    # 操作規範
├── README.md                    # 本文件
└── skills/                      # 16 個操作技能
    ├── mcp-rules/
    ├── buy-from-npc/
    ├── warehouse/
    ├── teleport/
    ├── fleet-ops/
    ├── use-item/
    ├── ui-popup/
    ├── combat-setup/
    ├── supply-system/
    ├── protect-system/
    ├── loot-system/
    ├── party-system/
    ├── navigation/
    ├── character-manage/
    ├── skill-script/
    └── low-level-ops/
```
## 安裝命令
```
  claude plugin marketplace add m1105/lollipop-mcp
  claude plugin install lollipop@mcp
```
