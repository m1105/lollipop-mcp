---
name: workshop-status
description: 工作室總覽 — 機台/角色/排程/績效一次看完
tools: [workshop_morning_report, opener_fleet_status, fleet_status, schedule_fleet_overview, fleet_health_check]
trigger: 報告|狀態|看一下|morning report|status
---

## 用途

管理員想快速了解整個工作室的狀態時使用。涵蓋：機台是否在線、bot 是否正常、排程是否啟用、昨日收益。

## 流程

1. 呼叫 `workshop_morning_report()` — 取得完整報告（機台+bot+排程+昨日收益）
2. 如果報告中有 `problems`（異常 bot）— 列出每個問題並建議操作
3. 如果某台機器 offline — 提醒管理員檢查該機台
4. 如果昨日 gold_per_hour 低於歷史平均 — 標記並建議分析原因

## 報告格式

```
工作室狀態 (YYYY-MM-DD HH:MM)
━━━━━━━━━━━━━━━━━━━━━━━
機台: X 台在線 / Y 台離線
Bot:  X 隻運行中 / Y 隻異常
排程: 啟用中 / 今日剩餘 N 個輪替

昨日收益:
  總金幣: XXX,XXX | 總時數: XX.X hr | 平均: X,XXX gold/hr

異常:
  ⚠ [角色名] HP 過低 (xxx/xxx)
  ⚠ [角色名] 離線

建議:
  → [具體操作建議]
```

## 注意事項

- 如果 SERVER_URL 沒設，昨日收益部分會是空的（只有即時數據）
- fleet_health_check 是即時的，morning_report 的 yesterday 區塊是歷史數據
