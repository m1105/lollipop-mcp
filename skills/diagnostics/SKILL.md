---
name: diagnostics
description: 診斷工具包 — 日誌/截圖/UI樹/對話框
tools: [bot_logs, bot_screenshot, bot_uitree, bot_dialogs]
trigger: 診斷|日誌|截圖|debug|logs|screenshot|卡住
---

## 用途

Bot 出問題時的診斷工具。

## 常見操作

### 查看日誌
```
bot_logs(port=5577, level="S")         → 重要日誌
bot_logs(port=5577, level="D", since=100)  → 詳細 debug
```
Level: S=重要, D=debug。since=序號 (增量讀取)

### 截圖
```
bot_screenshot(port=5577)
```

### UI 樹
```
bot_uitree(port=5577)   → 所有可見 dialog + widget 層級
bot_dialogs(port=5577)  → 可見 dialog 清單
```

## 診斷 SOP

### Bot 卡住不動
1. `bot_logs(level="S")` → 看最後日誌
2. `bot_combat_state()` → 看 state
3. `bot_dialogs()` → 是否有殘留 dialog
4. `bot_screenshot()` → 截圖確認

### Bot 一直死
1. `bot_logs(level="S")` → 找 death 日誌
2. `bot_entities()` → 周圍有 PK 玩家?
3. `death_alert()` → CUSUM 死亡加速檢測

### Dialog 卡住
1. `bot_dialogs()` → 找 dialog 名稱
2. `bot_click(dialog="XXX", widget="Bt_Close")` → 關閉
3. 常見: ServerSelect_MsgPopup → Bt_Ok

## 注意事項

- dialogs 只回傳 visible 的
- 點不可見的 dialog 會被判定外掛
- 日誌是環形緩衝，太久的會被覆蓋
