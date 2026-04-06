"""
Lollipop MCP Hub — Shared state, config, and utilities for all routers.

This module is a leaf dependency: it imports only stdlib + httpx.
All routers import from here; nothing imports from routers.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Any

import httpx


# ---------------------------------------------------------------------------
# Audit logger — records every MCP tool call to daily JSONL file
# ---------------------------------------------------------------------------
AUDIT_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_logs")
os.makedirs(AUDIT_DIR, exist_ok=True)

def audit_log(tool: str, params: dict, result_summary: str = "", success: bool = True) -> None:
    """Append one audit record. Called by routers after each tool execution."""
    entry = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tool": tool,
        "params": {k: v for k, v in params.items() if k not in ("password",)},
        "ok": success,
        "summary": result_summary[:200],
    }
    date = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(AUDIT_DIR, f"audit_{date}.jsonl")
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Discord webhook — send alerts
# ---------------------------------------------------------------------------
DISCORD_WEBHOOK_URL: str = os.environ.get("LOLLIPOP_DISCORD_WEBHOOK", "")

async def discord_notify(message: str, level: str = "info") -> None:
    """Send a notification to Discord. Silently fails if no webhook configured."""
    if not DISCORD_WEBHOOK_URL:
        return
    emoji = {"info": "ℹ️", "warn": "⚠️", "error": "🚨", "ok": "✅"}.get(level, "📋")
    body = {"content": f"{emoji} **Lollipop** | {message}"}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(DISCORD_WEBHOOK_URL, json=body)
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Config from environment
# ---------------------------------------------------------------------------
SERVER_URL: str = os.environ.get("LOLLIPOP_SERVER_URL", "")
CARD_ID: str = os.environ.get("LOLLIPOP_CARD_ID", "")
DIRECT_IP: str = os.environ.get("LOLLIPOP_DIRECT", "")
TAILSCALE_API_KEY: str = os.environ.get("LOLLIPOP_TAILSCALE_KEY", "")

DLL_PORT_LO: int = 5577
DLL_PORT_HI: int = 5578
PROBE_TIMEOUT: float = 1.0
CACHE_TTL: float = 30.0
OPENER_PORT: int = 8600

# ---------------------------------------------------------------------------
# Machine & instance discovery cache
# ---------------------------------------------------------------------------
_machines: dict[str, dict] = {}
_machines_ts: float = 0
_instances: list[dict] = []
_instances_ts: float = 0


async def _refresh_machines(force: bool = False) -> dict[str, dict]:
    global _machines, _machines_ts
    if not force and _machines and (time.time() - _machines_ts) < CACHE_TTL:
        return _machines

    new_machines: dict[str, dict] = {}

    if DIRECT_IP:
        new_machines["direct"] = {"ip": DIRECT_IP, "char_name": "direct"}

    if TAILSCALE_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    "https://api.tailscale.com/api/v2/tailnet/-/devices?fields=default",
                    auth=(TAILSCALE_API_KEY, ""),
                )
                if r.status_code == 200:
                    devices = r.json().get("devices", [])
                    for dev in devices:
                        ips = dev.get("addresses", [])
                        ip4 = next((ip for ip in ips if "." in ip), "")
                        if not ip4:
                            continue
                        hostname = dev.get("hostname", ip4)
                        new_machines[hostname] = {
                            "ip": ip4,
                            "hostname": hostname,
                            "char_name": "",
                        }
        except Exception:
            pass
    elif SERVER_URL and CARD_ID:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{SERVER_URL}/api/stats/mcp/machines",
                    params={"cards": CARD_ID},
                )
                if r.status_code == 200:
                    items = r.json().get("machines", [])
                    for m in items:
                        ip = m.get("tailscale_ip", "")
                        if not ip:
                            continue
                        key = m.get("char_name") or m.get("machine_fingerprint", ip)
                        new_machines[key] = {
                            "ip": ip,
                            "port": m.get("ws_port", 5577),
                            "char_name": m.get("char_name", ""),
                            "level": m.get("level", 0),
                            "map": m.get("map_name", ""),
                            "server": m.get("server_name", ""),
                        }
        except Exception:
            if _machines:
                return _machines

    _machines = new_machines
    _machines_ts = time.time()
    return _machines


async def _scan_instances(host: str = "", force: bool = False) -> list[dict]:
    global _instances, _instances_ts
    if not force and _instances and (time.time() - _instances_ts) < CACHE_TTL:
        return _instances

    machines = await _refresh_machines(force)
    hosts_to_scan: list[str] = []

    if host:
        hosts_to_scan = [host]
    else:
        for m in machines.values():
            ip = m.get("ip", "")
            if ip:
                hosts_to_scan.append(ip)

    if not hosts_to_scan:
        hosts_to_scan = ["127.0.0.1"]

    all_instances: list[dict] = []

    async def probe(ip: str, port: int) -> dict | None:
        try:
            async with httpx.AsyncClient(timeout=PROBE_TIMEOUT) as client:
                r = await client.get(f"http://{ip}:{port}/ping")
                if r.status_code != 200:
                    return None
                data = r.json()
                if "pong" not in data:
                    return None
                info: dict[str, Any] = {
                    "host": ip,
                    "port": port,
                    "card": data.get("card", ""),
                    "bot": data.get("bot", 0),
                }
                try:
                    s = await client.get(f"http://{ip}:{port}/status")
                    if s.status_code == 200:
                        sd = s.json()
                        info["email"] = sd.get("email", "")
                        info["char_name"] = sd.get("char_name", "")
                        info["version"] = sd.get("version", "")
                        info["hp"] = sd.get("hp", -1)
                        info["max_hp"] = sd.get("max_hp", 0)
                        info["mp"] = sd.get("mp", -1)
                        info["max_mp"] = sd.get("max_mp", 0)
                        info["level"] = sd.get("level", 0)
                        info["class"] = sd.get("class_name", "")
                        info["logged_in"] = sd.get("logged_in", 0)
                except Exception:
                    pass
                return info
        except Exception:
            return None

    tasks = []
    for ip in hosts_to_scan:
        for p in range(DLL_PORT_LO, DLL_PORT_HI):
            tasks.append(probe(ip, p))

    results = await asyncio.gather(*tasks)
    all_instances = [r for r in results if r is not None]
    all_instances.sort(key=lambda x: (x["host"], x["port"]))

    _instances = all_instances
    _instances_ts = time.time()
    return all_instances


async def _resolve(port: int = 0, host: str = "") -> tuple[str, int]:
    instances = await _scan_instances()

    if host and port:
        return host, port

    filtered = instances
    if host:
        filtered = [i for i in instances if i["host"] == host]
    if port:
        filtered = [i for i in instances if i["port"] == port]
    if host and port:
        filtered = [i for i in instances if i["host"] == host and i["port"] == port]

    if len(filtered) == 1:
        return filtered[0]["host"], filtered[0]["port"]
    if len(filtered) == 0:
        return "", 0
    if not host and not port and len(instances) == 1:
        return instances[0]["host"], instances[0]["port"]
    return "", -1  # ambiguous


def _make_error(host: str, port: int) -> str | None:
    if port == -1:
        summary = [f"{i['host']}:{i['port']}" for i in _instances]
        return json.dumps({
            "error": f"Multiple bots online ({', '.join(summary)}). Specify host+port.",
            "bots": summary,
        }, ensure_ascii=False)
    if port == 0:
        return json.dumps({
            "error": "No bot instances found. Is the game running with DLL injected?"
        })
    return None


# ---------------------------------------------------------------------------
# HTTP transport to DLL (unified, no WS)
# ---------------------------------------------------------------------------

async def _http(
    port: int,
    method: str,
    path: str,
    params: dict | None = None,
    body: dict | None = None,
    timeout: float = 10,
    host: str = "",
) -> str:
    h, p = await _resolve(port, host)
    err = _make_error(h, p)
    if err:
        return err
    base = f"http://{h}:{p}"
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                http1=True,
                http2=False,
                default_encoding="utf-8",
            ) as client:
                hdrs = {"Connection": "close", "Accept-Encoding": "identity"}
                if method == "GET":
                    r = await client.get(f"{base}{path}", params=params, headers=hdrs)
                else:
                    raw = json.dumps(body or {}, ensure_ascii=False).encode("utf-8")
                    r = await client.post(
                        f"{base}{path}",
                        content=raw,
                        headers={**hdrs, "Content-Type": "application/json"},
                    )
                try:
                    data = r.json()
                except Exception:
                    data = r.text
                return json.dumps({"host": h, "port": p, "data": data},
                                  ensure_ascii=False, indent=2)
        except httpx.ConnectError:
            _instances.clear()
            globals()["_instances_ts"] = 0
            return json.dumps({"error": f"Connection lost to {base}"})
        except (httpx.ReadError, httpx.RemoteProtocolError) as e:
            last_err = e
            await asyncio.sleep(0.3)
            continue
        except Exception as e:
            return json.dumps({"error": f"{type(e).__name__}: {e}"})
    return json.dumps({"error": f"ReadError after 3 retries: {last_err}"})


# ---------------------------------------------------------------------------
# HTTP transport to opener.py (port 8600)
# ---------------------------------------------------------------------------

async def _resolve_opener_host(host: str = "") -> str:
    """Resolve host for opener.py. Falls back to DIRECT_IP or first machine."""
    if host:
        return host
    if DIRECT_IP:
        return DIRECT_IP
    machines = await _refresh_machines()
    for m in machines.values():
        ip = m.get("ip", "")
        if ip:
            return ip
    return ""


async def _opener_http(
    method: str,
    path: str,
    params: dict | None = None,
    body: dict | None = None,
    host: str = "",
    timeout: float = 10,
) -> str:
    """HTTP call to opener.py on OPENER_PORT (8600)."""
    ip = await _resolve_opener_host(host)
    if not ip:
        return json.dumps({"error": "No host. Set LOLLIPOP_DIRECT or configure machines."})
    base = f"http://{ip}:{OPENER_PORT}"
    try:
        async with httpx.AsyncClient(
            timeout=timeout, http1=True, http2=False,
            default_encoding="utf-8",
        ) as client:
            hdrs = {"Connection": "close", "Accept-Encoding": "identity"}
            if method == "GET":
                r = await client.get(f"{base}{path}", params=params, headers=hdrs)
            elif method == "DELETE":
                r = await client.delete(f"{base}{path}", headers=hdrs)
            elif method == "PUT":
                raw = json.dumps(body or {}, ensure_ascii=False).encode("utf-8")
                r = await client.put(
                    f"{base}{path}", content=raw,
                    headers={**hdrs, "Content-Type": "application/json"},
                )
            else:  # POST
                raw = json.dumps(body or {}, ensure_ascii=False).encode("utf-8")
                r = await client.post(
                    f"{base}{path}", content=raw,
                    headers={**hdrs, "Content-Type": "application/json"},
                )
            try:
                data = r.json()
            except Exception:
                data = r.text
            return json.dumps({"host": ip, "port": OPENER_PORT, "data": data},
                              ensure_ascii=False, indent=2)
    except httpx.ConnectError:
        return json.dumps({"error": f"Opener unreachable at {base}"})
    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {e}"})
