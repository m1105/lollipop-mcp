---
name: grinding
description: 一鍵掛機 — 載入 profile + 傳送 + 開始
tools: [bot_start_grinding, bot_return_to_grind, bot_start, bot_stop]
trigger: 掛機|grinding|開始打|start grinding
---

## 用途

快速啟動掛機流程：載入 profile、傳送到掛機點、設定中心點、開始自動戰鬥。
補給或死亡後可用 bot_return_to_grind 快速回到掛機點繼續。

## 常見操作

### 一鍵啟動掛機

```
bot_start_grinding(profile="古魯丁地監B2", dest="古魯丁村|古魯丁地監入口")
```

此指令一次完成：
1. 載入指定 profile（覆蓋所有 148 個 config 參數）
2. 用說話的卷軸傳送到 dest
3. 走到掛機中心點
4. 啟動 bot 自動戰鬥

dest 格式與 bot_usescroll 相同（"村莊|傳送點"）。

### 補給/死亡後回掛機點

```
bot_return_to_grind()
```

從當前位置自動傳送回上次的掛機中心點並重新開始。

### 手動啟動/停止

```
# 只啟動 bot（不傳送，不載入 profile）
bot_start()

# 停止 bot
bot_stop()
```

### 完整流程範例

```
# 首次開始掛機
bot_start_grinding(profile="奇岩地監F1", dest="奇岩村|奇岩地監入口")

# 補給回來後繼續
bot_return_to_grind()

# 需要暫停（例如手動操作）
bot_stop()

# 暫停後繼續
bot_start()
```

### 查看可用 profile

```
bot_profile_list()
```

## 注意事項

- profile 名稱需完全符合 bot_profile_list 回傳的名稱
- dest 目的地依職業不同，確認 class_name 再選對應清單
- bot_start_grinding 失敗時，可手動拆分步驟：profile_load → usescroll → start
- bot_stop 後 bot_status 確認 running=false 再做其他操作
- 掛機中途不要手動移動角色，會影響中心點計算
