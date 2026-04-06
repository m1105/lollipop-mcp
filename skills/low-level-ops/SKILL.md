---
name: low-level-ops
description: 低階操作 — 直接點擊UI、GLFW輸入、DLL HTTP、攻擊、施法、撿取
---

# 低階操作

通常不需要直接使用，高階 tool 已封裝。特殊情況或除錯時用。

## UI 操作

- `bot_click(dialog, widget, addr)` — 點擊 UI 按鈕（dialog+widget 或 addr）
- `bot_npc_click(dialog, keyword, nth)` — 點擊 NPC 對話選項
- `bot_dialogs` — 查看目前可見的 dialog 列表
- `bot_uitree` — 完整 UI 樹狀結構

## GLFW 輸入

- `bot_glfw_click(x, y)` — 模擬滑鼠點擊
- `bot_glfw_key(key)` — 模擬鍵盤按鍵（F10=299, F11=300, F12=301, Enter=257）

## 戰鬥

- `bot_attack(entity_id)` — 攻擊指定實體
- `bot_cast(skill_id)` — 施放技能
- `bot_pickup(entity_id, qty)` — 撿取物品

## 卷軸（低階）

- `bot_scroll_show` — 顯示/隱藏說話的卷軸 UI
- `bot_scroll_list` — 列出卷軸目的地
- `bot_scroll_dest` — 點擊卷軸目的地
- `bot_usescroll(item_uid, dest)` — 使用傳送卷軸
- `bot_bookmarks` — 祝福卷軸書籤列表
- `bot_bm_scan` — 重新掃描書籤
- `bot_bm_click(idx)` — 點擊書籤

## NPC 互動

- `bot_interact(entity_addr)` — 與 NPC 互動（傳 hex addr，盡量用高階 tool 代替）
- `bot_shoplist` — 查看商店物品列表
- `bot_shop_buy(item_name, qty, confirm)` — 購買商店物品

## 直接 HTTP

- `dll_http(method, path, body)` — 直接呼叫 DLL HTTP API（萬能後門）

## 賣 NPC

- `bot_sell_npcs_get` — 查看自動賣出 NPC 設定
- `bot_sell_npcs_set(npcs)` — 設定自動賣出 NPC

## 補給觸發

- `bot_wh_trigger` — 手動觸發倉庫操作（DLL 狀態機）
