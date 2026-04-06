#!/usr/bin/env python3
"""
Lollipop Bot — MCP Hub v2 (HTTP-only)

All tools use HTTP transport. No WebSocket dependency.

Setup:
  pip install "mcp[cli]>=1.26" httpx
  Add to .mcp.json:
    {"mcpServers": {"lollipop": {
      "type": "stdio",
      "command": "python3",
      "args": ["/path/to/mcp_hub_v2.py"],
      "env": {"LOLLIPOP_DIRECT": "192.168.0.114"}
    }}}
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Config from environment
# ---------------------------------------------------------------------------
SERVER_URL: str = os.environ.get("LOLLIPOP_SERVER_URL", "")
CARD_ID: str = os.environ.get("LOLLIPOP_CARD_ID", "")  # supports comma-separated: "CARD1,CARD2"
DIRECT_IP: str = os.environ.get("LOLLIPOP_DIRECT", "")
TAILSCALE_API_KEY: str = os.environ.get("LOLLIPOP_TAILSCALE_KEY", "")

DLL_PORT_LO: int = 5577
DLL_PORT_HI: int = 5578  # Only scan 5577 (was 5600, caused 23 probes per machine)
PROBE_TIMEOUT: float = 1.0  # Was 2.0, faster timeout for unreachable machines
CACHE_TTL: float = 30.0

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "lollipop-hub",
    instructions="""\
Lollipop Bot MCP Hub -- manages bots across multiple machines.
Use bot_list() first to discover all online machines and bots.
Most tools take a 'port' param (DLL port) and optional 'host' param (machine IP).
If only one machine/bot is online, port/host auto-resolve.

## 遊戲資料參考

### 說話的卷軸 (F12) 目的地 — 依職業分類

卷軸目的地格式: "村莊|傳送點"，例如 "說話之島|雜貨商人"
使用前必須 bot_status 確認 class_name，不同職業可用的村莊不同。

**通用（無職業/未知）:**
- 說話之島: 旅館,倉庫管理員,傳送師,雜貨商人,妖魔族商人,魔法書商人,說話之島地監入口,北島
- 古魯丁村: 旅館,倉庫管理員,傳送師,雜貨商人,史萊姆競賽場,古魯丁地監入口
- 奇岩村: 倉庫管理員,傳送師,雜貨商人,武器商人,防具商人,藥水商人,奇岩地監入口,龍之谷入口,龍之谷地監入口
- 共同: 正義神殿,邪惡神殿,沙漠綠洲,沙漠地監入口,祝福之地

**妖精 (class_name含"妖精"):**
- 妖精森林村: 倉庫管理員,世界樹,精靈魔法,眠龍洞穴入口 (專屬)
- 燃柳村: 倉庫管理員,雜貨商人,寵物管理人 (專屬)
- 說話之島: 旅館,倉庫管理員,雜貨商人,妖魔族商人,魔法書商人,寵物管理人,無界擂台,說話之島港口,稻草人修練場,說話之島地監入口,北島,中央獵場,東邊獵場
- 古魯丁村: 旅館,倉庫管理員,雜貨商人,無界擂台,史萊姆競賽場,古魯丁地監入口,遠古戰場,葡萄田,食屍地
- 奇岩村: 倉庫管理員,雜貨商人,武器商人,防具商人,藥水商人,鐵匠,魔法煉金術師,神女,無界擂台,奇岩地監入口
- 共同: 15級任務,30級任務,正義神殿,邪惡神殿,沙漠綠洲,沙漠地監入口,祝福之地,妖魔森林高梁田,風木城北邊獵場,龍之谷入口,龍之谷地監入口

**魔法師:** 同妖精但沒有妖精森林村

**騎士 (class_name含"騎士"):**
- 銀騎士村: 旅館,倉庫管理員,稻草人修練場,雜貨商人,武器防具商人,傑瑞德,無界擂台 (專屬)
- 其餘同妖精但沒有妖精森林村和燃柳村

**王族 (class_name含"王族"):**
- 肯特村: 倉庫管理員,雜貨商人,寵物管理人 (專屬)
- 風木村: 旅館,倉庫管理員,雜貨商人,寵物管理人 (專屬)
- 其餘同妖精但沒有妖精森林村和燃柳村

### 村莊 NPC 對照

| 村莊 | 雜貨商人 | 其他商人 | 傳送師 |
| 說話之島村 | 潘朵拉 | 馬修 | 盧卡斯(32580,32929) |
| 古魯丁村 | 露西 | 凱蒂 | 史提夫(32611,32732) |
| 奇岩村 | 邁爾 | 溫諾(武器),范吉爾(防具) | 爾瑪(33437,32798) |
| 燃柳村 | 傑克森 | — | — |

### 關鍵地標座標

- 說話之島地監入口: (32478, 32851)
- 稻草人修練場: (32525, 32832)
- 古魯丁地監入口: (32728, 32929)
- 奇岩地監入口: (33311, 33061)
- 沙漠綠洲: (32860, 33253)
- 龍之谷入口: (33239, 32453)
- 螞蟻洞窟入口: (32911, 33223)

### 祝福卷軸 (F11)
F11 開啟 BookmarkLayout，選擇已存書籤傳送。用 bot_bookmarks 查書籤列表，bot_bm_click(idx) 傳送。

### 返回卷軸
直接 bot_useitem(uid) 使用，回到最近的村莊。

### NPC 互動注意
- NPC 只要在 entities 列表（畫面可見）就能 interact，不用走到旁邊
- 傳送到「雜貨商人」會直接出現在商人旁邊
- shop_buy 的 qty 是點擊次數，每次+10，所以 qty=20 = 買200個

### Skill 建立注意
- 傳送前先 bot_status 確認職業，選對應的目的地表
- F12=GLFW key 301 (說話的卷軸), F11=GLFW key 300 (祝福卷軸), F10=GLFW key 299 (變身)
- 傳送後等 3-5 秒 (sleep 3000-5000)
- walk 每步間隔 800ms
- interact 後等 1000ms 再點按鈕
- shop_buy 前要先點 Bt_Npc_Buy
""",
)

# ---------------------------------------------------------------------------
# Machine & instance discovery
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
        # Discover all Tailscale devices, extract IPv4 addresses
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
                            "char_name": "",  # filled by port scan
                        }
        except Exception:
            pass
    elif SERVER_URL and CARD_ID:
        # Fallback: query server for known machines by card numbers
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
# HTTP transport (unified, no WS)
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
                # Minimal headers for DLL compatibility (no gzip, no keep-alive)
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
#  Query Tools (12)
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
#  Action Tools (12)
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_walk(x: int, y: int, port: int = 0, host: str = "") -> str:
    """Walk one step toward (x,y)."""
    return await _http(port, "POST", "/bot/walk", body={"x": x, "y": y}, host=host)


@mcp.tool()
async def bot_smartmove(x: int, y: int, port: int = 0, host: str = "") -> str:
    """A* auto-walk to (x,y)."""
    return await _http(port, "POST", "/bot/smartmove", body={"x": x, "y": y}, host=host)


@mcp.tool()
async def bot_attack(entity_id: int, port: int = 0, host: str = "") -> str:
    """Attack entity by ID."""
    return await _http(port, "POST", "/bot/attack", body={"entity_id": entity_id}, host=host)


@mcp.tool()
async def bot_pickup(entity_id: int, qty: int = 1,
                     port: int = 0, host: str = "") -> str:
    """Pick up ground item by entity ID."""
    return await _http(port, "POST", "/bot/pickup",
                       body={"entity_id": entity_id, "qty": qty}, host=host)




@mcp.tool()
async def bot_cast(skill_id: int, port: int = 0, host: str = "") -> str:
    """Cast spell by skill_id."""
    return await _http(port, "POST", "/bot/cast", body={"skill_id": skill_id}, host=host)


@mcp.tool()
async def bot_useitem(item_uid: int, port: int = 0, host: str = "") -> str:
    """Use inventory item by uid."""
    return await _http(port, "POST", "/bot/useitem", body={"item_uid": item_uid}, host=host)


@mcp.tool()
async def bot_interact(entity_addr: str, port: int = 0, host: str = "") -> str:
    """Interact with NPC/object by hex addr."""
    return await _http(port, "POST", "/bot/interact",
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
    return await _http(port, "POST", "/bot/click", body=body, host=host)


@mcp.tool()
async def bot_npc_click(dialog: str = "", keyword: str = "", nth: int = 1,
                        port: int = 0, host: str = "") -> str:
    """Click item in UI dialog list by keyword match."""
    body: dict = {}
    if dialog:
        body["dialog"] = dialog
    if keyword:
        body["keyword"] = keyword
    if nth != 1:
        body["nth"] = nth
    return await _http(port, "POST", "/bot/npc_click", body=body, host=host)


@mcp.tool()
async def bot_glfw_click(x: int, y: int, port: int = 0, host: str = "") -> str:
    """Simulate mouse click at game client coords (x,y)."""
    return await _http(port, "POST", "/bot/glfw_click", body={"x": x, "y": y}, host=host)


@mcp.tool()
async def bot_glfw_key(key: int, port: int = 0, host: str = "") -> str:
    """Simulate key press (GLFW key code)."""
    return await _http(port, "POST", "/bot/glfw_key", body={"key": key}, host=host)


@mcp.tool()
async def bot_navpath(x: int, y: int, port: int = 0, host: str = "") -> str:
    """Get A* waypoints to (x,y) without walking."""
    return await _http(port, "POST", "/bot/navpath", body={"x": x, "y": y}, host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Bot Control (13) — previously WS, now HTTP
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_start(port: int = 0, host: str = "") -> str:
    """Start bot automation."""
    return await _http(port, "POST", "/bot/start", host=host)


@mcp.tool()
async def bot_stop(port: int = 0, host: str = "") -> str:
    """Stop bot."""
    return await _http(port, "POST", "/bot/stop", host=host)


@mcp.tool()
async def bot_config_get(port: int = 0, host: str = "") -> str:
    """ALL config fields as JSON."""
    return await _http(port, "GET", "/bot/config", host=host)


@mcp.tool()
async def bot_config_set(fields: str = "{}", port: int = 0,
                         host: str = "") -> str:
    """Update config. fields=JSON e.g. '{"combat_radius":15}'."""
    try:
        body = json.loads(fields)
        if not isinstance(body, dict):
            return json.dumps({"error": "fields must be a JSON object"})
    except Exception:
        return json.dumps({"error": "Invalid JSON in fields"})
    return await _http(port, "POST", "/bot/config", body=body, host=host)


@mcp.tool()
async def bot_config_reset(port: int = 0, host: str = "") -> str:
    """Reset config to defaults."""
    return await _http(port, "POST", "/bot/config/reset", host=host)


@mcp.tool()
async def bot_combat_state(port: int = 0, host: str = "") -> str:
    """Combat state machine: phase, target, timing, blacklist, kills."""
    return await _http(port, "GET", "/bot/combat_state", host=host)


@mcp.tool()
async def bot_spells(port: int = 0, host: str = "") -> str:
    """Available spells: {skill_id, name}."""
    return await _http(port, "GET", "/bot/spells", host=host)


@mcp.tool()
async def bot_daytime(on: int = 1, port: int = 0, host: str = "") -> str:
    """Force-daytime (1=on, 0=off)."""
    return await _http(port, "POST", "/bot/daytime", body={"on": on}, host=host)


@mcp.tool()
async def bot_stats_reset(port: int = 0, host: str = "") -> str:
    """Reset kill/gold stats."""
    return await _http(port, "POST", "/bot/stats_reset", host=host)


@mcp.tool()
async def bot_search_names(keyword: str, port: int = 0, host: str = "") -> str:
    """Search game name index by keyword."""
    return await _http(port, "GET", "/bot/search_names",
                       params={"q": keyword}, host=host)


@mcp.tool()
async def bot_log_level(level: str = "", port: int = 0, host: str = "") -> str:
    """Get/set log level. level='S'(important),'D'(debug)."""
    if level:
        return await _http(port, "POST", "/bot/log_level",
                           body={"level": level}, host=host)
    return await _http(port, "GET", "/bot/log_level", host=host)


@mcp.tool()
async def bot_rescan(port: int = 0, host: str = "") -> str:
    """Force rescan patterns + RTTI."""
    return await _http(port, "POST", "/bot/rescan", host=host)


@mcp.tool()
async def bot_auto_login(port: int = 0, host: str = "") -> str:
    """Trigger auto-login sequence."""
    return await _http(port, "POST", "/bot/auto_login", host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Player & Stats (3)
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
#  Target & NPC (2)
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_target(port: int = 0, host: str = "") -> str:
    """Get current selected target info."""
    return await _http(port, "GET", "/target", host=host)


@mcp.tool()
async def bot_dialogs(port: int = 0, host: str = "") -> str:
    """List open dialog windows."""
    return await _http(port, "GET", "/dialogs", host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Scroll & Teleport (6)
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_scroll_list(port: int = 0, host: str = "") -> str:
    """List teleport scrolls in inventory."""
    return await _http(port, "GET", "/scroll_list", host=host)


@mcp.tool()
async def bot_scroll_show(item_uid: int, port: int = 0, host: str = "") -> str:
    """Show scroll destination picker UI."""
    return await _http(port, "POST", "/scroll/show",
                       body={"item_uid": item_uid}, host=host)


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


# ═══════════════════════════════════════════════════════════════════════════
#  Bookmarks (3)
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
#  Party (15) — previously WS, now HTTP
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_party_status(port: int = 0, host: str = "") -> str:
    """Party system status: mode, squad, master."""
    return await _http(port, "GET", "/party/status", host=host)


@mcp.tool()
async def bot_party_members(port: int = 0, host: str = "") -> str:
    """List party members with HP/MP/position."""
    return await _http(port, "GET", "/party/members", host=host)


@mcp.tool()
async def bot_party_config_get(port: int = 0, host: str = "") -> str:
    """Get party config (heal/buff/attack settings)."""
    return await _http(port, "GET", "/party/config", host=host)


@mcp.tool()
async def bot_party_config_set(fields: str = "{}", port: int = 0,
                                host: str = "") -> str:
    """Set party config. fields=JSON."""
    try:
        body = json.loads(fields)
        if not isinstance(body, dict):
            return json.dumps({"error": "fields must be a JSON object"})
    except Exception:
        return json.dumps({"error": "Invalid JSON in fields"})
    return await _http(port, "POST", "/party/config", body=body, host=host)


@mcp.tool()
async def bot_party_mode(mode: str, port: int = 0, host: str = "") -> str:
    """Set party mode: follow|grind|rest|return|idle."""
    return await _http(port, "POST", "/party/mode",
                       body={"mode": mode}, host=host)


@mcp.tool()
async def bot_party_follow(port: int = 0, host: str = "") -> str:
    """Switch party to follow mode."""
    return await _http(port, "POST", "/party/follow", host=host)


@mcp.tool()
async def bot_party_stop(port: int = 0, host: str = "") -> str:
    """Stop party control."""
    return await _http(port, "POST", "/party/stop", host=host)


@mcp.tool()
async def bot_party_attack(name: str = "", x: int = 0, y: int = 0,
                           port: int = 0, host: str = "") -> str:
    """Command party to attack target by name/position."""
    return await _http(port, "POST", "/party/attack",
                       body={"name": name, "x": x, "y": y}, host=host)


@mcp.tool()
async def bot_party_focus(name: str, port: int = 0, host: str = "") -> str:
    """Set party focus target."""
    return await _http(port, "POST", "/party/focus",
                       body={"name": name}, host=host)


@mcp.tool()
async def bot_party_heal(target: str, port: int = 0, host: str = "") -> str:
    """Manual party heal on target name."""
    return await _http(port, "POST", "/party/heal",
                       body={"target": target}, host=host)


@mcp.tool()
async def bot_party_cast(skill_id: int, target: str = "",
                         port: int = 0, host: str = "") -> str:
    """Cast party skill on target."""
    return await _http(port, "POST", "/party/cast",
                       body={"skill_id": skill_id, "target": target}, host=host)


@mcp.tool()
async def bot_party_teleport(port: int = 0, host: str = "") -> str:
    """Trigger party teleport."""
    return await _http(port, "POST", "/party/teleport", host=host)


@mcp.tool()
async def bot_party_sync(port: int = 0, host: str = "") -> str:
    """Sync party config to all members."""
    return await _http(port, "POST", "/party/sync", host=host)


@mcp.tool()
async def bot_party_free_attack(enabled: int = 1, port: int = 0,
                                host: str = "") -> str:
    """Toggle free attack mode (1=on, 0=off)."""
    return await _http(port, "POST", "/party/free_attack",
                       body={"enabled": enabled}, host=host)


@mcp.tool()
async def bot_party_moveto(x: int, y: int, port: int = 0, host: str = "") -> str:
    """Move party to position."""
    return await _http(port, "POST", "/party/moveto",
                       body={"x": x, "y": y}, host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Navigation Scripts (5)
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_nav_exec(script_id: str = "", port: int = 0, host: str = "") -> str:
    """Execute navigation script by ID."""
    return await _http(port, "POST", "/nav/exec",
                       body={"script_id": script_id}, host=host)


@mcp.tool()
async def bot_nav_stop(port: int = 0, host: str = "") -> str:
    """Stop current navigation."""
    return await _http(port, "POST", "/nav/stop", host=host)


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
async def bot_nav_return_confirm(port: int = 0, host: str = "") -> str:
    """Confirm nav return dialog."""
    return await _http(port, "POST", "/nav/return_confirm", host=host)


@mcp.tool()
async def bot_portal_db(port: int = 0, host: str = "") -> str:
    """Get portal/teleport database."""
    return await _http(port, "GET", "/api/portal_db", host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Supply & Warehouse (6) — previously WS, now HTTP
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_supply_state(port: int = 0, host: str = "") -> str:
    """Supply module detailed state."""
    return await _http(port, "GET", "/supply/state", host=host)


@mcp.tool()
async def bot_supply_trigger(port: int = 0, host: str = "") -> str:
    """Manually trigger supply run."""
    return await _http(port, "POST", "/supply/trigger", host=host)


@mcp.tool()
async def bot_wh_trigger(port: int = 0, host: str = "") -> str:
    """Manually trigger warehouse run."""
    return await _http(port, "POST", "/wh/trigger", host=host)


@mcp.tool()
async def bot_shop_buy(item_name: str, qty: int = 1,
                       port: int = 0, host: str = "") -> str:
    """Buy item from open NPC shop."""
    return await _http(port, "POST", "/shop/buy",
                       body={"item_name": item_name, "qty": qty}, host=host)


@mcp.tool()
async def bot_sell_npcs_get(port: int = 0, host: str = "") -> str:
    """Get configured sell NPC list."""
    return await _http(port, "GET", "/sell_npcs", host=host)


@mcp.tool()
async def bot_sell_npcs_set(npcs: str, port: int = 0, host: str = "") -> str:
    """Set sell NPC list. npcs=JSON array."""
    try:
        parsed = json.loads(npcs)
    except Exception:
        return json.dumps({"error": "Invalid JSON"})
    return await _http(port, "POST", "/sell_npcs",
                       body={"npcs": parsed}, host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Profile Management (3) — previously WS, now HTTP
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_profile_list(port: int = 0, host: str = "") -> str:
    """List saved config profiles."""
    return await _http(port, "GET", "/profile/list", host=host)


@mcp.tool()
async def bot_profile_load(name: str, port: int = 0, host: str = "") -> str:
    """Load config profile by name."""
    return await _http(port, "POST", "/profile/load",
                       body={"name": name}, host=host)


@mcp.tool()
async def bot_profile_delete(name: str, port: int = 0, host: str = "") -> str:
    """Delete config profile."""
    return await _http(port, "POST", "/profile/delete",
                       body={"name": name}, host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Login & Auth (2)
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_auth_status(port: int = 0, host: str = "") -> str:
    """Get auth/license status."""
    return await _http(port, "GET", "/auth/status", host=host)


@mcp.tool()
async def bot_pledge_join(name: str, password: str = "",
                          port: int = 0, host: str = "") -> str:
    """Join blood pledge by name."""
    body: dict = {"name": name}
    if password:
        body["password"] = password
    return await _http(port, "POST", "/bot/pledge_join", body=body, host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  UI & Debug (3)
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_minimap(port: int = 0, host: str = "") -> str:
    """Minimap info."""
    return await _http(port, "GET", "/minimap", host=host)


@mcp.tool()
async def bot_screenshot(port: int = 0, host: str = "") -> str:
    """Take game window screenshot (BMP, base64)."""
    return await _http(port, "GET", "/screenshot", host=host, timeout=15)


# ═══════════════════════════════════════════════════════════════════════════
#  Update & System (2) — previously WS, now HTTP
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def bot_update_check(port: int = 0, host: str = "") -> str:
    """Check for DLL updates."""
    return await _http(port, "POST", "/update/check", host=host)


@mcp.tool()
async def bot_update_download(port: int = 0, host: str = "") -> str:
    """Download pending DLL update."""
    return await _http(port, "POST", "/update/download", host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Batch Operations (3)
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
    results: list[dict] = []
    for inst in instances:
        if inst.get("bot", 0):
            results.append({"host": inst["host"], "port": inst["port"],
                           "result": "already running"})
            continue
        try:
            r = await _http(inst["port"], "POST", "/bot/start", host=inst["host"])
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
    results: list[dict] = []
    for inst in instances:
        if not inst.get("bot", 0):
            results.append({"host": inst["host"], "port": inst["port"],
                           "result": "not running"})
            continue
        try:
            r = await _http(inst["port"], "POST", "/bot/stop", host=inst["host"])
            data = json.loads(r)
            results.append({"host": inst["host"], "port": inst["port"],
                           "result": data.get("data", {}).get("status", "unknown")})
        except Exception as e:
            results.append({"host": inst["host"], "port": inst["port"],
                           "result": f"error: {e}"})
    return json.dumps({"stopped": len(results), "results": results},
                      ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
#  Escape Hatch (1) — HTTP only
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def dll_http(method: str, path: str, body: str = "",
                   port: int = 0, host: str = "") -> str:
    """Generic HTTP call to DLL. method=GET|POST, path=/endpoint."""
    parsed = json.loads(body) if body else None
    return await _http(port, method.upper(), path, body=parsed, host=host)


# ═══════════════════════════════════════════════════════════════════════════
#  Skill Engine — 動態建立、管理、執行高階流程
# ═══════════════════════════════════════════════════════════════════════════

_skills: dict[str, dict] = {}
_SKILLS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills.json")

# High-level tools (Python functions) accessible from skill engine.
# Populated after function definitions — see bottom of file.
_HIGH_LEVEL_TOOLS: dict[str, Any] = {}

_TOOL_ROUTES: dict[str, tuple[str, str] | None] = {
    # 查詢 (舊端點)
    "bot_status": ("GET", "/status"), "bot_position": ("GET", "/position"),
    "bot_entities": ("GET", "/entities"), "bot_inventory": ("GET", "/inventory"),
    "bot_buffs": ("GET", "/buffs"), "bot_target": ("GET", "/target"),
    "bot_dialogs": ("GET", "/dialogs"), "bot_logs": ("GET", "/logs"),
    "bot_scan": ("GET", "/scan"), "bot_shoplist": ("GET", "/shop_list"),
    "bot_uitree": ("GET", "/uitree"), "bot_minimap": ("GET", "/minimap"),
    "bot_stats": ("GET", "/stats"), "bot_player": ("GET", "/player"),
    "bot_screenshot": ("GET", "/screenshot"), "bot_map_grid": ("GET", "/map_grid"),
    "bot_pathfind": ("GET", "/pathfind"), "bot_los": ("GET", "/los"),
    "bot_scroll_list": ("GET", "/scroll_list"), "bot_scroll_dest": ("GET", "/scroll_dest"),
    "bot_bookmarks": ("GET", "/bm_list"), "bot_bm_scan": ("GET", "/bm_scan"),
    "bot_nav_scripts": ("GET", "/api/nav_scripts"), "bot_portal_db": ("GET", "/api/portal_db"),
    "bot_auth_status": ("GET", "/auth/status"),
    # 查詢 (新端點)
    "bot_combat_state": ("GET", "/bot/combat_state"), "bot_config_get": ("GET", "/bot/config"),
    "bot_spells": ("GET", "/bot/spells"), "bot_search_names": ("GET", "/bot/search_names"),
    "bot_log_level": ("GET", "/bot/log_level"),
    "bot_party_status": ("GET", "/party/status"), "bot_party_members": ("GET", "/party/members"),
    "bot_party_config_get": ("GET", "/party/config"), "bot_profile_list": ("GET", "/profile/list"),
    "bot_supply_state": ("GET", "/supply/state"), "bot_sell_npcs_get": ("GET", "/sell_npcs"),
    # 動作
    "bot_walk": ("POST", "/bot/walk"), "bot_smartmove": ("POST", "/bot/smartmove"),
    "bot_attack": ("POST", "/bot/attack"), "bot_pickup": ("POST", "/bot/pickup"),
    "bot_cast": ("POST", "/bot/cast"), "bot_useitem": ("POST", "/bot/useitem"),
    "bot_interact": ("POST", "/bot/interact"), "bot_click": ("POST", "/bot/click"),
    "bot_npc_click": ("POST", "/bot/npc_click"), "bot_glfw_click": ("POST", "/bot/glfw_click"),
    "bot_glfw_key": ("POST", "/bot/glfw_key"), "bot_navpath": ("POST", "/bot/navpath"),
    "bot_pledge_join": ("POST", "/bot/pledge_join"),
    "bot_teleport": ("POST", "/teleport"), "bot_usescroll": ("POST", "/usescroll"),
    "bot_bm_click": ("POST", "/bm_click"), "bot_scroll_show": ("POST", "/scroll/show"),
    "bot_nav_upload": ("POST", "/api/nav_upload"),
    # Bot 控制
    "bot_start": ("POST", "/bot/start"), "bot_stop": ("POST", "/bot/stop"),
    "bot_config_set": ("POST", "/bot/config"), "bot_config_reset": ("POST", "/bot/config/reset"),
    "bot_daytime": ("POST", "/bot/daytime"), "bot_stats_reset": ("POST", "/bot/stats_reset"),
    "bot_rescan": ("POST", "/bot/rescan"), "bot_auto_login": ("POST", "/bot/auto_login"),
    "bot_log_level_set": ("POST", "/bot/log_level"),
    # Party
    "bot_party_mode": ("POST", "/party/mode"), "bot_party_attack": ("POST", "/party/attack"),
    "bot_party_focus": ("POST", "/party/focus"), "bot_party_cast": ("POST", "/party/cast"),
    "bot_party_heal": ("POST", "/party/heal"), "bot_party_moveto": ("POST", "/party/moveto"),
    "bot_party_stop": ("POST", "/party/stop"), "bot_party_follow": ("POST", "/party/follow"),
    "bot_party_free_attack": ("POST", "/party/free_attack"),
    "bot_party_sync": ("POST", "/party/sync"), "bot_party_teleport": ("POST", "/party/teleport"),
    "bot_party_config_set": ("POST", "/party/config"),
    # Supply / Warehouse / Shop
    "bot_supply_trigger": ("POST", "/supply/trigger"), "bot_wh_trigger": ("POST", "/wh/trigger"),
    "bot_shop_buy": ("POST", "/shop/buy"), "bot_sell_npcs_set": ("POST", "/sell_npcs"),
    # Profile / Nav / Update
    "bot_profile_load": ("POST", "/profile/load"), "bot_profile_delete": ("POST", "/profile/delete"),
    "bot_nav_exec": ("POST", "/nav/exec"), "bot_nav_stop": ("POST", "/nav/stop"),
    "bot_nav_return_confirm": ("POST", "/nav/return_confirm"),
    "bot_update_check": ("POST", "/update/check"), "bot_update_download": ("POST", "/update/download"),
    # 特殊
    "sleep": None, "log": None,
}


def _skills_load() -> None:
    global _skills
    try:
        with open(_SKILLS_FILE, "r", encoding="utf-8") as f:
            _skills = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _skills = {}


def _skills_save() -> None:
    with open(_SKILLS_FILE, "w", encoding="utf-8") as f:
        json.dump(_skills, f, ensure_ascii=False, indent=2)


_skills_load()


def _resolve_vars(params: dict, ctx: dict) -> dict:
    """替換 $var.field 變數"""
    resolved: dict = {}
    for k, v in params.items():
        if isinstance(v, str) and v.startswith("$"):
            parts = v[1:].split(".")
            val: Any = ctx
            for p in parts:
                if isinstance(val, dict):
                    val = val.get(p, val.get("data", {}).get(p) if isinstance(val.get("data"), dict) else None)
                else:
                    val = None
                    break
            resolved[k] = val if val is not None else v
        else:
            resolved[k] = v
    return resolved


async def _exec_step(tool: str, params: dict, port: int, host: str) -> str:
    """執行單一 step — 支援 simple routes + 高階 Python tool functions"""
    if tool == "sleep":
        ms = params.get("ms", 1000)
        if isinstance(ms, (int, float)):
            await asyncio.sleep(ms / 1000.0)
        return json.dumps({"ok": 1, "slept_ms": ms})
    if tool == "log":
        return json.dumps({"logged": params.get("msg", "")})

    # 1) Simple route → direct HTTP call
    route = _TOOL_ROUTES.get(tool)
    if route is not None:
        method, path = route
        if method == "GET":
            return await _http(port, "GET", path, params=params, host=host)
        return await _http(port, "POST", path, body=params, host=host)

    # 2) High-level Python tool function (setup_*, start_grinding, etc.)
    fn = _HIGH_LEVEL_TOOLS.get(tool)
    if fn is not None:
        p = dict(params)
        p["port"] = port
        p["host"] = host
        return await fn(**p)

    return json.dumps({"error": f"unknown tool: {tool}"})


async def _wait_for_condition(wf: dict, port: int, host: str) -> str:
    """輪詢等待條件成立"""
    tool = wf.get("tool", "bot_position")
    field = wf.get("field", "")
    value = wf.get("value")
    timeout_ms = wf.get("timeout_ms", 5000)

    deadline = time.time() + timeout_ms / 1000.0
    last_result = "{}"
    while time.time() < deadline:
        last_result = await _exec_step(tool, {}, port, host)
        try:
            data = json.loads(last_result)
            current: Any = data
            for part in field.split("."):
                current = current.get(part) if isinstance(current, dict) else None
            if current == value:
                return last_result
        except Exception:
            pass
        await asyncio.sleep(0.5)
    return json.dumps({"error": "wait_for timeout", "field": field, "expected": value})


# ── Skill 管理 Tools ──

@mcp.tool()
async def skill_create(name: str, description: str, steps: str) -> str:
    """建立或更新 skill。steps=JSON array，每個 step: {"tool":"bot_xxx","params":{...},"delay_ms":N}
    支援欄位: tool(必填), params(選填), delay_ms(選填), repeat(選填),
    save_as(選填), on_error(skip/stop), wait_for(選填), comment(選填)"""
    try:
        parsed = json.loads(steps)
        if not isinstance(parsed, list):
            return json.dumps({"error": "steps must be a JSON array"})
    except Exception:
        return json.dumps({"error": "Invalid JSON in steps"})
    _skills[name] = {"description": description, "steps": parsed}
    _skills_save()
    return json.dumps({"status": "created", "name": name, "step_count": len(parsed)},
                      ensure_ascii=False)


@mcp.tool()
async def skill_list() -> str:
    """列出所有已建立的 skill 及其步驟數"""
    items = [{"name": n, "description": s["description"], "steps": len(s["steps"])}
             for n, s in _skills.items()]
    return json.dumps({"count": len(items), "skills": items}, ensure_ascii=False)


@mcp.tool()
async def skill_delete(name: str) -> str:
    """刪除指定 skill"""
    if name not in _skills:
        return json.dumps({"error": f"skill '{name}' not found"}, ensure_ascii=False)
    del _skills[name]
    _skills_save()
    return json.dumps({"status": "deleted", "name": name}, ensure_ascii=False)


@mcp.tool()
async def skill_get(name: str) -> str:
    """查看指定 skill 的完整定義（含所有步驟）"""
    if name not in _skills:
        return json.dumps({"error": f"skill '{name}' not found"}, ensure_ascii=False)
    return json.dumps({"name": name, **_skills[name]}, ensure_ascii=False, indent=2)


# ── Skill 執行引擎 ──

@mcp.tool()
async def skill_run(name: str, port: int = 0, host: str = "") -> str:
    """執行指定 skill — 逐步呼叫 MCP tool，回傳每步結果"""
    if name not in _skills:
        return json.dumps({"error": f"skill '{name}' not found"}, ensure_ascii=False)

    skill = _skills[name]
    ctx: dict[str, Any] = {}
    results: list[dict] = []

    for i, step in enumerate(skill["steps"]):
        tool = step.get("tool", "")
        raw_params = step.get("params", {})
        params = _resolve_vars(raw_params, ctx) if raw_params else {}
        repeat = step.get("repeat", 1)
        delay = step.get("delay_ms", 0)
        on_error = step.get("on_error", "stop")
        comment = step.get("comment", "")

        step_ok = True
        last_result = "{}"

        for _r in range(repeat):
            last_result = await _exec_step(tool, params, port, host)

            # Human-like delay: minimum 800ms between steps, use delay_ms if larger
            effective_delay = max(delay, 800) if tool.startswith("bot_") else delay
            if effective_delay > 0:
                await asyncio.sleep(effective_delay / 1000.0)

            wf = step.get("wait_for")
            if wf:
                last_result = await _wait_for_condition(wf, port, host)

        # 檢查錯誤
        try:
            rd = json.loads(last_result)
            has_err = isinstance(rd, dict) and "error" in rd
        except Exception:
            has_err = True

        if has_err:
            step_ok = False
            if on_error == "stop":
                results.append({"step": i, "tool": tool, "ok": False,
                                "comment": comment, "error": last_result[:200]})
                break

        # 存變數
        try:
            parsed_result = json.loads(last_result) if isinstance(last_result, str) else last_result
        except Exception:
            parsed_result = {"raw": last_result}

        if "save_as" in step:
            ctx[step["save_as"]] = parsed_result
        ctx["prev"] = parsed_result

        results.append({"step": i, "tool": tool, "ok": step_ok, "comment": comment})

    return json.dumps({
        "skill": name,
        "steps_total": len(skill["steps"]),
        "steps_run": len(results),
        "all_ok": all(r["ok"] for r in results),
        "results": results,
    }, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
#  Fleet Management — 艦隊管理
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def fleet_status() -> str:
    """所有機器所有 bot 的狀態摘要：名稱、等級、HP、地圖、bot 狀態"""
    instances = await _scan_instances(force=True)
    summaries: list[dict] = []
    for inst in instances:
        try:
            r = await _http(inst["port"], "GET", "/status", host=inst["host"])
            data = json.loads(r).get("data", {})
            summaries.append({
                "host": inst["host"], "port": inst["port"],
                "name": data.get("char_name", "?"),
                "level": data.get("level", 0),
                "hp": data.get("hp", 0), "max_hp": data.get("max_hp", 0),
                "bot": data.get("bot_running", 0),
                "map": data.get("map_name", "?"),
            })
        except Exception:
            pass
    return json.dumps({"count": len(summaries), "bots": summaries},
                      ensure_ascii=False, indent=2)


@mcp.tool()
async def fleet_run_skill(name: str) -> str:
    """對所有在線 bot 逐台執行指定 skill"""
    if name not in _skills:
        return json.dumps({"error": f"skill '{name}' not found"})
    instances = await _scan_instances(force=True)

    async def _run_one(inst: dict) -> dict:
        try:
            r = await skill_run(name, port=inst["port"], host=inst["host"])
            rd = json.loads(r)
            return {"host": inst["host"], "port": inst["port"],
                    "name": inst.get("char_name", "?"),
                    "ok": rd.get("all_ok", False)}
        except Exception:
            return {"host": inst["host"], "port": inst["port"],
                    "name": inst.get("char_name", "?"), "ok": False}

    results = await asyncio.gather(*[_run_one(i) for i in instances])
    return json.dumps({"skill": name, "bots": len(results),
                       "results": list(results)},
                      ensure_ascii=False, indent=2)


@mcp.tool()
async def fleet_health_check() -> str:
    """巡檢所有 bot：HP、箭、bot 狀態，回報有問題的"""
    instances = await _scan_instances(force=True)
    issues: list[dict] = []
    healthy = 0
    for inst in instances:
        try:
            sr = await _http(inst["port"], "GET", "/status", host=inst["host"])
            status = json.loads(sr).get("data", {})
            ir = await _http(inst["port"], "GET", "/inventory", host=inst["host"])
            inv = json.loads(ir).get("data", {})

            max_hp = max(status.get("max_hp", 1), 1)
            hp_pct = (status.get("hp", 0) / max_hp) * 100
            arrows = sum(
                it.get("qty", 0) for it in inv.get("items", [])
                if "箭" in it.get("name", "")
            )
            bot_on = status.get("bot_running", 0)
            logged = status.get("logged_in", 0)

            problems: list[str] = []
            if not logged:
                problems.append("離線")
            elif hp_pct < 30:
                problems.append(f"HP低({hp_pct:.0f}%)")
            if arrows < 100 and arrows >= 0:
                problems.append(f"箭不足({arrows})")
            if logged and not bot_on:
                problems.append("bot未啟動")

            if problems:
                issues.append({
                    "host": inst["host"], "port": inst["port"],
                    "name": status.get("char_name", "?"),
                    "level": status.get("level", 0),
                    "problems": problems,
                })
            else:
                healthy += 1
        except Exception:
            issues.append({
                "host": inst["host"], "port": inst["port"],
                "name": "?", "problems": ["連線失敗"],
            })
    return json.dumps({
        "checked": len(instances), "healthy": healthy,
        "issues": len(issues), "details": issues,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def fleet_run_filtered(
    name: str,
    filter_field: str = "arrows",
    filter_op: str = "lt",
    filter_value: str = "100",
) -> str:
    """只對符合條件的 bot 執行 skill。
    filter_field: arrows | level | hp_pct | bot
    filter_op: lt(小於) | gt(大於) | eq(等於)
    filter_value: 比較值"""
    if name not in _skills:
        return json.dumps({"error": f"skill '{name}' not found"})
    instances = await _scan_instances(force=True)
    matched: list[dict] = []
    skipped = 0

    fval: int | float
    try:
        fval = float(filter_value)
    except ValueError:
        fval = 0

    for inst in instances:
        try:
            sr = await _http(inst["port"], "GET", "/status", host=inst["host"])
            status = json.loads(sr).get("data", {})

            # 計算 filter 值
            if filter_field == "arrows":
                ir = await _http(inst["port"], "GET", "/inventory", host=inst["host"])
                inv = json.loads(ir).get("data", {})
                current = sum(
                    it.get("qty", 0) for it in inv.get("items", [])
                    if "箭" in it.get("name", "")
                )
            elif filter_field == "level":
                current = status.get("level", 0)
            elif filter_field == "hp_pct":
                max_hp = max(status.get("max_hp", 1), 1)
                current = (status.get("hp", 0) / max_hp) * 100
            elif filter_field == "bot":
                current = status.get("bot_running", 0)
            else:
                current = 0

            # 比較
            match = False
            if filter_op == "lt" and current < fval:
                match = True
            elif filter_op == "gt" and current > fval:
                match = True
            elif filter_op == "eq" and current == fval:
                match = True

            if match:
                r = await skill_run(name, port=inst["port"], host=inst["host"])
                rd = json.loads(r)
                matched.append({
                    "host": inst["host"], "port": inst["port"],
                    "name": status.get("char_name", "?"),
                    "value": current,
                    "ok": rd.get("all_ok", False),
                })
            else:
                skipped += 1
        except Exception:
            pass

    return json.dumps({
        "skill": name, "filter": f"{filter_field} {filter_op} {filter_value}",
        "matched": len(matched), "skipped": skipped, "results": matched,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def fleet_supply_check() -> str:
    """檢查所有 bot 的補給狀態，回傳需要補給的清單（箭不足、負重高）。"""
    instances = await _scan_instances(force=True)
    need_supply: list[dict] = []
    ok_count = 0

    for inst in instances:
        try:
            sr = await _http(inst["port"], "GET", "/status", host=inst["host"])
            status = json.loads(sr).get("data", {})
            ir = await _http(inst["port"], "GET", "/inventory", host=inst["host"])
            inv = json.loads(ir).get("data", {})
            pr = await _http(inst["port"], "GET", "/player", host=inst["host"])
            player = json.loads(pr).get("data", {})

            arrows = sum(
                it.get("qty", 0) for it in inv.get("items", [])
                if "箭" in it.get("name", "")
            )
            weight = player.get("weight", 0)
            max_weight = player.get("max_weight", 1) or 1
            weight_pct = (weight / max_weight) * 100

            reasons: list[str] = []
            if arrows > 0 and arrows < 100:
                reasons.append(f"箭={arrows}")
            if weight_pct > 80:
                reasons.append(f"負重={weight_pct:.0f}%")

            if reasons:
                need_supply.append({
                    "host": inst["host"], "port": inst["port"],
                    "name": status.get("char_name", "?"),
                    "level": status.get("level", 0),
                    "arrows": arrows,
                    "weight_pct": round(weight_pct, 1),
                    "reasons": reasons,
                })
            else:
                ok_count += 1
        except Exception:
            pass

    return json.dumps({
        "checked": len(instances),
        "need_supply": len(need_supply),
        "ok": ok_count,
        "bots": need_supply,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def fleet_teleport(dest: str, profile: str = "") -> str:
    """全部 bot 傳送到指定地點（可選載入設定檔）。並行執行。
    dest: "村莊|傳送點" 格式
    profile: 設定檔名稱（可選）"""
    instances = await _scan_instances(force=True)

    async def _teleport_one(inst: dict) -> dict:
        try:
            if profile:
                await _http(inst["port"], "POST", "/profile/load",
                            body={"name": profile}, host=inst["host"])
                await asyncio.sleep(1.0)
            tp_r = await bot_teleport_scroll(dest, port=inst["port"], host=inst["host"])
            tp = json.loads(tp_r)
            return {
                "host": inst["host"], "port": inst["port"],
                "name": inst.get("char_name", "?"),
                "ok": "error" not in tp,
            }
        except Exception as e:
            return {
                "host": inst["host"], "port": inst["port"],
                "name": inst.get("char_name", "?"),
                "ok": False, "error": str(e)[:80],
            }

    results = await asyncio.gather(*[_teleport_one(i) for i in instances])

    return json.dumps({
        "dest": dest,
        "profile": profile or "(current)",
        "total": len(results),
        "success": sum(1 for r in results if r["ok"]),
        "results": list(results),
    }, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
#  High-Level Skill Tools — 硬編碼高階流程
# ═══════════════════════════════════════════════════════════════════════════


async def _wait_dialog_visible(
    dialog: str, port: int, host: str,
    timeout_ms: int = 5000, poll_ms: int = 500,
) -> bool:
    """等待指定 dialog 出現（用 /dialogs 檢查，不用其他 endpoint）。
    所有 UI 操作前必須先呼叫此函式，不可見就不能點。"""
    deadline = time.time() + timeout_ms / 1000.0
    while time.time() < deadline:
        r = await _http(port, "GET", "/dialogs", host=host)
        try:
            dialogs = json.loads(r).get("data", {}).get("dialogs", [])
            for d in dialogs:
                if d.get("name", "") == dialog:
                    return True
        except Exception:
            pass
        await asyncio.sleep(poll_ms / 1000.0)
    return False


def _fuzzy_match(user_name: str, candidates: list[str]) -> str | None:
    """模糊匹配物品名稱。玩家說的名字可能跟遊戲裡不完全一樣。
    優先順序：完全匹配 > 包含匹配 > 去空格匹配 > None"""
    user_name = user_name.strip()
    # 1) 完全匹配
    for c in candidates:
        if c.strip() == user_name:
            return c
    # 2) 包含匹配（候選包含用戶輸入，或用戶輸入包含候選）
    matches = []
    for c in candidates:
        cs = c.strip()
        if user_name in cs or cs in user_name:
            matches.append(c)
    if len(matches) == 1:
        return matches[0]
    # 3) 如果多個匹配，取最短的（最精確）
    if matches:
        return min(matches, key=lambda x: len(x.strip()))
    return None


async def _find_npc(name: str, port: int, host: str) -> dict | None:
    """從 entities 找 NPC（用最新資料，不用快取地址）。"""
    r = await _http(port, "GET", "/entities", host=host)
    try:
        ents = json.loads(r).get("data", {}).get("entities", [])
    except Exception:
        return None
    for e in ents:
        if name in e.get("name", "") and e.get("type", "") in ("InteractiveNPC", "NPC"):
            return e
    return None


async def _npc_interact_and_wait(
    npc_name: str, port: int, host: str,
) -> str | None:
    """強制規範：
    1. /entities 查最新 NPC addr（不用快取）
    2. /dialogs 確認操作前狀態
    3. interact
    4. 等 3s（DLL WH_NPC_WAIT_MS）
    5. /dialogs 確認 NpcTalkLayout visible"""
    # 1) 查最新 entities
    npc = await _find_npc(npc_name, port, host)
    if not npc:
        return json.dumps({"error": f"找不到 NPC '{npc_name}'，不在畫面中"},
                          ensure_ascii=False)
    # 2) interact — 用 entity_id（不會因重建而失效），不用 entity_addr
    await _http(port, "POST", "/bot/interact",
                body={"entity_id": npc["id"]}, host=host)
    # 3) 等 3s
    await asyncio.sleep(3.0)
    # 4) 確認 NpcTalkLayout visible
    if not await _wait_dialog_visible("NpcTalkLayout", port, host, timeout_ms=5000):
        return json.dumps({"error": "NpcTalkLayout 未出現"})
    return None


async def _npc_click_and_check(
    keyword: str, nth: int, port: int, host: str,
    max_retry: int = 15,
) -> str | None:
    """強制規範：點擊前必須確認 NpcTalkLayout visible。有重試。"""
    for attempt in range(max_retry):
        # 強制：確認 NpcTalkLayout visible
        if not await _wait_dialog_visible("NpcTalkLayout", port, host, timeout_ms=1000):
            await asyncio.sleep(1.0)
            continue
        # 點擊
        r = await _http(port, "POST", "/npc_click",
                        body={"dialog": "NpcTalkLayout",
                              "keyword": keyword, "nth": nth},
                        host=host)
        try:
            data = json.loads(r).get("data", {})
            if data.get("result") == 2:
                return None
        except Exception:
            pass
        await asyncio.sleep(1.0)
    return json.dumps({"error": f"點擊'{keyword}' nth={nth} 失敗（重試{max_retry}次）"},
                      ensure_ascii=False)


@mcp.tool()
async def bot_check_health(port: int = 0, host: str = "") -> str:
    """巡檢單機 bot 健康狀態：HP/MP、箭矢、buffs、weight、bot 是否運行。
    回傳問題列表，空=健康。"""
    sr = await _http(port, "GET", "/status", host=host)
    ir = await _http(port, "GET", "/inventory", host=host)
    br = await _http(port, "GET", "/buffs", host=host)
    pr = await _http(port, "GET", "/player", host=host)

    try:
        status = json.loads(sr).get("data", {})
        inv = json.loads(ir).get("data", {})
    except Exception:
        return json.dumps({"error": "failed to read status/inventory"})

    buffs: list = []
    try:
        buffs = json.loads(br).get("data", {}).get("buffs", [])
    except Exception:
        pass
    player: dict = {}
    try:
        player = json.loads(pr).get("data", {})
    except Exception:
        pass

    max_hp = max(status.get("max_hp", 1), 1)
    max_mp = max(status.get("max_mp", 1), 1)
    hp_pct = (status.get("hp", 0) / max_hp) * 100
    mp_pct = (status.get("mp", 0) / max_mp) * 100
    arrows = sum(
        it.get("qty", 0) for it in inv.get("items", [])
        if "箭" in it.get("name", "")
    )
    bot_on = status.get("bot_running", 0)
    logged = status.get("logged_in", 0)

    # Weight check
    weight = player.get("weight", 0)
    max_weight = player.get("max_weight", 1) or 1
    weight_pct = (weight / max_weight) * 100 if max_weight > 0 else 0

    problems: list[str] = []
    if not logged:
        problems.append("離線")
    if hp_pct < 30:
        problems.append(f"HP低({hp_pct:.0f}%)")
    if mp_pct < 10:
        problems.append(f"MP低({mp_pct:.0f}%)")
    if arrows > 0 and arrows < 100:
        problems.append(f"箭不足({arrows})")
    if not bot_on and logged:
        problems.append("bot未運行")
    if weight_pct > 80:
        problems.append(f"負重高({weight_pct:.0f}%)")

    return json.dumps({
        "name": status.get("char_name", "?"),
        "level": status.get("level", 0),
        "class": status.get("class_name", "?"),
        "map": status.get("map_name", "?"),
        "hp_pct": round(hp_pct, 1),
        "mp_pct": round(mp_pct, 1),
        "arrows": arrows,
        "weight_pct": round(weight_pct, 1),
        "buff_count": len(buffs),
        "bot_running": bot_on,
        "healthy": len(problems) == 0,
        "problems": problems,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def bot_teleport_scroll(dest: str, port: int = 0, host: str = "") -> str:
    """用說話的卷軸(F12)傳送到指定目的地。
    dest 格式: "村莊|傳送點" 例如 "說話之島|雜貨商人"。
    自動找卷軸 → 開啟 → 選目的地 → 等待傳送完成。"""
    # 1) 找說話的卷軸
    inv_r = await _http(port, "GET", "/inventory", host=host)
    try:
        inv = json.loads(inv_r).get("data", {})
        items = inv.get("items", [])
    except Exception:
        return json.dumps({"error": "cannot read inventory"})

    scroll = None
    for it in items:
        name = it.get("name", "")
        if "說話的卷軸" in name:
            scroll = it
            break
    if not scroll:
        return json.dumps({"error": "找不到說話的卷軸"})

    # 2) 按 F12 開啟說話的卷軸 UI
    await _http(port, "POST", "/bot/glfw_key",
                body={"key": 301}, host=host)

    # 3) 等 TalkingScrollLayout visible
    if not await _wait_dialog_visible("TalkingScrollLayout", port, host, timeout_ms=5000):
        return json.dumps({"error": "TalkingScrollLayout 未出現"})

    # 4) 點擊目的地傳送
    use_r = await _http(port, "POST", "/scroll_dest",
                        body={"dest": dest}, host=host)
    await asyncio.sleep(4.0)

    # 4) 確認新位置
    pos_r = await _http(port, "GET", "/position", host=host)
    try:
        pos = json.loads(pos_r).get("data", {})
    except Exception:
        pos = {}

    return json.dumps({
        "status": "teleported",
        "dest": dest,
        "scroll_used": scroll.get("name", ""),
        "position": pos,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def bot_teleport_blessed(dest: str, port: int = 0, host: str = "") -> str:
    """用祝福卷軸(F11)傳送到書籤位置。
    dest: 書籤名稱（模糊匹配）。
    自動掃描書籤 → 找匹配 → 傳送。"""
    # 1) 按 F11 開啟書籤 UI + 掃描
    await _http(port, "POST", "/bot/glfw_key",
                body={"key": 300}, host=host)
    if not await _wait_dialog_visible("BookmarkLayout", port, host, timeout_ms=5000):
        return json.dumps({"error": "BookmarkLayout 未出現"})

    scan_r = await _http(port, "POST", "/bm_scan", host=host)
    await asyncio.sleep(1.0)

    bm_r = await _http(port, "GET", "/bm_list", host=host)
    try:
        bm_data = json.loads(bm_r).get("data", {})
        bookmarks = bm_data.get("bookmarks", [])
    except Exception:
        return json.dumps({"error": "cannot read bookmarks"})

    if not bookmarks:
        return json.dumps({"error": "沒有書籤"})

    # 2) 模糊匹配
    matched = None
    for bm in bookmarks:
        if dest in bm.get("name", ""):
            matched = bm
            break
    if not matched:
        names = [b.get("name", "") for b in bookmarks]
        return json.dumps({"error": f"找不到書籤 '{dest}'",
                          "available": names}, ensure_ascii=False)

    # 3) 傳送
    click_r = await _http(port, "POST", "/bm_click",
                          body={"name": matched["name"]}, host=host)
    await asyncio.sleep(4.0)

    # 4) 確認位置
    pos_r = await _http(port, "GET", "/position", host=host)
    try:
        pos = json.loads(pos_r).get("data", {})
    except Exception:
        pos = {}

    return json.dumps({
        "status": "teleported",
        "bookmark": matched.get("name", ""),
        "position": pos,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def bot_buy_from_npc(
    npc: str,
    items: str,
    scroll_dest: str = "",
    port: int = 0,
    host: str = "",
) -> str:
    """從 NPC 購買物品。支援一次買多樣，自動模糊匹配物品名稱。
    npc: NPC 名稱（如 潘朵拉、露西）。
    items: 物品清單，支援多種格式：
      多樣: '[{"name":"治癒藥水","qty":10},{"name":"解毒藥水","qty":10}]'
      單樣: '{"name":"治癒藥水","qty":10}'
      簡寫: '治癒藥水'（預設 qty=1）
    qty=實際購買數量（10=買10個）。名稱會自動模糊匹配商店物品。
    scroll_dest: 可選，先用說話的卷軸傳送（格式 "村莊|NPC"）。"""
    try:
        item_list = json.loads(items)
        if not isinstance(item_list, list):
            item_list = [item_list]
    except Exception:
        item_list = [{"name": items, "qty": 1}]

    # 1) 傳送（如果指定）
    if scroll_dest:
        tp_r = await bot_teleport_scroll(scroll_dest, port, host)
        try:
            tp = json.loads(tp_r)
            if "error" in tp:
                return tp_r
        except Exception:
            pass
        await asyncio.sleep(1.0)

    # 2) interact NPC → 等 NpcTalkLayout
    err = await _npc_interact_and_wait(npc, port, host)
    if err:
        return err

    # 3) 點 Bt_Npc_Buy 開商店（不用文字搜尋）
    click_r = await _http(port, "POST", "/bot/click",
                          body={"dialog": "NpcTalkLayout", "widget": "Bt_Npc_Buy"}, host=host)
    try:
        cr = json.loads(click_r).get("data", {})
        if cr.get("result") != 2:
            return json.dumps({"error": "Bt_Npc_Buy 點擊失敗", "detail": cr},
                              ensure_ascii=False)
    except Exception:
        return json.dumps({"error": "Bt_Npc_Buy 失敗", "raw": click_r[:200]})

    # 4) 等 NpcShopLayout visible
    if not await _wait_dialog_visible("NpcShopLayout", port, host, timeout_ms=5000):
        return json.dumps({"error": "NpcShopLayout 未出現"})

    # 5) 查 shoplist 取得實際物品名稱（用於模糊匹配）
    shop_names: list[str] = []
    shop_r = await _http(port, "GET", "/shop/list", host=host)
    try:
        shop_data = json.loads(shop_r).get("data", {})
        shop_names = [si.get("name", "") for si in shop_data.get("items", [])]
    except Exception:
        pass

    # 6) 逐一選取物品（confirm=0，不按 Bt_Buy）
    results: list[dict] = []
    for item in item_list:
        name = item.get("name", item) if isinstance(item, dict) else str(item)
        qty = item.get("qty", 1) if isinstance(item, dict) else 1

        # 模糊匹配：玩家說的名字 → 商店實際名稱
        actual_name = _fuzzy_match(name, shop_names) if shop_names else name
        if actual_name and actual_name != name:
            matched_from = name
            name = actual_name
        else:
            matched_from = None

        if not await _wait_dialog_visible("NpcShopLayout", port, host, timeout_ms=2000):
            results.append({"name": name, "error": "NpcShopLayout 消失"})
            break

        r = await _http(port, "POST", "/shop/buy",
                        body={"item_name": name, "qty": qty, "confirm": 0}, host=host)
        try:
            data = json.loads(r).get("data", {})
            result_entry: dict = {"name": name, "qty": qty, "ok": data.get("ok", 0)}
            if matched_from:
                result_entry["matched_from"] = matched_from
            results.append(result_entry)
        except Exception:
            results.append({"name": name, "error": r[:200]})
        await asyncio.sleep(0.3)

    # 6) 統一按 Bt_Buy
    confirm_r = 0
    if any(r.get("ok") for r in results):
        cr = await _http(port, "POST", "/shop/confirm", host=host)
        try:
            confirm_r = json.loads(cr).get("data", {}).get("confirm", 0)
        except Exception:
            pass

    return json.dumps({
        "status": "purchased",
        "npc": npc,
        "confirm": confirm_r,
        "items": results,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def bot_teleport_npc(
    dest: str,
    scroll_dest: str = "",
    npc_name: str = "",
    port: int = 0,
    host: str = "",
) -> str:
    """透過傳送師 NPC 傳送到其他地區（說話卷軸無法直達的地點）。
    dest: 目的地名稱（如 海音、亞丁、乘風、象牙塔）。自動模糊匹配。
    scroll_dest: 先傳送到傳送師旁（如 '奇岩村|傳送師'），省略則假設已在傳送師旁。
    npc_name: 傳送師名稱，省略則自動從 entities 找 type=InteractiveNPC。
    流程：scroll傳送(可選) → interact 傳送師 → 想去其他地區 → 選目的地。"""
    # 1) 傳送到傳送師旁（如果指定）
    if scroll_dest:
        tp_r = await bot_teleport_scroll(scroll_dest, port, host)
        try:
            tp = json.loads(tp_r)
            if "error" in tp:
                return tp_r
        except Exception:
            pass
        await asyncio.sleep(1.0)

    # 2) 找傳送師 NPC
    if npc_name:
        npc = await _find_npc(npc_name, port, host)
    else:
        # 自動找：從 entities 找已知傳送師名稱
        known_teleporters = ["盧卡斯", "史提夫", "爾瑪"]
        npc = None
        r = await _http(port, "GET", "/entities", host=host)
        try:
            ents = json.loads(r).get("data", {}).get("entities", [])
            for e in ents:
                if e.get("type", "") in ("InteractiveNPC", "NPC"):
                    for kt in known_teleporters:
                        if kt in e.get("name", ""):
                            npc = e
                            break
                    if npc:
                        break
        except Exception:
            pass
    if not npc:
        return json.dumps({"error": "找不到傳送師 NPC"},
                          ensure_ascii=False)

    # 3) interact 傳送師
    await _http(port, "POST", "/bot/interact",
                body={"entity_id": npc["id"]}, host=host)
    await asyncio.sleep(3.0)
    if not await _wait_dialog_visible("NpcTalkLayout", port, host, timeout_ms=5000):
        return json.dumps({"error": "NpcTalkLayout 未出現"})

    # 4) 點「想去其他地區」
    r = await _http(port, "POST", "/npc_click",
                    body={"dialog": "NpcTalkLayout", "keyword": "想去其他地區", "nth": 1},
                    host=host)
    try:
        data = json.loads(r).get("data", {})
        if data.get("result") != 2:
            return json.dumps({"error": "點擊'想去其他地區'失敗", "detail": data},
                              ensure_ascii=False)
    except Exception:
        return json.dumps({"error": "npc_click 失敗", "raw": r[:200]})
    await asyncio.sleep(1.0)

    # 5) 點目的地（模糊匹配）
    r = await _http(port, "POST", "/npc_click",
                    body={"dialog": "NpcTalkLayout", "keyword": dest, "nth": 1},
                    host=host)
    try:
        data = json.loads(r).get("data", {})
        if data.get("result") != 2:
            return json.dumps({"error": f"點擊'{dest}'失敗", "detail": data},
                              ensure_ascii=False)
    except Exception:
        return json.dumps({"error": f"npc_click '{dest}' 失敗", "raw": r[:200]})

    # 6) 等待傳送完成（位置變化）
    await asyncio.sleep(5.0)
    sr = await _http(port, "GET", "/status", host=host)
    try:
        status = json.loads(sr).get("data", {})
        new_pos = {"x": status.get("x", 0), "y": status.get("y", 0)}
        new_map = status.get("map_name", "?")
    except Exception:
        new_pos = {}
        new_map = "?"

    return json.dumps({
        "status": "teleported",
        "dest": dest,
        "npc": npc.get("name", "?"),
        "position": new_pos,
        "map": new_map,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def bot_warehouse_list(
    npc_name: str = "朵琳",
    wh_type: str = "personal",
    port: int = 0,
    host: str = "",
) -> str:
    """查看倉庫物品列表。
    完整流程（學自 DLL mod_warehouse）：
      interact NPC → 等 NpcTalkLayout → 點「取回物品」→ 等 StorageLayout → /wh/list
    npc_name: 倉庫管理員名稱（預設朵琳=說話之島）。
    wh_type: personal(個人,nth=1) 或 pledge(血盟,nth=2)。"""
    nth = 1 if wh_type == "personal" else 2

    # 1) interact NPC → 等 NpcTalkLayout
    err = await _npc_interact_and_wait(npc_name, port, host)
    if err:
        return err

    # 2) 點「取回物品」nth=1(個人) 或 nth=2(血盟)
    err = await _npc_click_and_check("取回物品", nth, port, host)
    if err:
        return err

    # 3) 等 StorageLayout 出現 + 2.5s 載入（DLL: initial wait 2500ms）
    if not await _wait_dialog_visible("StorageLayout", port, host, timeout_ms=5000):
        return json.dumps({"error": "StorageLayout 未出現"})
    await asyncio.sleep(2.5)

    # 4) 讀物品列表
    list_r = await _http(port, "GET", "/wh/list", host=host)
    try:
        data = json.loads(list_r).get("data", {})
    except Exception:
        data = {"raw": list_r[:200]}

    return json.dumps({
        "status": "ok",
        "wh_type": wh_type,
        "npc": npc_name,
        "items": data.get("items", []),
        "count": data.get("count", 0),
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def bot_warehouse_deposit(
    items: str,
    npc_name: str = "朵琳",
    wh_type: str = "personal",
    port: int = 0,
    host: str = "",
) -> str:
    """存入物品到倉庫。自動模糊匹配物品名稱。
    items: 物品清單，支援多種格式：
      多樣: '[{"name":"金幣","qty":500},{"name":"蠟燭","qty":0}]'
      單樣: '{"name":"金幣","qty":500}'
      簡寫: '蠟燭'（預設 qty=0=全部存入）
    qty=存入數量（可堆疊物品用 GLFW 輸入精確數量），qty=0=全部。
    不可堆疊物品自動遍歷所有同名 slot 逐一選取。"""
    try:
        item_list = json.loads(items)
        if not isinstance(item_list, list):
            item_list = [item_list]
    except Exception:
        item_list = [{"name": items, "qty": 0}]

    # ── Step 0: 查包包，確認物品存在 ──
    inv_r = await _http(port, "GET", "/inventory", host=host)
    try:
        inv_data = json.loads(inv_r).get("data", {})
        inv_items = inv_data.get("items", []) if isinstance(inv_data, dict) else []
    except Exception:
        return json.dumps({"error": "無法讀取 inventory", "raw": inv_r[:200]},
                          ensure_ascii=False)

    # 建立每個請求物品的包包資訊（模糊匹配玩家說的名稱）
    inv_names = [inv.get("name", "").strip() for inv in inv_items]
    deposit_plan: list[dict] = []
    for item in item_list:
        name = item.get("name", item) if isinstance(item, dict) else str(item)
        qty = item.get("qty", 0) if isinstance(item, dict) else 0
        # 模糊匹配玩家名稱 → 包包實際名稱
        actual = _fuzzy_match(name, inv_names)
        if actual and actual != name:
            name = actual  # 用匹配到的實際名稱
        # 在包包裡找所有同名物品
        matching = [inv for inv in inv_items if name in inv.get("name", "")]
        total_on_char = sum(m.get("qty", 0) for m in matching)
        entry_count = len(matching)
        # 判斷是否可堆疊：只有 1 筆且 qty > 1，或 0 筆
        stackable = (entry_count == 1 and matching[0].get("qty", 1) > 1) if entry_count > 0 else False
        if entry_count == 0 or total_on_char == 0:
            deposit_plan.append({
                "name": name, "skip": True,
                "reason": f"包包沒有 '{name}'",
                "on_char": 0, "entries": 0,
            })
            continue
        deposit_plan.append({
            "name": name, "skip": False,
            "on_char": total_on_char, "entries": entry_count,
            "stackable": stackable, "qty": qty,
        })

    # 如果全部都 skip，不用開 NPC
    if all(p.get("skip") for p in deposit_plan):
        return json.dumps({
            "status": "deposit",
            "error": "包包沒有任何要存的物品",
            "plan": deposit_plan,
        }, ensure_ascii=False, indent=2)

    # ── Step 1: interact NPC → 等 NpcTalkLayout ──
    nth = 1 if wh_type == "personal" else 2
    err = await _npc_interact_and_wait(npc_name, port, host)
    if err:
        return err

    # ── Step 2: 點「存放物品」→ 等 StorageLayout ──
    err = await _npc_click_and_check("存放物品", nth, port, host)
    if err:
        return err
    if not await _wait_dialog_visible("StorageLayout", port, host, timeout_ms=5000):
        return json.dumps({"error": "StorageLayout 未出現"})
    await asyncio.sleep(2.5)

    # ── Step 3: 逐一選取物品（confirm=0） ──
    results: list[dict] = []
    total_selected = 0
    for plan in deposit_plan:
        if plan.get("skip"):
            results.append({"name": plan["name"], "selected": 0,
                            "reason": plan.get("reason", "skip")})
            continue

        name = plan["name"]
        qty = plan["qty"]

        # 每次操作前檢查 StorageLayout 還在
        if not await _wait_dialog_visible("StorageLayout", port, host, timeout_ms=2000):
            results.append({"name": name, "selected": 0,
                            "error": "StorageLayout 消失了"})
            break

        r = await _http(port, "POST", "/wh/click_slot",
                        body={"item_name": name, "qty": qty, "confirm": 0}, host=host)
        try:
            data = json.loads(r).get("data", {})
            selected = data.get("selected", 0)
            results.append({
                "name": name, "selected": selected,
                "on_char": plan["on_char"], "entries": plan["entries"],
                "stackable": plan["stackable"],
            })
            total_selected += selected
        except Exception:
            results.append({"name": name, "error": r[:200]})
        await asyncio.sleep(0.5)

    # ── Step 4: 全部選完，按 Bt_Ok 確認 ──
    confirm_r = 0
    if total_selected > 0:
        if not await _wait_dialog_visible("StorageLayout", port, host, timeout_ms=2000):
            return json.dumps({
                "status": "deposit", "error": "確認前 StorageLayout 消失",
                "total_selected": total_selected, "items": results,
            }, ensure_ascii=False, indent=2)
        cr = await _http(port, "POST", "/wh/confirm", host=host)
        try:
            confirm_r = json.loads(cr).get("data", {}).get("confirm", 0)
        except Exception:
            pass

    return json.dumps({
        "status": "deposit",
        "total_selected": total_selected,
        "confirm": confirm_r,
        "items": results,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def bot_warehouse_withdraw(
    items: str,
    npc_name: str = "朵琳",
    wh_type: str = "personal",
    port: int = 0,
    host: str = "",
) -> str:
    """從倉庫取回物品。自動模糊匹配物品名稱。
    items: 物品清單，支援多種格式：
      多樣: '[{"name":"蠟燭","qty":0},{"name":"金幣","qty":500}]'
      單樣: '{"name":"蠟燭","qty":0}'
      簡寫: '蠟燭'（預設 qty=0=全部取回）
    qty=取回數量（可堆疊物品用 GLFW 輸入精確數量），qty=0=全部。
    不可堆疊物品自動遍歷所有同名 slot 逐一選取。"""
    try:
        item_list = json.loads(items)
        if not isinstance(item_list, list):
            item_list = [item_list]
    except Exception:
        item_list = [{"name": items, "qty": 0}]

    # ── Step 1: interact NPC → 等 NpcTalkLayout ──
    nth = 1 if wh_type == "personal" else 2
    err = await _npc_interact_and_wait(npc_name, port, host)
    if err:
        return err

    # ── Step 2: 點「取回物品」→ 等 StorageLayout ──
    err = await _npc_click_and_check("取回物品", nth, port, host)
    if err:
        return err
    if not await _wait_dialog_visible("StorageLayout", port, host, timeout_ms=5000):
        return json.dumps({"error": "StorageLayout 未出現"})
    await asyncio.sleep(2.5)

    # ── Step 3: 先查倉庫有什麼（/wh/list） ──
    wh_items: list[dict] = []
    list_r = await _http(port, "GET", "/wh/list", host=host)
    try:
        list_data = json.loads(list_r).get("data", {})
        wh_items = list_data.get("items", []) if isinstance(list_data, dict) else []
    except Exception:
        pass

    # ── Step 4: 逐一選取物品（confirm=0，模糊匹配名稱） ──
    wh_names = [w.get("name", "").strip() for w in wh_items]
    results: list[dict] = []
    total_selected = 0
    for item in item_list:
        name = item.get("name", item) if isinstance(item, dict) else str(item)
        qty = item.get("qty", 0) if isinstance(item, dict) else 0

        # 模糊匹配玩家名稱 → 倉庫實際名稱
        actual = _fuzzy_match(name, wh_names) if wh_names else None
        if actual and actual != name:
            name = actual

        # 檢查倉庫裡是否有這個物品
        matching_wh = [w for w in wh_items if name in w.get("name", "")]
        if wh_items and not matching_wh:
            results.append({"name": name, "selected": 0,
                            "reason": f"倉庫沒有 '{name}'"})
            continue

        # 每次操作前檢查 StorageLayout 還在
        if not await _wait_dialog_visible("StorageLayout", port, host, timeout_ms=2000):
            results.append({"name": name, "selected": 0,
                            "error": "StorageLayout 消失了"})
            break

        r = await _http(port, "POST", "/wh/click_slot",
                        body={"item_name": name, "qty": qty, "confirm": 0}, host=host)
        try:
            data = json.loads(r).get("data", {})
            selected = data.get("selected", 0)
            results.append({"name": name, "selected": selected,
                            "in_wh": len(matching_wh)})
            total_selected += selected
        except Exception:
            results.append({"name": name, "error": r[:200]})
        await asyncio.sleep(0.5)

    # ── Step 5: 全部選完，按 Bt_Ok 確認 ──
    confirm_r = 0
    if total_selected > 0:
        if not await _wait_dialog_visible("StorageLayout", port, host, timeout_ms=2000):
            return json.dumps({
                "status": "withdraw", "error": "確認前 StorageLayout 消失",
                "total_selected": total_selected, "items": results,
            }, ensure_ascii=False, indent=2)
        cr = await _http(port, "POST", "/wh/confirm", host=host)
        try:
            confirm_r = json.loads(cr).get("data", {}).get("confirm", 0)
        except Exception:
            pass

    return json.dumps({
        "status": "withdraw",
        "total_selected": total_selected,
        "confirm": confirm_r,
        "items": results,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def bot_full_supply(port: int = 0, host: str = "") -> str:
    """觸發自動補給流程（DLL 內建狀態機）。
    會回城買東西再回到原位。輪詢 supply/state 等待完成。"""
    # 1) 觸發補給
    trig_r = await _http(port, "POST", "/supply/trigger", host=host)
    try:
        trig = json.loads(trig_r).get("data", {})
        if "error" in json.loads(trig_r):
            return trig_r
    except Exception:
        return json.dumps({"error": "trigger failed", "raw": trig_r[:200]})

    # 2) 輪詢等待完成（最多 120 秒）
    deadline = time.time() + 120
    last_state = "unknown"
    while time.time() < deadline:
        await asyncio.sleep(3.0)
        state_r = await _http(port, "GET", "/supply/state", host=host)
        try:
            state = json.loads(state_r).get("data", {})
            last_state = state.get("state", "unknown")
            if last_state in ("IDLE", "idle", "SUPPLY_IDLE"):
                return json.dumps({
                    "status": "supply_complete",
                    "final_state": last_state,
                }, ensure_ascii=False, indent=2)
        except Exception:
            pass

    return json.dumps({
        "status": "timeout",
        "last_state": last_state,
        "message": "補給超過120秒未完成",
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def bot_equip_status(port: int = 0, host: str = "") -> str:
    """查詢戰鬥裝備狀態：每件裝備 EQUIPPED/IN_BAG/MISSING + 狀態機進度。"""
    return await _http(port, "GET", "/bot/equip", host=host)


@mcp.tool()
async def bot_equip_wear(port: int = 0, host: str = "") -> str:
    """觸發穿戰鬥裝備流程（測試領取）。
    掃包包 → 缺少去倉庫領 → 逐一穿上 → 驗證。輪詢等待完成。"""
    r = await _http(port, "POST", "/bot/equip", body={"action": "wear"}, host=host)
    try:
        data = json.loads(r).get("data", {})
        if "error" in data:
            return r
    except Exception:
        return r

    # Poll until done (max 120s)
    deadline = time.time() + 120
    last_state = "unknown"
    while time.time() < deadline:
        await asyncio.sleep(3.0)
        sr = await _http(port, "GET", "/bot/equip", host=host)
        try:
            sd = json.loads(sr).get("data", {})
            last_state = sd.get("state", "unknown")
            if last_state in ("DONE", "IDLE"):
                return json.dumps({
                    "status": "equip_complete",
                    "state": last_state,
                    "items": sd.get("items", []),
                }, ensure_ascii=False, indent=2)
        except Exception:
            pass

    return json.dumps({
        "status": "timeout",
        "last_state": last_state,
        "message": "裝備流程超過120秒未完成",
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def bot_equip_return(port: int = 0, host: str = "") -> str:
    """觸發脫裝備+回存流程（測試下班）。
    脫下裝備 → 存回倉庫。輪詢等待完成。"""
    r = await _http(port, "POST", "/bot/equip", body={"action": "return"}, host=host)
    try:
        data = json.loads(r).get("data", {})
        if "error" in data:
            return r
    except Exception:
        return r

    # Poll until done (max 120s)
    deadline = time.time() + 120
    last_state = "unknown"
    while time.time() < deadline:
        await asyncio.sleep(3.0)
        sr = await _http(port, "GET", "/bot/equip", host=host)
        try:
            sd = json.loads(sr).get("data", {})
            last_state = sd.get("state", "unknown")
            if last_state in ("RETURN_DONE", "IDLE"):
                return json.dumps({
                    "status": "return_complete",
                    "state": last_state,
                    "items": sd.get("items", []),
                }, ensure_ascii=False, indent=2)
        except Exception:
            pass

    return json.dumps({
        "status": "timeout",
        "last_state": last_state,
        "message": "回存流程超過120秒未完成",
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def bot_start_grinding(
    profile: str = "",
    dest: str = "",
    set_center: int = 1,
    port: int = 0,
    host: str = "",
) -> str:
    """一鍵開始掛機：載入設定檔 → 傳送到目的地 → 設定掛機中心 → 啟動 bot。
    profile: 設定檔名稱（可選，不指定則用當前設定）。
    dest: 傳送目的地（可選，格式 "村莊|傳送點"）。
    set_center: 1=自動把當前座標設為掛機中心(預設)，0=不設。"""
    steps: list[dict] = []

    # 1) 載入設定檔
    if profile:
        prof_r = await _http(port, "POST", "/profile/load",
                             body={"name": profile}, host=host)
        try:
            prof = json.loads(prof_r)
            steps.append({"step": "profile_load", "ok": "error" not in prof,
                          "profile": profile})
            if "error" in prof:
                return json.dumps({"error": f"載入設定檔失敗: {profile}",
                                  "detail": prof}, ensure_ascii=False)
        except Exception:
            return json.dumps({"error": "profile_load failed"})
        await asyncio.sleep(1.0)

    # 2) 傳送
    if dest:
        tp_r = await bot_teleport_scroll(dest, port, host)
        try:
            tp = json.loads(tp_r)
            steps.append({"step": "teleport", "ok": "error" not in tp,
                          "dest": dest})
            if "error" in tp:
                return json.dumps({"error": f"傳送失敗: {dest}",
                                  "detail": tp}, ensure_ascii=False)
        except Exception:
            pass

    # 2.5) 設定掛機中心為當前座標
    if set_center:
        pos_r = await _http(port, "GET", "/position", host=host)
        try:
            pos = json.loads(pos_r).get("data", {})
            cx, cy = pos.get("x", 0), pos.get("y", 0)
            if cx > 0 and cy > 0:
                await _http(port, "POST", "/bot/config",
                            body={"combat_center_x": cx, "combat_center_y": cy},
                            host=host)
                steps.append({"step": "set_center", "ok": True,
                              "x": cx, "y": cy})
        except Exception:
            steps.append({"step": "set_center", "ok": False})

    # 3) 啟動 bot
    start_r = await _http(port, "POST", "/bot/start", host=host)
    try:
        start = json.loads(start_r)
        steps.append({"step": "bot_start",
                      "ok": "error" not in start})
    except Exception:
        steps.append({"step": "bot_start", "ok": False})

    return json.dumps({
        "status": "grinding_started",
        "steps": steps,
    }, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
#  Setup Tools — 語意化配置介面 (Layer 3)
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def bot_setup_supply(
    buy_items: str = "",
    sell_items: str = "",
    town_dest: str = "",
    return_dest: str = "",
    npc_name: str = "",
    npc_x: int = 0,
    npc_y: int = 0,
    town_scroll: str = "說話的卷軸",
    return_scroll: str = "說話的卷軸",
    weight_pct: int = 80,
    enabled: int = 1,
    port: int = 0,
    host: str = "",
) -> str:
    """配置自動補給系統。設完後 bot_supply_trigger 或 bot_full_supply 會用這些設定。
    buy_items: JSON array '[{"item_name":"回復藥水","buy_qty":100,"trigger_qty":20}]'
    sell_items: JSON array '[{"item_name":"短劍","keep_qty":0}]' (keep_qty=0=全賣)
    town_dest: 回城目的地 "村莊|傳送點" (如 "說話之島|雜貨商人")
    return_dest: 回掛機點目的地 "村莊|傳送點"
    npc_name: 購買NPC名稱 (如 "潘朵拉")
    npc_x, npc_y: NPC座標 (0=不走路，直接interact)"""
    cfg: dict = {
        "supply_enabled": enabled,
        "supply_weight_pct": weight_pct,
        "supply_town_scroll": town_scroll,
        "supply_return_scroll": return_scroll,
    }
    if town_dest:
        cfg["supply_town_dest"] = town_dest
    if return_dest:
        cfg["supply_return_dest"] = return_dest
    if npc_name:
        cfg["supply_npc_name"] = npc_name
    if npc_x > 0:
        cfg["supply_npc_x"] = npc_x
    if npc_y > 0:
        cfg["supply_npc_y"] = npc_y
    if buy_items:
        try:
            items = json.loads(buy_items)
            cfg["supply_items"] = items
            cfg["supply_item_count"] = len(items)
        except Exception:
            return json.dumps({"error": "buy_items JSON 格式錯誤"})
    if sell_items:
        try:
            items = json.loads(sell_items)
            cfg["supply_sell_items"] = items
            cfg["supply_sell_count"] = len(items)
        except Exception:
            return json.dumps({"error": "sell_items JSON 格式錯誤"})

    r = await _http(port, "POST", "/bot/config", body=cfg, host=host)
    try:
        data = json.loads(r)
        if isinstance(data, dict) and "error" in data:
            return r
    except Exception:
        pass

    return json.dumps({
        "status": "supply_configured",
        "config": cfg,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def bot_setup_combat(
    center_x: int = -1,
    center_y: int = -1,
    radius: int = 0,
    priority: str = "",
    blacklist: str = "",
    whitelist: str = "",
    blacklist_mode: int = -1,
    attack_dist: int = 0,
    roam_mode: int = -1,
    enabled: int = 1,
    port: int = 0,
    host: str = "",
) -> str:
    """設置掛機戰鬥參數。center_x/y=-1 時自動用角色當前座標。
    priority: 優先怪物 pipe 分隔 "怪物A|怪物B"
    blacklist: 黑名單 pipe 分隔
    whitelist: 白名單 pipe 分隔
    blacklist_mode: 0=黑名單, 1=白名單
    roam_mode: 0=raycast, 1=spiral, 2=levy, 3=sector"""
    cfg: dict = {"combat_enabled": enabled}

    # 自動取當前座標
    if center_x < 0 or center_y < 0:
        pos_r = await _http(port, "GET", "/position", host=host)
        try:
            pos = json.loads(pos_r).get("data", {})
            if center_x < 0:
                cfg["combat_center_x"] = pos.get("x", 0)
            if center_y < 0:
                cfg["combat_center_y"] = pos.get("y", 0)
        except Exception:
            pass
    else:
        cfg["combat_center_x"] = center_x
        cfg["combat_center_y"] = center_y

    if radius > 0:
        cfg["combat_radius"] = radius
    if priority:
        cfg["combat_priority"] = priority
    if blacklist:
        cfg["combat_blacklist"] = blacklist
    if whitelist:
        cfg["combat_whitelist"] = whitelist
    if blacklist_mode >= 0:
        cfg["combat_blacklist_mode"] = blacklist_mode
    if attack_dist > 0:
        cfg["combat_attack_dist"] = attack_dist
    if roam_mode >= 0:
        cfg["combat_roam_mode"] = roam_mode

    r = await _http(port, "POST", "/bot/config", body=cfg, host=host)
    try:
        data = json.loads(r)
        if isinstance(data, dict) and "error" in data:
            return r
    except Exception:
        pass

    return json.dumps({
        "status": "combat_configured",
        "config": cfg,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def bot_setup_protect(
    escape_enabled: int = -1,
    escape_items: str = "",
    escape_hp_pct: int = 0,
    death_enabled: int = -1,
    death_count: int = 0,
    death_window_min: int = 0,
    death_pause_min: int = 0,
    resurrect: int = -1,
    resurrect_delay_ms: int = 0,
    return_enabled: int = -1,
    return_item: str = "",
    return_dest: str = "",
    return_script: str = "",
    port: int = 0,
    host: str = "",
) -> str:
    """設置保護系統（死亡重生、緊急逃跑、死頻暫停、回點）。
    escape_items: 逃跑用物品 pipe 分隔 "傳送捲軸|回城捲軸"
    escape_hp_pct: HP%低於此值觸發逃跑
    death_count: N次死亡觸發暫停
    death_window_min: 在M分鐘內
    death_pause_min: 暫停N分鐘
    return_item: 回點用卷軸名
    return_dest: 回點目的地 "村莊|傳送點"
    return_script: 回掛機點nav腳本名"""
    cfg: dict = {"protect_enabled": 1}

    if escape_enabled >= 0:
        cfg["protect_escape_enabled"] = escape_enabled
    if escape_items:
        cfg["protect_escape_items"] = escape_items
    if escape_hp_pct > 0:
        cfg["protect_escape_hp_pct"] = escape_hp_pct
    if death_enabled >= 0:
        cfg["protect_death_enabled"] = death_enabled
    if death_count > 0:
        cfg["protect_death_count"] = death_count
    if death_window_min > 0:
        cfg["protect_death_window_min"] = death_window_min
    if death_pause_min > 0:
        cfg["protect_death_pause_min"] = death_pause_min
    if resurrect >= 0:
        cfg["protect_resurrect"] = resurrect
    if resurrect_delay_ms > 0:
        cfg["protect_resurrect_delay_ms"] = resurrect_delay_ms
    if return_enabled >= 0:
        cfg["protect_return_enabled"] = return_enabled
    if return_item:
        cfg["protect_return_item"] = return_item
    if return_dest:
        cfg["protect_return_dest"] = return_dest
    if return_script:
        cfg["protect_return_script"] = return_script

    r = await _http(port, "POST", "/bot/config", body=cfg, host=host)
    try:
        data = json.loads(r)
        if isinstance(data, dict) and "error" in data:
            return r
    except Exception:
        pass

    return json.dumps({
        "status": "protect_configured",
        "config": cfg,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def bot_setup_loot(
    enabled: int = 1,
    filter_mode: int = -1,
    filter_items: str = "",
    loot_range: int = 0,
    priority: int = -1,
    my_kill_only: int = -1,
    crowd_threshold: int = 0,
    port: int = 0,
    host: str = "",
) -> str:
    """設置撿物系統。
    filter_mode: 0=無過濾, 1=黑名單(不撿), 2=白名單(只撿)
    filter_items: 物品名稱 pipe 分隔 "短劍|木材|回復藥水"
    loot_range: 撿物範圍(格數)
    priority: 0=先打後撿, 1=先撿後打
    my_kill_only: 1=只撿自己殺的
    crowd_threshold: 周圍玩家>N時不撿"""
    cfg: dict = {"loot_enabled": enabled}

    if filter_mode >= 0:
        cfg["loot_filter_mode"] = filter_mode
    if filter_items:
        cfg["loot_items"] = filter_items
    if loot_range > 0:
        cfg["loot_range"] = loot_range
    if priority >= 0:
        cfg["loot_priority"] = priority
    if my_kill_only >= 0:
        cfg["loot_my_kill_only"] = my_kill_only
    if crowd_threshold > 0:
        cfg["loot_crowd_threshold"] = crowd_threshold

    r = await _http(port, "POST", "/bot/config", body=cfg, host=host)
    try:
        data = json.loads(r)
        if isinstance(data, dict) and "error" in data:
            return r
    except Exception:
        pass

    return json.dumps({
        "status": "loot_configured",
        "config": cfg,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def bot_return_to_grind(
    scroll_dest: str = "",
    nav_script: str = "",
    start_bot: int = 1,
    port: int = 0,
    host: str = "",
) -> str:
    """回到掛機點：傳送 → 跑nav腳本 → 啟動bot。
    scroll_dest: 傳送目的地 "村莊|傳送點" (不指定則用config中的supply_return_dest)
    nav_script: 導航腳本名稱 (不指定則跳過)
    start_bot: 1=最後自動啟動bot"""
    steps: list[dict] = []

    # 1) 決定傳送目的地
    dest = scroll_dest
    if not dest:
        cfg_r = await _http(port, "GET", "/bot/config", host=host)
        try:
            parts = json.loads(cfg_r).get("data", {}).get("parts", [])
            for part in parts:
                if isinstance(part, dict) and "supply_return_dest" in part:
                    dest = part["supply_return_dest"]
                    break
        except Exception:
            pass

    # 2) 傳送
    if dest:
        tp_r = await bot_teleport_scroll(dest, port, host)
        try:
            tp = json.loads(tp_r)
            steps.append({"step": "teleport", "ok": "error" not in tp, "dest": dest})
        except Exception:
            steps.append({"step": "teleport", "ok": False, "dest": dest})

    # 3) 執行nav腳本
    if nav_script:
        nav_r = await _http(port, "POST", "/nav/exec",
                            body={"script_id": nav_script}, host=host)
        try:
            nav = json.loads(nav_r)
            steps.append({"step": "nav_exec", "ok": "error" not in nav,
                          "script": nav_script})
        except Exception:
            steps.append({"step": "nav_exec", "ok": False, "script": nav_script})

        # 等nav完成（最多60秒）
        deadline = time.time() + 60
        while time.time() < deadline:
            await asyncio.sleep(2.0)
            status_r = await _http(port, "GET", "/status", host=host)
            try:
                st = json.loads(status_r).get("data", {})
                if not st.get("nav_running", False):
                    break
            except Exception:
                pass

    # 4) 啟動bot
    if start_bot:
        start_r = await _http(port, "POST", "/bot/start", host=host)
        try:
            start = json.loads(start_r)
            steps.append({"step": "bot_start", "ok": "error" not in start})
        except Exception:
            steps.append({"step": "bot_start", "ok": False})

    return json.dumps({
        "status": "return_complete",
        "steps": steps,
    }, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════════════════

# Populate high-level tools for skill engine access
_HIGH_LEVEL_TOOLS.update({
    "bot_setup_supply": bot_setup_supply,
    "bot_setup_combat": bot_setup_combat,
    "bot_setup_protect": bot_setup_protect,
    "bot_setup_loot": bot_setup_loot,
    "bot_return_to_grind": bot_return_to_grind,
    "bot_check_health": bot_check_health,
    "bot_start_grinding": bot_start_grinding,
    "bot_teleport_scroll": bot_teleport_scroll,
    "bot_teleport_blessed": bot_teleport_blessed,
    "bot_buy_from_npc": bot_buy_from_npc,
    "bot_full_supply": bot_full_supply,
    "bot_warehouse_list": bot_warehouse_list,
    "bot_warehouse_deposit": bot_warehouse_deposit,
    "bot_warehouse_withdraw": bot_warehouse_withdraw,
})

# Register router modules (new tools in separate files)
from routers import opener as _r_opener, schedule as _r_schedule, workshop as _r_workshop
from routers import analytics_router as _r_analytics
_r_opener.register(mcp)
_r_schedule.register(mcp)
_r_workshop.register(mcp)
_r_analytics.register(mcp)

if __name__ == "__main__":
    mcp.run(transport="stdio")
