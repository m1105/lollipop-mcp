---
name: supply-system
description: 自動補給系統 — 設定買賣物品、回城補給、觸發補給
---

# 自動補給系統

## 設定補給

`bot_setup_supply(...)`:
- buy_items: JSON array `'[{"item_name":"回復藥水","buy_qty":100,"trigger_qty":20}]'`
  - buy_qty: 每次補到多少
  - trigger_qty: 低於多少時觸發補給
- sell_items: JSON array `'[{"item_name":"短劍","keep_qty":0}]'`（keep_qty=0=全賣）
- town_dest: 回城目的地 `"村莊|傳送點"`
- return_dest: 回掛機點目的地
- npc_name: 購買 NPC 名稱（如 "潘朵拉"）
- npc_x, npc_y: NPC 座標（0=不走路直接 interact）
- town_scroll / return_scroll: 使用的卷軸（預設 "說話的卷軸"）
- weight_pct: 負重百分比觸發（預設 80%）

## 觸發補給

- `bot_supply_trigger` — 手動觸發補給（DLL 狀態機）
- `bot_full_supply` — 觸發完整補給流程，等待完成
- `bot_supply_state` — 查看補給模組狀態

## 自然語言範例

- "設定補給：藥水低於20瓶就回說話島買到100瓶" → bot_setup_supply(...)
- "去補貨" → bot_supply_trigger 或 bot_full_supply
- "補給狀態" → bot_supply_state
