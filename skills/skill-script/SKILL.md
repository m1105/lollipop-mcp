---
name: skill-script
description: Skill 腳本系統 — 建立/執行/管理自動化腳本，組合多個 MCP tool 成流程
---

# Skill 腳本系統

將多個 MCP tool 呼叫組合成可重複執行的腳本。

## 管理腳本

- `skill_list` — 列出所有已建立的 skill
- `skill_get(name)` — 查看 skill 完整定義
- `skill_create(name, description, steps)` — 建立/更新 skill
- `skill_delete(name)` — 刪除 skill
- `skill_run(name, port, host)` — 執行 skill

## steps 格式

JSON array，每個 step:
```json
{
  "tool": "bot_xxx",
  "params": {"key": "value"},
  "delay_ms": 1000,
  "repeat": 3,
  "save_as": "result_var",
  "on_error": "skip",
  "wait_for": {"dialog": "X", "timeout_ms": 5000},
  "comment": "說明"
}
```

- tool: MCP tool 名稱（必填）
- params: 傳給 tool 的參數（選填）
- delay_ms: 執行後等待毫秒（選填）
- repeat: 重複次數（選填）
- on_error: "skip"=跳過繼續, "stop"=停止（選填）
- wait_for: 等待條件（選填）

## 艦隊執行

- `fleet_run_skill(name)` — 全部機器執行同一個 skill

## 自然語言範例

- "建一個去買藥的腳本" → skill_create(name="buy_pots", steps=[...])
- "跑買藥腳本" → skill_run(name="buy_pots")
- "全部跑補給腳本" → fleet_run_skill(name="supply")
- "有哪些腳本" → skill_list
