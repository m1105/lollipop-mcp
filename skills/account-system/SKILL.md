---
name: account-system
description: 帳號管理 — 登入/授權/血盟
tools: [bot_auto_login, bot_auth_status, bot_pledge_join]
trigger: 登入|授權|血盟|login|auth|pledge
---

## 用途

觸發自動登入流程、查詢授權/License 狀態、加入血盟（公會）。

## 常見操作

### 觸發自動登入
```json
{ "tool": "bot_auto_login", "bot_id": "bot1" }
```
觸發 DLL 內建的登入狀態機：
1. 偵測登入畫面
2. 填入帳號密碼（從 DLL config 讀取）
3. 選擇伺服器 / 角色
4. 等待進入遊戲

回傳：`{ "status": "started" }` — 非同步，登入完成前 bot 指令會 queue 等待。

### 查詢授權狀態
```json
{ "tool": "bot_auth_status", "bot_id": "bot1" }
```
回傳：
```json
{
  "licensed": true,
  "machine_id": "ABC123",
  "expire_at": "2026-12-31T00:00:00Z",
  "plan": "pro"
}
```
- `licensed: false` 時大部分 bot 功能會被鎖定
- `expire_at` 接近時提醒用戶續期

### 加入血盟
```json
{ "tool": "bot_pledge_join", "bot_id": "bot1", "pledge_name": "NightWolves" }
```
需要角色已收到血盟邀請。若未有待處理邀請，指令會失敗並回傳錯誤。

## 注意事項

- `bot_auto_login` 是非同步操作，登入過程約需 15-30 秒
- 登入完成後用 `bot_player` 確認角色狀態再執行後續操作
- `bot_auth_status` 不需要遊戲在線，可在任何時候查詢
- 血盟加入後需等待伺服器確認（約 2-3 秒），建議 sleep 3000ms 後再查詢 `bot_player.pledge`
- 帳號密碼存於 DLL config 中，`bot_auto_login` 不接受明文密碼參數（安全設計）
