"""Schedule tools: shift scheduling & account rotation via opener.py scheduler.

The scheduler runs inside opener.py on each Windows machine. These tools
bridge Claude Code to the scheduler's HTTP API (port 8600).
"""
from __future__ import annotations

import asyncio
import json


def register(mcp) -> None:
    from core import _opener_http, _refresh_machines

    # ------------------------------------------------------------------
    #  Query
    # ------------------------------------------------------------------

    @mcp.tool()
    async def schedule_status(host: str = "") -> str:
        """查看排程狀態 / Full schedule state: entries, slots, enabled."""
        return await _opener_http("GET", "/api/schedule", host=host)

    @mcp.tool()
    async def schedule_running(host: str = "") -> str:
        """查看目前執行中的排程 / Currently running schedule entries."""
        return await _opener_http("GET", "/api/schedule/status", host=host)

    @mcp.tool()
    async def schedule_templates(host: str = "") -> str:
        """查看班表模板 / List shift schedule templates."""
        return await _opener_http("GET", "/api/schedule/templates", host=host)

    @mcp.tool()
    async def schedule_account_flags(host: str = "") -> str:
        """查看帳號狀態 / Account flags: active, banned, jailed, suspended."""
        return await _opener_http("GET", "/api/account_flags", host=host)

    # ------------------------------------------------------------------
    #  CRUD
    # ------------------------------------------------------------------

    @mcp.tool()
    async def schedule_add(
        slot_id: str,
        acc_id: str,
        start: str,
        end: str,
        profile: str = "",
        host: str = "",
    ) -> str:
        """新增排程 / Add a schedule entry. Times: 'YYYY-MM-DD HH:MM'."""
        return await _opener_http("POST", "/api/schedule/entry", body={
            "slot_id": slot_id,
            "acc_id": acc_id,
            "start": start,
            "end": end,
            "profile": profile,
        }, host=host)

    @mcp.tool()
    async def schedule_update(entry_id: str, fields: str = "{}", host: str = "") -> str:
        """更新排程 / Update a schedule entry. fields: JSON of fields to change."""
        try:
            body = json.loads(fields)
        except json.JSONDecodeError:
            return json.dumps({"error": f"Invalid JSON: {fields}"})
        return await _opener_http("PUT", f"/api/schedule/entry/{entry_id}",
                                  body=body, host=host)

    @mcp.tool()
    async def schedule_delete(entry_id: str, host: str = "") -> str:
        """刪除排程 / Delete a schedule entry."""
        return await _opener_http("DELETE", f"/api/schedule/entry/{entry_id}", host=host)

    # ------------------------------------------------------------------
    #  Generation
    # ------------------------------------------------------------------

    @mcp.tool()
    async def schedule_generate(
        template_name: str,
        from_date: str,
        to_date: str,
        host: str = "",
    ) -> str:
        """從模板生成排程 / Generate schedule entries from a template."""
        return await _opener_http("POST", "/api/schedule/generate", body={
            "template_name": template_name,
            "from": from_date,
            "to": to_date,
        }, host=host)

    # ------------------------------------------------------------------
    #  Control
    # ------------------------------------------------------------------

    @mcp.tool()
    async def schedule_toggle(enabled: int = 1, host: str = "") -> str:
        """開關排程器 / Toggle scheduler on (1) or off (0)."""
        return await _opener_http("POST", "/api/schedule/toggle", body={
            "enabled": bool(enabled),
        }, host=host)

    # ------------------------------------------------------------------
    #  Maintenance
    # ------------------------------------------------------------------

    @mcp.tool()
    async def schedule_copy_day(
        from_date: str,
        to_date: str,
        slot_id: str = "",
        host: str = "",
    ) -> str:
        """複製排程 / Copy schedule entries from one day to another."""
        body: dict = {"from_date": from_date, "to_date": to_date}
        if slot_id:
            body["slot_id"] = slot_id
        return await _opener_http("POST", "/api/schedule/copy_day", body=body, host=host)

    @mcp.tool()
    async def schedule_clear_day(date: str, slot_id: str = "", host: str = "") -> str:
        """清除某天排程 / Clear all entries for a specific day."""
        body: dict = {"date": date}
        if slot_id:
            body["slot_id"] = slot_id
        return await _opener_http("POST", "/api/schedule/clear_day", body=body, host=host)

    @mcp.tool()
    async def schedule_clear_range(
        from_date: str,
        to_date: str,
        slot_id: str = "",
        host: str = "",
    ) -> str:
        """清除日期範圍排程 / Clear entries in a date range."""
        body: dict = {"from": from_date, "to": to_date}
        if slot_id:
            body["slot_id"] = slot_id
        return await _opener_http("POST", "/api/schedule/clear_range", body=body, host=host)

    # ------------------------------------------------------------------
    #  Settings & templates
    # ------------------------------------------------------------------

    @mcp.tool()
    async def schedule_settings(
        slot_count: int = 0,
        rest_minutes: int = -1,
        check_interval: int = 0,
        host: str = "",
    ) -> str:
        """更新排程器設定 / Update scheduler settings. Only non-zero values are sent."""
        body: dict = {}
        if slot_count > 0:
            body["slot_count"] = slot_count
        if rest_minutes >= 0:
            body["rest_minutes"] = rest_minutes
        if check_interval > 0:
            body["check_interval"] = check_interval
        if not body:
            return await _opener_http("GET", "/api/schedule", host=host)
        return await _opener_http("PUT", "/api/schedule/settings", body=body, host=host)

    @mcp.tool()
    async def schedule_save_template(template_json: str, host: str = "") -> str:
        """儲存班表模板 / Save a shift schedule template."""
        try:
            body = json.loads(template_json)
        except json.JSONDecodeError:
            return json.dumps({"error": f"Invalid JSON: {template_json}"})
        return await _opener_http("POST", "/api/schedule/templates", body=body, host=host)

    # ------------------------------------------------------------------
    #  Fleet aggregate
    # ------------------------------------------------------------------

    @mcp.tool()
    async def schedule_fleet_overview() -> str:
        """全工作室排程總覽 / Aggregate schedule status across all machines."""
        machines = await _refresh_machines(force=True)
        if not machines:
            return json.dumps({"error": "No machines discovered"})

        tasks = []
        hosts = []
        for m in machines.values():
            ip = m.get("ip", "")
            if ip:
                hosts.append(ip)
                tasks.append(_opener_http("GET", "/api/schedule/status", host=ip))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        overview = []
        for ip, result in zip(hosts, results):
            if isinstance(result, Exception):
                overview.append({"host": ip, "status": "offline", "error": str(result)})
                continue
            try:
                data = json.loads(result)
                sched = data.get("data", {})
                overview.append({
                    "host": ip,
                    "status": "online",
                    "schedule": sched,
                })
            except Exception as e:
                overview.append({"host": ip, "status": "error", "error": str(e)})

        return json.dumps({
            "machines": len(overview),
            "overview": overview,
        }, ensure_ascii=False, indent=2)
