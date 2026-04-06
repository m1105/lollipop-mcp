---
name: workshop-emergency
description: 緊急應變 — 全停/單停/診斷/復原
tools: [bot_all_stop, opener_stop_all, bot_stop, opener_stop, fleet_health_check, bot_logs, bot_screenshot]
trigger: 全停|emergency|出事了|緊急|stop everything
---

## 用途

遊戲維護、帳號異常、被 PK、伺服器斷線等緊急狀況的應變流程。

## 緊急等級

### Level 1: 全停（最高緊急）
```
1. bot_all_stop()           → 停止所有 bot 自動化
2. opener_stop_all(host)    → 停止所有遊戲客戶端（每台機器）
3. schedule_toggle(0, host) → 關閉排程器（防止自動重啟）
```

### Level 2: 單隻問題
```
1. bot_stop(port, host)     → 停止該 bot
2. bot_logs(port, host)     → 查看日誌找原因
3. bot_screenshot(port, host) → 截圖看畫面狀態
```

### Level 3: 診斷
```
1. fleet_health_check()     → 全艦隊健康巡檢
2. workshop_risk_report()   → 風險報告
3. workshop_account_audit() → 帳號稽核
```

## 復原流程

```
1. 確認問題已解決
2. schedule_toggle(1, host)  → 重啟排程器
3. opener_start_all(host)    → 重啟遊戲客戶端
4. bot_all_start()           → 重啟 bot 自動化
5. fleet_health_check()      → 確認恢復正常
```

## 注意事項

- 全停後排程器也要關，否則它會自動重啟帳號
- 復原時先等遊戲客戶端完全載入再啟動 bot
- 如果是被 ban，先用 `schedule_account_flags` 標記帳號，不要重啟它
