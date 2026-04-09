#!/usr/bin/env python3
"""
Lollipop Bot — MCP Hub (Mac-side, multi-machine)

Single MCP server that auto-discovers all machines via Lollipop server API,
then routes tool calls to each machine's DLL HTTP/WS API over Tailscale.

Setup:
  1. pip install "mcp[cli]>=1.26" httpx websockets
  2. Add to ~/.claude/settings.json or .mcp.json:
     {"mcpServers": {"lollipop": {
       "type": "stdio",
       "command": "python3",
       "args": ["/path/to/mcp_hub.py"],
       "env": {
         "LOLLIPOP_SERVER_URL": "https://your-server.com",
         "LOLLIPOP_CARD_ID": "your-card-id"
       }
     }}}

  Or for single-machine (no server):
     "env": {"LOLLIPOP_DIRECT": "192.168.0.114"}
"""

import asyncio
import json
import os
import sys
import time
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Config from environment
# ---------------------------------------------------------------------------
SERVER_URL = os.environ.get("LOLLIPOP_SERVER_URL", "")
CARD_ID = os.environ.get("LOLLIPOP_CARD_ID", "")
DIRECT_IP = os.environ.get("LOLLIPOP_DIRECT", "")  # single-machine mode

DLL_PORT_LO, DLL_PORT_HI = 5577, 5600
PROBE_TIMEOUT = 2.0  # remote over Tailscale, allow more time
CACHE_TTL = 30.0

# ---------------------------------------------------------------------------
# MCP Server (stdio transport)
# ---------------------------------------------------------------------------
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "lollipop-hub",
    instructions=(
        "Lollipop Bot MCP Hub — manages bots across multiple machines.\n"
        "Use bot_list() first to discover all online machines and bots.\n"
        "Most tools take a 'port' param (DLL port) and optional 'host' param (machine IP).\n"
        "If only one machine/bot is online, port/host auto-resolve."
    ),
)

# ---------------------------------------------------------------------------
# Machine & instance discovery
# ---------------------------------------------------------------------------
_machines: dict[str, dict] = {}  # key=char_name -> {ip, port, ...}
_machines_ts: float = 0
_instances: list[dict] = []  # flattened list of all bot instances
_instances_ts: float = 0


async def _refresh_machines(force: bool = False) -> dict[str, dict]:
    """Discover machines from Lollipop server API or direct IP."""
    global _machines, _machines_ts
    if not force and _machines and (time.time() - _machines_ts) < CACHE_TTL:
        return _machines

    new_machines: dict[str, dict] = {}

    if DIRECT_IP:
        # Single-machine mode: use direct IP
        new_machines["direct"] = {"ip": DIRECT_IP, "char_name": "direct"}
    elif SERVER_URL and CARD_ID:
        # Multi-machine mode: query server API
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{SERVER_URL}/api/liff/machines",
                    headers={"x-card-id": CARD_ID},
                )
                if r.status_code == 200:
                    data = r.json()
                    items = data if isinstance(data, list) else data.get("machines", [])
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
        except Exception as e:
            # Keep old cache on error
            if _machines:
                return _machines
            new_machines["error"] = {"ip": "", "error": str(e)}

    _machines = new_machines
    _machines_ts = time.time()
    return _machines


async def _scan_instances(host: str = "", force: bool = False) -> list[dict]:
    """Scan DLL ports on a specific host (or all machines)."""
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
            if ip and ip != "":
                hosts_to_scan.append(ip)

    if not hosts_to_scan:
        # Fallback: localhost
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
                info = {
                    "host": ip,
                    "port": port,
                    "card": data.get("card", ""),
                    "bot": data.get("bot", 0),
                }
                # Enrich with /status
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
    """Resolve host+port. Auto-select if only 1 instance."""
    instances = await _scan_instances()

    if host and port:
        return host, port

    # Filter by host if specified
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
    # Multiple — if no filter, try auto
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
# HTTP / WS transport to remote DLL
# ---------------------------------------------------------------------------

async def _http(port: int, method: str, path: str,
                params: dict | None = None, body: dict | None = None,
                timeout: float = 10, host: str = "") -> str:
    h, p = await _resolve(port, host)
    err = _make_error(h, p)
    if err:
        return err
    base = f"http://{h}:{p}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            if method == "GET":
                r = await client.get(f"{base}{path}", params=params)
            else:
                r = await client.post(f"{base}{path}", json=body or {})
            try:
                data = r.json()
            except Exception:
                data = r.text
            return json.dumps({"host": h, "port": p, "data": data},
                              ensure_ascii=False, indent=2)
    except httpx.ConnectError:
        global _instances, _instances_ts
        _instances = []
        _instances_ts = 0
        return json.dumps({"error": f"Connection lost to {base}"})
    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {e}"})


async def _ws(port: int, cmd_data: dict, timeout: float = 10,
              host: str = "") -> str:
    h, p = await _resolve(port, host)
    err = _make_error(h, p)
    if err:
        return err
    uri = f"ws://{h}:{p}"
    try:
        import websockets
        async with websockets.connect(uri, open_timeout=5, close_timeout=2) as ws:
            await ws.send(json.dumps(cmd_data, ensure_ascii=False))
            deadline = time.time() + timeout
            while True:
                remaining = deadline - time.time()
                if remaining <= 0:
                    return json.dumps({"error": "Timeout waiting for WS response"})
                try:
                    resp = await asyncio.wait_for(ws.recv(), timeout=remaining)
                except asyncio.TimeoutError:
                    return json.dumps({"error": "Timeout waiting for WS response"})
                try:
                    data = json.loads(resp)
                except Exception:
                    return json.dumps({"host": h, "port": p, "data": resp},
                                      ensure_ascii=False, indent=2)
                if isinstance(data, dict) and data.get("event") in ("connected", "push"):
                    continue
                return json.dumps({"host": h, "port": p, "data": data},
                                  ensure_ascii=False, indent=2)
    except ImportError:
        return json.dumps({"error": "pip install websockets"})
    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {e}"})


# ═══════════════════════════════════════════════════════════════════════════
#  Discovery (2)
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_list() -> str:
    """Scan ALL active bot instances across all machines.
    Returns [{host, port, char_name, email, hp, level, class, bot}].
    Call this FIRST to see what's online."""
    instances = await _scan_instances(force=True)
    return json.dumps({
        "machines": len(set(i["host"] for i in instances)),
        "instances_online": len(instances),
        "instances": instances,
    }, ensure_ascii=False, indent=2)

@mcp.tool()
async def machine_list() -> str:
    """List discovered machines from server API (no port scan, faster)."""
    machines = await _refresh_machines(force=True)
    return json.dumps({
        "count": len(machines),
        "machines": [{"key": k, **{kk: vv for kk, vv in v.items() if kk != "error"}}
                     for k, v in machines.items()],
    }, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
#  Query Tools
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_status(port: int = 0, host: str = "") -> str:
    """Full status: version, hp/mp, level, class, bot state, scan, entity cache."""
    return await _http(port, "GET", "/status", host=host)


@mcp.tool()
async def bot_position(port: int = 0, host: str = "") -> str:
    """Current character position (x, y)."""
    return await _http(port, "GET", "/position", host=host)


@mcp.tool()
async def bot_entities(port: int = 0, host: str = "") -> str:
    """Nearby entities: {type, id, x, y, name, dist, dead, move}."""
    return await _http(port, "GET", "/entities", host=host)


@mcp.tool()
async def bot_inventory(port: int = 0, host: str = "") -> str:
    """Inventory items: {uid, rid, name, qty, bless}."""
    return await _http(port, "GET", "/inventory", host=host)


@mcp.tool()
async def bot_buffs(port: int = 0, host: str = "") -> str:
    """Active buffs."""
    return await _http(port, "GET", "/buffs", host=host)


@mcp.tool()
async def bot_logs(port: int = 0, host: str = "", level: str = "",
                   since_seq: int = -1) -> str:
    """Bot logs. level='S'/'D', since_seq=N for incremental."""
    params: dict = {}
    if level:
        params["level"] = level
    if since_seq >= 0:
        params["since"] = str(since_seq)
    return await _http(port, "GET", "/logs", params=params, host=host)


@mcp.tool()
async def bot_scan(port: int = 0, host: str = "") -> str:
    """Pattern scanner results + subsystem addresses."""
    return await _http(port, "GET", "/scan", host=host)


@mcp.tool()
async def bot_uitree(port: int = 0, host: str = "") -> str:
    """UI widget tree (3 levels deep)."""
    return await _http(port, "GET", "/uitree", host=host)


@mcp.tool()
async def bot_shoplist(port: int = 0, host: str = "") -> str:
    """NPC shop items (shop must be open)."""
    return await _http(port, "GET", "/shop_list", host=host)


@mcp.tool()
async def bot_pathfind(sx: int, sy: int, ex: int, ey: int,
                       port: int = 0, host: str = "") -> str:
    """A* path between two world coords. Returns waypoints."""
    return await _http(port, "GET", "/pathfind",
                       params={"sx": sx, "sy": sy, "ex": ex, "ey": ey}, host=host)


@mcp.tool()
async def bot_los(x1: int, y1: int, x2: int, y2: int,
                  port: int = 0, host: str = "") -> str:
    """Line-of-sight check between two points."""
    return await _http(port, "GET", "/los",
                       params={"x1": x1, "y1": y1, "x2": x2, "y2": y2}, host=host)


@mcp.tool()
async def bot_map_grid(port: int = 0, host: str = "") -> str:
    """Map grid info: dimensions, walkability, origin."""
    return await _http(port, "GET", "/map_grid", host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  WS Query Tools
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_combat_state(port: int = 0, host: str = "") -> str:
    """Combat state machine: phase, target, timing, blacklist, kills."""
    return await _ws(port, {"cmd": "combat_state"}, host=host)


@mcp.tool()
async def bot_config_get(port: int = 0, host: str = "") -> str:
    """ALL config fields as JSON."""
    return await _ws(port, {"cmd": "config_get"}, host=host)


@mcp.tool()
async def bot_spells(port: int = 0, host: str = "") -> str:
    """Available spells: {skill_id, name}."""
    return await _ws(port, {"cmd": "spells"}, host=host)


@mcp.tool()
async def bot_supply_state(port: int = 0, host: str = "") -> str:
    """Supply module detailed state."""
    return await _ws(port, {"cmd": "supply_state"}, host=host)


@mcp.tool()
async def bot_search_names(keyword: str, port: int = 0, host: str = "") -> str:
    """Search game name index by keyword."""
    return await _ws(port, {"cmd": "search_names", "keyword": keyword}, host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Action Tools
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_walk(x: int, y: int, port: int = 0, host: str = "") -> str:
    """Walk one step toward (x,y)."""
    return await _http(port, "POST", "/walk", body={"x": x, "y": y}, host=host)


@mcp.tool()
async def bot_smartmove(x: int, y: int, port: int = 0, host: str = "") -> str:
    """A* auto-walk to (x,y)."""
    return await _http(port, "POST", "/smartmove", body={"x": x, "y": y}, host=host)


@mcp.tool()
async def bot_attack(entity_id: int, port: int = 0, host: str = "") -> str:
    """Attack entity by ID."""
    return await _http(port, "POST", "/attack", body={"entity_id": entity_id}, host=host)


@mcp.tool()
async def bot_pickup(entity_id: int, qty: int = 1,
                     port: int = 0, host: str = "") -> str:
    """Pick up ground item by entity ID."""
    return await _http(port, "POST", "/pickup",
                       body={"entity_id": entity_id, "qty": qty}, host=host)


@mcp.tool()
async def bot_cast(skill_id: int, port: int = 0, host: str = "") -> str:
    """Cast spell by skill_id."""
    return await _http(port, "POST", "/cast", body={"skill_id": skill_id}, host=host)


@mcp.tool()
async def bot_useitem(item_uid: int, port: int = 0, host: str = "") -> str:
    """Use inventory item by uid."""
    return await _http(port, "POST", "/useitem", body={"item_uid": item_uid}, host=host)


@mcp.tool()
async def bot_teleport(item_uid: int, bookmark_id: int = 0,
                       map_id: int = 0, x: int = 0, y: int = 0,
                       port: int = 0, host: str = "") -> str:
    """Teleport via blessed scroll. Provide bookmark_id OR (map_id+x+y)."""
    body: dict = {"item_uid": item_uid}
    if bookmark_id:
        body["bookmark_id"] = bookmark_id
    if map_id:
        body["map_id"] = map_id
        body["x"] = x
        body["y"] = y
    return await _http(port, "POST", "/teleport", body=body, timeout=15, host=host)


@mcp.tool()
async def bot_interact(entity_addr: str, port: int = 0, host: str = "") -> str:
    """Interact with NPC/object by hex addr."""
    return await _http(port, "POST", "/interact",
                       body={"entity_addr": entity_addr}, host=host)


@mcp.tool()
async def bot_click(dialog: str = "", widget: str = "", addr: str = "",
                    port: int = 0, host: str = "") -> str:
    """Click UI widget by dialog+widget name, or by hex addr."""
    body: dict = {}
    if dialog:
        body["dialog"] = dialog
    if widget:
        body["widget"] = widget
    if addr:
        body["addr"] = addr
    return await _http(port, "POST", "/click", body=body, host=host)



@mcp.tool()
async def bot_navpath(x: int, y: int, port: int = 0, host: str = "") -> str:
    """Get A* waypoints to (x,y) without walking."""
    return await _http(port, "POST", "/navpath", body={"x": x, "y": y}, host=host)


@mcp.tool()
async def bot_pledge_join(name: str, password: str = "",
                          port: int = 0, host: str = "") -> str:
    """Join blood pledge by name."""
    body: dict = {"name": name}
    if password:
        body["password"] = password
    return await _http(port, "POST", "/pledge_join", body=body, host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Bot Control
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_start(port: int = 0, host: str = "") -> str:
    """Start bot automation."""
    return await _ws(port, {"cmd": "bot_start"}, host=host)


@mcp.tool()
async def bot_stop(port: int = 0, host: str = "") -> str:
    """Stop bot."""
    return await _ws(port, {"cmd": "bot_stop"}, host=host)


@mcp.tool()
async def bot_config_set(fields: str = "{}", port: int = 0,
                         host: str = "") -> str:
    """Update config. fields=JSON e.g. '{"combat_radius":15}'."""
    cmd: dict = {"cmd": "config_set"}
    try:
        extra = json.loads(fields)
        if isinstance(extra, dict):
            cmd.update(extra)
    except Exception:
        return json.dumps({"error": "Invalid JSON in fields"})
    return await _ws(port, cmd, host=host)


@mcp.tool()
async def bot_config_reset(port: int = 0, host: str = "") -> str:
    """Reset config to defaults."""
    return await _ws(port, {"cmd": "config_reset"}, host=host)


@mcp.tool()
async def bot_rescan(port: int = 0, host: str = "") -> str:
    """Force rescan patterns + RTTI."""
    return await _http(port, "POST", "/rescan", host=host)


@mcp.tool()
async def bot_daytime(on: int = 1, port: int = 0, host: str = "") -> str:
    """Force-daytime (1=on, 0=off)."""
    return await _ws(port, {"cmd": "daytime", "on": on}, host=host)


@mcp.tool()
async def bot_stats_reset(port: int = 0, host: str = "") -> str:
    """Reset kill/gold stats."""
    return await _ws(port, {"cmd": "stats_reset"}, host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Player & Stats
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_player(port: int = 0, host: str = "") -> str:
    """Detailed player info: name, class, stats, weight, food, align."""
    return await _http(port, "GET", "/player", host=host)


@mcp.tool()
async def bot_stats(port: int = 0, host: str = "") -> str:
    """Bot farming stats: kills, loots, deaths, gold, uptime."""
    return await _http(port, "GET", "/stats", host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Target & NPC
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_target(port: int = 0, host: str = "") -> str:
    """Get current selected target info."""
    return await _http(port, "GET", "/target", host=host)



@mcp.tool()
async def bot_npc_click(dialog: str = "", keyword: str = "", nth: int = 1,
                        port: int = 0, host: str = "") -> str:
    """Click item in UI dialog list by keyword match. dialog=layout name, keyword=text to find."""
    body: dict = {}
    if dialog:
        body["dialog"] = dialog
    if keyword:
        body["keyword"] = keyword
    if nth != 1:
        body["nth"] = nth
    return await _http(port, "POST", "/npc_click", body=body, host=host)


@mcp.tool()
async def bot_dialogs(port: int = 0, host: str = "") -> str:
    """List open dialog windows."""
    return await _http(port, "GET", "/dialogs", host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Scroll & Teleport
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_scroll_list(port: int = 0, host: str = "") -> str:
    """List teleport scrolls in inventory."""
    return await _http(port, "GET", "/scroll_list", host=host)


@mcp.tool()
async def bot_scroll_show(item_uid: int, port: int = 0, host: str = "") -> str:
    """Show scroll destination picker UI."""
    return await _ws(port, {"cmd": "scroll_show", "item_uid": item_uid}, host=host)


@mcp.tool()
async def bot_scroll_dest(port: int = 0, host: str = "") -> str:
    """Get scroll destination list (after scroll_show)."""
    return await _http(port, "GET", "/scroll_dest", host=host)


@mcp.tool()
async def bot_usescroll(item_uid: int, dest: str = "",
                        port: int = 0, host: str = "") -> str:
    """Use teleport scroll to destination."""
    body: dict = {"item_uid": item_uid}
    if dest:
        body["dest"] = dest
    return await _http(port, "POST", "/usescroll", body=body, host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Party (組隊)
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def bot_party_members(port: int = 0, host: str = "") -> str:
    """List party members with HP/MP/position."""
    return await _ws(port, {"cmd": "party_members"}, host=host)


@mcp.tool()
async def bot_party_status(port: int = 0, host: str = "") -> str:
    """Party system status: mode, squad, master."""
    return await _ws(port, {"cmd": "party_status"}, host=host)


@mcp.tool()
async def bot_party_config_get(port: int = 0, host: str = "") -> str:
    """Get party config (heal/buff/attack settings)."""
    return await _ws(port, {"cmd": "party_config_get"}, host=host)


@mcp.tool()
async def bot_party_config_set(fields: str = "{}", port: int = 0,
                                host: str = "") -> str:
    """Set party config. fields=JSON."""
    cmd: dict = {"cmd": "party_config_set"}
    try:
        extra = json.loads(fields)
        if isinstance(extra, dict):
            cmd.update(extra)
    except Exception:
        return json.dumps({"error": "Invalid JSON in fields"})
    return await _ws(port, cmd, host=host)


@mcp.tool()
async def bot_party_mode(mode: str, port: int = 0, host: str = "") -> str:
    """Set party mode: follow|grind|rest|return|idle."""
    return await _ws(port, {"cmd": "party_mode", "mode": mode}, host=host)


@mcp.tool()
async def bot_party_follow(port: int = 0, host: str = "") -> str:
    """Switch party to follow mode."""
    return await _ws(port, {"cmd": "party_follow"}, host=host)


@mcp.tool()
async def bot_party_stop(port: int = 0, host: str = "") -> str:
    """Stop party control."""
    return await _ws(port, {"cmd": "party_stop"}, host=host)


@mcp.tool()
async def bot_party_attack(name: str = "", x: int = 0, y: int = 0,
                           port: int = 0, host: str = "") -> str:
    """Command party to attack target by name/position."""
    return await _ws(port, {"cmd": "party_attack", "name": name, "x": x, "y": y}, host=host)


@mcp.tool()
async def bot_party_focus(name: str, port: int = 0, host: str = "") -> str:
    """Set party focus target."""
    return await _ws(port, {"cmd": "party_focus", "name": name}, host=host)


@mcp.tool()
async def bot_party_heal(target: str, port: int = 0, host: str = "") -> str:
    """Manual party heal on target name."""
    return await _ws(port, {"cmd": "party_heal", "target": target}, host=host)


@mcp.tool()
async def bot_party_cast(skill_id: int, target: str = "",
                         port: int = 0, host: str = "") -> str:
    """Cast party skill on target."""
    return await _ws(port, {"cmd": "party_cast", "skill_id": skill_id, "target": target}, host=host)


@mcp.tool()
async def bot_party_teleport(port: int = 0, host: str = "") -> str:
    """Trigger party teleport."""
    return await _ws(port, {"cmd": "party_teleport"}, host=host)


@mcp.tool()
async def bot_party_sync(port: int = 0, host: str = "") -> str:
    """Sync party config to all members."""
    return await _ws(port, {"cmd": "party_sync"}, host=host)


@mcp.tool()
async def bot_party_free_attack(enabled: int = 1, port: int = 0,
                                host: str = "") -> str:
    """Toggle free attack mode (1=on, 0=off)."""
    return await _ws(port, {"cmd": "party_free_attack", "enabled": enabled}, host=host)


@mcp.tool()
async def bot_party_moveto(x: int, y: int, port: int = 0, host: str = "") -> str:
    """Move party to position."""
    return await _ws(port, {"cmd": "party_moveto", "x": x, "y": y}, host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Navigation Scripts
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_nav_exec(script_id: str = "", port: int = 0, host: str = "") -> str:
    """Execute navigation script by ID."""
    return await _ws(port, {"cmd": "nav_exec", "script_id": script_id}, host=host)


@mcp.tool()
async def bot_nav_stop(port: int = 0, host: str = "") -> str:
    """Stop current navigation."""
    return await _ws(port, {"cmd": "nav_stop"}, host=host)


@mcp.tool()
async def bot_nav_scripts(port: int = 0, host: str = "") -> str:
    """List saved navigation scripts."""
    return await _http(port, "GET", "/api/nav_scripts", host=host)


@mcp.tool()
async def bot_nav_upload(name: str, waypoints: str, port: int = 0,
                         host: str = "") -> str:
    """Upload navigation script. waypoints=JSON array of {x,y,action}."""
    return await _http(port, "POST", "/api/nav_upload",
                       body={"name": name, "waypoints": waypoints}, host=host)


@mcp.tool()
async def bot_portal_db(port: int = 0, host: str = "") -> str:
    """Get portal/teleport database."""
    return await _http(port, "GET", "/api/portal_db", host=host)


@mcp.tool()
async def bot_nav_return_confirm(port: int = 0, host: str = "") -> str:
    """Confirm nav return dialog."""
    return await _ws(port, {"cmd": "nav_return_confirm"}, host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Supply & Warehouse Triggers
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_shop_buy(item_name: str, qty: int = 1, port: int = 0, host: str = "") -> str:
    """Buy item from open NPC shop. Shop must be open (NpcShopLayout visible)."""
    return await _ws(port, {"cmd": "shop_buy", "item_name": item_name, "qty": qty}, host=host)

@mcp.tool()
async def bot_supply_trigger(port: int = 0, host: str = "") -> str:
    """Manually trigger supply run (buy arrows/potions)."""
    return await _ws(port, {"cmd": "supply_test"}, host=host)


@mcp.tool()
async def bot_wh_trigger(port: int = 0, host: str = "") -> str:
    """Manually trigger warehouse run."""
    return await _ws(port, {"cmd": "wh_trigger"}, host=host)


@mcp.tool()
async def bot_sell_npcs_get(port: int = 0, host: str = "") -> str:
    """Get configured sell NPC list."""
    return await _ws(port, {"cmd": "sell_npcs_get"}, host=host)


@mcp.tool()
async def bot_sell_npcs_set(npcs: str, port: int = 0, host: str = "") -> str:
    """Set sell NPC list. npcs=JSON array."""
    cmd: dict = {"cmd": "sell_npcs_set"}
    try:
        cmd["npcs"] = json.loads(npcs)
    except Exception:
        return json.dumps({"error": "Invalid JSON"})
    return await _ws(port, cmd, host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Profile Management
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_profile_list(port: int = 0, host: str = "") -> str:
    """List saved config profiles."""
    return await _ws(port, {"cmd": "profile_list"}, host=host)


@mcp.tool()
async def bot_profile_load(name: str, port: int = 0, host: str = "") -> str:
    """Load config profile by name."""
    return await _ws(port, {"cmd": "profile_load", "name": name}, host=host)


@mcp.tool()
async def bot_profile_delete(name: str, port: int = 0, host: str = "") -> str:
    """Delete config profile."""
    return await _ws(port, {"cmd": "profile_delete", "name": name}, host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Login & Auth
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_auto_login(port: int = 0, host: str = "") -> str:
    """Trigger auto-login sequence."""
    return await _ws(port, {"cmd": "auto_login"}, host=host)


@mcp.tool()
async def bot_auth_status(port: int = 0, host: str = "") -> str:
    """Get auth/license status."""
    return await _http(port, "GET", "/auth/status", host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Input Simulation (GLFW)
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_glfw_click(x: int, y: int, port: int = 0, host: str = "") -> str:
    """Simulate mouse click at game client coords (x,y)."""
    return await _http(port, "POST", "/glfw_click", body={"x": x, "y": y}, host=host)


@mcp.tool()
async def bot_glfw_key(key: int, port: int = 0, host: str = "") -> str:
    """Simulate key press (GLFW key code)."""
    return await _ws(port, {"cmd": "glfw_key", "key": key}, host=host)



# ═══════════════════════════════════════════════════════════════════════════
#  UI & Debug
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def bot_minimap(port: int = 0, host: str = "") -> str:
    """Minimap info."""
    return await _http(port, "GET", "/minimap", host=host)



@mcp.tool()
async def bot_log_level(level: str = "", port: int = 0, host: str = "") -> str:
    """Get/set log level. level='S'(important),'D'(debug)."""
    if level:
        return await _ws(port, {"cmd": "log_level", "level": level}, host=host)
    return await _http(port, "GET", "/log_level", host=host)



@mcp.tool()
async def bot_screenshot(port: int = 0, host: str = "") -> str:
    """Take game window screenshot (BMP, base64)."""
    return await _http(port, "GET", "/screenshot", host=host, timeout=15)


# ═══════════════════════════════════════════════════════════════════════════
#  Bookmarks (detailed)
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_bookmarks(port: int = 0, host: str = "") -> str:
    """Detailed bookmark list with addresses."""
    return await _http(port, "GET", "/bm_list", host=host)


@mcp.tool()
async def bot_bm_scan(port: int = 0, host: str = "") -> str:
    """Scan/refresh bookmarks from memory."""
    return await _http(port, "GET", "/bm_scan", host=host)


@mcp.tool()
async def bot_bm_click(idx: int, port: int = 0, host: str = "") -> str:
    """Click bookmark by index."""
    return await _http(port, "POST", "/bm_click", body={"idx": idx}, host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Update & System
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_update_check(port: int = 0, host: str = "") -> str:
    """Check for DLL updates."""
    return await _ws(port, {"cmd": "update_check"}, host=host)


@mcp.tool()
async def bot_update_download(port: int = 0, host: str = "") -> str:
    """Download pending DLL update."""
    return await _ws(port, {"cmd": "update_download"}, host=host)





# ═══════════════════════════════════════════════════════════════════════════
#  Reverse Engineering / Development (via generic dll_http/dll_ws)
#  These endpoints were removed from DLL to reduce binary size but
#  can be accessed via dll_http() if restored. Listed here for reference:
#    /rtti_all, /rtti_scan, /rtti_vtable — RTTI analysis
#    /disasm — disassembly at RVA
#    /memsearch — memory pattern search
#    /probe_entity — deep entity field probe
#    /target_scan — entity target scanner
#    /nametable, /resolve, /resolve_ex, /names — name resolution
#    /deep_comp, /find_comp — component analysis
# ═══════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════
#  Batch Operations (all instances across all machines)
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_all_status() -> str:
    """Status of ALL online instances across all machines."""
    instances = await _scan_instances(force=True)
    return json.dumps({
        "machines": len(set(i["host"] for i in instances)),
        "count": len(instances),
        "instances": instances,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def bot_all_start() -> str:
    """Start ALL online bots not already running."""
    instances = await _scan_instances(force=True)
    results = []
    for inst in instances:
        if inst.get("bot", 0):
            results.append({"host": inst["host"], "port": inst["port"],
                           "result": "already running"})
            continue
        try:
            r = await _ws(inst["port"], {"cmd": "bot_start"}, host=inst["host"])
            data = json.loads(r)
            results.append({"host": inst["host"], "port": inst["port"],
                           "result": data.get("data", {}).get("status", "unknown")})
        except Exception as e:
            results.append({"host": inst["host"], "port": inst["port"],
                           "result": f"error: {e}"})
    return json.dumps({"started": len(results), "results": results},
                      ensure_ascii=False, indent=2)


@mcp.tool()
async def bot_all_stop() -> str:
    """Stop ALL running bots."""
    instances = await _scan_instances(force=True)
    results = []
    for inst in instances:
        if not inst.get("bot", 0):
            results.append({"host": inst["host"], "port": inst["port"],
                           "result": "not running"})
            continue
        try:
            r = await _ws(inst["port"], {"cmd": "bot_stop"}, host=inst["host"])
            data = json.loads(r)
            results.append({"host": inst["host"], "port": inst["port"],
                           "result": data.get("data", {}).get("status", "unknown")})
        except Exception as e:
            results.append({"host": inst["host"], "port": inst["port"],
                           "result": f"error: {e}"})
    return json.dumps({"stopped": len(results), "results": results},
                      ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
#  Escape Hatch (generic HTTP/WS to any DLL)
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def dll_http(method: str, path: str, body: str = "",
                   port: int = 0, host: str = "") -> str:
    """Generic HTTP call to DLL. method=GET|POST, path=/endpoint."""
    parsed = json.loads(body) if body else None
    return await _http(port, method.upper(), path, body=parsed, host=host)


@mcp.tool()
async def dll_ws(cmd: str, params: str = "{}",
                 port: int = 0, host: str = "") -> str:
    """Generic WS command to DLL. cmd=command_name, params=JSON."""
    data = {"cmd": cmd}
    try:
        extra = json.loads(params)
        if isinstance(extra, dict):
            data.update(extra)
    except Exception:
        pass
    return await _ws(port, data, host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    mcp.run(transport="stdio")
