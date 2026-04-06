---
name: direct-combat
description: 手動戰鬥操作 — 攻擊/施法/撿物/互動
tools: [bot_attack, bot_cast, bot_pickup, bot_interact, bot_click, bot_npc_click]
trigger: 攻擊|施法|撿|interact|attack|cast
---

## 用途

手動（非自動掛機）的單次戰鬥操作：對指定目標攻擊、施放技能、撿取地面物品、與 NPC 互動。

## 常見操作

### 攻擊目標
```json
{ "tool": "bot_attack", "bot_id": "bot1", "entity_id": 12345 }
```
單次普通攻擊。entity_id 從 `bot_entities` 或 `bot_scan` 取得。

### 施放技能
```json
{ "tool": "bot_cast", "bot_id": "bot1", "spell_id": 3001, "target_id": 12345 }
```
對地面施法（AOE）改用 `target_x` / `target_y` 取代 `target_id`：
```json
{ "tool": "bot_cast", "bot_id": "bot1", "spell_id": 3002, "target_x": 5120, "target_y": 3200 }
```

### 撿取地面物品
```json
{ "tool": "bot_pickup", "bot_id": "bot1", "entity_id": 99001 }
```
entity_id 為地面掉落物的 id（type="item" 從 `bot_entities` 取得）。

### 與 NPC 互動 (開啟對話)
```json
{ "tool": "bot_npc_click", "bot_id": "bot1", "entity_id": 50012 }
```
**必須用 entity_id，不可用 addr。**
addr 隨每次記憶體重掃改變，entity_id 在整個遊戲 session 中穩定。

### 點擊對話框選項
```json
{ "tool": "bot_click", "bot_id": "bot1", "dialog": "ShopDialog", "widget": "Btn_Buy" }
```
用於 NPC 對話後的 UI 操作（確認購買、關閉視窗等）。

### 通用互動
```json
{ "tool": "bot_interact", "bot_id": "bot1", "entity_id": 50012 }
```
適用於傳送門、物件、NPC 等任何可互動實體。

## 注意事項

- **NPC 互動永遠用 entity_id，不用 addr** — addr 不穩定，重掃後即失效
- `bot_attack` 不會自動追蹤目標，目標超出攻擊範圍會失敗（先用 `bot_pathfind` 靠近）
- `bot_cast` 施法前確認 MP 足夠（`bot_player` 查詢）
- 連續操作之間加 sleep 800ms-1500ms，避免觸發遊戲反作弊
- 撿物前確認背包重量未滿（`bot_player.weight < max_weight * 0.85`）
- `bot_click` 的 dialog/widget 名稱區分大小寫，可從 `bot_screenshot` 確認 UI 狀態
