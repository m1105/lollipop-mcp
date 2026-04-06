# 04 — 多機台與進階功能

> 最後更新: 2026-04-06

掌握工作室多機台協調、排班自動化、績效分析和 A/B 測試，讓你的 bot 艦隊高效運轉。

---

## 你需要準備

- 已熟悉 [03 — 日常操作](03-daily-ops.md)
- 有多台 Windows 遊戲機（或同台機器上多個帳號）
- 穩定的網路連線（同一 LAN 或 Tailscale VPN）

---

## 1. 多機台設定與探索

### 為什麼需要多機台

工作室通常有多台 Windows 機器同時執行遊戲。Lollipop 提供統一的 MCP Hub，讓你用一個 Claude Code 視窗管理所有機器上的 bot。

### 設定環境變數

在 `.mcp.json` 中選擇一種連線模式：

**單機模式**（本地網路，推薦新手）：
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

**多機 Tailscale 模式**（跨地點、跨網路）：
```json
{
  "mcpServers": {
    "lollipop": {
      "command": "python3",
      "args": ["/path/to/Lollipop/mcp/dist/run.py"],
      "env": {
        "LOLLIPOP_TAILSCALE_KEY": "tskey-...",
        "LOLLIPOP_CARD_ID": "card-id-1,card-id-2"
      }
    }
  }
}
```

### 探索所有在線機台和 Bot

執行指令：
```bash
bot_list
```

預期輸出（例）：
```
[
  {
    "host": "192.168.0.114",
    "port": 5577,
    "char_name": "Knight_A",
    "level": 76,
    "class": "騎士",
    "map": "說話之島",
    "hp": 420,
    "mp": 180
  },
  {
    "host": "192.168.0.115",
    "port": 5577,
    "char_name": "Fairy_B",
    "level": 65,
    "class": "妖精",
    "map": "古魯丁地監",
    "hp": 220,
    "mp": 380
  }
]
```

這個列表會自動記錄在記憶體中。後續操作可用 `char_name` 或 `host:port` 指定目標。

---

## 2. Fleet 指令 — 快速總覽與診斷

### fleet_status — 所有 bot 當前狀態

查看艦隊的即時快照：
```bash
fleet_status
```

輸出包括：名字、等級、HP、MP、地圖、bot 執行狀態。適合定期檢查整體健康狀況。

### fleet_health_check — 找出問題 bot

自動掃描所有 bot，檢查：
- HP/MP 是否低於閾值
- 背包是否滿
- 是否有殘留 dialog
- 是否卡住（沒有移動）

```bash
fleet_health_check
```

輸出清單列出問題 bot，例：
```
Knight_A: HP 低於 30%
Fairy_B: 背包 96% 滿
Mage_C: 無運動信號（卡住）
```

**Tip**：每 10 分鐘自動執行一次（見本文末 Cron 自動化）。

### fleet_run_filtered — 對特定 bot 批次操作

只對符合條件的 bot 執行指令。例：

**停止所有在「說話之島地監」的 bot**：
```bash
fleet_run_filtered \
  --filter_field "map" \
  --filter_op "eq" \
  --filter_value "說話之島地監" \
  --name "bot_stop"
```

**啟動所有 HP 低於 50% 的 bot 進行補給**：
```bash
fleet_run_filtered \
  --filter_field "hp_pct" \
  --filter_op "lt" \
  --filter_value "50" \
  --name "bot_supply_trigger"
```

可用條件：
- `arrows` — 箭矢數（小於 = 補給）
- `level` — 等級
- `hp_pct` — HP 百分比
- `bot` — 執行狀態（running/stopped）

---

## 3. 排班系統 — 自動輪替管理

### 概念：輪班 vs 固定掛機

**固定掛機**：24 小時同一位置，容易被偵測
**輪班**：根據時間表自動切換角色、地點、配置，降低風險

### 排班流程

1. **檢視已存排班模板**

```bash
schedule_templates
```

輸出包括：模板名稱、工時、休息時間。

2. **選擇或建立模板**

預設模板 `default_shift`：
```
08:00-16:00: 角色A 說話之島
16:00-00:00: 角色B 古魯丁地監
00:00-08:00: 角色C 奇岩地監
```

3. **產生排班日程**

為 7 天產生排班表：
```bash
schedule_generate \
  --template_name "default_shift" \
  --from_date "2026-04-06" \
  --to_date "2026-04-12"
```

4. **啟用排班**

```bash
schedule_toggle --enabled 1
```

5. **檢查目前狀態**

```bash
schedule_status
```

輸出：
```
排班啟用: 是
目前執行中:
  - 時段1 (08:00-16:00): Knight_A 執行中
  - 時段2 (16:00-00:00): 等待啟動 (01:30 後)
  - 時段3 (00:00-08:00): 待機

下一步驟: 16:00 自動停止 Knight_A，啟動 Fairy_B
```

### 自訂排班模板

建立 JSON 模板：
```json
{
  "name": "aggressive_3shift",
  "description": "3 班制高效率",
  "slots": [
    {
      "slot_id": 1,
      "name": "早班",
      "time_start": "06:00",
      "time_end": "14:00",
      "account_id": "acc-001",
      "profile": "fast_grind"
    },
    {
      "slot_id": 2,
      "name": "中班",
      "time_start": "14:00",
      "time_end": "22:00",
      "account_id": "acc-002",
      "profile": "balanced"
    },
    {
      "slot_id": 3,
      "name": "晚班",
      "time_start": "22:00",
      "time_end": "06:00",
      "account_id": "acc-003",
      "profile": "safe_passive"
    }
  ]
}
```

儲存：
```bash
schedule_save_template \
  --template_json '{"name":"aggressive_3shift",...}'
```

---

## 4. 績效分析 — 誰賺最多，誰有風險

### fleet_performance — 金幣排行

過去 7 天，每個 bot 的金幣時薪排名：
```bash
fleet_performance --days 7
```

輸出（例）：
```
按地點分組，平均 gold/hr = 12500

說話之島地監 (avg 13200):
  1. Knight_A      15800 gold/hr  (優秀)
  2. Fairy_B       12600 gold/hr
  3. Mage_C        11200 gold/hr

古魯丁地監 (avg 11800):
  1. Warrior_D     13200 gold/hr
  2. Rogue_E        8400 gold/hr  (低於 70%，需檢查)

奇岩地監 (avg 10200):
  1. Paladin_F      9800 gold/hr
  ...
```

**注意**：低於某地點平均 70% 的 bot 會標記為「需檢查」。可能原因：
- 配置不合適
- 網路延遲
- 物品掉落不佳的時段
- bot 有 bug

### fleet_risk_scores — 誰可能被 Ban

計算 7 天風險評分（0-100，越高越危險）：
```bash
fleet_risk_scores
```

輸出（例）：
```
Knight_A:      15  綠色 (安全)
Fairy_B:       32  黃色 (警告 - 連續 45 小時掛機)
Mage_C:        68  紅色 (高危 - 死亡率 12%，同地點 3 角色)
Warrior_D:     22  黃色 (死亡集群 - 2 小時內死 4 次)
```

風險因子：
- **連續掛機時間** — 超過 22 小時紅旗
- **死亡率** — 同時段死亡次數異常高
- **位置重複** — 多角色在同地點導致模式可預測
- **排班模式** — 完全相同的排班時間表

**應對**：
- `Fairy_B` 改排班時間或地點
- `Mage_C` 立即停止，改用其他角色
- `Warrior_D` 增加死後等待時間

---

## 5. 地點分配最佳化 — Nash 均衡

### 概念：避免同地點過擠

在同一地點掛機的 bot 過多會：
- 搶怪，效率下降
- 行為模式相同，被偵測風險上升
- 加重伺服器負荷

**Nash 均衡**：理論上最優的 bot 分配，使得所有位置的金幣時薪相等。

### 地點均衡建議

查詢地點清單和基礎掉落：
```bash
location_equilibrium \
  --locations_json '{
    "說話之島地監": {"base_gold_hr": 13000, "crowding_factor": 0.85},
    "古魯丁地監":   {"base_gold_hr": 11800, "crowding_factor": 0.90},
    "奇岩地監":     {"base_gold_hr": 10200, "crowding_factor": 0.88}
  }' \
  --total_bots 0
```

`total_bots=0` 自動從 `bot_list` 計算。

輸出（例）：
```
目前分配 (不均衡):
  說話之島地監: 4 個 bot,  12800 gold/hr (8% 過擠)
  古魯丁地監:  2 個 bot,  10800 gold/hr (會賠)
  奇岩地監:    1 個 bot,   9600 gold/hr (嚴重虧損)

推薦分配 (Nash 均衡):
  說話之島地監: 3 個 bot,  11050 gold/hr
  古魯丁地監:  2 個 bot,  10620 gold/hr
  奇岩地監:    2 個 bot,  10200 gold/hr

行動:
  移動 1 個 bot 從說話之島地監 → 奇岩地監
```

**實施**：
```bash
# 停止 Fairy_B（說話之島）
bot_stop --char_name Fairy_B

# 傳送到奇岩地監
bot_teleport_scroll --char_name Fairy_B --dest "奇岩村|傳送師"

# 設定新的掛機點
bot_setup_combat \
  --char_name Fairy_B \
  --center_x 33100 \
  --center_y 33050 \
  --radius 30
```

---

## 6. A/B 測試 — 用數據決定配置

### 概念：比較兩個配置的效果

你想知道：「快速攻擊配置 vs 穩定掉落配置，哪個 gold/hr 更高？」

A/B 測試流程：
1. 建立 2 組 bot，配置不同
2. 各執行 2 小時
3. 收集數據
4. 統計分析（Welch's t-test）

### 執行 A/B 測試

**第 1 步**：檢查 2 個 bot 的差異

```bash
bot_compare \
  --bot_a_host 192.168.0.114 \
  --bot_a_port 5577 \
  --bot_b_host 192.168.0.114 \
  --bot_b_port 5578
```

輸出：
```
比較: Knight_A (5577) vs Knight_B (5578)

配置差異:
  combat_radius: 25 vs 30
  attack_speed:  normal vs 快速
  roam_mode:     raycast vs spiral
  其他配置:      相同

效能差異 (過去 2 小時):
  Knight_A: 平均 13200 gold/hr, 89 kills
  Knight_B: 平均 12800 gold/hr, 76 kills
```

**第 2 步**：微調配置並監控

假設你想測試 `attack_speed` 的影響：

bot_A（控制組）保持現狀，bot_B（實驗組）改快速：
```bash
bot_config_set \
  --host 192.168.0.114 \
  --port 5578 \
  --fields '{"attack_speed_boost": 1.2}'
```

讓兩個 bot 各跑 2 小時（真實遊戲時間）。

**第 3 步**：採集數據

透過 `opener_snapshots` 得到 5 分鐘快照。本文件末尾 Cron 自動化 會定期記錄。

或手動查詢（例，查過去 2 小時）：
```bash
opener_snapshots \
  --host 192.168.0.114 \
  --port 5577 \
  --limit 30 \
  --since 1712345678
```

**第 4 步**：統計分析

假設你已收集兩組 gold/hr 樣本：
```bash
experiment_evaluate \
  --control_values '[13200, 13100, 13300, 13250, 13180, 12900, 13400, 13150]' \
  --treatment_values '[14100, 14200, 13950, 14000, 14150, 13800, 14050, 14100]'
```

輸出（Welch's t-test）：
```
控制組 (原始配置):     平均 13181 gold/hr, 標準差 134
實驗組 (快速攻擊):     平均 14019 gold/hr, 標準差 145

差異: 838 gold/hr (6.4%)
信心度: 99.2% (p-value = 0.002)

結論: 快速攻擊配置 **顯著更好**，建議全體採用。
```

**信心度解讀**：
- p < 0.05（信心度 > 95%）：差異有統計意義，改採新配置
- p >= 0.05：無顯著差異，維持現狀

### 完整 A/B 測試流程對話例

```
User: 我想測試「寬攻擊範圍」和「精準攻擊」哪個金幣更多。

Claude:
1. 我會拿 Knight_A 和 Knight_B 比較
2. Knight_A 保持現狀 (radius=25)
3. Knight_B 改寬攻擊 (radius=35)
4. 各跑 2 小時

準備好了嗎？

User: 開始

Claude:
[設定 Knight_B 攻擊範圍 35]
bot_config_set --port 5578 --fields '{"combat_radius": 35}'

Knight_B 配置已更新，開始 2 小時計時...
(使用者不用等，Claude 會自動在 2 小時後統計)

User: 已經 2 小時，check 結果

Claude:
實驗完成！統計結果：
- Knight_A (radius=25): 13200 gold/hr
- Knight_B (radius=35): 13800 gold/hr
- 差異: +4.5%, 信心度 87%

結論: 寬攻擊範圍微幅更好，但差異不明顯。
      可試試中間值 (radius=30) 再測一次。
```

---

## 7. 巡邏路線最佳化

### 概念：從擊殺熱力圖優化路線

bot 的巡邏效率 = 怪物遇到率 × 攻擊速度。

**熱力圖分析**：過去 24 小時，在地圖哪些位置擊殺最多怪？
→ 產生最優巡邏路線（TSP 近似）

### 查詢擊殺熱力圖

```bash
kill_heatmap \
  --host 192.168.0.114 \
  --port 5577 \
  --map_id 0 \
  --hours 24
```

輸出（ASCII 熱力圖）：
```
說話之島地監 (過去 24 小時)

   32480        32520        32560
32860 ░░░░░░░░░░ 65 kill
      ░░░░░░░░░░
32840 ░░░██████░ 128 kill ← 熱點
      ░░░██████░
32820 ░░░██████░ 145 kill ← 最熱點
      ░░░██░░░░░
32800 ░░░░░░░░░░ 38 kill
```

黑點 (░) = 低活動，紅點 (█) = 高活動。

### 生成最優路線

```bash
patrol_route \
  --host 192.168.0.114 \
  --port 5577 \
  --map_id 0 \
  --algorithm "tsp_greedy" \
  --start_x 32500 \
  --start_y 32840
```

輸出：
```
推薦巡邏路線 (TSP 貪心):
點 1: (32500, 32840)   ← 起點
點 2: (32520, 32820)   [高密度] 距離 25
點 3: (32540, 32840)   [高密度] 距離 20
點 4: (32560, 32830)   [中密度] 距離 30
點 5: (32480, 32860)   [低密度] 距離 85
...
點 N: (32500, 32840)   ← 回起點 (迴圈)

總距離: 1,250 world units (~3.1 分鐘掠過一圈)
預估 24hr 金幣: 15,200 gold/hr (+15% 較固定範圍)
```

### 上傳為導航腳本

把路線轉換成 nav_script，上傳到 bot：

```bash
bot_nav_upload \
  --name "optimal_talk_dungeon_24h" \
  --waypoints '[
    {"x": 32500, "y": 32840, "action": "roam"},
    {"x": 32520, "y": 32820, "action": "fight"},
    {"x": 32540, "y": 32840, "action": "fight"},
    {"x": 32560, "y": 32830, "action": "roam"},
    {"x": 32480, "y": 32860, "action": "roam"}
  ]'
```

執行路線：
```bash
bot_nav_exec --script_id "optimal_talk_dungeon_24h"
```

**Tip**：每週重新分析熱力圖和優化路線。季節更新、新副本開放時熱力圖會變。

---

## 8. Cron 自動化 — 定時監控與維護

### 為什麼需要 Cron

你不能每小時手動執行 `fleet_health_check`。Cron 會在背景定時執行，有問題時通知你。

### 常見 Cron 排程

**生成推薦的 Cron 指令**：
```bash
workshop_setup_crons
```

輸出（複製貼上執行）：
```bash
# 每 10 分鐘檢查艦隊健康
schedule add --name "fleet_health_10m" \
  --interval "*/10 * * * *" \
  --command "fleet_health_check"

# 每 30 分鐘補給檢查
schedule add --name "supply_check_30m" \
  --interval "*/30 * * * *" \
  --command "fleet_supply_check"

# 每天 08:00 晨報
schedule add --name "morning_report_8am" \
  --interval "0 8 * * *" \
  --command "workshop_morning_report"

# 每週一 18:00 績效排行
schedule add --name "weekly_perf_mon_6pm" \
  --interval "0 18 * * 1" \
  --command "fleet_performance --days 7"

# 每天 23:00 風險評估
schedule add --name "risk_score_11pm" \
  --interval "0 23 * * *" \
  --command "fleet_risk_scores"
```

### 手動設定排程

假設你想每 5 分鐘檢查一次最關鍵的 bot：

```bash
# Cron 語法: min hour day month weekday
# 每 5 分鐘: */5 * * * *
schedule add \
  --name "critical_bot_check" \
  --interval "*/5 * * * *" \
  --command "fleet_run_filtered --filter_field 'bot' --filter_op 'eq' --filter_value 'Knight_A' --name 'bot_status'"
```

### 實時通知整合

設定 Discord 或 Telegram 通知（如果有風險）：

```bash
# 設定 Telegram Bot（由系統管理員提供）
schedule settings \
  --notification_channel "telegram" \
  --notification_token "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11" \
  --alert_level "HIGH"
```

當偵測到：
- 某 bot HP < 20%
- 誰超過 22 小時連續掛機
- 死亡率異常高

會自動發 Telegram 通知：
```
[LOLLIPOP ALERT] 高危
Knight_A HP 15% @ 說話之島地監
建議立即補血或檢查狀態
```

---

## 對話範例：完整艦隊管理流程

### 情景：啟動艦隊，監控一整天

**早上 8:00**：
```
User: 我要啟動艦隊，查看所有機台狀態，然後套用「3班制」排班。

Claude:
步驟 1: 列表所有 bot
[執行 bot_list]
發現 6 個 bot 在線：Knight_A, Fairy_B, Mage_C, Warrior_D, Rogue_E, Paladin_F

步驟 2: 檢查健康狀況
[執行 fleet_health_check]
全部健康 ✓

步驟 3: 生成排班
[執行 schedule_generate --template_name "aggressive_3shift" --from_date "2026-04-06" --to_date "2026-04-12"]
排班已生成，已啟用。

目前時段：
- Knight_A, Fairy_B (早班 06:00-14:00)
- Mage_C, Warrior_D (中班 14:00-22:00)
- Rogue_E, Paladin_F (晚班 22:00-06:00)

早班已啟動，接下來自動輪替。
```

**中午 12:00**：
```
User: 查績效排行。

Claude:
[執行 fleet_performance --days 1]
過去 24 小時:
說話之島地監 (平均 13200):
  Knight_A:      14500 ★ (優秀)
  Fairy_B:       11900
古魯丁地監 (平均 11800):
  Warrior_D:     12200
  Mage_C:        11400
奇岩地監 (平均 10200):
  Rogue_E:        9800
  Paladin_F:     10600

建議: Rogue_E 在奇岩效率不佳，可考慮轉移到古魯丁。
```

**下午 14:00**：
```
User: 執行排班切換（從早班轉中班）。

Claude:
[自動檢查排班]
時間已達 14:00，執行排班變更：

停止早班: Knight_A, Fairy_B
[bot_stop Knight_A, bot_stop Fairy_B]

等待 3 秒...

啟動中班: Mage_C, Warrior_D
[bot_start Mage_C, bot_start Warrior_D]

驗證:
  Mage_C:   已啟動 @ 古魯丁地監
  Warrior_D: 已啟動 @ 古魯丁地監

排班變更完成 ✓
```

**晚上 18:00**：
```
User: 檢查風險評分，有沒有要被 Ban 的跡象？

Claude:
[執行 fleet_risk_scores]
風險評分:
  Knight_A:      12 綠色 ✓
  Fairy_B:       28 黃色 ⚠ (連續 38 小時，建議休息)
  Mage_C:        18 綠色 ✓
  Warrior_D:     35 黃色 ⚠ (今天死 3 次，間隔近)
  Rogue_E:       45 紅色 ⚠⚠ (高密度位置，與 Paladin_F 同地)
  Paladin_F:     42 紅色 ⚠⚠ (同上)

建議行動:
1. Fairy_B 立即停止，休息 12 小時
2. Warrior_D 改變排班時間或位置
3. Rogue_E, Paladin_F 改為不同地圖
```

**晚上 20:00**：
```
User: 執行我的建議。

Claude:
步驟 1: 停止 Fairy_B 休息
[bot_stop --char_name Fairy_B]

步驟 2: 移動 Warrior_D 到奇岩
[bot_teleport_scroll --char_name Warrior_D --dest "奇岩村|傳送師"]
[bot_setup_combat --char_name Warrior_D --center_x 33100 --center_y 33050 --radius 30]

步驟 3: 移動 Rogue_E 到說話之島
[bot_teleport_scroll --char_name Rogue_E --dest "說話之島|雜貨商人"]
[bot_setup_combat --char_name Rogue_E --center_x 32500 --center_y 32850 --radius 25]

步驟 4: Paladin_F 保留古魯丁（改時段）
[修改排班]

全體調整完成 ✓
預計風險評分明天下降。
```

**晚上 22:00**：
```
User: Cron 跑了今天的晨報，看結果。

Claude:
[workshop_morning_report 已執行]

早報 (2026-04-06):
═══════════════════════════
艦隊狀態: 6 個 bot，5 執行中，1 休息

位置分布:
  說話之島地監: Rogue_E (1.5h)
  古魯丁地監:  Mage_C, Warrior_D (8.5h)
  奇岩地監:    Paladin_F (6.0h)

排班: 3 班制，無異常

績效 (昨日):
  平均 12,100 gold/hr
  總獲利: 145,200 gold

風險: 3 個黃色 (已調整)

下一步驟: 晚班 22:00 啟動 Rogue_E, Paladin_F
```

---

## 常見問題

### Q1: 多機台之間的延遲會怎樣？

Lollipop MCP 使用 HTTP 長連線，典型延遲 200-500ms（同 LAN）。影響不大。Tailscale VPN 則 100-300ms（取決於地理距離）。

### Q2: 排班切換時會卡住嗎？

不會。排班系統會在目標時間前 10 秒準備，自動停止當前 bot，等 3 秒確保狀態穩定，再啟動下一個。期間可能有 20-30 秒的「空檔」，這是正常的。

### Q3: A/B 測試最少要跑多久？

至少 2 小時真實遊戲時間，採樣 24+ 次。6-8 小時最理想（得到 96+ 樣本，信心度 > 99%）。

### Q4: 風險評分 > 50 是什麼意思？

紅色級別，有高風險被偵測到不正常行為。常見原因：
- 連續掛機 > 20 小時
- 死亡集群（短時間內死多次）
- 多角色同地點掛機

建議立即調整（改地點、改排班、休息）或降級為被動 bot。

### Q5: 怎麼確認排班自動化有沒有跑起來？

檢查排班狀態：
```bash
schedule_status
```

輸出會顯示「已啟用」和「下一步驟」時間。或檢查 log：
```bash
opener_logs --host <machine_ip>
```

看有沒有排班相關的執行記錄。

---

## 下一步

→ [05 — 常見問題排除](05-troubleshooting.md)
