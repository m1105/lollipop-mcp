---
name: protect-system
description: 保護系統 — 死亡重生、緊急逃跑、死頻暫停、回點設定
---

# 保護系統

## 設定保護

`bot_setup_protect(...)`:

### 緊急逃跑
- escape_enabled: 1=啟用
- escape_items: 逃跑用物品 pipe 分隔 `"傳送捲軸|回城捲軸"`
- escape_hp_pct: HP% 低於此值觸發逃跑

### 死亡暫停
- death_enabled: 1=啟用
- death_count: N 次死亡觸發暫停
- death_window_min: 在 M 分鐘內
- death_pause_min: 暫停 N 分鐘

### 重生
- resurrect: 1=自動重生
- resurrect_delay_ms: 重生延遲（毫秒）

### 回掛機點
- return_enabled: 1=啟用
- return_item: 回點用卷軸名
- return_dest: 回點目的地 `"村莊|傳送點"`
- return_script: 回掛機點 nav 腳本名

## 自然語言範例

- "HP低於30%就逃跑" → bot_setup_protect(escape_enabled=1, escape_hp_pct=30)
- "5分鐘內死3次就暫停10分鐘" → bot_setup_protect(death_enabled=1, death_count=3, death_window_min=5, death_pause_min=10)
- "自動重生" → bot_setup_protect(resurrect=1)
