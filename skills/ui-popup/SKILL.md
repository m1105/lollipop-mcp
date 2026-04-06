---
name: ui-popup
description: UI 彈窗處理 — 偵測並關閉 ServerSelect_MsgPopup 等
---

# UI Popup 處理

## ServerSelect_MsgPopup（伺服器維護公告）

`bot_click(dialog="ServerSelect_MsgPopup", widget="Bt_Ok")` 關閉

會擋住所有遊戲操作，需要偵測並關閉。

## 已知 Layout + Button 組合

| Layout | Button | 功能 |
|--------|--------|------|
| NpcTalkLayout | Bt_Npc_Buy | 開購買 |
| NpcTalkLayout | Bt_Npc_Sell | 開出售 |
| NpcTalkLayout | Bt_Close | 關閉 NPC 對話 |
| NpcShopLayout | Bt_Buy | 確認購買 |
| NpcShopLayout | Bt_Close | 關閉商店 |
| StorageLayout | Bt_Ok | 確認存取 |
| StorageLayout | Bt_Close | 關閉倉庫 |
| ServerSelect_MsgPopup | Bt_Ok | 關閉公告 |
| TalkingScrollLayout | Bt_Close | 關閉卷軸選單 |
| QuitLayout | Bt_Ok | 確認離開 |
