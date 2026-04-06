---
name: config-tuning
description: Config 參數完整指南 — 148 個可調參數
tools: [bot_config_get, bot_config_set]
trigger: config|參數|調整|tuning|設定
---

## 用途

查看和修改 bot 的 148 個 config 參數。

## 基本操作

```
bot_config_get(port=5577)              → 查看全部
bot_config_set(fields='{"combat_radius":15}', port=5577)  → 改特定欄位
```

## 關鍵參數

### 戰鬥 (combat_*)
| 參數 | 值域 | 說明 |
|------|------|------|
| combat_radius | 5-50 | 戰鬥半徑 (格) |
| combat_attack_dist | 1-25 | 攻擊距離 |
| combat_roam_mode | 0-3 | 0=raycast, 1=spiral, 2=levy, 3=sector |
| combat_los_enabled | 0/1 | 視線檢查 |
| combat_stand_fight | 0/1 | 站樁打 |
| combat_counter_attack | 0/1 | 被打反擊 |
| combat_blacklist | "怪A\|怪B" | 不打的怪物 |
| combat_whitelist | "怪C\|怪D" | 只打的怪物 |
| combat_blacklist_mode | 0/1 | 0=黑名單, 1=白名單 |

### 補給 (supply_*)
| 參數 | 說明 |
|------|------|
| supply_enabled | 開關 |
| supply_weight_pct | 負重%觸發 (60-90) |
| supply_items | JSON: `[{"item_name":"銀箭","buy_qty":500,"trigger_qty":100}]` |

### 拾取 (loot_*)
| 參數 | 說明 |
|------|------|
| loot_enabled | 開關 |
| loot_filter_mode | 0=黑名單, 1=白名單 |
| loot_range | 拾取距離 (5-20) |
| loot_priority | 1=先撿後打, 0=先打後撿 |

### 保護 (protect_*)
| 參數 | 說明 |
|------|------|
| protect_escape_hp_pct | HP%以下逃跑 |
| protect_death_count | N次死亡後暫停 |
| protect_death_window_min | 在M分鐘內計算 |

### 陣列類型
```json
heal_list: [{"trigger":"H","threshold":50,"item_name":"治癒藥水","delay_ms":500}]
buff_list: [{"item_name":"加速藥水","buff_id":33,"is_skill":0,"duration_ms":300000}]
```

## 注意事項

- config_set 只改指定欄位，其他不動
- 陣列類型必須用完整 JSON array
- 修改後立刻生效，不需重啟
- 重要改動前先 config_get 記錄原始值
