---
name: equip-system
description: 裝備系統 — 查看/穿戴/取下裝備
tools: [bot_equip_status, bot_equip_wear, bot_equip_return]
trigger: 裝備|穿|脫|equip|wear
---

## 用途

查看角色目前穿戴的裝備、從背包穿上指定物品、或將已穿裝備放回背包。
uid 是物品的唯一識別碼，從 bot_inventory 取得。

## 常見操作

### 查看目前裝備欄位

```
bot_equip_status()
```

回傳每個裝備槽（頭盔、上衣、護手、靴子、武器、盾牌、項鍊、戒指等）
及其物品名稱與 uid。

### 從背包穿上裝備

先查 inventory 取得 uid：
```
bot_inventory()
```

找到目標物品的 uid，再穿上：
```
bot_equip_wear(uid=12345678)
```

- uid 是 uint64，從 inventory 的 `uid` 欄位取得
- 系統自動判斷裝備槽，無需指定位置
- 若裝備需求等級不足，操作會失敗

### 取下裝備放回背包

```
bot_equip_return(uid=12345678)
```

uid 從 bot_equip_status 取得（已穿裝備的 uid）。

### 完整流程範例

```
# 1. 查看背包找到新武器
bot_inventory()
# → 找到 "精煉長劍+4", uid=98765432

# 2. 查看目前武器槽
bot_equip_status()
# → 武器槽: "老舊長劍", uid=11111111

# 3. 取下舊武器
bot_equip_return(uid=11111111)

# 4. 穿上新武器
bot_equip_wear(uid=98765432)
```

## 注意事項

- 穿戴失敗通常是等級、職業、或背包滿
- bot_equip_return 不會刪除物品，只是移回背包
- 同槽位的舊裝備會自動移回背包（遊戲內建行為）
