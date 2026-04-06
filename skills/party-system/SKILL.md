---
name: party-system
description: 組隊系統 — 隊伍模式、跟隨、攻擊、治療、同步設定
---

# 組隊系統

## 查看隊伍

- `bot_party_status` — 隊伍狀態（模式、小隊、隊長）
- `bot_party_members` — 隊員列表（HP/MP/位置）
- `bot_party_config_get` — 隊伍設定（治療/buff/攻擊）

## 隊伍模式

`bot_party_mode(mode)`:
- `follow` — 跟隨模式
- `grind` — 掛機模式
- `rest` — 休息
- `return` — 回城
- `idle` — 閒置

快捷：`bot_party_follow` — 直接切跟隨模式

## 隊伍指令

- `bot_party_attack(name, x, y)` — 指揮攻擊目標（名稱或座標）
- `bot_party_heal(target)` — 手動治療指定隊員
- `bot_party_cast(skill_id, target)` — 對目標施法
- `bot_party_moveto(x, y)` — 全隊移動到座標
- `bot_party_teleport` — 觸發隊伍傳送
- `bot_party_free_attack(enabled)` — 自由攻擊模式（1=開, 0=關）
- `bot_party_stop` — 停止隊伍控制

## 設定

- `bot_party_config_set(fields)` — JSON 格式設定
- `bot_party_sync` — 同步設定到所有隊員
- `bot_party_focus(name)` — 設定集火目標

## 自然語言範例

- "全隊跟著我" → bot_party_follow
- "打那隻哥布林" → bot_party_attack(name="哥布林")
- "治療狗子" → bot_party_heal(target="狗子")
- "全隊移動到 32500,32800" → bot_party_moveto(x=32500, y=32800)
- "開自由攻擊" → bot_party_free_attack(enabled=1)
