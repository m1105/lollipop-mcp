---
name: ats-watch-and-start
description: ATS 結束後自動啟動 bot
tools: [bot_dialogs, bot_start]
trigger: ATS結束|ats結束|等ATS
---

## 用途

搭配 `goto-blessed-ats` 使用。ATS 啟動後執行此 skill，等 ATS 時間到自動啟動外掛。

## 流程

```
# 1. 檢查 ATSMsgHudLayout 是否還在
bot_dialogs()

# 2. 如果 ATSMsgHudLayout 不在 = ATS 結束 → 啟動 bot
#    如果還在 = ATS 還在跑 → 等待
bot_start()  # 只在 ATSMsgHudLayout 消失後執行
```

## 判斷邏輯

- `bot_dialogs()` 回傳有 `ATSMsgHudLayout` → ATS 還在跑，不動
- `bot_dialogs()` 回傳沒有 `ATSMsgHudLayout` → ATS 結束，執行 `bot_start()`

## 搭配 cron 使用

建議搭配 cron 每 5 分鐘執行一次，自動偵測 ATS 結束：
```
cron_create(name="ats_watch", interval_min=5, skill="ats-watch-and-start")
```
