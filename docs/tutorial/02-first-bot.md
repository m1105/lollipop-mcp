# 02 — 第一隻 Bot 上線

> Last updated: 2026-04-06

透過 Claude Code 啟動遊戲帳號、注入 DLL、驗證 bot 連線，然後自動練功。本教學涵蓋從啟動到自動戰鬥的完整流程。

---

## 你需要準備

- **已完成 [01.5 — Windows 端部署](01.5-deploy-environment.md)**
  - opener.py 正在 Windows 機器上運行
  - DLL 已編譯並放在 `C:\Lollipop\` 或類似位置
  - 帳號已配置在 `accounts.json` 中

- **Claude Code 已啟動**
  - Lollipop MCP 連線正常（可以調用 bot_* 和 opener_* 工具）

- **在 Claude Code 中輸入命令**
  - 你可以用自然語言（例如「看一下 opener 狀態」）或直接調用工具函式

---

## Step 1: 確認 Opener 狀態

### 你要做什麼

確認 Windows 機器上 opener.py 已啟動，帳號配置已讀取。

### 在 Claude Code 中輸入

**自然語言：**
```
看一下 opener 狀態，告訴我有哪些機器和帳號
```

**或直接呼叫工具：**
```
opener_status
```

### 預期結果

你會看到類似的輸出：
```json
{
  "machine_name": "DESKTOP-ABC123",
  "ip": "192.168.1.100",
  "port": 8080,
  "status": "running",
  "accounts": [
    {
      "id": "1",
      "username": "player_001@linuxgg.com",
      "password": "***",
      "server": 1,
      "slot": 1,
      "char_name": "Warrior_01"
    },
    {
      "id": "2",
      "username": "player_002@linuxgg.com",
      "password": "***",
      "server": 1,
      "slot": 2,
      "char_name": "Mage_01"
    }
  ]
}
```

### 這表示什麼

- **machine_name**: Windows 機器識別碼
- **status: running**: opener.py 正在運行，DLL 準備好注入
- **accounts[]**: 已配置的帳號列表，每個帳號對應一個遊戲角色

如果你看不到任何帳號，請檢查：
- opener.py 是否正在運行（在 Windows 上執行 `python C:\Lollipop\stealth\opener.py`）
- `accounts.json` 是否有帳號配置
- 帳號的 `server` 和 `slot` 欄位是否填寫正確

---

## Step 2: 啟動遊戲帳號

### 你要做什麼

啟動第一個帳號的遊戲客戶端。opener.py 會自動注入 DLL。

### 在 Claude Code 中輸入

**自然語言：**
```
啟動 id=1 的帳號
```

**或直接呼叫工具：**
```
opener_start(acc_id="1")
```

### 預期結果

遊戲窗口會在 Windows 上彈出，顯示登入畫面。你會看到 Claude Code 返回：
```json
{
  "acc_id": "1",
  "status": "starting",
  "message": "Game process launched (PID: 12345)"
}
```

### 這表示什麼

- 遊戲客戶端程序已啟動
- launcher.exe 正在注入 DLL 到遊戲進程
- 下一步是等待 DLL 初始化

### 如果出現問題

| 問題 | 原因 | 解決方案 |
|------|------|---------|
| `Game process failed to start` | 遊戲路徑不正確 | 檢查 `servers.json` 中的 `game_path` |
| `Access denied` | 權限不足 | 以管理員身份執行 opener.py |
| `DLL injection failed` | DLL 路徑或 launcher.exe 不存在 | 檢查 `C:\Lollipop\` 目錄結構 |
| `Process timed out` | 遊戲啟動太慢 | 等待 60 秒後重試 |

---

## Step 3: 等待 DLL 注入和初始化

### 你要做什麼

遊戲啟動後，DLL 需要時間初始化。等待 30-60 秒。

### 需要多久

- **遊戲載入**: 10-20 秒（看硬體速度）
- **登入畫面**: 5-10 秒
- **DLL 初始化**: 10-20 秒（連接本地 HTTP 伺服器、掃描模式、讀取內存）
- **總計**: 約 30-60 秒

### 這段時間發生了什麼

在 Windows 機器上，遊戲正在：
1. 載入客戶端（顯示登入畫面）
2. launcher.exe 將 DLL 注入到遊戲進程
3. DLL 初始化，掃描遊戲模式，啟動本地 HTTP 伺服器
4. DLL 向 Claude Code（MCP）註冊，準備接收命令

你可以選擇在遊戲登入畫面上手動登入，或讓 bot 自動登入（如果配置了帳號密碼）。

### 無需任何操作

**不要** 在 Claude Code 中輸入任何命令。只需等待。

---

## Step 4: 確認 Bot 連線

### 你要做什麼

檢查新啟動的 bot 是否已連線到 Claude Code。

### 在 Claude Code 中輸入

**自然語言：**
```
列出所有在線的 bot
```

**或直接呼叫工具：**
```
bot_list
```

### 預期結果

你會看到類似的輸出：
```json
[
  {
    "host": "192.168.1.100",
    "port": 11001,
    "char_name": "Warrior_01",
    "email": "player_001@linuxgg.com",
    "level": 42,
    "hp": 850,
    "class": "warrior",
    "bot": {
      "enabled": false,
      "state": "idle"
    }
  }
]
```

### 這表示什麼

| 欄位 | 說明 |
|------|------|
| `host` | Windows 機器 IP 位址 |
| `port` | DLL 本地 HTTP 伺服器端口（通常 11001-11009） |
| `char_name` | 角色名稱 |
| `level` | 角色等級 |
| `class` | 職業類別（warrior, mage, archer 等） |
| `bot.enabled` | bot 自動化是否啟用（false = 尚未開始） |
| `bot.state` | bot 目前狀態（idle, grinding, supply 等） |

### 如果沒看到 Bot

| 問題 | 原因 | 解決方案 |
|------|------|---------|
| bot_list 為空 | DLL 尚未初始化 | 再等 10-20 秒 |
| 仍然為空 | DLL 注入失敗 | 檢查 Windows 事件日誌，查看 launcher.exe 是否出錯 |
| 端口衝突 | 已有其他 bot 佔用該端口 | 啟動不同的帳號 |
| 遊戲仍在登入畫面 | 未登入遊戲 | 手動或自動完成登入 |

---

## Step 5: 查看 Bot 詳細狀態

### 你要做什麼

深入查看新 bot 的詳細狀態，包含座標、技能、裝備、戰鬥狀態等。

### 在 Claude Code 中輸入

**自然語言：**
```
查看第一隻 bot 的詳細狀態
```

**或直接呼叫工具（使用 bot_list 中的 port 和 host）：**
```
bot_status(host="192.168.1.100", port=11001)
```

### 預期結果

```json
{
  "version": "2.25",
  "char_name": "Warrior_01",
  "level": 42,
  "exp": 123456,
  "class_name": "Elf Warrior",
  "hp": 850,
  "hp_max": 850,
  "mp": 300,
  "mp_max": 300,
  "x": 32525,
  "y": 32832,
  "map_id": 0,
  "map_name": "說話之島",
  "weight": 1250,
  "weight_max": 1800,
  "food": 85,
  "alignment": 2500,
  "scan": {
    "subsystems_found": 57,
    "game_manager": "0x7FF619B50000",
    "pattern_matches": 23
  },
  "bot": {
    "enabled": false,
    "state": "idle",
    "combat": {
      "phase": "idle",
      "target": null,
      "roaming": false
    }
  }
}
```

### 詳解重要欄位

| 欄位 | 說明 | 範例值 |
|------|------|--------|
| `char_name` | 角色名稱 | "Warrior_01" |
| `level` | 角色等級 | 42 |
| `hp / hp_max` | 當前/最大血量 | 850 / 850 |
| `mp / mp_max` | 當前/最大魔法值 | 300 / 300 |
| `x, y` | 世界座標 | (32525, 32832) |
| `map_id` | 地圖識別碼 | 0 = 說話之島 |
| `weight / weight_max` | 當前/最大負重 | 1250 / 1800 |
| `food` | 飽食度（0-100） | 85 |
| `bot.enabled` | bot 是否運行 | false（尚未啟動） |
| `bot.state` | bot 狀態機 | "idle" |
| `bot.combat.phase` | 戰鬥階段 | "idle"（未戰鬥） |
| `scan.subsystems_found` | DLL 找到的遊戲子系統數 | 57（正常） |

### 座標速查表

常見位置及其坐標：

| 位置 | 座標 | 用途 |
|------|------|------|
| 稻草人修練場 | (32525, 32832) | 新手練功點 |
| 說話之島雜貨 | (32478, 32851) 附近 | NPC 補給 |
| 古魯丁地監入口 | (32728, 32929) | 進階練功 |
| 沙漠綠洲 | (32860, 33253) | 高等練功點 |
| 說話之島港口 | (32478, 32851) | 傳送點 |

### 如果狀態異常

| 狀況 | 可能原因 | 下一步 |
|------|--------|--------|
| `hp` 為 0 | 角色已死亡 | 使用 `/teleport` 傳送到安全位置或村莊 |
| `weight > weight_max` | 背包超重 | 使用 `bot_warehouse_deposit` 存入倉庫或賣掉物品 |
| `food < 50` | 飽食度過低 | 使用食物或去村莊補給 |
| `scan.subsystems_found < 50` | DLL 掃描不完整 | 等待 10 秒後重新執行 `bot_rescan` |

---

## Step 6: 開始自動練功

### 你要做什麼

啟動 bot 自動化。bot 會自動搜索怪物、攻擊、撿取掉落物、補給、巡邏。

### 在 Claude Code 中輸入

**自然語言：**
```
開始練功（使用預設設定）
```

**或直接呼叫工具：**
```
bot_start_grinding(host="192.168.1.100", port=11001)
```

### 預期結果

```json
{
  "success": true,
  "message": "Grinding started",
  "config": {
    "combat_enabled": true,
    "loot_enabled": true,
    "supply_enabled": true,
    "protect_enabled": true,
    "roam_mode": "raycast"
  },
  "status": "grinding"
}
```

### 這表示什麼

Bot 現在開始自動運行，包含以下模組：

| 模組 | 功能 |
|------|------|
| **Combat** | 掃描周圍怪物，自動攻擊（預設範圍 15 格） |
| **Loot** | 怪物死亡後自動撿取掉落物（預設範圍 10 格） |
| **Supply** | 當消耗品不足時自動回城補給 |
| **Protect** | 血量低時自動逃離危險區域 |
| **Roaming** | 沒有怪物時使用 raycast 巡邏搜索 |

### 自動化做什麼

一旦啟動，bot 會循環執行以下動作：

```
1. 掃描周圍 30 格內的怪物
   ↓
2. 如果有怪物：選擇優先目標 → 移動靠近 → 攻擊
   如果沒怪物：巡邏搜索（raycast/spiral 模式）
   ↓
3. 怪物死亡後自動撿取掉落物
   ↓
4. 如果背包滿或血量低：回城補給 → 返回原地繼續練功
   ↓
5. 重複步驟 1-4
```

### 實時監控

練功期間，你可以隨時查看進度：

```
bot_stats(host="192.168.1.100", port=11001)
```

預期結果：
```json
{
  "kills": 245,
  "loots": 1520,
  "deaths": 0,
  "gold_earned": 125000,
  "uptime_ms": 300000,
  "kills_per_hour": 294,
  "gold_per_hour": 150000
}
```

| 欄位 | 說明 |
|------|------|
| `kills` | 累計擊殺怪物數 |
| `loots` | 累計撿取掉落物數 |
| `deaths` | 累計死亡次數 |
| `gold_earned` | 累計獲得金幣 |
| `uptime_ms` | 運行時間（毫秒） |
| `kills_per_hour` | 時間鐘點戰鬥效率 |
| `gold_per_hour` | 時間鐘點金幣收益 |

---

## Step 7: 檢查成果（等待 5 分鐘）

### 你要做什麼

讓 bot 練習 5 分鐘，然後查看數據。

### 時間表

```
T+0:00  啟動 bot_start_grinding
T+5:00  查看 bot_stats 確認成果
```

### 在 Claude Code 中輸入

```
bot_stats(host="192.168.1.100", port=11001)
```

### 預期的 5 分鐘成績

根據地圖難度：

| 地圖 | 預期 kills | 預期金幣 | 預期 gold/hr |
|------|-----------|---------|-------------|
| 稻草人修練場 (LV 20) | 150-200 | 75K-100K | 900K-1.2M |
| 說話之島森林 (LV 25) | 100-150 | 100K-150K | 1.2M-1.8M |
| 古魯丁地監 (LV 35) | 50-100 | 150K-250K | 1.8M-3M |
| 龍之谷 (LV 50+) | 20-50 | 250K-500K | 3M-6M |

### 結果解讀

**好的進度：**
```json
{
  "kills": 180,
  "gold_earned": 120000,
  "kills_per_hour": 2160,
  "gold_per_hour": 1440000
}
```
→ Bot 正常運行，已進入穩定狀態。

**需要調整：**
```json
{
  "kills": 5,
  "deaths": 3,
  "gold_earned": 0
}
```
→ 地圖太難或 bot 配置有問題（見下方排查）。

---

## 如果出現問題

### 問題 1: Bot 列表為空（沒有看到 bot 連線）

| 症狀 | 檢查項目 |
|------|---------|
| `bot_list()` 回傳 `[]` | 1. Windows 上 opener.py 是否正在運行？ |
| | 2. 遊戲窗口是否可見？ |
| | 3. DLL 是否已正確注入？（檢查 Windows 事件日誌） |
| | 4. 防火牆是否阻擋了 11001-11009 端口？ |
| | 5. 再等 30 秒後重試（DLL 初始化需要時間） |

**解決方案：**
```
# 強制重掃描 bot（已連線的情況下）
bot_rescan()

# 檢查 opener 日誌
opener_logs()

# 重啟 opener
# 1. 在 Windows 上停止 opener.py (Ctrl+C)
# 2. 重新執行：python C:\Lollipop\stealth\opener.py
# 3. 重新啟動遊戲
```

---

### 問題 2: Bot 連線後無法攻擊（kills 為 0）

| 症狀 | 可能原因 | 解決方案 |
|------|---------|---------|
| `bot_stats` 顯示 `kills: 0` | 1. 地圖沒有怪物 | 使用 `bot_teleport_scroll` 換到有怪物的地圖 |
| | 2. 怪物等級太高 | 檢查 `bot_combat_state`，改為較簡單的地圖 |
| | 3. Combat 模組未啟用 | 執行 `bot_setup_combat(enabled=1)` |
| | 4. 距離怪物太遠 | 檢查 `combat_radius` 設定，改為 20 或更大 |

**立即診斷：**
```
bot_combat_state(host="192.168.1.100", port=11001)
```

預期結果：
```json
{
  "phase": "searching",          // 或 "attacking"
  "target": null,                // 或怪物 ID
  "nearby_mobs": [
    {"id": 12345, "name": "Goblin", "distance": 8}
  ],
  "blacklist_count": 0
}
```

**如果 `nearby_mobs` 為空：** 該地圖沒有怪物，立即傳送到其他地圖。

---

### 問題 3: Bot 一直死亡（deaths > kills）

| 症狀 | 可能原因 | 解決方案 |
|------|---------|---------|
| 死亡超過攻擊次數 | 1. 地圖怪物等級太高 | 用 `bot_teleport_scroll("說話之島")` 傳送到簡單地圖 |
| | 2. 裝備不足 | 確保角色有穿上武器和防具 |
| | 3. Protect 模組禁用 | 執行 `bot_setup_protect(escape_enabled=1)` |

**緊急停止：**
```
bot_stop(host="192.168.1.100", port=11001)
```

**檢查防護狀態：**
```
bot_check_health(host="192.168.1.100", port=11001)
```

回傳 health issues 列表，例如：
```json
{
  "issues": [
    "HP 低於最大值的 30%",
    "背包超重 (1800/1800)",
    "食物不足 (10/100)"
  ]
}
```

---

### 問題 4: Bot 負重過高（背包滿）

| 症狀 | 解決方案 |
|------|---------|
| `weight >= weight_max` | 執行倉庫存儲：`bot_warehouse_deposit("[{\\"name\\": \\"金幣\\", \\"qty\\": 0}]")` |
| 掉落物無法撿取 | 或手動賣掉物品 |

**自動補給和存儲：**
```
bot_full_supply()
```
會自動回城 → 存儲 → 補給 → 返回原地。

---

### 問題 5: Bot 補給失敗或卡住

| 症狀 | 可能原因 | 解決方案 |
|------|---------|---------|
| 無法傳送到城鎮 | 說話的卷軸不足或配置錯誤 | 檢查 `bot_scroll_list()` 確認有卷軸 |
| 傳送後卡在城鎮 | 返回卷軸配置錯誤 | 檢查 `bot_setup_supply` 中的 `return_dest` |
| NPC 不互動 | NPC 不在線或 npc_x/npc_y 座標錯誤 | 手動傳送到該 NPC，用 `bot_interact` 測試 |

**重設補給配置：**
```
bot_setup_supply(
  enabled=1,
  town_dest="說話之島|雜貨商人",
  return_dest="稻草人修練場"
)
```

---

## 下一步

當第一隻 bot 穩定運行後：

1. **啟動更多 bot**
   - 在 `accounts.json` 中配置其他帳號
   - 重複 Step 2-6 啟動新的 bot

2. **優化 bot 配置**
   - 閱讀 [03 — 管理員日常操作](03-daily-ops.md)
   - 調整 combat_radius、loot_range、supply 閾值

3. **監控全隊效能**
   - 使用 `bot_all_status()` 監控所有 bot
   - 用 `fleet_performance()` 比較 bot 間的金幣效率

4. **設定自動化排程**
   - 使用 Cron 排程定時開啟/關閉 bot
   - 配置自動重啟和故障恢復

---

## 快速參考

### 常用命令

| 任務 | 命令 |
|------|------|
| 看所有 bot | `bot_list()` |
| 查看特定 bot 狀態 | `bot_status(host="IP", port=PORT)` |
| 查看 bot 成績 | `bot_stats(host="IP", port=PORT)` |
| 啟動自動練功 | `bot_start_grinding(host="IP", port=PORT)` |
| 停止練功 | `bot_stop(host="IP", port=PORT)` |
| 傳送到村莊 | `bot_teleport_scroll(host="IP", port=PORT, dest="說話之島")` |
| 檢查 bot 健康度 | `bot_check_health(host="IP", port=PORT)` |
| 查看戰鬥狀態 | `bot_combat_state(host="IP", port=PORT)` |
| 強制補給 | `bot_full_supply(host="IP", port=PORT)` |

### 常用傳送目的地

| 目標 | 說話的卷軸目的地 | 用途 |
|------|---------------|------|
| 新手練功 | `"說話之島\|稻草人修練場"` | LV 15-25 |
| 進階練功 | `"古魯丁村\|古魯丁地監入口"` | LV 30-40 |
| 高等練功 | `"說話之島\|龍之谷入口"` | LV 45+ |
| 回城補給 | `"說話之島\|雜貨商人"` | 補充消耗品 |

### 故障排查快速表

| 症狀 | 快速檢查 |
|------|---------|
| Bot 未上線 | `bot_list()` → 等 30 秒 → `opener_logs()` |
| 不攻擊怪物 | `bot_combat_state()` → 檢查 nearby_mobs |
| 一直死 | `bot_check_health()` → 傳送到簡單地圖 |
| 背包滿 | `bot_full_supply()` → 自動存儲並返回 |
| 卡住不動 | `bot_stop()` → 檢查座標 → `bot_position()` |

---

## 支援和反饋

如遇到問題或想提建議：

1. **查看本教學的常見問題區段**
2. **檢查 opener.py 日誌**：`opener_logs(host="...")`
3. **檢查 DLL 掃描結果**：`bot_scan(host="...", port=...)`
4. **提交 GitHub Issue**（附上錯誤訊息和 bot_status 輸出）

---

## 重要安全提示

- **勿分享 API Key 或帳號密碼** — 任何人獲取這些資訊都可以控制你的 bot 和帳號
- **勿在公開的 GitHub repo 中存儲敏感信息** — 使用環境變數或本地 `.env` 文件
- **勿修改 DLL 注入機制** — NCGuard 會檢測任何異常的代碼修改
- **勿嘗試使用 hooks 或 debug registers** — 已導致帳號被鎖定

如意外洩露帳號密碼或 API Key，立即：
1. 改變遊戲帳號密碼
2. 在 console.anthropic.com 撤銷 API Key 並建立新的

