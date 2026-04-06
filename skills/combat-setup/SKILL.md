---
name: combat-setup
description: 戰鬥掛機設定 — 掛機中心、範圍、怪物黑白名單、漫遊模式、啟停
---

# 戰鬥掛機設定

## 一鍵開始掛機

`bot_start_grinding(profile, dest, set_center)` — 載入設定檔 → 傳送 → 設中心 → 啟動

- profile: 設定檔名稱（可選）
- dest: 傳送目的地 "村莊|傳送點"（可選）
- set_center=1: 自動以當前座標為掛機中心

## 設定戰鬥參數

`bot_setup_combat(...)`:
- center_x/y: 掛機中心座標（-1=用角色當前位置）
- radius: 掛機範圍（格數）
- priority: 優先怪物，pipe 分隔 `"怪物A|怪物B"`
- blacklist: 黑名單，pipe 分隔
- whitelist: 白名單，pipe 分隔
- blacklist_mode: 0=黑名單模式, 1=白名單模式
- attack_dist: 攻擊距離
- roam_mode: 0=raycast, 1=spiral, 2=levy, 3=sector
- enabled: 1=啟用, 0=停用

## 啟動/停止

- `bot_start` — 啟動掛機
- `bot_stop` — 停止掛機
- `bot_return_to_grind(scroll_dest, nav_script, start_bot)` — 回掛機點 + 啟動

## 查看狀態

- `bot_combat_state` — 戰鬥模組狀態
- `bot_status` — 完整狀態（HP/MP/等級/職業/bot 狀態）
- `bot_stats` — 掛機統計（擊殺/金幣/死亡/運行時間）
- `bot_stats_reset` — 重置統計

## 自然語言範例

- "在這裡掛機" → bot_setup_combat(center_x=-1, center_y=-1) + bot_start
- "掛機範圍改成20格" → bot_setup_combat(radius=20)
- "只打哥布林" → bot_setup_combat(whitelist="哥布林", blacklist_mode=1)
- "不要打骷髏" → bot_setup_combat(blacklist="骷髏", blacklist_mode=0)
- "停止掛機" → bot_stop
- "回去繼續掛" → bot_return_to_grind
