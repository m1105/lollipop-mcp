---
name: workshop-verify
description: 新人環境驗證 — 一鍵確認所有元件正常
tools: [bot_list, opener_status, schedule_status, fleet_health_check, opener_snapshots]
trigger: 驗證|verify|檢查環境|新人|第一次
---

## 用途

新操作員第一次使用，或環境有問題時，跑一次驗證確認所有元件正常。

## 驗證流程

依序執行以下檢查，每項回報 ✅ 或 ❌:

### Step 1: MCP 連線
```
bot_list()
```
- ✅ 回傳至少 1 個 instance
- ❌ "No bot instances found" → DLL 沒注入或遊戲沒開

### Step 2: Opener 連線
```
opener_status()
```
- ✅ 回傳 instances 清單
- ❌ "Opener unreachable" → opener.py 沒在跑或 IP 錯

### Step 3: 排程系統
```
schedule_status()
```
- ✅ 回傳 JSON 含 enabled, slot_count, jitter_minutes
- ❌ 連不上 → scheduler 沒啟動

### Step 4: Jitter 防 ban
```
確認 schedule_status 回傳中有 jitter_minutes >= 5
```
- ✅ jitter_minutes 存在且 >= 5
- ❌ 缺少或為 0 → scheduler.py 是舊版

### Step 5: 數據收集器
```
opener_snapshots(limit=1)
```
- ✅ 回傳至少 1 筆 snapshot
- ❌ 空 → data_collector 沒啟動或 bot 沒在跑 (等 5 分鐘再試)

### Step 6: 艦隊巡檢
```
fleet_health_check()
```
- ✅ 回傳健康狀態，無嚴重問題
- ❌ 有 problems → 列出每個問題

## 驗證報告格式

```
環境驗證報告
━━━━━━━━━━━
[✅] MCP 連線      — X 隻 bot 在線
[✅] Opener 連線    — X 個帳號
[✅] 排程系統       — enabled=X, slots=X
[✅] Jitter 防 ban  — ±X 分鐘
[⏳] 數據收集       — 等待中 (需 5 分鐘)
[✅] 艦隊健康       — 全部正常

結果: 5/6 通過, 1 等待中
```

## 常見問題

| 症狀 | 原因 | 解法 |
|------|------|------|
| bot_list 空 | 遊戲沒開 | 用 opener_start 啟動 |
| opener 連不上 | opener.py 沒跑 | 在 Windows 上啟動 opener |
| jitter=0 | 舊版 scheduler | 重新部署 scheduler.py |
| snapshots 空 | 剛啟動 | 等 5 分鐘 |
| health 有問題 | bot 異常 | 照 workshop-help 處理 |
