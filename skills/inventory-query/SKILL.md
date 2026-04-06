---
name: inventory-query
description: 背包/角色狀態查詢
tools: [bot_inventory, bot_buffs, bot_player, bot_spells]
trigger: 背包|狀態|buff|inventory|player
---

## 用途

查詢角色背包內容、當前 Buff 列表、角色基本狀態（重量/食物/陣營），以及可用技能列表。

## 常見操作

### 查詢背包
```json
{ "tool": "bot_inventory", "bot_id": "bot1" }
```
回傳每個格子：
```json
{
  "slot": 0,
  "item_id": 1001,
  "name": "Short Sword",
  "qty": 1,
  "uid": "a3f9b21c"
}
```
- `uid` 為唯一識別碼，`bot_interact` / `bot_use_item` 需要此值
- `qty` > 1 表示可疊加道具（藥水、箭矢等）

### 查詢 Buff 狀態
```json
{ "tool": "bot_buffs", "bot_id": "bot1" }
```
回傳：buff_id, name, remain_ms（剩餘毫秒）, stack

### 查詢角色基本狀態
```json
{ "tool": "bot_player", "bot_id": "bot1" }
```
常用欄位：
- `hp` / `mp` / `max_hp` / `max_mp`
- `weight` / `max_weight`（滿載時 bot 無法撿物）
- `food` — 食物值，低於閾值影響恢復速度
- `alignment` — 陣營值（正數=善, 負數=惡）
- `pos_x` / `pos_y` — 當前座標

### 查詢技能列表
```json
{ "tool": "bot_spells", "bot_id": "bot1" }
```
回傳：spell_id, name, mp_cost, cooldown_ms, level

## 注意事項

- 背包查詢不含快速欄，快速欄由 `bot_player` 的 `hotbar` 欄位提供
- `bot_buffs` 的 `remain_ms` 為近似值，誤差約 ±500ms
- 重量超過 `max_weight * 0.9` 時 bot 移動速度下降，建議提前整理
- `bot_spells` 僅列出已學習的技能，未學習的不會出現
