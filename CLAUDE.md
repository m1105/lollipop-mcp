# Lollipop Bot MCP — 操作規範

> 此文件包含所有 MCP tool 操作所需的知識。Claude Code 開啟專案時自動載入。

---

## 新手教學 (Tutorial)

當用戶說「教學」「tutorial」「教我」「新手」「怎麼用」時，**必須讀取對應教學文件並照著做**：

1. **偵測環境**: 呼叫 `bot_list`
   - 成功 → 讀取 `Lollipop/docs/tutorial/03-daily-ops.md`，照裡面的 demo 帶用戶操作
   - 失敗 → 讀取 `Lollipop/docs/tutorial/00-windows-setup.md`，從頭引導安裝

2. **教學文件對照** (依用戶需求讀取對應文件):

| 用戶說... | 讀取並執行 |
|-----------|-----------|
| "教學" / "新手" / "怎麼用" | `03-daily-ops.md` (已連線) 或 `00-windows-setup.md` (未連線) |
| "怎麼安裝" / "安裝教學" | `00-windows-setup.md` → `01-install-plugin.md` → `01.5-deploy-environment.md` |
| "怎麼上線 bot" | `02-first-bot.md` |
| "日常操作" / "管理教學" | `03-daily-ops.md` |
| "多機台" / "排班" / "進階" | `04-fleet-management.md` |
| "出問題了" / "不會修" | `05-troubleshooting.md` |

3. **執行方式**: 用 Read tool 讀取文件內容，然後**逐步照文件裡的步驟帶用戶走**，包括實際呼叫 MCP tool 讓用戶看到真實結果。文件裡的對話 demo 就是範本，照著做。

---

## 角色名稱 → IP 對照

呼叫 `bot_list` 建立角色名 → host:port 對照表。用戶說角色名時自動對應。

---

## 強制規範（違反會 crash 或被封號）

### 1. 每次操作前必須檢查
- `bot_dialogs` — 確認沒有殘留 dialog
- `bot_entities` — 確認 NPC 在畫面
- 有殘留 dialog 要先關掉

### 2. 不可見不能點
- `/dialogs` 只回傳 visible 的
- 點不可見的 dialog 會被伺服器判定外掛

### 3. 只改被要求的
- 不要自己亂改周圍的代碼
- bug fix 要精確，不要重構

---

## MCP 使用規範

- **所有遊戲操作必須用 MCP tool**，不寫 Python 腳本
- 不要問「要繼續嗎」— 直接做
- 查背包 → `bot_inventory`
- 走路 → `bot_walk`
- 連續操作 → 連續呼叫 MCP tool

---

## NPC 互動規範

- **必須用 entity_id**（不用 entity_addr）— addr 會失效導致 crash
- `/bot/interact` 傳 `{"entity_id": NPC_ID}`
- 人太多時 NPC 可能不在 entity cache（已分離 NPC cache 解決）
- 已知 NPC id：朵琳=1269, 潘朵拉=1267, 爾瑪=1605

---

## 商店購買流程

1. interact NPC（用 entity_id）
2. 等 3 秒
3. `bot_click("NpcTalkLayout", "Bt_Npc_Buy")` — **不用文字搜尋「購買」**
4. 等 NpcShopLayout visible
5. `/shop/buy` 每樣 `confirm=0`（批次）
6. 全選完 → `/shop/confirm` 統一結帳

### qty 規則
- qty = **實際購買數量**（不用 -1）
- 商店預設數量是 0
- 箭例外：Count_Up 每次 +10
- 有 TextField 時用 GLFW char callback 直接輸入數字

### 高階 tool
- `bot_buy_from_npc(npc, items, scroll_dest)` — 一次買多樣，自動模糊匹配名稱
- 物品名稱可能跟遊戲不同（如「治療藥水」→ 遊戲叫「治癒藥水」），tool 自動匹配

---

## 倉庫存取流程

1. interact NPC
2. 點「存放物品」nth=1(個人) / nth=2(血盟)
3. 等 StorageLayout visible + 2.5 秒載入
4. `/wh/click_slot` 每個物品 `confirm=0`
5. 全選完 → `/wh/confirm`

### 物品類型
- **不可堆疊**：遍歷所有同名 slot 逐一選取
- **可堆疊**：點擊 TextField → GLFW char 輸入數量
- **已裝備**：名字含「穿戴」= 已裝備，StorageLayout 自動過濾
- qty=0 = 全部存入/取回

### 高階 tool
- `bot_warehouse_deposit(items, npc_name, wh_type)`
- `bot_warehouse_withdraw(items, npc_name, wh_type)`
- 支援 JSON array 多物品、自動模糊匹配

---

## 傳送系統

### 說話的卷軸（F12）
- `bot_teleport_scroll(dest="村莊|傳送點")`
- **不要用 `game_use_item()`** — 會觸發隨機傳送
- 正確流程：`/scroll_show` → `/scroll_dest`

### NPC 傳送師
- `bot_teleport_npc(dest="海音", scroll_dest="奇岩村|傳送師")`
- 流程：scroll 傳送 → interact 傳送師 → 「想去其他地區」→ 選目的地
- 已知傳送師：盧卡斯(說話之島), 史提夫(古魯丁), 爾瑪(奇岩)

### 祝福卷軸（F11）
- `bot_teleport_blessed(dest)`

---

## 數量輸入方式

- **GLFW char callback**：`game_glfw_char(codepoint)` 逐字輸入
- 點擊 TextField focus → 逐字發 char event
- `game_glfw_key` 不能輸入文字（只處理功能鍵）

---

## 艦隊操作

- `bot_list` — 查所有在線機器
- `bot_all_start` / `bot_all_stop` — 全部啟動/停止
- `fleet_teleport(dest)` — 全部傳送
- `bot_return_to_grind` — 回到掛機點
- 排除特定角色時，逐台操作其他角色

---

## 使用物品

- `bot_useitem(item_uid)` — 用 uid 使用
- 先 `bot_inventory` 查 uid
- 不可堆疊物品（如活力方塊）每個有獨立 uid，要逐一使用
- 可堆疊物品 uid 不變，重複呼叫即可

---

## 說話的卷軸目的地

格式: `"村莊|傳送點"`

### 通用
- 說話之島: 旅館, 倉庫管理員, 傳送師, 雜貨商人, 魔法書商人, 說話之島地監入口, 北島
- 古魯丁村: 旅館, 倉庫管理員, 傳送師, 雜貨商人, 古魯丁地監入口
- 奇岩村: 倉庫管理員, 傳送師, 雜貨商人, 武器商人, 防具商人, 藥水商人, 奇岩地監入口
- 共同: 正義神殿, 邪惡神殿, 沙漠綠洲, 祝福之地

### 村莊 NPC 對照
| 村莊 | 雜貨商人 | 傳送師 | 倉庫管理員 |
|------|---------|--------|----------|
| 說話之島 | 潘朵拉 | 盧卡斯(32580,32929) | 朵琳 |
| 古魯丁村 | 露西 | 史提夫(32611,32732) | — |
| 奇岩村 | 邁爾 | 爾瑪(33437,32798) | — |

---

## UI Popup 處理

### ServerSelect_MsgPopup（伺服器維護公告）
- `bot_click(dialog="ServerSelect_MsgPopup", widget="Bt_Ok")` 關閉
- 會擋住所有遊戲操作，需要自動偵測並關閉

### 已知 Layout + Button 組合
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

---

## 注意事項

- 操作間要等待：interact 後等 3 秒，StorageLayout 等 2.5 秒
- 不要連續快速操作同一個 NPC
- 操作完確認 UI 乾淨再做下一步
- 各模組流程不能混用（商店/倉庫/傳送各有各的按鈕和流程）

---

## Skill 系統

### 查看 / 執行 skill
```
# 列出所有 skill
skill_list()

# 查看 skill 詳細步驟
skill_get(name="goto-blessed-ats")

# 執行 skill（自動逐步呼叫 MCP tool）
skill_run(name="goto-blessed-ats", host="100.85.235.33", port=5577)
```

### 目前可用的 skill

| skill | 用途 | 參數 |
|-------|------|------|
| goto-blessed-ats | 前往祝福之地掛 ATS | $zone, $race |
| ats-watch-and-start | ATS 結束後自動啟動 bot | 無 |
| switch-profile | 切換設定檔並重啟 | $profile |

### skill 參數傳遞

skill 步驟中的 `$variable` 是參數佔位符，執行前需替換：
- `$zone` = `前往污染的祝福之地` 或 `前往墮落的祝福之地`
- `$race` = `妖精之地` | `人類之地` | `妖魔之地` | `精靈之地`
- `$profile` = 設定檔名稱（從 `bot_profile_list()` 查）

### skill 手動執行

如果 `skill_run` 失敗，可以照 `skill_get` 回傳的步驟**逐步手動執行**：
1. 每步呼叫對應的 MCP tool
2. 遵守 `delay_ms` 等待時間
3. 檢查 `wait_for` 條件（bot_dialogs 找指定 Layout）
4. 失敗時不要繼續，先處理錯誤

### skill 建立
```
skill_create(
  name="my-skill",
  description="skill 說明",
  steps='[{"tool":"bot_stop","comment":"停止"},{"tool":"bot_start","delay_ms":1000,"comment":"啟動"}]'
)
```

---

## ATS（自動訓練系統）

### ATS 流程
1. 用說話的卷軸傳送到「祝福之地」（共同|祝福之地）
2. 找 NPC **諾納梅**，互動
3. 選地區：「前往污染的祝福之地」或「前往墮落的祝福之地」
4. 選種族：「妖精之地」「人類之地」「妖魔之地」「精靈之地」
5. 按 **F8**（key=297）啟動 ATS
6. 確認 `ATSMsgHudLayout` 出現 = ATS 啟動成功

### ATS 時間讀取
- `bot_uitree()` → 找 `ATSMsgHudLayout` → `Root` → `Tx_Time` → `protectedChildren[0]` → `label_text`
- 例如顯示 `"2小時59分鐘"`
- addr 是動態的，每次要從 uitree 重新找

### ATS 結束偵測
- `bot_dialogs()` 沒有 `ATSMsgHudLayout` = ATS 結束
- 結束後執行 `bot_start()` 開始掛機

---

## 祝福之地 NPC 與座標

| NPC | 功能 | 備註 |
|-----|------|------|
| 諾納梅 | 選擇祝福之地區域 | entity_id 每次不同，從 bot_entities 取 |

### 祝福之地區域
| 地區 | 種族選項 |
|------|---------|
| 污染的祝福之地 | 妖精之地、人類之地、妖魔之地、精靈之地 |
| 墮落的祝福之地 | 妖精之地、人類之地、妖魔之地、精靈之地 |

---

## 操作時序要求

每步之間的**最低等待時間**（太快會操作失敗）：

| 操作 | 等待 |
|------|------|
| interact NPC 後 | 1500-3000ms |
| 點 NPC 對話選項後 | 2000ms |
| 傳送後確認位置 | 5000ms |
| F12/F8 按鍵後 | 1500-3000ms |
| bot_click 後 | 1000ms |
| shop_buy 前點 Bt_Npc_Buy 後 | 等 NpcShopLayout visible |
| StorageLayout 開啟後 | 2500ms（載入物品） |
| walk 每步間隔 | 800ms |

---

## 多機台操作

- 每台機器用 `host` + `port` 區分
- `bot_list()` 查所有在線機器
- 操作時**永遠帶 host 和 port 參數**
- 每台的狀態（ATS時間、profile、bot狀態）獨立追蹤，不可混用
- 角色名可從 bot_list 對應到 host:port

---

## 說話的卷軸注意

- **絕對不可用 bot_useitem 使用說話的卷軸** — 會觸發隨機傳送
- 正確流程：F12 開選單 → `/scroll_dest` POST 點目的地
- `bot_teleport_scroll(dest="村莊|傳送點")` 是封裝好的高階 tool
- 如果 `bot_teleport_scroll` 報錯「找不到卷軸」，改用手動流程：
  1. `bot_glfw_key(key=301)` — F12
  2. `bot_dialogs()` — 確認 TalkingScrollLayout
  3. `dll_http(POST, /scroll_dest, {"dest":"目的地"})` — 點擊

---

## 斷線與異常處理

### 伺服器斷線偵測
- DLL 監測 `ServerSelect_MsgPopup` 內容含「伺服器中斷」「與伺服器」「中斷連線」「斷線」
- 偵測到 → 通知 opener → kill LC.exe → opener 自動重啟

### bot 死亡
- `bot_status()` → hp=0 表示角色死亡
- 死亡後自動回村（如果有設定）或等待手動處理

---

## API 回傳值參考

### result 值含義

| result | 含義 | 說明 |
|--------|------|------|
| 2 | **成功** | 點擊/互動/操作成功執行 |
| 1 | **成功（部分）** | 操作執行但可能需確認結果 |
| 0 | **無效/未執行** | 按鍵無效、UI 不可見、目標不存在 |
| -17 | **找不到** | widget/keyword 在指定 dialog 中不存在 |
| 負數（大）| **記憶體位址** | npc_click 回傳點擊的 node 地址（非錯誤） |

### 常見 tool 回傳判斷

| tool | 成功 | 失敗 |
|------|------|------|
| bot_interact | result=2 | result=0 或 error |
| bot_click | result=2 | widget not found |
| bot_npc_click | result=1 或負數（地址）| result=-17（找不到） |
| bot_glfw_key | result=0（正常）| - |
| dll_http POST /scroll_dest | result=2 | error |
| bot_start / bot_stop | ok=1 | error |

### 狀態確認方式

| 要確認什麼 | 方法 |
|-----------|------|
| UI 選單是否開啟 | `bot_dialogs()` → 找 Layout 名稱 |
| 角色是否登入 | `bot_status()` → logged_in=1 |
| Bot 是否運行 | `bot_status()` → bot_running=1 |
| ATS 是否啟動 | `bot_dialogs()` → 有 ATSMsgHudLayout |
| 傳送是否完成 | `bot_position()` → 座標改變 |
| NPC 對話是否開啟 | `bot_dialogs()` → 有 NpcTalkLayout |

### GLFW 快捷鍵對照

| 鍵 | code | 用途 |
|----|------|------|
| ESC | 256 | 關閉 UI |
| F8 | 297 | ATS 開關 |
| F10 | 299 | 變身 |
| F11 | 300 | 祝福卷軸書籤 |
| F12 | 301 | 說話的卷軸 |

### dll_http 重要端點

| method | path | 用途 |
|--------|------|------|
| POST | /scroll_dest | 點擊卷軸目的地（{"dest":"祝福之地"}） |
| POST | /bot/interact | 互動 NPC（{"entity_id":1665}） |
| GET | /scroll_list | 列出卷軸目的地清單 |
| GET | /status | DLL 狀態 |
| GET | /uitree | UI 節點樹 |
