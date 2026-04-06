---
name: recon
description: 偵察工具 — 查看周圍怪物/玩家/地形/截圖
tools: [bot_entities, bot_scan, bot_los, bot_map_grid, bot_minimap, bot_screenshot, bot_target, bot_search_names, bot_portal_db]
trigger: 偵察|周圍|怪物|地形|截圖|recon|entities|scan
---

## 用途

掃描周圍環境：附近怪物、玩家、NPC、地形格子、傳送門資料庫，以及截圖和視線判斷。

## 常見操作

### 查看附近所有實體
```json
{ "tool": "bot_entities", "bot_id": "bot1", "range": 500 }
```
回傳：entity_id, addr, name, type (monster/player/npc), hp, pos (x,y)

### 掃描指定類型
```json
{ "tool": "bot_scan", "bot_id": "bot1", "type": "monster", "range": 300 }
```
type 選項：monster | player | npc | all

### 以名稱搜尋實體
```json
{ "tool": "bot_search_names", "bot_id": "bot1", "query": "Goblin" }
```
模糊比對，回傳所有符合的 entity_id + 位置

### 視線判斷 (LoS)
```json
{ "tool": "bot_los", "bot_id": "bot1", "target_id": 12345 }
```
回傳 has_los: true/false，用於判斷能否施法/攻擊

### 讀取地形格子
```json
{ "tool": "bot_map_grid", "bot_id": "bot1", "cx": 100, "cy": 200, "radius": 5 }
```
回傳二維陣列，flags: 0=可走, 1=障礙, 2=傳送門, 8=水

### 取得小地圖截圖
```json
{ "tool": "bot_minimap", "bot_id": "bot1" }
```

### 截圖 (全螢幕)
```json
{ "tool": "bot_screenshot", "bot_id": "bot1" }
```
回傳 base64 PNG

### 查看目前目標
```json
{ "tool": "bot_target", "bot_id": "bot1" }
```
回傳當前選中目標的 entity_id, name, hp, distance

### 傳送門資料庫
```json
{ "tool": "bot_portal_db", "bot_id": "bot1" }
```
回傳地圖中所有已知傳送門位置與目的地

## 注意事項

- `bot_entities` range 過大（>1000）會返回大量資料，建議 300-500
- 視線判斷 `bot_los` 不等同於攻擊距離，還需確認 range
- 地形格子使用世界座標，`radius` 單位為格子數（1格=64世界單位）
- `bot_screenshot` 需要 bot 視窗在前景，否則可能截到黑屏
