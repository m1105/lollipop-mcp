---
name: warehouse
description: 倉庫存取流程 — deposit/withdraw，支援不可堆疊、可堆疊、金幣
---

# 倉庫存取流程

## 高階 tool（推薦）

- `bot_warehouse_deposit(items, npc_name, wh_type)` — 存入
- `bot_warehouse_withdraw(items, npc_name, wh_type)` — 取出
- 支援 JSON array 多物品、自動模糊匹配

## 手動流程

1. interact 倉庫 NPC（用 entity_id）
2. 點「存放物品」nth=1(個人) / nth=2(血盟)
3. 等 StorageLayout visible + **2.5 秒**載入
4. 每個物品 `confirm=0`（批次選取）
5. 全選完 → confirm 統一確認

## 物品類型處理

| 類型 | 處理方式 |
|------|---------|
| **不可堆疊** | 遍歷所有同名 slot 逐一選取 |
| **可堆疊** | 點擊 TextField → GLFW char 輸入數量 |
| **已裝備** | 名字含「穿戴」= 已裝備，StorageLayout 自動過濾 |
| **金幣** | StorageLayout 用 Tx_Adena（不是 Tx_Item） |

- qty=0 = 全部存入/取回

## NpcTalkLayout 選項

- 存放物品 nth=1 (個人), nth=2 (血盟)
- 取回物品 nth=1 (個人), nth=2 (血盟)

## 倉庫管理員

| 村莊 | NPC |
|------|-----|
| 說話之島 | 朵琳 |
