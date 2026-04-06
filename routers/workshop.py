"""Workshop tools: high-level management for the entire bot workshop.

Composite tools that aggregate data from fleet, opener, schedule, and server
stats into actionable reports for the workshop manager.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timedelta


def register(mcp) -> None:
    from core import (
        _http, _opener_http, _refresh_machines, _scan_instances,
        SERVER_URL, CARD_ID, audit_log, discord_notify,
    )

    # ------------------------------------------------------------------
    #  Helper: query server stats API
    # ------------------------------------------------------------------
    async def _query_server_stats(
        date_from: str = "", date_to: str = "", limit: int = 500,
    ) -> list[dict]:
        """Query server bot_stats table. Returns list of stat rows."""
        if not SERVER_URL:
            return []
        import httpx
        params: dict = {"limit": str(limit)}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if CARD_ID:
            params["card_id"] = CARD_ID.split(",")[0].strip()
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Use server stats endpoint (requires admin or license token)
                # For now, try without auth (server may allow MCP calls)
                r = await client.get(
                    f"{SERVER_URL}/api/stats",
                    params=params,
                    headers={"Accept": "application/json"},
                )
                if r.status_code == 200:
                    return r.json().get("stats", [])
        except Exception:
            pass
        return []

    # ------------------------------------------------------------------
    #  Helper: compute hourly rates
    # ------------------------------------------------------------------
    def _calc_rates(stat: dict) -> dict:
        bot_ms = stat.get("total_bot_ms", 0)
        hours = bot_ms / 3_600_000 if bot_ms > 0 else 0
        if hours < 0.1:
            return {"kills_hr": 0, "gold_hr": 0, "deaths_hr": 0, "hours": 0}
        return {
            "kills_hr": round(stat.get("total_kills", 0) / hours, 1),
            "gold_hr": round(stat.get("total_gold_gain", 0) / hours, 0),
            "deaths_hr": round(stat.get("total_deaths", 0) / hours, 2),
            "hours": round(hours, 1),
        }

    # ------------------------------------------------------------------
    #  workshop_morning_report
    # ------------------------------------------------------------------

    @mcp.tool()
    async def workshop_morning_report() -> str:
        """早班報告 / Morning report: machines, bots, schedule, yesterday's earnings.

        Combines opener fleet status + bot fleet status + schedule overview +
        server stats from yesterday into a single report."""

        # Fan out all queries in parallel
        machines_task = _refresh_machines(force=True)
        instances_task = _scan_instances(force=True)

        machines = await machines_task
        instances = await instances_task

        # Opener status (parallel across machines)
        opener_tasks = []
        hosts = []
        for m in machines.values():
            ip = m.get("ip", "")
            if ip:
                hosts.append(ip)
                opener_tasks.append(_opener_http("GET", "/api/instances", host=ip))
        opener_results = await asyncio.gather(*opener_tasks, return_exceptions=True)

        # Schedule status (parallel)
        sched_tasks = [_opener_http("GET", "/api/schedule/status", host=h) for h in hosts]
        sched_results = await asyncio.gather(*sched_tasks, return_exceptions=True)

        # Bot health check (use existing fleet data)
        bot_problems = []
        for inst in instances:
            problems = []
            hp = inst.get("hp", -1)
            max_hp = inst.get("max_hp", 1)
            if hp >= 0 and max_hp > 0 and hp / max_hp < 0.3:
                problems.append(f"HP={hp}/{max_hp}")
            if inst.get("logged_in", 0) == 0 and inst.get("bot", 0) == 0:
                problems.append("offline")
            if problems:
                bot_problems.append({
                    "name": inst.get("char_name", "?"),
                    "host": inst.get("host", ""),
                    "port": inst.get("port", 0),
                    "problems": problems,
                })

        # Yesterday's stats from server
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        stats = await _query_server_stats(date_from=yesterday, date_to=yesterday)

        total_gold = sum(s.get("total_gold_gain", 0) for s in stats)
        total_kills = sum(s.get("total_kills", 0) for s in stats)
        total_deaths = sum(s.get("total_deaths", 0) for s in stats)
        total_hours = sum(s.get("total_bot_ms", 0) for s in stats) / 3_600_000

        # Per-bot summary
        bot_earnings = []
        for s in stats:
            rates = _calc_rates(s)
            if rates["hours"] > 0.5:
                bot_earnings.append({
                    "name": s.get("char_name", "?"),
                    "map": s.get("map_name", "?"),
                    "level": s.get("level", 0),
                    **rates,
                })
        bot_earnings.sort(key=lambda x: x["gold_hr"], reverse=True)

        # Machine summary
        machine_summary = []
        for ip, oresult, sresult in zip(hosts, opener_results, sched_results):
            entry = {"host": ip, "status": "online"}
            has_content = False
            if isinstance(oresult, Exception):
                entry["status"] = "offline"
            else:
                try:
                    data = json.loads(oresult).get("data", [])
                    if isinstance(data, list):
                        entry["instances"] = len(data)
                        entry["running"] = sum(1 for d in data if d.get("status") == "running")
                        if len(data) > 0:
                            has_content = True
                            # Add char names for running instances
                            entry["chars"] = [
                                d.get("char_name", "?") for d in data
                                if d.get("status") == "running" and d.get("char_name")
                            ]
                except Exception:
                    pass
            if not isinstance(sresult, Exception):
                try:
                    sdata = json.loads(sresult).get("data", {})
                    entry["schedule_enabled"] = sdata.get("enabled", False)
                    if sdata.get("enabled"):
                        has_content = True
                except Exception:
                    pass
            # Only include machines with accounts or schedule
            if has_content or entry["status"] == "offline":
                machine_summary.append(entry)

        report = {
            "report_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "machines": {
                "total": len(machine_summary),
                "online": sum(1 for m in machine_summary if m["status"] == "online"),
                "details": machine_summary,
            },
            "bots": {
                "online": len(instances),
                "problems": bot_problems,
            },
            "yesterday": {
                "date": yesterday,
                "total_gold": total_gold,
                "total_kills": total_kills,
                "total_deaths": total_deaths,
                "total_hours": round(total_hours, 1),
                "gold_per_hour": round(total_gold / max(total_hours, 0.1), 0),
                "per_bot": bot_earnings[:20],
            },
        }

        audit_log("workshop_morning_report", {},
                  f"machines={len(machine_summary)} bots={len(instances)} problems={len(bot_problems)}")

        if bot_problems:
            names = ", ".join(p["name"] for p in bot_problems[:5])
            await discord_notify(f"Morning report: {len(bot_problems)} bot(s) 有問題 — {names}", "warn")

        return json.dumps(report, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    #  workshop_profitability
    # ------------------------------------------------------------------

    @mcp.tool()
    async def workshop_profitability(days: int = 7) -> str:
        """績效報表 / Profitability report: gold/hr per bot, per location, trends.

        Args:
            days: Number of days to analyze (default 7)."""

        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        date_to = datetime.now().strftime("%Y-%m-%d")
        stats = await _query_server_stats(date_from=date_from, date_to=date_to, limit=1000)

        if not stats:
            return json.dumps({"error": "No stats data available", "hint": "Check SERVER_URL and CARD_ID"})

        # Per-bot aggregation
        bot_agg: dict[str, dict] = {}
        for s in stats:
            name = s.get("char_name", "unknown")
            if name not in bot_agg:
                bot_agg[name] = {
                    "name": name, "level": 0, "maps": set(),
                    "total_kills": 0, "total_gold": 0, "total_deaths": 0,
                    "total_ms": 0, "days": 0,
                }
            a = bot_agg[name]
            a["total_kills"] += s.get("total_kills", 0)
            a["total_gold"] += s.get("total_gold_gain", 0)
            a["total_deaths"] += s.get("total_deaths", 0)
            a["total_ms"] += s.get("total_bot_ms", 0)
            a["level"] = max(a["level"], s.get("level", 0))
            a["maps"].add(s.get("map_name", "?"))
            a["days"] += 1

        # Compute rates and rank
        rankings = []
        for a in bot_agg.values():
            hours = a["total_ms"] / 3_600_000
            if hours < 1:
                continue
            rankings.append({
                "name": a["name"],
                "level": a["level"],
                "maps": list(a["maps"]),
                "days_active": a["days"],
                "hours": round(hours, 1),
                "gold_hr": round(a["total_gold"] / hours, 0),
                "kills_hr": round(a["total_kills"] / hours, 1),
                "deaths_hr": round(a["total_deaths"] / hours, 2),
                "total_gold": a["total_gold"],
            })
        rankings.sort(key=lambda x: x["gold_hr"], reverse=True)

        # Per-location aggregation
        loc_agg: dict[str, dict] = {}
        for s in stats:
            loc = s.get("map_name", "unknown")
            if loc not in loc_agg:
                loc_agg[loc] = {"map": loc, "total_gold": 0, "total_ms": 0, "bots": set()}
            l = loc_agg[loc]
            l["total_gold"] += s.get("total_gold_gain", 0)
            l["total_ms"] += s.get("total_bot_ms", 0)
            l["bots"].add(s.get("char_name", "?"))

        loc_rankings = []
        for l in loc_agg.values():
            hours = l["total_ms"] / 3_600_000
            if hours < 1:
                continue
            loc_rankings.append({
                "map": l["map"],
                "bots": len(l["bots"]),
                "hours": round(hours, 1),
                "gold_hr": round(l["total_gold"] / hours, 0),
                "total_gold": l["total_gold"],
            })
        loc_rankings.sort(key=lambda x: x["gold_hr"], reverse=True)

        # Fleet totals
        total_gold = sum(a["total_gold"] for a in bot_agg.values())
        total_hours = sum(a["total_ms"] for a in bot_agg.values()) / 3_600_000

        return json.dumps({
            "period": f"{date_from} ~ {date_to}",
            "days": days,
            "fleet_total": {
                "gold": total_gold,
                "hours": round(total_hours, 1),
                "gold_per_hour": round(total_gold / max(total_hours, 0.1), 0),
            },
            "by_bot": rankings,
            "by_location": loc_rankings,
        }, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    #  workshop_risk_report
    # ------------------------------------------------------------------

    @mcp.tool()
    async def workshop_risk_report() -> str:
        """風險報告 / Risk report: flag accounts with high ban risk.

        Checks: death rate, continuous uptime, location repetition,
        accounts running on same schedule patterns."""

        date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        stats = await _query_server_stats(date_from=date_from, limit=1000)

        if not stats:
            return json.dumps({"error": "No stats data"})

        # Group by account
        accounts: dict[str, list[dict]] = {}
        for s in stats:
            name = s.get("char_name", "unknown")
            accounts.setdefault(name, []).append(s)

        risks = []
        for name, days in accounts.items():
            score = 0
            flags = []

            # Check: high death rate
            total_deaths = sum(d.get("total_deaths", 0) for d in days)
            total_hours = sum(d.get("total_bot_ms", 0) for d in days) / 3_600_000
            if total_hours > 0:
                dph = total_deaths / total_hours
                if dph > 2:
                    score += 30
                    flags.append(f"high_deaths={dph:.1f}/hr")
                elif dph > 1:
                    score += 15
                    flags.append(f"elevated_deaths={dph:.1f}/hr")

            # Check: excessive uptime (>18hr in a single day)
            for d in days:
                day_hours = d.get("total_bot_ms", 0) / 3_600_000
                if day_hours > 18:
                    score += 20
                    flags.append(f"excessive_uptime={day_hours:.0f}hr on {d.get('date','?')}")
                    break

            # Check: same location 3+ consecutive days
            maps = [d.get("map_name", "") for d in sorted(days, key=lambda x: x.get("date", ""))]
            if len(maps) >= 3:
                consec = 1
                for i in range(1, len(maps)):
                    if maps[i] == maps[i - 1] and maps[i]:
                        consec += 1
                    else:
                        consec = 1
                    if consec >= 3:
                        score += 20
                        flags.append(f"same_location_3days={maps[i]}")
                        break

            # Check: zero deaths with long sessions (suspiciously perfect)
            for d in days:
                ms = d.get("total_bot_ms", 0)
                if ms > 28_800_000 and d.get("total_deaths", 0) == 0:  # 8hr+, 0 deaths
                    score += 10
                    flags.append("zero_deaths_long_session")
                    break

            if score > 0:
                risks.append({
                    "name": name,
                    "level": max((d.get("level", 0) for d in days), default=0),
                    "risk_score": min(score, 100),
                    "risk_level": "HIGH" if score >= 40 else "MEDIUM" if score >= 20 else "LOW",
                    "flags": flags,
                    "days_active": len(days),
                    "total_hours": round(total_hours, 1),
                })

        risks.sort(key=lambda x: x["risk_score"], reverse=True)

        return json.dumps({
            "report_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_accounts": len(accounts),
            "at_risk": len([r for r in risks if r["risk_score"] >= 20]),
            "high_risk": len([r for r in risks if r["risk_score"] >= 40]),
            "accounts": risks,
            "recommendations": [
                f"REST: {r['name']} — 建議增加離線時間" for r in risks if r["risk_score"] >= 40
            ] + [
                f"MOVE: {r['name']} — 建議換地圖" for r in risks
                if any("same_location" in f for f in r["flags"])
            ],
        }, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    #  workshop_account_audit
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    #  workshop_setup_crons
    # ------------------------------------------------------------------

    @mcp.tool()
    async def workshop_setup_crons() -> str:
        """取得自動化 cron 設定指令 / Get all cron trigger setup commands.

        Returns the exact /schedule commands to set up automated monitoring.
        Copy and run each command to activate."""

        crons = [
            {
                "name": "fleet-health",
                "cron": "*/10 * * * *",
                "description": "艦隊健康巡檢 (每 10 分鐘)",
                "prompt": "呼叫 fleet_health_check()。如果有問題，列出每個問題 bot 和建議操作。如果有 bot 離線超過 10 分鐘，嘗試 opener_start 重啟。",
            },
            {
                "name": "supply-monitor",
                "cron": "*/30 * * * *",
                "description": "補給監控 (每 30 分鐘)",
                "prompt": "呼叫 fleet_supply_check()。如果有 bot 需要補給，按急迫度排序，對最急的 1-2 隻執行 bot_supply_trigger。不要同時補給超過 2 隻。",
            },
            {
                "name": "analytics-snapshot",
                "cron": "0 */2 * * *",
                "description": "績效快照 (每 2 小時)",
                "prompt": "呼叫 fleet_performance(days=1)。如果有 underperformer (gold_hr 低於平均 30%)，呼叫 bot_compare 比較它和最好的 bot，找出 config 差異並建議調整。",
            },
            {
                "name": "daily-report",
                "cron": "0 8 * * *",
                "description": "早班報告 (每天 08:00)",
                "prompt": "呼叫 workshop_morning_report()，以結構化格式呈現完整報告。如果有異常，標記優先處理項目。",
            },
            {
                "name": "daily-audit",
                "cron": "0 23 * * *",
                "description": "每日稽核 (每天 23:00)",
                "prompt": "依序執行：1) workshop_account_audit() 找出問題帳號，2) workshop_risk_report() 評估風險，3) fleet_risk_scores() 風險評分。彙整成報告，標記需要明天處理的事項。",
            },
        ]

        commands = []
        for c in crons:
            cmd = f'/schedule create "{c["name"]}" --cron "{c["cron"]}" --prompt "{c["prompt"]}"'
            commands.append({
                "name": c["name"],
                "description": c["description"],
                "cron": c["cron"],
                "command": cmd,
            })

        return json.dumps({
            "total_crons": len(commands),
            "crons": commands,
            "management": {
                "list": "/schedule list",
                "delete": "/schedule delete <name>",
                "run_once": "/schedule run <name>",
            },
        }, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    #  workshop_account_audit
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    #  workshop_verify
    # ------------------------------------------------------------------

    @mcp.tool()
    async def workshop_verify(host: str = "") -> str:
        """環境驗證 / Run 6-step verification to confirm all components work.

        Checks: MCP connection, opener, schedule, jitter, data collector, fleet health."""

        checks = []

        # Step 1: Bot list (MCP → DLL)
        try:
            instances = await _scan_instances(force=True)
            checks.append({
                "step": "MCP 連線", "ok": len(instances) > 0,
                "detail": f"{len(instances)} bot(s) 在線",
            })
        except Exception as e:
            checks.append({"step": "MCP 連線", "ok": False, "detail": str(e)})

        # Step 2: Opener
        try:
            raw = await _opener_http("GET", "/api/instances", host=host)
            data = json.loads(raw).get("data", [])
            ok = isinstance(data, list)
            checks.append({
                "step": "Opener 連線", "ok": ok,
                "detail": f"{len(data)} 帳號" if ok else "連線失敗",
            })
        except Exception as e:
            checks.append({"step": "Opener 連線", "ok": False, "detail": str(e)})

        # Step 3: Schedule
        try:
            raw = await _opener_http("GET", "/api/schedule", host=host)
            sdata = json.loads(raw).get("data", {})
            checks.append({
                "step": "排程系統", "ok": "slot_count" in sdata,
                "detail": f"enabled={sdata.get('enabled')} slots={sdata.get('slot_count')}",
            })
        except Exception as e:
            checks.append({"step": "排程系統", "ok": False, "detail": str(e)})

        # Step 4: Jitter
        jitter = sdata.get("jitter_minutes", 0) if 'sdata' in dir() else 0
        checks.append({
            "step": "Jitter 防 ban", "ok": jitter >= 5,
            "detail": f"±{jitter} 分鐘" if jitter else "未設定或舊版 scheduler",
        })

        # Step 5: Data collector (snapshots)
        try:
            raw = await _opener_http("GET", "/api/snapshots", params={"limit": "1"}, host=host)
            snaps = json.loads(raw).get("data", {}).get("snapshots", [])
            has_data = len(snaps) > 0
            checks.append({
                "step": "數據收集器", "ok": has_data,
                "detail": f"{len(snaps)} 筆快照" if has_data else "等待中 (需 5 分鐘)",
            })
        except Exception as e:
            checks.append({"step": "數據收集器", "ok": False, "detail": str(e)})

        # Step 6: Fleet health
        try:
            ok_count = sum(1 for i in instances if i.get("hp", 0) > 0)
            checks.append({
                "step": "艦隊健康", "ok": True,
                "detail": f"{ok_count}/{len(instances)} bot(s) 有 HP 數據",
            })
        except Exception:
            checks.append({"step": "艦隊健康", "ok": False, "detail": "無法檢查"})

        passed = sum(1 for c in checks if c["ok"])
        total = len(checks)

        audit_log("workshop_verify", {"host": host}, f"{passed}/{total} passed")

        return json.dumps({
            "passed": passed,
            "total": total,
            "all_ok": passed == total,
            "checks": checks,
        }, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    #  workshop_audit_log
    # ------------------------------------------------------------------

    @mcp.tool()
    async def workshop_audit_log(lines: int = 50) -> str:
        """操作日誌 / View recent audit log entries.

        Shows all MCP tool calls with timestamps, parameters, and results.
        All operator actions are automatically logged here.

        Args:
            lines: number of recent entries to return (default 50)"""

        import glob
        audit_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audit_logs")
        files = sorted(glob.glob(os.path.join(audit_dir, "audit_*.jsonl")), reverse=True)

        entries = []
        for fpath in files:
            if len(entries) >= lines:
                break
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            entries.append(json.loads(line))
            except (OSError, json.JSONDecodeError):
                continue

        entries.sort(key=lambda e: e.get("ts", ""), reverse=True)
        entries = entries[:lines]

        return json.dumps({
            "total_entries": len(entries),
            "entries": entries,
        }, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    #  workshop_account_audit
    # ------------------------------------------------------------------

    @mcp.tool()
    async def workshop_account_audit() -> str:
        """帳號稽核 / Account audit: detect banned, stuck, or inactive accounts.

        Cross-references server stats with scheduler flags to find
        accounts that may be banned, jailed, or stuck."""

        date_from = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        stats = await _query_server_stats(date_from=date_from, limit=500)

        # Get scheduler account flags from all machines
        machines = await _refresh_machines()
        flag_tasks = [_opener_http("GET", "/api/account_flags", host=m.get("ip", ""))
                      for m in machines.values() if m.get("ip")]
        flag_results = await asyncio.gather(*flag_tasks, return_exceptions=True)

        all_flags: dict[str, str] = {}
        for result in flag_results:
            if isinstance(result, Exception):
                continue
            try:
                data = json.loads(result).get("data", {})
                if isinstance(data, dict):
                    all_flags.update(data)
            except Exception:
                pass

        # Group stats by account
        accounts: dict[str, list[dict]] = {}
        for s in stats:
            name = s.get("char_name", "unknown")
            accounts.setdefault(name, []).append(s)

        issues = []

        for name, days in accounts.items():
            flags_list = []

            # Check: zero kills despite having bot_ms (stuck or jailed)
            for d in days:
                if d.get("total_bot_ms", 0) > 3_600_000 and d.get("total_kills", 0) == 0:
                    flags_list.append(f"zero_kills_with_uptime on {d.get('date','?')}")
                    break

            # Check: not seen for 2+ days
            dates = sorted(d.get("date", "") for d in days)
            if dates:
                last_seen = dates[-1]
                days_ago = (datetime.now().date() - datetime.strptime(last_seen, "%Y-%m-%d").date()).days
                if days_ago >= 2:
                    flags_list.append(f"not_seen_{days_ago}_days")

            # Check: scheduler has banned/jailed flag
            flag = all_flags.get(name, "active")
            if flag in ("banned", "jailed", "suspended"):
                flags_list.append(f"scheduler_flag={flag}")

            if flags_list:
                issues.append({
                    "name": name,
                    "scheduler_flag": flag,
                    "issues": flags_list,
                    "last_date": dates[-1] if dates else "?",
                    "suggestion": "REMOVE" if "banned" in str(flags_list) else "INVESTIGATE",
                })

        issues.sort(key=lambda x: len(x["issues"]), reverse=True)

        return json.dumps({
            "audit_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_accounts": len(accounts),
            "accounts_with_issues": len(issues),
            "issues": issues,
        }, ensure_ascii=False, indent=2)
