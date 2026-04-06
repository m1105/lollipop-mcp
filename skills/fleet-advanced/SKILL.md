---
name: fleet-advanced
description: 進階艦隊操作 — 條件過濾執行/批量傳送
tools: [fleet_run_filtered, fleet_teleport, fleet_supply_check, fleet_health_check]
trigger: 過濾|條件|fleet filter|fleet teleport|批量傳送
---

## 用途

對符合條件的 bot 批量執行 skill，或將整個艦隊傳送到指定地點。

## 常見操作

### 條件過濾執行 skill
```
fleet_run_filtered(
  name="supply_run",
  filter_field="arrows",
  filter_op="lt",
  filter_value="100"
)
```
可用 filter_field: `arrows`, `level`, `hp_pct`, `bot`
可用 filter_op: `lt` (小於), `gt` (大於), `eq` (等於)

### 批量傳送
```
fleet_teleport(dest="說話之島|雜貨商人")
fleet_teleport(dest="說話之島|雜貨商人", profile="grind_si1")
```

### 艦隊巡檢
```
fleet_health_check()   → HP/箭/bot狀態/離線 全面檢查
fleet_supply_check()   → 只檢查補給狀態
```

## 注意事項

- fleet_run_skill 對所有 bot 執行；fleet_run_filtered 只對符合條件的
- 傳送目的地格式: "村莊|傳送點"
- 大量 bot 同時傳送有 800ms+ 間隔
