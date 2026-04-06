# 00 — Windows 環境安裝

> Last updated: 2026-04-06

Windows 從零開始安裝 Python、Node.js 和 Claude Code，為 Lollipop 開發做準備。

---

## 你需要準備

- **Windows 10 或 11**（64 位元）
- **管理員權限**（安裝軟體時需要）
- **穩定的網路連線**
- **Anthropic API Key**（到 [console.anthropic.com](https://console.anthropic.com) 申請免費額度）

---

## Step 1: 安裝 Python 3.11+

### 下載 Python

1. 開啟瀏覽器，前往 [python.org/downloads](https://www.python.org/downloads/)
2. 點擊大按鈕下載最新 Python 版本（3.11 或更新）
3. 選擇 **Windows installer (64-bit)**

### 執行安裝程式

1. 找到下載的 `python-3.xx.exe` 檔案，雙擊執行
2. **重要**：勾選下方兩個選項
   - `Install launcher for all users`
   - `Add Python 3.xx to PATH` ← **務必勾選**
3. 點擊 `Install Now`
4. 等待安裝完成（約 1-2 分鐘）

### 驗證安裝

開啟 **PowerShell**（按 `Win + R`，輸入 `powershell`，按 Enter）：

```powershell
python --version
```

預期輸出：
```
Python 3.11.x
```
或更新版本。如果看到此訊息，表示安裝成功。

如果出現 `python: The term 'python' is not recognized...`，請重新執行安裝程式，務必勾選 "Add Python to PATH"，然後重新開啟 PowerShell。

### 驗證 pip（Python 套件管理器）

```powershell
pip --version
```

預期輸出：
```
pip 24.x.x from C:\Users\<你的帳戶>\AppData\Local\Programs\Python\Python311\lib\site-packages\pip (python 3.11)
```

---

## Step 2: 安裝 Node.js 18+

### 下載 Node.js

1. 開啟瀏覽器，前往 [nodejs.org](https://nodejs.org/)
2. 下載 **LTS（長期支援）** 版本（18.x 或更新）
3. 選擇 **Windows Installer (.msi) 64-bit**

### 執行安裝程式

1. 找到下載的 `.msi` 檔案，雙擊執行
2. 按照提示完成安裝
   - 接受授權條款
   - 選擇安裝位置（預設即可）
   - 勾選 `Automatically install necessary tools`（可選但建議）
3. 點擊 `Install`
4. 等待完成（約 2-3 分鐘）

### 驗證安裝

重新開啟 **PowerShell**（或在現有 PowerShell 中關閉並重新打開）：

```powershell
node --version
```

預期輸出：
```
v18.x.x
```
或更新版本。

驗證 npm（Node 套件管理器）：

```powershell
npm --version
```

預期輸出：
```
9.x.x
```
或更新版本。

---

## Step 3: 安裝 Claude Code

### 使用 npm 全域安裝

在 PowerShell 中執行：

```powershell
npm install -g @anthropic-ai/claude-code
```

等待安裝完成。你會看到類似輸出：
```
added XXX packages, and audited XXX packages in Xs
```

### 驗證安裝

```powershell
claude --version
```

預期輸出：
```
Claude Code vX.X.X
```

如果出現 `claude: The term 'claude' is not recognized...`，可能需要：
1. 重新開啟 PowerShell
2. 或以管理員身份執行 PowerShell 後重新安裝

---

## Step 4: 首次啟動 Claude Code

### 取得 Anthropic API Key

1. 前往 [console.anthropic.com](https://console.anthropic.com)
2. 註冊或登入帳戶
3. 在左側選單選擇 **API Keys**
4. 點擊 **Create Key**
5. 複製生成的金鑰（保管好，不要分享給他人）

### 啟動 Claude Code

在 PowerShell 中執行：

```powershell
claude
```

第一次執行時，Claude Code 會提示輸入 API Key：

```
🔑 Enter your Anthropic API Key:
```

貼上你複製的 API Key，按 Enter。

Claude Code 會驗證金鑰。如果成功，你會看到互動介面：

```
Claude Code v0.X.X ready
Type /help for available commands
>
```

輸入 `/help` 查看可用命令列表，確認安裝成功。

輸入 `exit` 或 `quit` 退出 Claude Code。

---

## Step 5: 驗證完整環境

在 PowerShell 中一次性驗證所有元件：

```powershell
echo "=== Python ===" ; python --version ; echo "=== Node.js ===" ; node --version ; echo "=== npm ===" ; npm --version ; echo "=== Claude Code ===" ; claude --version
```

預期輸出：
```
=== Python ===
Python 3.11.x
=== Node.js ===
vX.X.X
=== npm ===
X.X.X
=== Claude Code ===
Claude Code vX.X.X
```

如果全部顯示版本號，表示環境配置完成。

---

## 常見問題

### Q: "python" 不是內部或外部命令

**原因**：Python 未加入系統 PATH 環境變數。

**解決方案**：
1. 重新執行 Python 安裝程式
2. 選擇 `Modify`
3. 確認勾選 `Add Python to PATH`
4. 點擊 `Install`
5. 重新開啟 PowerShell

### Q: npm install 時出現權限錯誤

**原因**：需要管理員權限。

**解決方案**：
1. 以管理員身份開啟 PowerShell
   - 按 `Win + X`
   - 選擇 `Windows PowerShell (Admin)` 或 `Terminal (Admin)`
2. 再次執行 npm install 命令

### Q: Claude Code 啟動失敗或無法驗證 API Key

**原因**：
- API Key 無效或已過期
- 網路連線問題

**解決方案**：
1. 檢查網路連線
2. 重新檢查 API Key（務必複製完整）
3. 在 [console.anthropic.com](https://console.anthropic.com) 驗證 API Key 狀態
4. 如果 Key 無效，建立新的 Key 並重試

### Q: Node.js 安裝後 npm 仍無法使用

**原因**：PATH 環境變數未更新。

**解決方案**：
1. 重新開啟 PowerShell（全部關閉再開啟）
2. 或重新啟動 Windows

### Q: API Key 應該怎麼保管？

**最佳實踐**：
- **不要**把 API Key 放在 GitHub、Discord 或任何公開位置
- **不要**把 API Key 寫在程式碼註解中
- 使用 `.env` 檔案（加入 `.gitignore`）或環境變數存放
- 如果不小心洩露，立即在 console.anthropic.com 刪除該 Key 並建立新的

---

## 下一步

環境安裝完成後，你已準備好開始開發 Lollipop。

→ [01 — 安裝 Lollipop Plugin](01-install-plugin.md)

---

## 快速參考

| 工具 | 驗證命令 | 最低版本 |
|------|---------|---------|
| Python | `python --version` | 3.11+ |
| Node.js | `node --version` | 18+ |
| npm | `npm --version` | 9+ |
| Claude Code | `claude --version` | 最新 |

## 支援

如遇到問題：
1. 確認網路連線正常
2. 檢查防火牆或 VPN 是否阻擋安裝程式
3. 查閱上方「常見問題」區段
4. 在 GitHub Issues 或社群論壇提問
