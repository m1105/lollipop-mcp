---
name: scroll-management
description: 卷軸/書籤完整管理
tools: [bot_scroll_list, bot_scroll_show, bot_scroll_dest, bot_bookmarks, bot_bm_scan, bot_bm_click, bot_usescroll]
trigger: 卷軸|書籤|scroll|bookmark
---

## 用途

管理說話的卷軸（F12）與祝福卷軸書籤（F11）。
說話的卷軸可傳送到各村莊指定 NPC；祝福卷軸用已存書籤傳送。

## 常見操作

### 說話的卷軸傳送（F12）

**CRITICAL: 不可用 bot_useitem 使用說話的卷軸，會造成隨機傳送。**
必須走 scroll_show → scroll_dest 流程。

```
# 1. 查看背包有哪些卷軸
bot_scroll_list()

# 2. 開啟卷軸 UI（F12）
bot_scroll_show()

# 3. 查看可用目的地（依職業不同）
bot_scroll_dest()

# 4. 傳送到目的地
bot_usescroll(dest="古魯丁村|倉庫管理員")
```

dest 格式為 "村莊|傳送點"，必須完全符合 bot_scroll_dest 回傳的選項。

### 常用目的地範例

```
# 補給常用
bot_usescroll(dest="古魯丁村|雜貨商人")
bot_usescroll(dest="說話之島|雜貨商人")
bot_usescroll(dest="奇岩村|雜貨商人")

# 倉庫
bot_usescroll(dest="古魯丁村|倉庫管理員")

# 地監入口
bot_usescroll(dest="古魯丁村|古魯丁地監入口")
bot_usescroll(dest="說話之島|說話之島地監入口")
```

### 祝福卷軸書籤（F11）

```
# 開啟書籤列表（F11 = GLFW key 300）
bot_bookmarks()

# 掃描可用書籤
bot_bm_scan()

# 點擊第 0 個書籤傳送
bot_bm_click(idx=0)
```

### 返回卷軸

返回卷軸可直接 useitem，不會造成問題：
```
# 從 bot_inventory 找到返回卷軸的 uid
bot_inventory()
bot_useitem(uid=12345678)
```

## 注意事項

- 說話的卷軸 ≠ bot_useitem，禁用！用 scroll_show + scroll_dest 流程
- 目的地清單依職業不同，先 bot_status 確認 class_name
- 傳送後等待 3-5 秒再執行下一步
- 若 scroll_dest 回傳空，確認背包內有說話的卷軸且 scroll_show 已成功
