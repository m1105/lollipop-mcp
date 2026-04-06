---
name: workshop-supply
description: 艦隊補給管理 — 偵測缺貨 bot 並逐一補給
tools: [fleet_supply_check, bot_full_supply, bot_supply_trigger, fleet_supply_efficiency]
trigger: 補給|缺箭|supply|誰需要補
---

## 用途

檢查哪些 bot 需要補給（箭不夠、負重過高），然後逐一觸發補給，避免全部同時停機。

## 流程

1. 呼叫 `fleet_supply_check()` — 取得需要補給的 bot 清單
2. 如果 `need_supply` > 0：
   - **逐一補給**（不要同時全部補），避免工作室產值歸零
   - 對每隻需要補給的 bot：`bot_supply_trigger(port=X, host=Y)`
   - 等該 bot 補給完成（poll `bot_supply_state` 直到 state=IDLE）再處理下一隻
3. 如果全部 ok — 回報 "全員補給充足"
4. 可選：呼叫 `fleet_supply_efficiency()` 分析補給效率

## Rolling Supply 策略

```
1. 取得需補給清單 (fleet_supply_check)
2. 按急迫度排序 (arrows 最少的先補)
3. for each bot in sorted_list:
   a. bot_supply_trigger(port, host)
   b. 等待完成 (poll bot_supply_state, max 120s)
   c. 確認回到 IDLE
   d. 下一隻
```

## 注意事項

- 每次只補一隻，其他繼續打怪
- 補給過程中如果 bot 死了，supply 會中斷，需要先處理死亡
- `bot_full_supply` 是高階封裝（傳送→買→賣→回），`bot_supply_trigger` 是觸發 DLL 內建的供給流程
