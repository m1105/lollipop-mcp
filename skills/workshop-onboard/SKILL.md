---
name: workshop-onboard
description: 新帳號上架 — 加帳號→設排程→開始掛機
tools: [opener_add_account, opener_start, schedule_add, bot_profile_load, bot_start_grinding]
trigger: 加新帳號|onboard|新帳號上架
---

## 用途

把一個新帳號加入工作室，從零到能自動掛機。

## 流程

1. **加入 opener**
   ```
   opener_add_account(
     username="email@example.com",
     password="xxx",
     server_page=1,
     server_num=3,
     char_slot=0,
     host="192.168.0.114"
   )
   ```

2. **啟動遊戲**
   ```
   opener_start(acc_id="email@example.com", host="192.168.0.114")
   ```
   等待遊戲載入完成（約 2-3 分鐘）

3. **確認連線**
   ```
   bot_list()  → 確認新 bot 出現在清單中
   bot_status(port=新bot的port, host="192.168.0.114")
   ```

4. **載入 profile**
   ```
   bot_profile_load(name="grind_gd1", port=新port, host=新host)
   ```

5. **加入排程**
   ```
   schedule_add(
     slot_id="2",
     acc_id="email@example.com",
     start="2026-04-07 08:00",
     end="2026-04-07 20:00",
     profile="grind_gd1",
     host="192.168.0.114"
   )
   ```

6. **開始掛機**
   ```
   bot_start_grinding(
     profile="grind_gd1",
     dest="說話之島|雜貨商人",
     port=新port, host=新host
   )
   ```

## 注意事項

- 新帳號第一天建議排較短班次（8hr），觀察穩定度
- 確認 char_slot 是正確的（0=第一個角色, 1=第二個）
- server_page 和 server_num 要對應遊戲的伺服器選擇頁面
- 密碼會加密存儲在 opener 的 config 中
