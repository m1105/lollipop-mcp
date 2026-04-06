# 05 — 常見問題排除

> Last updated: 2026-04-06

當 Lollipop bot 出現問題時，本指南提供快速診斷和解決方案。

---

## 快速診斷流程

在深入各個問題之前，先執行這個快速檢查清單：

### 步驟 1: 檢查 bot 線上狀態

```bash
bot_list
```

**預期結果：** 至少一個 bot 在線。若為空陣列，跳到 [問題 1](#問題-1-bot_list-回傳空的)。

### 步驟 2: 檢查 bot 狀態

```bash
bot_status
```

**預期結果：** 顯示 HP、MP、位置、combat_state 等。若連接失敗，跳到 [問題 2](#問題-2-connection-refused-錯誤)。

### 步驟 3: 檢查 opener 運行狀態

```bash
opener_status
```

**預期結果：** 顯示所有帳號和遊戲進程狀態。若無進程，跳到 [問題 2](#問題-2-connection-refused-錯誤)。

### 步驟 4: 檢查網路連線

在 macOS 終端測試：

```bash
ping 192.168.0.114
```

改為你的 Windows IP。若 timeout，檢查網路和防火牆。

---

## 問題列表

### 問題 1: bot_list 回傳空的

**症狀：** 執行 `bot_list` 回傳 `[]` 空陣列，沒有任何 bot 線上。

**原因：**
- DLL 未注入到遊戲進程
- Windows 防火牆阻擋 bot 連接埠
- 遊戲進程已停止或崩潰
- IP 設定錯誤

**診斷步驟：**

1. **確認 opener 正在運行：**

```bash
opener_status
```

若無任何帳號實例，說明遊戲未啟動。

2. **確認防火牆開放連接埠：**

在 Windows 上（以系統管理員身份開啟 PowerShell）：

```powershell
netsh advfirewall firewall show rule name="Lollipop DLL API"
```

若無結果，表示防火牆規則未設定。

3. **驗證 DLL HTTP API 是否回應：**

```bash
curl http://192.168.0.114:5577/stats
```

改為你的 Windows IP。若 timeout 或 refused，DLL 未注入或防火牆阻擋。

4. **檢查 opener 日誌：**

在 Windows 上執行 opener 的 PowerShell 視窗，查看是否有錯誤訊息（例如 DLL 路徑錯誤、遊戲進程無法啟動等）。

**解決方案：**

#### 方案 A: 開放防火牆

在 Windows PowerShell（管理員模式）執行：

```powershell
netsh advfirewall firewall add rule name="Lollipop DLL API" dir=in action=allow protocol=tcp localport=5577-5599
```

#### 方案 B: 重新啟動遊戲帳號

```bash
opener_stop(acc_id="account_1")
# 等待 5 秒
opener_start(acc_id="account_1")
# 等待 30-60 秒讓遊戲和 DLL 完全啟動
bot_list
```

#### 方案 C: 驗證 IP 設定

檢查 `.mcp.json` 中的 `LOLLIPOP_DIRECT` 是否正確：

```bash
# macOS
cat ~/.mcp.json | grep LOLLIPOP_DIRECT
```

確認該 IP 確實是 Windows 遊戲機的 IP：

```bash
# Windows PowerShell
ipconfig
```

查找 `IPv4 Address`。

---

### 問題 2: "Connection refused" 錯誤

**症狀：** 執行任何 bot 命令時，得到 `Connection refused` 或 `Cannot connect to host`。

**原因：**
- opener.py 或 DLL HTTP server 沒在運行
- 網路不通（IP 錯誤或跨網路）
- 防火牆完全阻擋連接

**診斷步驟：**

1. **檢查 opener 是否正在執行：**

在 Windows 上，查看 opener.py 的 PowerShell 視窗是否仍開啟。若視窗已關閉或顯示錯誤，opener 已停止。

2. **測試 opener 的 HTTP API：**

```bash
curl http://192.168.0.114:8600/api/instances
```

改為你的 Windows IP。若無回應，opener 未運行。

3. **測試網路連通性：**

```bash
ping 192.168.0.114
```

若 timeout，兩台機器網路隔離或 IP 錯誤。

**解決方案：**

#### 方案 A: 在 Windows 上重新啟動 opener

在 Windows PowerShell 中：

```powershell
cd C:\Lollipop\stealth
python opener.py
```

將 PowerShell 視窗保持開啟，不要最小化。

#### 方案 B: 驗證 IP 連通性

```bash
# macOS
ping 192.168.0.114
# 按 Ctrl+C 停止

# 若 ping 失敗，嘗試
ifconfig | grep "inet "
```

確認 Windows 和 macOS 在同一網路。若在不同網路，需要設定 Tailscale VPN。

#### 方案 C: 檢查防火牆設定

在 Windows PowerShell（管理員模式）檢查規則：

```powershell
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*Lollipop*"} | Format-Table DisplayName, Enabled
```

若 `Enabled` 為 `False`，啟用規則：

```powershell
Set-NetFirewallRule -DisplayName "Lollipop DLL API" -Enabled True
```

---

### 問題 3: Bot 不打怪 (0 kills)

**症狀：** Bot 在線但不攻擊怪物，擊殺計數為 0，貨幣未增加。

**原因：**
- 戰鬥模組未啟動
- 設置有誤（攻擊範圍、優先怪物等）
- 地圖沒有怪物
- Bot 卡住或在等待某個狀態

**診斷步驟：**

1. **檢查戰鬥狀態：**

```bash
bot_combat_state
```

檢查輸出：
- `phase`：應為 `search`、`approach`、`attack` 等，不應為 `idle`
- `target`：應有一個怪物目標，如為 `null`，表示未發現怪物
- `blacklist`：可能的黑名單怪物

2. **檢查周圍是否有怪物：**

```bash
bot_entities
```

查看是否有 `type="monster"` 的實體。若無，地圖沒有怪物。

3. **檢查 bot 位置：**

```bash
bot_position
```

確認座標是否在有怪物的地區。

4. **檢查戰鬥設置：**

```bash
bot_config_get | grep -E "(combat|radius|attack)"
```

查看戰鬥半徑和優先怪物設置。

**解決方案：**

#### 方案 A: 啟動自動打怪流程

使用 `bot_start_grinding` 一鍵初始化：

```bash
bot_start_grinding(profile="default", dest="說話之島|稻草人修練場")
```

此命令會：
1. 傳送 bot 到指定位置
2. 設定打怪中心點
3. 啟動戰鬥模組
4. 開始自動打怪

#### 方案 B: 手動設定戰鬥參數

```bash
bot_setup_combat(enabled=1, center_x=32525, center_y=32832, radius=20, attack_dist=15)
```

然後啟動 bot：

```bash
bot_start
```

#### 方案 C: 重置配置

若設置混亂，重置為預設值：

```bash
bot_config_reset
```

然後重新執行 `bot_start_grinding`。

---

### 問題 4: "No bots online" 警告

**症狀：** 執行 `bot_list` 後，立即看到 `"No bots online"` 警告訊息。

**原因：**
- `.mcp.json` 的 IP 設定錯誤
- 網路沒有連通
- DNS 解析失敗（若用域名而非 IP）

**診斷步驟：**

1. **確認 .mcp.json 的 IP 設定：**

```bash
cat ~/.mcp.json | grep LOLLIPOP
```

輸出應類似：
```json
"LOLLIPOP_DIRECT": "192.168.0.114"
```

2. **確認 IP 是否對應正確的機器：**

```bash
ping 192.168.0.114
```

若無回應，IP 錯誤或該機器不在線。

3. **檢查 DNS（若使用域名）：**

```bash
nslookup your-server.com
```

若 DNS 失敗，使用 IP 位址代替。

**解決方案：**

#### 方案 A: 更新 .mcp.json

編輯 `~/.mcp.json`（或工作目錄的 `.mcp.json`）：

```json
{
  "mcpServers": {
    "lollipop": {
      "command": "python3",
      "args": ["/path/to/Lollipop/mcp/dist/run.py"],
      "env": {
        "LOLLIPOP_DIRECT": "192.168.1.50"
      }
    }
  }
}
```

確認 IP 與 Windows 機器的實際 IP 一致。在 Windows 上執行 `ipconfig` 查詢。

#### 方案 B: 重啟 Claude Code

更新 `.mcp.json` 後，重啟 Claude Code：

```bash
# 關閉 Claude Code
exit

# 重新啟動
claude
```

MCP server 會重新初始化，加載新的 IP 設定。

---

### 問題 5: Plugin 沒載入

**症狀：** Claude Code 沒有識別 Lollipop Plugin，無法執行 `bot_list` 等命令。錯誤訊息類似 `"lollipop" tool not found`。

**原因：**
- `.mcp.json` 語法錯誤
- `.mcp.json` 路徑不正確（不在工作目錄或 `~/.claude/`）
- Python 路徑錯誤或不存在
- MCP server 初始化失敗

**診斷步驟：**

1. **驗證 .mcp.json 存在且路徑正確：**

```bash
# 在工作目錄
ls -la .mcp.json

# 或在全域
ls -la ~/.mcp.json
```

至少一個應存在。

2. **驗證 JSON 語法：**

```bash
cat .mcp.json | python3 -m json.tool > /dev/null && echo "JSON valid" || echo "JSON invalid"
```

若輸出 "JSON invalid"，JSON 有語法錯誤。

3. **驗證 Python 路徑：**

```bash
which python3
# 或
/usr/bin/python3 --version
```

確認路徑存在且可執行。

4. **檢查 Claude Code 日誌：**

在 Claude Code 終端，查看是否有加載錯誤。

**解決方案：**

#### 方案 A: 修復 .mcp.json 語法

常見錯誤：
- 逗號位置不對
- 引號不匹配
- 路徑中反斜槓未雙倍

```json
{
  "mcpServers": {
    "lollipop": {
      "command": "python3",
      "args": ["/Users/yourname/Projects/Lollipop/mcp/dist/run.py"],
      "env": {
        "LOLLIPOP_DIRECT": "192.168.0.114"
      }
    }
  }
}
```

用線上 JSON 驗證器（例如 [jsonlint.com](https://www.jsonlint.com/)）檢查。

#### 方案 B: 確認路徑正確

```bash
# 驗證 run.py 存在
ls -la /Users/yourname/Projects/Lollipop/mcp/dist/run.py

# 確認 python3 可執行
python3 --version
```

若路徑不同，更新 `.mcp.json`。

#### 方案 C: 使用自動設定 skill

若手動編輯困難，使用自動設定：

```bash
/lollipop:setup
```

此 skill 會引導你完成設定並自動建立 `.mcp.json`。

#### 方案 D: 手動啟動 MCP server

在 Claude Code 終端，測試 MCP server 是否能獨立啟動：

```bash
cd /Users/yourname/Projects/Lollipop/mcp/dist
python3 run.py
```

若出現錯誤，檢查相依套件：

```bash
pip install -r requirements.txt
```

---

### 問題 6: 補給失敗 (補給跑不完)

**症狀：** 執行 `bot_supply_trigger` 或 `bot_full_supply` 後，bot 不動或補給卡住。物品未購買，金幣未消耗。

**原因：**
- NPC 位置設定錯誤
- 傳送卷軸目的地不對
- NPC 不存在或名稱拼錯
- bot 背包滿了
- 金幣不足

**診斷步驟：**

1. **檢查補給設置：**

```bash
bot_supply_state
```

查看輸出：
- `state`：應為 `idle`、`buying`、`selling` 等狀態
- `town_dest`：目的地（格式 `"村莊|NPC"`）
- `npc_name`：NPC 名稱
- `buy_items`：要購買的物品列表

2. **確認 NPC 在該位置：**

```bash
bot_position
```

傳送到 NPC 附近，然後執行 `bot_entities` 查看周圍 NPC。

3. **檢查背包空間：**

```bash
bot_inventory
```

若 `weight_percent` 接近 100%，背包已滿。

4. **確認金幣足夠：**

```bash
bot_player
```

查看 `money` 欄位。

**解決方案：**

#### 方案 A: 手動設定補給位置

```bash
bot_setup_supply(
  enabled=1,
  town_dest="說話之島|潘朵拉",
  town_scroll="說話的卷軸",
  return_dest="說話之島|雜貨商人",
  return_scroll="說話的卷軸",
  npc_name="潘朵拉",
  npc_x=32580,
  npc_y=32929
)
```

確認 `town_dest` 和 `return_dest` 格式正確。常見村莊和 NPC：

| 村莊 | 推薦 NPC | 座標 |
|------|---------|------|
| 說話之島 | 潘朵拉（雜貨） | (32580, 32929) |
| 古魯丁村 | 露西（雜貨） | (32611, 32732) |
| 奇岩村 | 邁爾（雜貨） | (33437, 32798) |

#### 方案 B: 清空背包

若背包滿了，先賣掉不需要的物品：

```bash
bot_warehouse_deposit(items='{"name":"短劍","qty":0}')
```

然後重試補給。

#### 方案 C: 使用一鍵補給

最簡單的方式是使用整合命令：

```bash
bot_full_supply
```

此命令會自動傳送、購買、返回，無需手動設定。

---

### 問題 7: 排程沒執行

**症狀：** 設定了排程（schedule），但到時間時沒有執行。Bot 未按預期啟動或停止。

**原因：**
- 排程器被禁用
- 排程時間設定錯誤
- 時區不匹配
- 排程語法錯誤

**診斷步驟：**

1. **檢查排程器狀態：**

```bash
schedule_status
```

查看輸出：
- `enabled`：應為 `true`
- `entries`：應列出所有排程條目

2. **驗證排程時間：**

```bash
schedule_running
```

顯示目前正在運行的排程。若為空，表示無排程命中。

3. **檢查排程時間格式：**

排程時間格式應為 `YYYY-MM-DD HH:MM`，例如 `2026-04-06 14:30`。

**解決方案：**

#### 方案 A: 啟用排程器

```bash
schedule_toggle(enabled=1)
```

#### 方案 B: 驗證排程時間

列出所有排程：

```bash
schedule_status | grep entries
```

確認時間格式正確（例如 `2026-04-06 14:30`），並確認時間已到達。

#### 方案 C: 重新建立排程

刪除舊排程並新建：

```bash
schedule_delete(entry_id="entry_123")

# 新建排程（格式: 開始時間、帳號、結束時間）
schedule_add(
  slot_id="slot_1",
  acc_id="account_1",
  start="2026-04-06 14:00",
  end="2026-04-06 18:00",
  profile="default"
)
```

---

### 問題 8: 死亡率太高

**症狀：** Bot 頻繁死亡，擊殺數低，消耗的補給品和時間超過預期收益。

**原因：**
- 地圖難度太高
- 被其他玩家 PK
- 保護模組未啟動（未設定自動逃跑/回點）
- 移動速度或躲避不足
- 怪物等級超過 bot 等級太多

**診斷步驟：**

1. **檢查死亡率和風險分數：**

```bash
fleet_risk_scores
```

若 `death_rate` 高於 5%（每小時 3+ 死亡），視為風險偏高。

2. **查看周圍玩家數量：**

```bash
bot_entities | grep type=player
```

若玩家過多，地圖可能被占領，易被 PK。

3. **檢查怪物等級：**

```bash
bot_entities | grep -E "(level|name)"
```

若怪物等級遠高於 bot，需要搬家。

4. **檢查保護模組設置：**

```bash
bot_config_get | grep -E "(protect|escape|death)"
```

**解決方案：**

#### 方案 A: 啟用自動逃跑

```bash
bot_setup_protect(
  escape_enabled=1,
  escape_hp_pct=30,
  escape_items="說話的卷軸|傳送師"
)
```

當 HP 低於 30% 時，自動使用傳送卷軸逃跑。

#### 方案 B: 設定死亡重生

```bash
bot_setup_protect(
  death_enabled=1,
  death_count=3,
  death_window_min=10,
  death_pause_min=5,
  return_item="說話的卷軸",
  return_dest="說話之島|旅館"
)
```

死亡 3 次後，暫停 5 分鐘，然後返回城鎮。

#### 方案 C: 搬到更安全的地圖

```bash
bot_teleport_scroll(dest="說話之島|稻草人修練場")
# 等待 3 秒
bot_start_grinding(dest="說話之島|稻草人修練場")
```

稻草人修練場是新手區，怪物較弱且玩家少。

#### 方案 D: 降低攻擊範圍

```bash
bot_setup_combat(
  enabled=1,
  center_x=32525,
  center_y=32832,
  radius=10,
  attack_dist=5
)
```

縮小打怪範圍，避免聚集過多怪物。

---

## 還是解決不了？

若以上方案都無法解決問題，進行深度診斷：

### 步驟 1: 收集日誌

```bash
# 收集 bot DLL 日誌
bot_logs(level="D", since_seq=-1)

# 收集 opener 日誌（在 Windows 的 PowerShell 視窗複製）
opener_logs
```

### 步驟 2: 檢查 MCP server 日誌

```bash
# macOS
cat ~/.claude/logs/lollipop.log | tail -100
```

### 步驟 3: 測試基本連通性

```bash
# 直接 HTTP 請求 DLL API
curl -s http://192.168.0.114:5577/stats | python3 -m json.tool

# 測試 opener API
curl -s http://192.168.0.114:8600/api/instances | python3 -m json.tool
```

### 步驟 4: 重啟整個系統

順序很重要：

```bash
# 1. macOS: 重啟 Claude Code
exit

# 2. Windows: 停止 opener
# Ctrl+C 在 opener.py 的 PowerShell 視窗中

# 3. Windows: 關閉遊戲
# 手動關閉遊戲視窗

# 4. Windows: 重新啟動 opener
cd C:\Lollipop\stealth
python opener.py

# 5. macOS: 重新啟動 Claude Code
claude

# 6. macOS: 驗證連線
bot_list
```

### 步驟 5: 聯絡技術支援

如有需要，提供以下資訊：
- bot_status 的完整輸出
- bot_logs 最後 100 行
- Windows 防火牆規則列表
- 錯誤發生時的準確時間和操作步驟
- macOS 和 Windows 的 IP 位址

---

## 常見問題速查表

| 症狀 | 最可能原因 | 快速修復 |
|------|----------|--------|
| `bot_list` 為空 | DLL 未注入或防火牆阻擋 | `opener_start(acc_id="account_1")` 並等待 60s |
| Connection refused | opener 未運行 | Windows 上重啟 `opener.py` |
| 0 kills | 戰鬥未啟動 | `bot_start_grinding(dest="...")` |
| "No bots online" | IP 錯誤 | 驗證 `.mcp.json` 的 `LOLLIPOP_DIRECT` |
| Plugin 不載入 | `.mcp.json` 語法或路徑錯誤 | 驗證 JSON 語法並用絕對路徑 |
| 補給卡住 | NPC 位置或傳送卷軸錯誤 | 用 `bot_full_supply` 替代 |
| 排程未執行 | 排程器禁用或時間格式錯誤 | `schedule_toggle(enabled=1)` |
| 死亡率高 | 地圖太難或被 PK | `bot_setup_protect(escape_enabled=1)` 或搬地圖 |

---

## 進階診斷命令

若基本步驟無法解決，嘗試以下進階命令：

### 掃描記憶體和模式

```bash
# 重新掃描遊戲記憶體中的 bot 結構
bot_rescan
```

### 檢查 bot 的全面狀態

```bash
# 包含 DLL 版本、掃描結果、記憶體地址等
bot_status | python3 -m json.tool
```

### 列出所有機器

```bash
# 若使用 Tailscale 多機設定
machine_list
```

### 比較兩個 bot 的配置

```bash
# A/B 對比，找出差異
bot_compare(bot_a_host="192.168.0.114", bot_a_port=5577, bot_b_host="192.168.0.114", bot_b_port=5578)
```

---

## 獲得幫助

如遇到無法解決的問題：

1. **查看本文檔** — 99% 的問題在這裡都有答案
2. **檢查日誌** — `bot_logs`、`opener_logs` 通常會指出根本原因
3. **重啟系統** — 大多數問題可通過「冷啟動」解決（關閉所有程式再重開）
4. **聯絡開發者** — 提供完整的日誌輸出和重現步驟

---

**祝你順利解決問題！** 若本文檔有遺漏或不夠清楚之處，歡迎提交反饋。
