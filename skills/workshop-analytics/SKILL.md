---
name: workshop-analytics
description: 績效分析 — 排名/比較/實驗/風險評估
tools: [workshop_profitability, fleet_performance, bot_compare, experiment_evaluate, fleet_risk_scores, fleet_supply_efficiency]
trigger: 分析|效率|哪裡賺最多|analytics|比較|誰最差
---

## 用途

用數據驅動的方式優化工作室產值：績效排名、bot 比較、A/B 實驗判定、風險評分。

## 常見操作

### 績效排名
```
workshop_profitability(days=7)  → 過去 7 天的績效報表
fleet_performance(days=1)       → 今日即時績效排名（按地圖分組）
```

### 比較兩隻 bot
```
bot_compare(bot_a_port=5577, bot_b_port=5578, bot_a_host="192.168.0.114", bot_b_host="192.168.0.114")
→ 顯示 config 差異 + 績效差異
→ 用來找出為什麼一隻比另一隻好/差
```

### A/B 實驗判定
```
# 1. 收集數據: 控制組和實驗組各跑 2+ 小時的 gold/hr
# 2. 判定:
experiment_evaluate(
  control_values="[150,155,148,160,145,152]",
  treatment_values="[200,210,195,205,198,215]"
)
→ 回傳: significant=true, improvement=33%, recommendation=ADOPT
```

### 風險評估
```
fleet_risk_scores()  → 全帳號風險評分（HIGH/MEDIUM/LOW）
```

### 補給效率
```
fleet_supply_efficiency()  → 每隻 bot 的補給頻率和時間浪費
```

## A/B 實驗 SOP

1. **觀察問題**: fleet_performance → 找出最差的 bot
2. **比較 config**: bot_compare(好的 bot, 差的 bot) → 找差異
3. **假設**: 例如 "combat_radius 8→12 會提升 kills/hr"
4. **執行**: `bot_config_set(fields='{"combat_radius":12}', port=差的bot)` 
5. **等待**: 2 小時收集數據
6. **判定**: `experiment_evaluate(control, treatment)`
7. **推廣**: 如果 ADOPT → 套用到所有同地點 bot

## 注意事項

- 每次只改一個變數（否則無法知道是哪個變數的效果）
- 需要至少 6-10 個樣本點才有統計意義（每個 5 分鐘 snapshot = 2 小時約 24 個點）
- p_value < 0.05 才判定顯著
- 同時段比較（不要拿凌晨 vs 晚間比，玩家數不同）
