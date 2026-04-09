"""Opener tools: multi-launcher control via opener.py (port 8600).

Each Windows machine runs opener.py which manages game client instances,
accounts, and integrates with the scheduler.
"""
from __future__ import annotations

import asyncio
import json


def register(mcp) -> None:
    from core import _opener_http, _refresh_machines, audit_log, discord_notify

    # ------------------------------------------------------------------
    #  Discovery
    # ------------------------------------------------------------------

    @mcp.tool()
    async def opener_status(host: str = "") -> str:
        """查看單台機器的遊戲實例狀態 / List game instances on one machine."""
        return await _opener_http("GET", "/api/instances", host=host)

    @mcp.tool()
    async def opener_fleet_status() -> str:
        """全工作室實例總覽 / Aggregate all machines' opener status."""
        machines = await _refresh_machines(force=True)
        if not machines:
            return json.dumps({"error": "No machines discovered"})

        tasks = []
        hosts = []
        for m in machines.values():
            ip = m.get("ip", "")
            if ip:
                hosts.append(ip)
                tasks.append(_opener_http("GET", "/api/instances", host=ip))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_instances = []
        machine_summary = []
        for ip, result in zip(hosts, results):
            if isinstance(result, Exception):
                machine_summary.append({"host": ip, "status": "offline", "error": str(result)})
                continue
            try:
                data = json.loads(result)
                instances = data.get("data", [])
                if isinstance(instances, list):
                    for inst in instances:
                        inst["host"] = ip
                    all_instances.extend(instances)
                    machine_summary.append({
                        "host": ip, "status": "online",
                        "instances": len(instances),
                    })
                else:
                    machine_summary.append({"host": ip, "status": "online", "data": instances})
            except Exception as e:
                machine_summary.append({"host": ip, "status": "error", "error": str(e)})

        return json.dumps({
            "machines": len(machine_summary),
            "total_instances": len(all_instances),
            "machine_summary": machine_summary,
            "instances": all_instances,
        }, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    #  Account management
    # ------------------------------------------------------------------

    @mcp.tool()
    async def opener_accounts(host: str = "") -> str:
        """查看帳號清單 / List configured accounts on a machine."""
        return await _opener_http("GET", "/api/accounts", host=host)

    @mcp.tool()
    async def opener_add_account(
        username: str,
        password: str,
        server_page: int = 1,
        server_num: int = 1,
        char_slot: int = 0,
        country_code: str = "",
        phone: str = "",
        sms_api_url: str = "",
        mail_password: str = "",
        mail_domain: str = "",
        host: str = "",
    ) -> str:
        """新增帳號 / Add a new account to opener. 含裝置認證用欄位 (country_code, phone, sms_api_url)."""
        body = {
            "username": username,
            "password": password,
            "server_page": server_page,
            "server_num": server_num,
            "char_slot": char_slot,
        }
        if country_code: body["country_code"] = country_code
        if phone: body["phone"] = phone
        if sms_api_url: body["sms_api_url"] = sms_api_url
        if mail_password: body["mail_password"] = mail_password
        if mail_domain: body["mail_domain"] = mail_domain
        return await _opener_http("POST", "/api/accounts", body=body, host=host)

    # ------------------------------------------------------------------
    #  Instance control
    # ------------------------------------------------------------------

    @mcp.tool()
    async def opener_start(acc_id: str, host: str = "") -> str:
        """啟動單一帳號 / Start a game instance for an account."""
        result = await _opener_http("POST", f"/api/start/{acc_id}", host=host)
        audit_log("opener_start", {"acc_id": acc_id, "host": host})
        await discord_notify(f"啟動帳號 {acc_id} on {host or 'default'}", "info")
        return result

    @mcp.tool()
    async def opener_stop(acc_id: str, host: str = "") -> str:
        """停止單一帳號 / Stop a game instance."""
        result = await _opener_http("POST", f"/api/stop/{acc_id}", host=host)
        audit_log("opener_stop", {"acc_id": acc_id, "host": host})
        await discord_notify(f"停止帳號 {acc_id} on {host or 'default'}", "warn")
        return result

    @mcp.tool()
    async def opener_start_all(host: str = "") -> str:
        """啟動全部帳號 / Start all configured instances on a machine."""
        result = await _opener_http("POST", "/api/start_all", host=host)
        audit_log("opener_start_all", {"host": host})
        await discord_notify(f"全部啟動 on {host or 'default'}", "info")
        return result

    @mcp.tool()
    async def opener_stop_all(host: str = "") -> str:
        """停止全部帳號 / Stop all running instances on a machine."""
        result = await _opener_http("POST", "/api/stop_all", host=host)
        audit_log("opener_stop_all", {"host": host})
        await discord_notify(f"🛑 全部停止 on {host or 'default'}", "error")
        return result

    # ------------------------------------------------------------------
    #  Settings & info
    # ------------------------------------------------------------------

    @mcp.tool()
    async def opener_settings(host: str = "") -> str:
        """查看 opener 設定 / Get opener settings."""
        return await _opener_http("GET", "/api/settings", host=host)

    @mcp.tool()
    async def opener_auth(host: str = "") -> str:
        """查看授權狀態 / Get auth/license status."""
        return await _opener_http("GET", "/api/auth", host=host)

    @mcp.tool()
    async def opener_versions(host: str = "") -> str:
        """查看 DLL/腳本版本 / Get DLL and scripts versions."""
        return await _opener_http("GET", "/api/update/versions", host=host)

    @mcp.tool()
    async def opener_logs(host: str = "") -> str:
        """查看 opener 日誌 / Get recent opener logs."""
        return await _opener_http("GET", "/api/logs", host=host)

    # ------------------------------------------------------------------
    #  Data collection (Phase 0)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def opener_snapshots(
        port: int = 0, since: int = 0, limit: int = 50, host: str = "",
    ) -> str:
        """取得 5 分鐘績效快照 / Get periodic performance snapshots.

        Collected by opener's data_collector from DLL APIs every 5 minutes.
        Each snapshot has: kills_delta, gold_delta, deaths_delta, mobs_nearby,
        players_nearby, combat_state, nomob_ms.

        Args:
            port: DLL port (0=all bots on this machine)
            since: Unix timestamp, only return snapshots after this time
            limit: max records to return (default 50)
        """
        params = {"limit": str(limit)}
        if port:
            params["port"] = str(port)
        if since:
            params["since"] = str(since)
        return await _opener_http("GET", "/api/snapshots", params=params, host=host)

    @mcp.tool()
    async def opener_mob_spawns(min_count: int = 2, host: str = "") -> str:
        """取得怪物重生點統計 / Get mob spawn location statistics.

        Tracks where monsters first appear (spawn points).
        Accumulated over time by observing entity cache changes.

        Args:
            min_count: minimum sighting count to include (filter noise)
        """
        return await _opener_http("GET", "/api/mob_spawns",
                                  params={"min_count": str(min_count)}, host=host)
