---
name: workshop-shift
description: 排班管理 — 查看/生成/調整班表
tools: [schedule_status, schedule_templates, schedule_generate, schedule_add, schedule_toggle, schedule_fleet_overview, schedule_account_flags]
trigger: 排班|班表|排程|shift|schedule|明天的班
---

## 用途

管理帳號輪班：查看目前排程、從模板生成新班表、手動調整 entry、開關排程器。

## 常見操作

### 查看目前排程
```
schedule_fleet_overview()  → 全工作室排程總覽
schedule_status(host)      → 單台排程詳情
schedule_running(host)     → 目前執行中的 entries
```

### 從模板生成班表
```
1. schedule_templates(host)           → 看有哪些模板
2. schedule_generate(                 → 從模板生成
     template_name="standard_grind",
     from_date="2026-04-07",
     to_date="2026-04-13",
     host="192.168.0.114"
   )
3. schedule_toggle(enabled=1, host)   → 啟用排程器
```

### 手動新增排程
```
schedule_add(
  slot_id="1",
  acc_id="account_email",
  start="2026-04-07 08:00",
  end="2026-04-07 16:00",
  profile="grind_gd1",
  host="192.168.0.114"
)
```

### 帳號狀態管理
```
schedule_account_flags(host)  → 查看帳號狀態 (active/banned/jailed/suspended)
```

## 注意事項

- 時間格式: `YYYY-MM-DD HH:MM`
- jitter 已啟用：實際上下線時間會 ±10 分鐘隨機偏移（防巨集偵測）
- `rest_minutes` 設定控制 slot 交接之間的休息時間
- 被標記 banned/jailed 的帳號會被自動跳過
