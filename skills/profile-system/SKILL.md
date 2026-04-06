---
name: profile-system
description: Profile 管理 — 存取 148 參數的設定檔
tools: [bot_profile_list, bot_profile_load, bot_profile_delete]
trigger: profile|設定檔|載入設定
---

## 用途

管理 bot 設定檔。每個 profile 是 148 個 config 欄位的完整快照。

## 常見操作

### 列出 profile
```
bot_profile_list(port=5577)
→ {"current": "default", "profiles": ["default", "grind_gd1", "party_heal"]}
```

### 載入 profile
```
bot_profile_load(name="grind_gd1", port=5577)
→ 覆蓋所有 148 個 config 欄位
```

### 刪除 profile
```
bot_profile_delete(name="old_config", port=5577)
```

## 注意事項

- profile_load 是原子操作：148 欄位同時替換
- 載入後需要 bot_start 才會開始掛機
- 不同機台的 profile 獨立
- bot_start_grinding(profile="xxx") 可以載入+傳送+啟動一步完成
