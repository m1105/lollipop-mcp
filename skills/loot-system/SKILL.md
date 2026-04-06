---
name: loot-system
description: 撿物系統 — 過濾模式、撿物範圍、優先順序
---

# 撿物系統

## 設定撿物

`bot_setup_loot(...)`:
- enabled: 1=啟用
- filter_mode: 0=無過濾, 1=黑名單(不撿), 2=白名單(只撿)
- filter_items: 物品名稱 pipe 分隔 `"短劍|木材|回復藥水"`
- loot_range: 撿物範圍（格數）
- priority: 0=先打後撿, 1=先撿後打
- my_kill_only: 1=只撿自己殺的
- crowd_threshold: 周圍玩家超過 N 時不撿

## 自然語言範例

- "只撿金幣和藥水" → bot_setup_loot(filter_mode=2, filter_items="金幣|藥水")
- "不要撿短劍" → bot_setup_loot(filter_mode=1, filter_items="短劍")
- "先撿東西再打怪" → bot_setup_loot(priority=1)
- "旁邊超過3個人就不撿" → bot_setup_loot(crowd_threshold=3)
