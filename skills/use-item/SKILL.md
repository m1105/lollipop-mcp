---
name: use-item
description: 使用物品 — bot_useitem + bot_inventory 查 uid
---

# 使用物品

## 流程

1. `bot_inventory` — 查背包，找到物品的 uid
2. `bot_useitem(item_uid)` — 使用該物品

## 注意事項

- **不可堆疊物品**（如活力方塊）每個有獨立 uid，要逐一使用
- **可堆疊物品** uid 不變，重複呼叫即可
- **說話的卷軸** — 不要用 bot_useitem，用 `bot_teleport_scroll` 代替
