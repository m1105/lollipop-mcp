---
name: sell-npc
description: NPC 出售設定 — 設定自動出售清單
tools: [bot_sell_npcs_get, bot_sell_npcs_set]
trigger: 出售|賣|sell npc
---

## 用途

設定 supply 系統在補給時要到哪些 NPC 出售物品。Supply 模組在觸發補給時，
會依照此清單找最近的 NPC 並自動出售。

## 常見操作

### 查看目前設定

```
bot_sell_npcs_get()
```

回傳範例：
```json
{
  "sell_npcs": ["潘朵拉", "露西", "邁爾"]
}
```

### 設定出售 NPC 清單

```
bot_sell_npcs_set(npcs='["潘朵拉", "露西"]')
```

- 傳入 JSON 陣列字串
- 名稱必須完全符合遊戲內 NPC 名稱
- 支援多個 NPC，系統選最近的

### 常用 NPC 名稱對照

| 村莊 | 雜貨商人 |
|------|----------|
| 說話之島 | 潘朵拉 |
| 古魯丁村 | 露西 |
| 奇岩村 | 邁爾 |
| 燃柳村 | 傑克森 |

### 完整設定四個村莊

```
bot_sell_npcs_set(npcs='["潘朵拉", "露西", "邁爾", "傑克森"]')
```

## 注意事項

- 至少設定一個 NPC，否則 supply 補給時無法出售
- NPC 名稱區分大小寫，需與 entities 列表一致
- 若掛機地圖離某村莊較近，只設定該村莊的 NPC 可加快補給速度
