---
name: workshop-cron
description: 自動化排程 — 設定定時巡檢、補給、分析、報告
tools: [workshop_setup_crons, fleet_health_check, fleet_supply_check, workshop_morning_report, workshop_risk_report, fleet_performance]
trigger: 自動化|cron|定時|自動巡檢|setup crons
---

## 用途

設定 Claude Code 定時自動執行工作室監控任務。使用 `/schedule` 建立 cron triggers。

## 預設 Cron 配置

| 名稱 | 頻率 | 說明 |
|------|------|------|
| fleet-health | 每 10 分鐘 | 巡檢全艦隊健康 + 自動修復建議 |
| supply-monitor | 每 30 分鐘 | 偵測缺貨 bot + 補給建議 |
| analytics-snapshot | 每 2 小時 | 績效快照 + 異常偵測 |
| daily-report | 每天 08:00 | 早班報告 |
| daily-audit | 每天 23:00 | 帳號稽核 + 風險報告 |

## 設定方式

呼叫 `workshop_setup_crons()` 取得所有 cron 的設定指令，然後逐一執行。

或手動使用 `/schedule`:

### 1. 艦隊健康巡檢 (每 10 分鐘)
```
/schedule create "fleet-health" --cron "*/10 * * * *" --prompt "呼叫 fleet_health_check()。如果有問題，列出每個問題 bot 和建議操作。如果有 bot 離線超過 10 分鐘，嘗試 opener_start 重啟。"
```

### 2. 補給監控 (每 30 分鐘)
```
/schedule create "supply-monitor" --cron "*/30 * * * *" --prompt "呼叫 fleet_supply_check()。如果有 bot 需要補給，按急迫度排序，對最急的 1-2 隻執行 bot_supply_trigger。不要同時補給超過 2 隻。"
```

### 3. 績效快照 (每 2 小時)
```
/schedule create "analytics-snapshot" --cron "0 */2 * * *" --prompt "呼叫 fleet_performance(days=1) 取得今日績效。如果有 underperformer (gold_hr 低於平均 30%)，呼叫 bot_compare 比較它和最好的 bot，找出 config 差異並建議調整。"
```

### 4. 早班報告 (每天 08:00)
```
/schedule create "daily-report" --cron "0 8 * * *" --prompt "呼叫 workshop_morning_report()，以結構化格式呈現完整報告。如果有異常，標記優先處理項目。"
```

### 5. 每日稽核 (每天 23:00)
```
/schedule create "daily-audit" --cron "0 23 * * *" --prompt "依序執行：1) workshop_account_audit() 找出問題帳號，2) workshop_risk_report() 評估風險，3) fleet_risk_scores() 風險評分。彙整成一份報告，標記需要明天處理的事項。"
```

## 管理 Cron

```
/schedule list          → 查看所有排程
/schedule delete NAME   → 刪除排程
/schedule run NAME      → 手動觸發一次
```

## 注意事項

- Cron triggers 是 Claude Code 的 remote agents，每次觸發開一個新 session
- 每個 session 獨立，不共享 context — 所以 prompt 要寫完整
- 太頻繁的 cron (< 5 分鐘) 會消耗大量 API tokens
- 建議先手動跑幾次確認正常，再設成自動
