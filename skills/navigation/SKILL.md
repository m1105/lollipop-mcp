---
name: navigation
description: 導航系統 — 移動、尋路、nav腳本、地圖資訊
---

# 導航系統

## 基本移動

- `bot_walk(x, y)` — 走一步到 (x,y)
- `bot_smartmove(x, y)` — A* 自動尋路到 (x,y)
- `bot_position` — 查看當前座標

## 尋路工具

- `bot_pathfind(sx, sy, ex, ey)` — A* 路徑計算，回傳路點
- `bot_los(x1, y1, x2, y2)` — 視線檢查（兩點之間是否有障礙）
- `bot_map_grid` — 當前位置周圍地形資訊

## Nav 腳本

導航腳本 = 預錄的路點序列，可重複執行。

- `bot_nav_scripts` — 列出所有已存腳本
- `bot_nav_exec(script_id)` — 執行指定腳本
- `bot_nav_stop` — 停止當前導航
- `bot_nav_upload(name, waypoints)` — 上傳腳本，waypoints=JSON `[{"x":100,"y":200,"action":"walk"}]`
- `bot_nav_return_confirm` — 確認導航返回 dialog

## 地圖資訊

- `bot_portal_db` — 傳送門資料庫
- `bot_minimap` — 小地圖資訊

## 自然語言範例

- "走到 32500,32800" → bot_smartmove(x=32500, y=32800)
- "我在哪" → bot_position
- "有什麼導航腳本" → bot_nav_scripts
- "跑去奇岩地監的腳本" → bot_nav_exec(script_id="...")
