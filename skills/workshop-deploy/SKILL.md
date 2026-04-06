---
name: workshop-deploy
description: 部署更新 — DLL/腳本/Server 更新流程
tools: [opener_versions, bot_update_check, bot_update_download, opener_stop_all, opener_start_all]
trigger: 更新|部署|deploy|上新版
---

## 用途

部署新版 DLL、腳本或 Server 到工作室所有機台。

## DLL 更新流程

1. **檢查版本**
   ```
   opener_versions(host="192.168.0.114")
   → {"dll": "1.2.3", "scripts": "1.0.5"}
   ```

2. **從 bot 端檢查**
   ```
   bot_update_check(port=5577, host="192.168.0.114")
   → {"update_available": true, "current": "1.2.3", "latest": "1.2.4"}
   ```

3. **停機**
   ```
   bot_all_stop()                         → 停止所有 bot
   opener_stop_all(host="192.168.0.114")  → 停止所有遊戲客戶端
   ```

4. **下載更新**
   ```
   bot_update_download(port=5577, host="192.168.0.114")
   ```

5. **重啟**
   ```
   opener_start_all(host="192.168.0.114")  → 重啟遊戲（會自動注入新 DLL）
   ```

6. **驗證**
   ```
   opener_versions(host="192.168.0.114")  → 確認版本已更新
   fleet_health_check()                    → 確認全部正常
   ```

## 多機台更新

每台機器逐一更新（不要全部同時停）：
```
for each machine in machines:
  1. opener_stop_all(host=machine)
  2. 等待所有客戶端關閉
  3. bot_update_download (觸發更新)
  4. opener_start_all(host=machine)
  5. 確認該機台正常
  6. 下一台
```

## Server 更新

Server 更新由 git push 觸發（Lollipop/ 是獨立 git repo）：
```bash
cd Lollipop/ && git add -A && git commit -m "feat: ..." && git push
```
Server 會自動重啟（PM2/systemd）。

## 注意事項

- DLL 不要放在遊戲目錄內（NCGuard 會掃描）
- 更新後第一個小時要密切觀察 fleet_health_check
- 如果新版有問題，opener 的 config 中可以回退 DLL 版本
- 排程器在停機期間應該關閉 `schedule_toggle(0)`，更新完再開 `schedule_toggle(1)`
