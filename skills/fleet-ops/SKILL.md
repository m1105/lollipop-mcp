---
name: fleet-ops
description: 艦隊操作 — 多機管理、全部啟動/停止、全部傳送
---

# 艦隊操作

## 查看所有機器

`bot_list` — 回傳所有在線機器的角色名、host:port、狀態

## 全部操作

- `bot_all_start` — 全部啟動掛機
- `bot_all_stop` — 全部停止
- `fleet_teleport(dest)` — 全部傳送到指定地點
- `bot_return_to_grind` — 回到掛機點

## 排除特定角色

需要排除某些角色時，逐台操作其他角色（用 port 指定）。

## 健康檢查

- `fleet_health_check` — 巡檢所有 bot 的 HP/MP/箭/狀態
- `fleet_supply_check` — 檢查補給品數量

## 自然語言操作範例

- "所有角色停止掛機" → `bot_all_stop`
- "除了狗子全部啟動" → 逐台 `bot_start`（排除狗子）
- "全部去海音城" → `fleet_teleport(dest="海音")`
- "煎餅狗子去奇岩" → 用 bot_list 找到對應 port → `bot_teleport_scroll`
