---
name: system-admin
description: 系統管理 — 重掃/日誌等級/白天模式/重置
tools: [bot_rescan, bot_log_level, bot_daytime, bot_stats_reset, bot_config_get, bot_config_reset]
trigger: 重掃|日誌|debug|admin|rescan|log level
---

## 用途

維護 DLL 運行環境：重新掃描記憶體偏移、調整日誌詳細程度、切換白天模式、重置統計計數器、查詢/重置設定。

## 常見操作

### 重掃記憶體偏移
```json
{ "tool": "bot_rescan", "bot_id": "bot1" }
```
遊戲更新後 RVA 可能改變，重掃重新定位所有偏移量。
通常在遊戲有版本更新後執行一次。回傳 `{ "ok": true, "found": 42 }`。

### 調整日誌等級
```json
{ "tool": "bot_log_level", "bot_id": "bot1", "level": "D" }
```
等級選項：
- `S` — 僅重要事件（預設，低噪音）
- `I` — 一般資訊
- `D` — Debug 詳細輸出（排查問題時使用）
- `W` — 僅警告+錯誤

### 切換白天模式
```json
{ "tool": "bot_daytime", "bot_id": "bot1", "enabled": true }
```
強制遊戲環境光設為白天，移除黑霧效果，提高截圖/視覺辨識準確度。
`enabled: false` 恢復正常晝夜循環。

### 重置統計計數器
```json
{ "tool": "bot_stats_reset", "bot_id": "bot1" }
```
清零 kills / exp_gained / adena_looted 等掛機統計數據（session 計數器）。

### 查詢目前設定
```json
{ "tool": "bot_config_get", "bot_id": "bot1" }
```
回傳 DLL 目前所有設定值（combat_range, loot_filter, heal_threshold 等）。

### 重置設定為預設值
```json
{ "tool": "bot_config_reset", "bot_id": "bot1" }
```
將所有設定恢復出廠預設。**不可逆**，執行前先用 `bot_config_get` 記錄當前值。

## 注意事項

- `bot_rescan` 執行期間（約 1-3 秒）bot 暫停所有操作
- Debug 日誌 (`D`) 會大幅增加記憶體寫入，長時間開啟可能影響效能，排查後記得改回 `S`
- `bot_daytime` 是持續寫入（每 0.5s），關閉後約 1 秒恢復自然光照
- `bot_config_reset` 不會重置帳號密碼等登入憑證
