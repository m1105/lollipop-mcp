---
name: buy-from-npc
description: NPC 商店購買流程 — interact → Bt_Npc_Buy → shop/buy → shop/confirm
---

# 商店購買流程

## 高階 tool（推薦）

`bot_buy_from_npc(npc, items, scroll_dest)` — 一次買多樣，自動模糊匹配名稱

物品名稱可能跟遊戲不同（如「治療藥水」→ 遊戲叫「治癒藥水」），tool 自動匹配。

## 手動流程

1. interact NPC（用 entity_id）
2. 等 3 秒
3. `bot_click("NpcTalkLayout", "Bt_Npc_Buy")` — **不用文字搜尋「購買」**
4. 等 NpcShopLayout visible
5. `bot_shop_buy` 每樣 `confirm=0`（批次）
6. 全選完 → `bot_shop_buy` confirm=1 統一結帳

## qty 規則

- qty = **實際購買數量**（不用 -1）
- 商店預設數量是 0
- 箭例外：Count_Up 每次 +10
- 有 TextField 時用 GLFW char callback 直接輸入數字

## 村莊 NPC 對照

| 村莊 | 雜貨商人 | 其他商人 |
|------|---------|---------|
| 說話之島 | 潘朵拉 | 馬修 |
| 古魯丁村 | 露西 | 凱蒂 |
| 奇岩村 | 邁爾 | 溫諾(武器), 范吉爾(防具) |
| 燃柳村 | 傑克森 | — |
