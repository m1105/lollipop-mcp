---
name: mcp-rules
description: Lollipop MCP 操作強制規範 — 每次操作前必讀，違反會 crash 或封號
---

# MCP 操作規範

## 強制檢查（每次操作前）

1. `bot_dialogs` — 確認沒有殘留 dialog，有的話先關掉
2. `bot_entities` — 確認目標 NPC 在畫面中
3. 不可見的 dialog **不能點** — 會被伺服器判定外掛

## NPC 互動

- 高階 tool（bot_buy_from_npc, bot_warehouse_deposit 等）內部自動用 entity_id，直接用即可
- 低階 `bot_interact` 傳的是 entity_addr（hex 字串），從 `bot_entities` 取得
- 盡量用高階 tool，避免直接用 bot_interact（addr 可能失效導致 crash）
- 已知 NPC id：朵琳=1269, 潘朵拉=1267, 爾瑪=1605
- interact 後等 **3 秒**再操作

## 基本原則

- **所有遊戲操作用 MCP tool**，不寫 Python 腳本
- 不要問「要繼續嗎」— 直接做
- 只改被要求的，不要自己亂改
- 操作完確認 UI 乾淨再做下一步
- 各模組流程不能混用（商店/倉庫/傳送各有各的按鈕和流程）

## 數量輸入

- GLFW char callback 逐字輸入（不用 game_glfw_key）
- 點擊 TextField focus → 逐字發 char event

## 角色對應

呼叫 `bot_list` 建立角色名 → host:port 對照表。用戶說角色名時自動對應。
