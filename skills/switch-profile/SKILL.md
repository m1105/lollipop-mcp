---
name: switch-profile
description: 切換設定檔並重啟 bot
tools: [bot_stop, bot_profile_load, bot_start, bot_profile_list]
trigger: 切換設定|換設定|switch profile|換profile
---

## 用途

停止 bot → 載入新的設定檔（全部設定更新）→ 重新啟動 bot。

## 參數

- `$profile`: 設定檔名稱（從 `bot_profile_list()` 查詢可用的）

## 流程

```
# 1. 查看可用設定檔
bot_profile_list()

# 2. 停止 bot
bot_stop()

# 3. 載入新設定檔（會重置所有設定）
bot_profile_load(name="設定檔名稱")
sleep 1000

# 4. 重啟 bot
bot_start()
```

## 注意事項

- profile_load 會**全部重置**設定，不是只改部分
- 切換前確認設定檔名稱正確（用 bot_profile_list 查）
- 載入後等 1 秒再啟動，確保設定寫入完成
