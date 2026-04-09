---
name: goto-blessed-ats
description: 前往祝福之地掛ATS（自動訓練系統）
tools: [bot_scroll_list, bot_glfw_key, bot_dialogs, dll_http, bot_position, bot_entities, bot_npc_click, bot_start]
trigger: ATS|祝福之地|blessed|ats
---

## 用途

傳送到祝福之地，選擇地區+種族，啟動 ATS 自動訓練。

## 前置條件

- 玩家必須將 ATS 開關放到快捷鍵 **F8**
- 背包需有**說話的卷軸**

## 參數

- `$zone`: 前往污染的祝福之地 | 前往墮落的祝福之地
- `$race`: 妖精之地 | 人類之地 | 妖魔之地 | 精靈之地

## 完整流程

```
# 1. 查背包卷軸
bot_scroll_list()

# 2. 按 F12 開卷軸選單
bot_glfw_key(key=301)
sleep 1500

# 3. 確認 TalkingScrollLayout 可見
bot_dialogs()  → 找 TalkingScrollLayout

# 4. 點擊祝福之地
dll_http(method="POST", path="/scroll_dest", body='{"dest":"祝福之地"}')
sleep 1000

# 5. 等傳送完成（5秒），確認位置
bot_position()
sleep 5000

# 6. 找 NPC 諾納梅
bot_entities()  → 找 InteractiveNPC 諾納梅，記 entity_id

# 7. 互動 NPC（用 entity_id，不要硬編 1665）
dll_http(method="POST", path="/bot/interact", body='{"entity_id": NPC_ID}')
sleep 1500

# 8. 確認 NpcTalkLayout 可見
bot_dialogs()  → 找 NpcTalkLayout

# 9. 選地區（污染/墮落）
bot_npc_click(dialog="NpcTalkLayout", keyword="前往污染的祝福之地")
sleep 2000

# 10. 選種族（妖精/人類/妖魔/精靈）
bot_npc_click(dialog="NpcTalkLayout", keyword="妖精之地")
sleep 3000

# 11. 按 F8 啟動 ATS
bot_glfw_key(key=297)
sleep 3000

# 12. 確認 ATS 啟動成功
bot_dialogs()  → 找 ATSMsgHudLayout = 成功
```

## 注意事項

- NPC 諾納梅的 entity_id 每次不同，必須從 bot_entities 結果取
- scroll_dest 用 POST 不是 GET
- 選地區後等 2 秒再選種族，太快會失敗
- F8 按完後等 3 秒確認 ATSMsgHudLayout 出現
- ATS 結束後用 `ats-watch-and-start` skill 自動啟動 bot
