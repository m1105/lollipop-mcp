---
name: update-system
description: DLL 更新系統 — 檢查/下載更新
tools: [bot_update_check, bot_update_download, bot_check_health]
trigger: 更新|update|版本|version
---

## 用途

管理 DLL 版本：檢查是否有新版本可用、下載並安裝更新、確認 bot 服務健康狀態。

## 常見操作

### 檢查更新
```json
{ "tool": "bot_update_check", "bot_id": "bot1" }
```
回傳：
```json
{
  "current_version": "1.4.2",
  "latest_version": "1.4.5",
  "has_update": true,
  "changelog": "Fix combat range, improve loot speed"
}
```
`has_update: false` 表示已是最新版本。

### 下載並套用更新
```json
{ "tool": "bot_update_download", "bot_id": "bot1" }
```
流程：
1. 從 server 下載最新 DLL
2. 替換本地 DLL 檔案
3. 回傳 `{ "ok": true, "version": "1.4.5", "restart_required": true }`

**更新後必須重啟遊戲**才能載入新 DLL（DLL 已注入，無法熱替換）。

### 健康狀態檢查
```json
{ "tool": "bot_check_health", "bot_id": "bot1" }
```
回傳：
```json
{
  "dll_loaded": true,
  "ws_connected": true,
  "game_running": true,
  "uptime_s": 3601,
  "last_heartbeat_ms": 120
}
```
- `ws_connected: false` — WebSocket 連線中斷，需重連
- `last_heartbeat_ms > 5000` — DLL 可能卡住，建議重掃

## 注意事項

- `bot_update_download` 期間 bot 會暫停約 5-15 秒（視網速）
- 更新後 **必須完全關閉遊戲再重新啟動**，Launcher 會自動注入新版 DLL
- 不要在掛機中途更新，先停止 bot (`bot_all_stop`) 再更新
- `bot_check_health` 可作為日常巡檢的第一步，確認所有 bot 正常後再執行操作
- `game_running: false` 時除 `bot_update_check` 外的工具都會失敗
