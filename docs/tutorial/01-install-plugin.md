# 01 — Lollipop Plugin 安裝及連線設定

> 最後更新: 2026-04-06

Lollipop Plugin 不是透過 `claude plugin add` 安裝，而是在 Claude Code 設定檔中直接配置。Plugin 會自動建立 Python 虛擬環境、安裝依賴，並啟動 MCP server。

---

## 你需要準備

- **Claude Code** 已安裝
- **Python 3.8+** （系統內建或 `brew install python@3.12`）
- **Windows 遊戲機 IP**（遊戲執行的那台機器，例如 `192.168.0.114`）
  - 查詢方式: Windows 開啟 PowerShell，執行 `ipconfig`，找 `IPv4 Address`
- **防火牆允許** TCP 埠 5577-5599 及 8600（見本文檔末尾）

---

## Step 1: 取得 Plugin 檔案

### 方式 A: Git Clone（推薦）

如果你已經有 Lollipop 專案的 git access:

```bash
cd ~/Projects
git clone https://github.com/m1105/lollipop.git
```

Plugin 檔案位於 `Lollipop/mcp/dist/`

### 方式 B: 下載 ZIP

從 GitHub releases 下載 `lollipop-mcp.zip`，解壓到任意資料夾。

---

## Step 2: 在 Claude Code 建立連線設定

在你的 Claude Code **工作目錄根**（或 `~/.claude/` 全域）建立 `.mcp.json` 檔案。

### 單機模式（推薦開始用）

如果你只有一台 Windows 機器執行遊戲：

```json
{
  "mcpServers": {
    "lollipop": {
      "command": "python3",
      "args": ["/path/to/Lollipop/mcp/dist/run.py"],
      "env": {
        "LOLLIPOP_DIRECT": "192.168.0.114"
      }
    }
  }
}
```

**請改成你的 IP 位址**。例如若你的遊戲機 IP 是 `192.168.1.50`，改為:

```json
"LOLLIPOP_DIRECT": "192.168.1.50"
```

### 多機模式（Tailscale VPN）

如果你有多台 Windows 機器，或遊戲機不在同一網路：

```json
{
  "mcpServers": {
    "lollipop": {
      "command": "python3",
      "args": ["/path/to/Lollipop/mcp/dist/run.py"],
      "env": {
        "LOLLIPOP_SERVER_URL": "https://your-server.com",
        "LOLLIPOP_CARD_ID": "your-card-id",
        "LOLLIPOP_TAILSCALE_KEY": "tskey-..."
      }
    }
  }
}
```

需要由系統管理員提供 `SERVER_URL`、`CARD_ID` 及 `TAILSCALE_KEY`。

### macOS 完整範例

如果你用 macOS，完整的 `.mcp.json` 看起來像這樣:

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

**重點**: 用 `/path/to/` 的**絕對路徑**，不要用相對路徑。

---

## Step 3: 啟動 Claude Code

1. 開啟 Claude Code
2. 開啟你的工作目錄（包含 `.mcp.json` 的那個）
3. Claude Code 會自動偵測到 `.mcp.json`
4. **首次啟動時**：
   - 自動建立 Python 虛擬環境 (`.venv/`)
   - 自動安裝相依套件:
     - `mcp[cli]>=1.26` — MCP server framework
     - `httpx>=0.27` — HTTP client（與 Windows DLL 通訊）
   - 啟動 MCP server

你會在 Claude Code 的終端看到類似的訊息:

```
[lollipop-mcp] Setting up Python venv...
[lollipop-mcp] Setup complete.
```

---

## Step 4: 驗證連線

在 Claude Code 的對話框輸入以下命令來驗證連線:

```
bot_list
```

### 成功的回應

你會看到所有線上的 bot 列表，例如:

```
[
  {
    "host": "192.168.0.114",
    "port": 5577,
    "char_name": "煎餅狗子",
    "email": "example@gmail.com",
    "hp": 450,
    "level": 42,
    "class": "妖精",
    "bot": true
  }
]
```

### 連線失敗

如果看到錯誤訊息如 `Connection refused` 或 `Timeout`:

1. **確認 IP 正確**: `ping 192.168.0.114`（改成你的 IP）
2. **檢查 Windows 防火牆**: 見本文檔末尾「防火牆設定」
3. **確認 DLL 執行中**: Windows 上 `Lollipop/build/` 內的 DLL 應該正在執行
4. **檢查 .mcp.json 路徑**: 確保路徑正確且不含空格

---

## 進階: 用 `/lollipop:setup` 自動設定

如果你不想手動編輯 `.mcp.json`，可以使用自動設定 skill:

```
/lollipop:setup
```

這個 skill 會提示你:

1. 選擇連線模式（單機或多機）
2. 輸入遊戲機 IP 或 Tailscale key
3. 自動建立 `.mcp.json`
4. 自動重啟連線

---

## 進階: Tailscale 多機台配置

### 什麼時候用 Tailscale?

- 你有多台 Windows 機器，遊戲分別執行在不同機器
- 遊戲機不在同一家網路（例如: 辦公室 + 家裡）
- 需要統一的 bot 管理後台（admin UI）

### 設定步驟

1. **取得 Tailscale key**
   - 向系統管理員要 `tskey-xxxx-yyyy` 開頭的 key
   
2. **更新 .mcp.json**

```json
{
  "mcpServers": {
    "lollipop": {
      "command": "python3",
      "args": ["/path/to/Lollipop/mcp/dist/run.py"],
      "env": {
        "LOLLIPOP_SERVER_URL": "https://your-server.com",
        "LOLLIPOP_CARD_ID": "prod-001",
        "LOLLIPOP_TAILSCALE_KEY": "tskey-client-xxxxxxxxxxxx"
      }
    }
  }
}
```

3. **重啟 Claude Code**

MCP server 會透過 Tailscale VPN 自動發現所有線上機器。

---

## 防火牆設定

Plugin 與 Windows DLL 透過 HTTP 通訊。Windows 防火牆需要開放以下埠:

### Windows Defender 防火牆設定

**在 Windows 上執行**（以系統管理員身份）:

```powershell
# 開放 DLL HTTP API (5577-5599)
netsh advfirewall firewall add rule name="Lollipop DLL API" dir=in action=allow protocol=tcp localport=5577-5599

# 開放 Opener (8600)
netsh advfirewall firewall add rule name="Lollipop Opener" dir=in action=allow protocol=tcp localport=8600
```

或在 GUI 中手動設定:

1. **開啟 Windows Defender 防火牆** → 「進階設定」
2. **新增輸入規則**:
   - 埠: `5577-5599` (DLL API)
   - 埠: `8600` (Opener)
   - 協定: TCP
   - 動作: 允許
   - 適用: 所有設定檔

### macOS/Linux（如果 DLL 執行在虛擬機）

如果 DLL 執行在 Parallels Desktop 或 Docker:

```bash
# 允許本機網路存取
sudo pfctl -f /etc/pf.conf
# 或設定 VirtualBox port forwarding:
# Host: 127.0.0.1:5577 → Guest: 192.168.x.x:5577
```

---

## 常見問題

### Q: Plugin 沒有載入，Claude Code 報錯 "lollipop" 不存在

**A**: 檢查 `.mcp.json`:

1. 檔案是否在工作目錄根（和 `package.json` 同層）
2. 或是否在 `~/.claude/` 全域（適用所有專案）
3. JSON 語法是否正確（用線上 JSON validator）
4. 路徑是否正確且無空格

```bash
# 驗證 JSON 語法
cat ~/.mcp.json | python3 -m json.tool
```

### Q: `bot_list` 傳回空陣列

**A**: 可能的原因:

1. **IP 錯誤**: 確認 `LOLLIPOP_DIRECT` 值是否正確
   ```bash
   # 在 Windows 上測試
   ping 192.168.0.114
   ```

2. **DLL 沒執行**: 確認 Windows 上的遊戲 bot DLL 正在執行

3. **防火牆擋住**: 檢查 Windows 防火牆規則（見上節）

4. **網路隔離**: 檢查兩台機器是否在同一網路或 VPN

### Q: `Connection refused` 或 `Timeout`

**A**:

1. 確認 IP 及埠正確
2. 測試 ping（確認網路連通）
3. 檢查防火牆日誌
4. 重啟 DLL 及 Claude Code

### Q: 首次啟動時安裝很慢

**A**: 正常。venv 和 pip 套件安裝需要 1-3 分鐘。之後啟動會快很多。

### Q: Python 版本不符

**A**: 如果系統 Python 版本 < 3.8:

```bash
# macOS
brew install python@3.12

# 更新 .mcp.json 的 command
"command": "/usr/local/bin/python3.12"
```

### Q: 用 Tailscale 時連不上

**A**:

1. 確認 `LOLLIPOP_TAILSCALE_KEY` 正確（複製時勿含空白）
2. 確認 `LOLLIPOP_SERVER_URL` 可訪問（試試瀏覽器開啟）
3. 確認 Tailscale client 已連接（Windows 系統列有 Tailscale icon）
4. 檢查 server log：`~/.claude/logs/lollipop.log`

---

## 下一步

連線驗證成功後:

1. **學習操作規範**: 閱讀 `/Lollipop/mcp/dist/CLAUDE.md`（自動載入到 Claude Code）
2. **試試基本命令**: 
   ```
   bot_status
   bot_position
   bot_inventory
   ```
3. **閱讀進階教程**: 
   - `01.5-deploy-environment.md` — Windows 環境部署
   - `02-basic-operations.md` — 基本操作（走路、攻擊、互動）
   - `03-automation-skills.md` — 自動化 Skill 建立

---

## 技術細節（選讀）

### Plugin 結構

```
Lollipop/mcp/dist/
├── run.py              # 跨平台啟動器（自動檢測 venv）
├── setup.py            # 虛擬環境初始化
├── requirements.txt    # Python 依賴
├── mcp_hub.py          # MCP server（91 個 tools）
├── CLAUDE.md           # 操作規範（自動載入）
├── README.md           # 簡要說明
└── skills/             # 操作 skills（14 個）
    ├── combat-setup/
    ├── teleport/
    ├── warehouse/
    └── ...
```

### 啟動流程

1. Claude Code 偵測 `.mcp.json` 中的 `lollipop` server
2. 執行 `python3 run.py`
3. `run.py` 檢查 `.venv/` 是否存在
4. 若不存在，執行 `setup.py` 建立 venv + 安裝依賴
5. 用 venv 內的 python 執行 `mcp_hub.py`
6. `mcp_hub.py` 啟動 stdio MCP server
7. Claude Code 自動連接並載入 91 個 tools

### 環境變數

| 變數 | 說明 | 範例 |
|------|------|------|
| `LOLLIPOP_DIRECT` | 單機直連 IP（推薦） | `192.168.0.114` |
| `LOLLIPOP_TAILSCALE_KEY` | Tailscale VPN key | `tskey-client-xxx` |
| `LOLLIPOP_SERVER_URL` | 多機 server URL | `https://server.com` |
| `LOLLIPOP_CARD_ID` | 機器卡號 | `prod-001` |

---

## 獲得幫助

- **檢查 Claude Code 終端**: 看是否有錯誤訊息
- **查看 MCP log**: `~/.claude/logs/lollipop.log`（若存在）
- **測試 HTTP API 直接**: 用 `curl` 或 Postman 測試 Windows DLL
  ```bash
  curl http://192.168.0.114:5577/ping
  ```
- **聯絡技術支援**: 提供 Claude Code 終端完整輸出及 IP 地址

---

**恭喜!** 你已經完成 Lollipop Plugin 的安裝及連線設定。接下來可以閱讀更多教程學習如何操作 bot。
