"""Analytics tools: performance evaluation, A/B experiments, anomaly detection.

Uses pure functions from analytics.py + server stats data.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta


def register(mcp) -> None:
    from core import _http, _scan_instances, SERVER_URL, CARD_ID, audit_log, discord_notify
    import analytics

    # ------------------------------------------------------------------
    #  Helper: query server stats
    # ------------------------------------------------------------------
    async def _query_stats(date_from: str = "", date_to: str = "", limit: int = 500) -> list[dict]:
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
                r = await client.get(f"{SERVER_URL}/api/stats", params=params,
                                     headers={"Accept": "application/json"})
                if r.status_code == 200:
                    return r.json().get("stats", [])
        except Exception:
            pass
        return []

    # ------------------------------------------------------------------
    #  fleet_performance
    # ------------------------------------------------------------------

    @mcp.tool()
    async def fleet_performance(days: int = 1) -> str:
        """全艦隊績效排名 / Rank all bots by gold/hr, flag underperformers.

        Groups bots by location. Underperformers are those below 70% of
        the location average gold/hr."""

        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        stats = await _query_stats(date_from=date_from)

        if not stats:
            # Fallback: use live bot_stats from DLL
            instances = await _scan_instances(force=True)
            live = []
            for inst in instances:
                try:
                    raw = await _http(inst["port"], "GET", "/stats", host=inst["host"])
                    data = json.loads(raw).get("data", {})
                    if isinstance(data, dict):
                        data["char_name"] = data.get("char_name", inst.get("char_name", "?"))
                        live.append(data)
                except Exception:
                    pass
            stats = live

        if not stats:
            return json.dumps({"error": "No stats available"})

        result = analytics.rank_bots_by_location(stats)

        # Flatten for readability
        output = {"period_days": days, "locations": {}}
        for loc, data in result.items():
            output["locations"][loc] = {
                "avg_gold_hr": data["avg_gold_hr"],
                "bots": data["ranking"],
            }

        return json.dumps(output, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    #  bot_compare
    # ------------------------------------------------------------------

    @mcp.tool()
    async def bot_compare(bot_a_port: int = 0, bot_b_port: int = 0,
                          bot_a_host: str = "", bot_b_host: str = "") -> str:
        """比較兩隻 bot 的 config 和績效 / Compare two bots' config + performance.

        Useful for A/B testing: find what's different between a good and bad bot."""

        # Get configs
        raw_a = await _http(bot_a_port, "GET", "/bot/config", host=bot_a_host)
        raw_b = await _http(bot_b_port, "GET", "/bot/config", host=bot_b_host)

        try:
            config_a = json.loads(raw_a).get("data", {})
            config_b = json.loads(raw_b).get("data", {})
        except Exception:
            return json.dumps({"error": "Could not read configs"})

        diffs = analytics.compare_configs(config_a, config_b)

        # Get stats
        raw_sa = await _http(bot_a_port, "GET", "/stats", host=bot_a_host)
        raw_sb = await _http(bot_b_port, "GET", "/stats", host=bot_b_host)

        try:
            stats_a = json.loads(raw_sa).get("data", {})
            stats_b = json.loads(raw_sb).get("data", {})
        except Exception:
            stats_a, stats_b = {}, {}

        rates_a = analytics.calc_hourly_rates(stats_a) if isinstance(stats_a, dict) else {}
        rates_b = analytics.calc_hourly_rates(stats_b) if isinstance(stats_b, dict) else {}

        return json.dumps({
            "bot_a": {
                "port": bot_a_port, "host": bot_a_host,
                "name": stats_a.get("char_name", "?"),
                "rates": rates_a,
            },
            "bot_b": {
                "port": bot_b_port, "host": bot_b_host,
                "name": stats_b.get("char_name", "?"),
                "rates": rates_b,
            },
            "config_diffs": diffs,
            "performance_diff": {
                "gold_hr_delta": (rates_b.get("gold_hr", 0) - rates_a.get("gold_hr", 0)),
                "kills_hr_delta": (rates_b.get("kills_hr", 0) - rates_a.get("kills_hr", 0)),
            },
        }, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    #  experiment_evaluate
    # ------------------------------------------------------------------

    @mcp.tool()
    async def experiment_evaluate(
        control_values: str = "[]",
        treatment_values: str = "[]",
    ) -> str:
        """A/B 實驗判定 / Evaluate an A/B experiment with Welch's t-test.

        Args:
            control_values: JSON array of gold/hr (or kills/hr) samples from control group
            treatment_values: JSON array from treatment group

        Example: experiment_evaluate('[150,155,148]', '[200,210,195]')"""

        try:
            control = json.loads(control_values)
            treatment = json.loads(treatment_values)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON arrays"})

        if not isinstance(control, list) or not isinstance(treatment, list):
            return json.dumps({"error": "Both inputs must be JSON arrays of numbers"})

        result = analytics.evaluate_experiment(
            [float(x) for x in control],
            [float(x) for x in treatment],
        )

        return json.dumps(result, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    #  fleet_risk_scores
    # ------------------------------------------------------------------

    @mcp.tool()
    async def fleet_risk_scores() -> str:
        """全艦隊風險評分 / Calculate ban risk score for every account.

        Uses 7-day history to score: uptime, death rate, location repetition."""

        date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        stats = await _query_stats(date_from=date_from, limit=1000)

        if not stats:
            return json.dumps({"error": "No stats data"})

        # Group by account
        accounts: dict[str, list[dict]] = {}
        for s in stats:
            name = s.get("char_name", "unknown")
            accounts.setdefault(name, []).append(s)

        scores = []
        for name, history in accounts.items():
            r = analytics.calc_risk_score(history)
            r["name"] = name
            r["days"] = len(history)
            scores.append(r)

        scores.sort(key=lambda x: x["score"], reverse=True)

        return json.dumps({
            "total_accounts": len(scores),
            "high_risk": len([s for s in scores if s["level"] == "HIGH"]),
            "medium_risk": len([s for s in scores if s["level"] == "MEDIUM"]),
            "accounts": scores,
        }, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    #  fleet_supply_efficiency
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    #  allocation_suggest
    # ------------------------------------------------------------------

    @mcp.tool()
    async def allocation_suggest(locations_json: str, total_bots: int = 0) -> str:
        """資源分配建議 / Suggest optimal bot allocation across locations.

        Uses marginal utility with diminishing returns to avoid overcrowding.

        Args:
            locations_json: JSON object of locations, e.g.:
                {"map1": {"base_gold_hr": 10000, "crowding_factor": 0.85},
                 "map2": {"base_gold_hr": 8000, "crowding_factor": 0.9}}
            total_bots: number of bots to allocate (0 = auto from fleet_status)
        """
        try:
            locations = json.loads(locations_json)
        except json.JSONDecodeError:
            return json.dumps({"error": f"Invalid JSON: {locations_json}"})

        if total_bots <= 0:
            instances = await _scan_instances()
            total_bots = len(instances)

        result = analytics.optimal_allocation(locations, total_bots, return_details=True)
        return json.dumps({
            "total_bots": total_bots,
            "allocation": {k: v for k, v in result.items() if k != "total_gold_hr"},
            "estimated_total_gold_hr": result.get("total_gold_hr", 0),
        }, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    #  death_alert
    # ------------------------------------------------------------------

    @mcp.tool()
    async def death_alert(port: int = 0, host: str = "") -> str:
        """死亡預警 / Check if a bot's death rate is accelerating (CUSUM).

        Analyzes recent death timestamps to detect clustering."""
        import time

        raw = await _http(port, "GET", "/stats", host=host)
        try:
            data = json.loads(raw).get("data", {})
        except Exception:
            return json.dumps({"error": "Could not read stats"})

        # Get death count and estimate timestamps from rate
        deaths = data.get("total_deaths", 0)
        bot_ms = data.get("total_bot_ms", 0)

        if deaths < 3 or bot_ms < 600_000:
            return json.dumps({
                "alert": False,
                "deaths": deaths,
                "note": "Not enough data for CUSUM analysis",
            })

        # Estimate: spread deaths evenly, then check recent logs for clustering
        raw_logs = await _http(port, "GET", "/logs", host=host,
                               params={"level": "S", "since": "0"})
        try:
            logs_data = json.loads(raw_logs).get("data", {})
            log_lines = logs_data.get("lines", []) if isinstance(logs_data, dict) else []
        except Exception:
            log_lines = []

        # Extract death timestamps from logs
        death_ts = []
        now = time.time()
        for line in log_lines:
            text = line.get("text", "") if isinstance(line, dict) else str(line)
            if "death" in text.lower() or "died" in text.lower() or "dead" in text.lower():
                ts = line.get("ts", 0) if isinstance(line, dict) else 0
                if ts > 0:
                    death_ts.append(ts)

        if len(death_ts) < 3:
            # Fallback: can't do CUSUM without timestamps
            hours = bot_ms / 3_600_000
            dph = deaths / hours if hours > 0 else 0
            return json.dumps({
                "alert": dph > 2,
                "deaths": deaths,
                "deaths_per_hour": round(dph, 2),
                "note": "Rate-based check (no timestamps available for CUSUM)",
            })

        result = analytics.cusum_death_alert(death_ts, return_details=True)
        return json.dumps({
            "alert": result["alert"],
            "cusum_max": result["cusum_max"],
            "death_count": len(death_ts),
            "deaths_total": deaths,
        }, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    #  fleet_supply_efficiency
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    #  fleet_anomaly_scan (uses opener snapshots + EWMA)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def fleet_anomaly_scan(host: str = "") -> str:
        """即時異常掃描 / Scan all bots for performance anomalies using EWMA.

        Uses 5-minute snapshots from opener's data_collector.
        Detects: kills drop, death spike, prolonged no-mob."""

        from core import _opener_http

        # Get snapshots from opener
        raw = await _opener_http("GET", "/api/snapshots",
                                 params={"limit": "200"}, host=host)
        try:
            data = json.loads(raw)
            snapshots = data.get("data", {}).get("snapshots", [])
            if not snapshots:
                snapshots = data.get("snapshots", [])
        except Exception:
            return json.dumps({"error": "Could not read snapshots from opener"})

        if not snapshots:
            return json.dumps({
                "anomalies": [],
                "note": "No snapshots available. Data collector may not be running yet (needs ~30 min of data).",
            })

        # Group by bot name
        by_bot: dict[str, list[dict]] = {}
        for s in snapshots:
            name = s.get("name", s.get("acc", "?"))
            by_bot.setdefault(name, []).append(s)

        all_anomalies = []

        for name, series in by_bot.items():
            series.sort(key=lambda x: x.get("ts", 0))

            # Check kills_d for drops
            kills_series = [{"kills_hr": s.get("kills_d", 0) * 12, "ts": s.get("dt", "")}
                           for s in series]  # *12 to convert 5min delta to hourly rate
            kill_anomalies = analytics.detect_anomalies(
                kills_series, field="kills_hr", direction="down", threshold_sigma=2.0
            )
            for a in kill_anomalies:
                all_anomalies.append({
                    "bot": name, "type": "kills_drop",
                    "time": a["ts"], "value": a["value"],
                    "expected": a["expected"], "z": a["z_score"],
                })

            # Check deaths_d for spikes
            death_series = [{"deaths_hr": s.get("deaths_d", 0) * 12, "ts": s.get("dt", "")}
                           for s in series]
            death_anomalies = analytics.detect_anomalies(
                death_series, field="deaths_hr", direction="up", threshold_sigma=2.0
            )
            for a in death_anomalies:
                all_anomalies.append({
                    "bot": name, "type": "death_spike",
                    "time": a["ts"], "value": a["value"],
                    "expected": a["expected"], "z": a["z_score"],
                })

            # Check prolonged nomob
            last = series[-1] if series else {}
            if last.get("nomob_ms", 0) > 120000:  # >2 min no mob
                all_anomalies.append({
                    "bot": name, "type": "no_mob",
                    "time": last.get("dt", ""),
                    "nomob_seconds": last["nomob_ms"] // 1000,
                    "note": "Bot may be stuck or area is empty",
                })

        all_anomalies.sort(key=lambda a: abs(a.get("z", 0)), reverse=True)

        audit_log("fleet_anomaly_scan", {"host": host},
                  f"scanned={len(by_bot)} anomalies={len(all_anomalies)}")

        if all_anomalies:
            top = all_anomalies[0]
            await discord_notify(
                f"異常偵測: {len(all_anomalies)} 筆 — {top['bot']} {top['type']} (z={top.get('z',0)})",
                "warn"
            )

        return json.dumps({
            "scan_time": datetime.now().strftime("%H:%M"),
            "bots_scanned": len(by_bot),
            "anomalies_found": len(all_anomalies),
            "anomalies": all_anomalies,
        }, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    #  fleet_supply_efficiency
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    #  kill_heatmap
    # ------------------------------------------------------------------

    @mcp.tool()
    async def kill_heatmap(
        port: int = 0, host: str = "", grid_size: int = 8, top_n: int = 10,
    ) -> str:
        """擊殺熱力圖 / Build kill heatmap from bot's pos_log data.

        Shows where kills happen most. Use for patrol route optimization
        and finding the best grind spots.

        Args:
            port: DLL port
            host: machine IP
            grid_size: grid cell size in world units (8=default, 4=high detail)
            top_n: number of hotspots to highlight
        """
        raw = await _http(port, "GET", "/stats", host=host)
        try:
            data = json.loads(raw).get("data", {})
        except Exception:
            return json.dumps({"error": "Could not read stats"})

        # pos_log from DLL: [[x, y, kills, gold, tick], ...]
        pos_log = data.get("pos_log", [])
        if not pos_log:
            return json.dumps({
                "heatmap": [],
                "hotspots": [],
                "note": "No pos_log data. Bot needs to run longer to accumulate position records.",
            })

        heatmap = analytics.build_heatmap(pos_log, grid_size=grid_size)
        hotspots = analytics.extract_hotspots(heatmap, top_n=top_n, min_kills=1)

        total_kills = sum(c["kills"] for c in heatmap)
        total_cells = len(heatmap)

        audit_log("kill_heatmap", {"port": port, "host": host, "grid_size": grid_size},
                  f"cells={total_cells} hotspots={len(hotspots)} total_kills={total_kills}")

        return json.dumps({
            "char_name": data.get("char_name", "?"),
            "map": data.get("map_name", "?"),
            "grid_size": grid_size,
            "total_cells": total_cells,
            "total_kills": total_kills,
            "hotspots": hotspots,
            "heatmap": heatmap,
        }, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    #  fleet_supply_efficiency
    # ------------------------------------------------------------------

    @mcp.tool()
    async def fleet_supply_efficiency() -> str:
        """補給效率分析 / Analyze supply run efficiency across fleet.

        Shows runs/hour and estimated time wasted on supply per bot."""

        instances = await _scan_instances()
        results = []

        for inst in instances:
            try:
                raw = await _http(inst["port"], "GET", "/stats", host=inst["host"])
                data = json.loads(raw).get("data", {})
                if isinstance(data, dict):
                    eff = analytics.calc_supply_efficiency(data)
                    eff["name"] = data.get("char_name", inst.get("char_name", "?"))
                    eff["map"] = data.get("map_name", "?")
                    results.append(eff)
            except Exception:
                pass

        results.sort(key=lambda x: x["runs_per_hour"], reverse=True)

        return json.dumps({
            "bots": results,
            "fleet_avg_runs_per_hour": round(
                sum(r["runs_per_hour"] for r in results) / max(len(results), 1), 2
            ),
        }, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    #  schedule_optimize (A8: Hungarian assignment)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def schedule_optimize(gold_matrix_json: str = "[]") -> str:
        """排程最佳化 / Optimal account-to-slot assignment using Hungarian algorithm.

        Maximizes total fleet gold/hr by assigning accounts to time slots
        based on their historical performance at each slot's location.

        Args:
            gold_matrix_json: JSON 2D array where gold_matrix[i][j] = gold/hr
                of account i at slot j's location. E.g.:
                '[[100,200],[300,100],[150,250]]' (3 accounts × 2 slots)

        Returns optimal assignment with total estimated gold/hr."""

        try:
            gold_matrix = json.loads(gold_matrix_json)
        except json.JSONDecodeError:
            return json.dumps({"error": f"Invalid JSON: {gold_matrix_json}"})

        if not isinstance(gold_matrix, list) or not gold_matrix:
            return json.dumps({"error": "gold_matrix must be a non-empty 2D array"})

        result = analytics.hungarian_schedule(gold_matrix)
        total = sum(r["gold_hr"] for r in result)

        audit_log("schedule_optimize", {
            "accounts": len(gold_matrix),
            "slots": len(gold_matrix[0]) if gold_matrix else 0,
        }, f"assignments={len(result)} total_gold_hr={total}")

        return json.dumps({
            "assignments": result,
            "total_gold_hr": total,
            "accounts": len(gold_matrix),
            "slots": len(gold_matrix[0]) if gold_matrix else 0,
        }, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    #  location_equilibrium (A9: Best-Response game equilibrium)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def location_equilibrium(locations_json: str = "{}") -> str:
        """地點均衡分配 / Find Nash equilibrium for bot location assignment.

        Uses best-response dynamics to spread bots across locations,
        avoiding overcrowding while maximizing total gold.

        Args:
            locations_json: JSON object of locations with base rates:
                {"map1": {"base_gold_hr": 10000, "crowding_factor": 0.8}, ...}

        Auto-discovers current fleet assignments from live bot data."""

        try:
            locations = json.loads(locations_json)
        except json.JSONDecodeError:
            return json.dumps({"error": f"Invalid JSON: {locations_json}"})

        if not locations:
            return json.dumps({"error": "locations must be a non-empty object"})

        # Discover current fleet
        instances = await _scan_instances(force=True)
        accounts = []
        for inst in instances:
            try:
                raw = await _http(inst["port"], "GET", "/stats", host=inst["host"])
                data = json.loads(raw).get("data", {})
                accounts.append({
                    "name": data.get("char_name", inst.get("char_name", "?")),
                    "current_location": data.get("map_name", "unknown"),
                    "port": inst["port"],
                    "host": inst["host"],
                })
            except Exception:
                pass

        if not accounts:
            return json.dumps({"error": "No bots online"})

        result = analytics.best_response_equilibrium(accounts, locations)

        moves = [r for r in result if r["moved"]]
        total_gold = sum(r["gold_hr"] for r in result)

        audit_log("location_equilibrium", {
            "bots": len(accounts), "locations": len(locations),
        }, f"moves={len(moves)} total_gold_hr={total_gold}")

        if moves:
            move_desc = ", ".join(f"{m['name']}→{m['location']}" for m in moves)
            await discord_notify(f"均衡建議: {len(moves)} 移動 — {move_desc}", "info")

        return json.dumps({
            "equilibrium": result,
            "total_gold_hr": total_gold,
            "moves_suggested": len(moves),
            "bots_total": len(accounts),
        }, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    #  patrol_route (A10: hotspot → waypoint patrol path)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def patrol_route(
        port: int = 0, host: str = "",
        grid_size: int = 8, max_waypoints: int = 8, loop: bool = True,
    ) -> str:
        """巡邏路線生成 / Generate optimal patrol route from kill heatmap.

        Reads pos_log, builds heatmap, extracts hotspots, then generates
        a nearest-neighbor patrol path. Can be uploaded as nav_script.

        Args:
            port: DLL port
            host: machine IP
            grid_size: heatmap grid cell size (8=default)
            max_waypoints: max patrol stops (8=default)
            loop: close the route back to start (default True)
        """
        raw = await _http(port, "GET", "/stats", host=host)
        try:
            data = json.loads(raw).get("data", {})
        except Exception:
            return json.dumps({"error": "Could not read stats"})

        pos_log = data.get("pos_log", [])
        if not pos_log:
            return json.dumps({
                "path": [],
                "note": "No pos_log data. Bot needs to run longer.",
            })

        heatmap = analytics.build_heatmap(pos_log, grid_size=grid_size)
        hotspots = analytics.extract_hotspots(heatmap, top_n=max_waypoints, min_kills=1)

        if not hotspots:
            return json.dumps({"path": [], "note": "No hotspots found"})

        path = analytics.generate_patrol_path(hotspots, max_waypoints=max_waypoints, loop=loop)
        total_dist = sum(p["distance_from_prev"] for p in path)

        # Generate nav_script compatible format
        nav_steps = []
        for p in path:
            nav_steps.append({"action": "walk", "x": p["x"], "y": p["y"], "wait": 2000})

        audit_log("patrol_route", {"port": port, "host": host},
                  f"waypoints={len(path)} total_dist={total_dist:.0f}")

        return json.dumps({
            "char_name": data.get("char_name", "?"),
            "map": data.get("map_name", "?"),
            "waypoints": len(path),
            "total_distance": round(total_dist, 0),
            "loop": loop,
            "path": path,
            "nav_script": nav_steps,
        }, ensure_ascii=False, indent=2)
