---
name: batch-ops
description: 批量操作 — 全部啟停/狀態
tools: [bot_all_status, bot_all_start, bot_all_stop]
trigger: 全部|批量|all start|all stop
---

## 用途

一次性查詢所有 bot 狀態、啟動全部 bot、停止全部 bot。適合快速掌控或緊急停止整個艦隊。

## 常見操作

### 查詢所有 bot 狀態
```json
{ "tool": "bot_all_status" }
```
回傳陣列，每個 bot 一筆：
```json
[
  { "bot_id": "bot1", "running": true,  "map": "大陸", "hp_pct": 85, "uptime_s": 3600 },
  { "bot_id": "bot2", "running": false, "map": null,   "hp_pct": 0,  "uptime_s": 0 },
  { "bot_id": "bot3", "running": true,  "map": "地監", "hp_pct": 62, "uptime_s": 1200 }
]
```

### 啟動全部 bot
```json
{ "tool": "bot_all_start" }
```
對每個已設定的 bot 執行啟動序列。回傳：
```json
{ "started": ["bot1", "bot3"], "failed": ["bot2"], "errors": { "bot2": "game not running" } }
```

### 停止全部 bot
```json
{ "tool": "bot_all_stop" }
```
立即停止所有 bot 的自動行為（戰鬥/撿物/移動）。回傳：
```json
{ "stopped": ["bot1", "bot3"], "already_stopped": ["bot2"] }
```

## 與 fleet_* 工具的差異

| 工具 | 範圍 | 過濾 | 健康檢查 |
|------|------|------|----------|
| `bot_all_*` | 全部 bot | 無 | 無 |
| `fleet_run_filtered` | 條件過濾 | 有 | 有 |
| `fleet_health_check` | 全部 bot | 無 | 有 |

- `bot_all_*` 是最快速的批量操作，無條件全部執行
- 需要過濾（如只對低血量 bot 操作）或健康檢查，請改用 `fleet_*` 工具

## 注意事項

- `bot_all_start` 不等待各 bot 登入完成，僅觸發啟動信號
- 緊急停止建議用 `bot_all_stop`（比逐一停止快 10x）
- `bot_all_status` 不需要 bot_id 參數，直接呼叫即可
