---
name: workshop-help
description: AI 教學助手 — 操作員問什麼就教什麼
tools: [bot_list, fleet_health_check, workshop_morning_report]
trigger: 怎麼|教我|help|如何|什麼是
---

## 用途

操作員不需要背指令。直接用中文問 AI，AI 會找到對應的 skill 並用白話解釋。

## 常見問題 → AI 回答方式

### "怎麼看工作室狀態？"
→ 呼叫 `workshop_morning_report()`，用白話解釋結果

### "某隻 bot 死了怎麼辦？"
→ 流程:
1. `bot_logs(port=X)` 查看死因
2. 如果是 PK → 建議換地點或時段
3. 如果是怪太強 → 建議降低 combat_radius
4. `opener_start(acc_id)` 重新啟動

### "怎麼補給？"
→ 呼叫 `fleet_supply_check()` 看誰需要，然後 `bot_supply_trigger(port=X)` 觸發

### "怎麼排班？"
→ 呼叫 `schedule_status()` 看目前排程
→ 用 `schedule_add(...)` 新增，或 `schedule_generate(...)` 從模板生成

### "效率怎樣？"
→ 呼叫 `fleet_performance()` 或 `workshop_profitability()`

### "這帳號安全嗎？"
→ 呼叫 `fleet_risk_scores()` 看風險評分

### "怎麼加新帳號？"
→ 參考 workshop-onboard skill 的流程

## 操作員日常流程

```
上班:
  1. 說 "報告" → 看 morning_report
  2. 有問題 → 按 AI 建議處理
  3. 沒問題 → bot 自己跑，不用管

有空時:
  - "分析效率" → 看哪隻最差，考慮調整
  - "風險報告" → 看誰該休息

下班前:
  - "稽核" → account_audit + risk_report
  - 確認排程正常 → schedule_status

出事時:
  - "全停" → emergency skill
  - 查日誌找原因 → bot_logs
```

## 注意事項

- AI 回應變慢或怪怪的 → 開新 session (context 可能滿了)
- 不確定的操作先問 AI "這樣做安全嗎？"
- 所有操作都有記錄 (audit log)，不用怕做錯
