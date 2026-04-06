---
name: character-manage
description: 角色管理 — 狀態查詢、設定檔、掃描、登入、血盟
---

# 角色管理

## 狀態查詢

- `bot_status` — 完整狀態（版本/HP/MP/等級/職業/bot 狀態/entity cache）
- `bot_player` — 詳細角色資訊（名稱/職業/屬性/負重/飽食/正邪值）
- `bot_target` — 當前選取目標資訊
- `bot_buffs` — 當前 buff 列表
- `bot_spells` — 可用法術列表
- `bot_entities` — 周圍實體列表（NPC/怪物/玩家）
- `bot_inventory` — 背包物品列表（含 uid）

## 設定檔

- `bot_config_get` — 取得全部設定
- `bot_config_set(fields)` — 修改設定，fields=JSON `'{"combat_radius":15}'`
- `bot_config_reset` — 重置為預設值
- `bot_profile_list` — 列出已存設定檔
- `bot_profile_load(name)` — 載入設定檔
- `bot_profile_delete(name)` — 刪除設定檔

## 系統操作

- `bot_scan` / `bot_rescan` — 重新掃描遊戲記憶體
- `bot_auto_login` — 觸發自動登入
- `bot_daytime(on)` — 白天模式（1=開, 0=關）
- `bot_log_level(level)` — 設定日誌等級
- `bot_logs(level, lines)` — 查看 DLL 日誌
- `bot_pledge_join(name, password)` — 加入血盟

## 更新

- `bot_update_check` — 檢查 DLL 更新
- `bot_update_download` — 下載最新版 DLL

## 截圖/搜尋

- `bot_screenshot` — 遊戲截圖
- `bot_search_names(keyword)` — 搜尋物品/怪物名稱

## 自然語言範例

- "狗子什麼狀態" → bot_status
- "身上有什麼" → bot_inventory
- "周圍有什麼怪" → bot_entities
- "載入掛機設定檔A" → bot_profile_load(name="A")
- "把天亮起來" → bot_daytime(on=1)
