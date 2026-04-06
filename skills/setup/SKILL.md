---
name: lollipop-setup
description: Lollipop 安裝/設定精靈 — 一鍵設定連線
tools: [bot_list, opener_status, fleet_health_check]
trigger: setup|安裝|設定|lollipop setup
---

## 用途

新玩家安裝完 plugin 後，引導完成連線設定。也可用於現有用戶重新設定或遷移。

## 使用方式

```
/lollipop:setup              # 新安裝精靈
/lollipop:setup --migrate    # 從手動 .mcp.json 遷移到 plugin
/lollipop:setup --update     # 只更新 skills 和 CLAUDE.md
```

## 新安裝流程

### Phase 1: 環境檢查

1. 確認 Python 版本 >= 3.9
2. 確認 httpx 已安裝
   - 如果沒有: `pip install httpx "mcp[cli]>=1.26"`
3. 確認網路連通

### Phase 2: 連線模式

詢問玩家:

**單台模式** (最簡單):
- 問: 機器 IP (例: `192.168.0.114`)
- 設定: `LOLLIPOP_DIRECT=192.168.0.114`
- 驗證: `bot_list()` 應回傳至少一個 instance

**多台模式** (工作室):
- 問: Server URL (例: `https://lolly.lc1llm.xyz`)
- 問: Card ID (例: `XXXX-XXXX-XXXX-XXXX`)
- 問: Tailscale API Key (可選，自動發現機器)
- 設定: `LOLLIPOP_SERVER_URL` + `LOLLIPOP_CARD_ID` + `LOLLIPOP_TAILSCALE_KEY`
- 驗證: `bot_list()` 應回傳所有機器

### Phase 3: 驗證連線

```
bot_list()              → 確認能看到 bot
opener_status(host)     → 確認能看到 opener (可選)
fleet_health_check()    → 全面巡檢
```

### Phase 4: 完成

顯示:
```
Lollipop 設定完成!

連線模式: 單台 / 多台
機器數: X
Bot 數: Y

快速開始:
  "報告"          → 工作室總覽
  "誰在線"        → bot 清單
  "開始掛機"      → 載入 profile + 傳送 + 啟動
  "排班"          → 查看/設定排程

完整指令列表: 說 "help" 或查看 skills 目錄
```

## 遷移流程 (--migrate)

### 偵測舊設定

檢查 `.mcp.json` 是否有 lollipop 配置:
```json
{
  "mcpServers": {
    "lollipop": {
      "env": {
        "LOLLIPOP_DIRECT": "192.168.0.114"
      }
    }
  }
}
```

### 遷移步驟

1. 讀取舊 `.mcp.json` 中的 env vars
2. 遷移到 plugin userConfig:
   - `LOLLIPOP_DIRECT` → `direct_ip`
   - `LOLLIPOP_SERVER_URL` → `server_url`
   - `LOLLIPOP_CARD_ID` → `card_id`
   - `LOLLIPOP_TAILSCALE_KEY` → `tailscale_key`
3. 移除 `.mcp.json` 中的舊 lollipop 條目 (備份到 `.mcp.json.backup`)
4. 驗證 plugin 連線正常

## 更新流程 (--update)

1. 比對 plugin 版本與 skills 版本
2. 如果 skills 較舊，自動更新
3. 如果 CLAUDE.md 較舊，更新 lollipop 區塊

## Windows 注意事項

- Python 路徑: 自動搜尋 `py -3`, `python3`, `python`
- pip 安裝失敗: 嘗試 `py -3 -m pip install httpx`
- 路徑問題: 使用 `${CLAUDE_PLUGIN_ROOT}` 變數 (plugin.json 已處理)
- 中文路徑: 確保 UTF-8 編碼

## 故障排除

| 問題 | 解決 |
|------|------|
| `bot_list()` 回傳空 | 確認遊戲已啟動 + DLL 已注入 |
| `Connection refused` | 確認 IP 正確 + 防火牆允許 5577 端口 |
| `httpx not found` | `pip install httpx` |
| `opener unreachable` | 確認 opener.py 在 Windows 機器上運行 |
| 多台但只看到一台 | 確認 Tailscale 已連線或 SERVER_URL 正確 |
