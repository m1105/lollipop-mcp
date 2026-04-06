"""Analytics — pure calculation functions for bot performance analysis.

All functions are stateless and take dicts/lists as input.
No MCP, no HTTP, no side effects. Easy to unit test.
"""
from __future__ import annotations

import math
from typing import Any

# Minimum bot_ms (5 minutes) to consider a session valid for rate calculation
MIN_SESSION_MS = 300_000


def calc_hourly_rates(stats: dict) -> dict:
    """Calculate kills/hr, gold/hr, deaths/hr from cumulative stats.

    Returns zeros for sessions shorter than 5 minutes (noise filter).
    """
    bot_ms = stats.get("total_bot_ms", 0)
    if bot_ms < MIN_SESSION_MS:
        return {"kills_hr": 0, "gold_hr": 0, "deaths_hr": 0, "hours": 0}
    hours = bot_ms / 3_600_000
    return {
        "kills_hr": round(stats.get("total_kills", 0) / hours, 1),
        "gold_hr": round(stats.get("total_gold_gain", 0) / hours, 0),
        "deaths_hr": round(stats.get("total_deaths", 0) / hours, 2),
        "hours": round(hours, 1),
    }


def rank_bots_by_location(bot_stats: list[dict]) -> dict[str, dict]:
    """Group bots by map, rank by gold/hr, flag underperformers.

    An underperformer is a bot whose gold/hr is < 70% of the location average.
    Returns {map_name: {avg_gold_hr, ranking: [{name, gold_hr, underperformer}]}}.
    """
    by_map: dict[str, list[dict]] = {}
    for s in bot_stats:
        loc = s.get("map_name", "unknown")
        rates = calc_hourly_rates(s)
        if rates["hours"] < 0.5:
            continue
        by_map.setdefault(loc, []).append({
            "name": s.get("char_name", "?"),
            "gold_hr": rates["gold_hr"],
            "kills_hr": rates["kills_hr"],
            "deaths_hr": rates["deaths_hr"],
            "hours": rates["hours"],
        })

    result: dict[str, dict] = {}
    for loc, bots in by_map.items():
        if not bots:
            continue
        avg = sum(b["gold_hr"] for b in bots) / len(bots)
        threshold = avg * 0.7
        for b in bots:
            b["underperformer"] = b["gold_hr"] < threshold
        bots.sort(key=lambda x: x["gold_hr"], reverse=True)
        result[loc] = {"avg_gold_hr": round(avg, 0), "ranking": bots}

    return result


def compare_configs(config_a: dict, config_b: dict) -> list[dict]:
    """Find differences between two bot configs.

    Returns list of {field, value_a, value_b} for differing fields.
    """
    all_keys = set(config_a.keys()) | set(config_b.keys())
    diffs = []
    for k in sorted(all_keys):
        va = config_a.get(k)
        vb = config_b.get(k)
        if va != vb:
            diffs.append({"field": k, "value_a": va, "value_b": vb})
    return diffs


def evaluate_experiment(
    control: list[float],
    treatment: list[float],
    alpha: float = 0.05,
) -> dict:
    """Evaluate A/B experiment using Welch's t-test.

    Returns {significant, p_value, improvement_pct, recommendation, ...}.
    Recommendation: ADOPT (better), REJECT (worse), INCONCLUSIVE.
    """
    if len(control) < 3 or len(treatment) < 3:
        return {
            "significant": False,
            "p_value": 1.0,
            "improvement_pct": 0,
            "recommendation": "INCONCLUSIVE",
            "note": "Need at least 3 samples per group",
            "control_mean": _mean(control),
            "treatment_mean": _mean(treatment),
        }

    mean_c = _mean(control)
    mean_t = _mean(treatment)
    var_c = _variance(control)
    var_t = _variance(treatment)
    n_c = len(control)
    n_t = len(treatment)

    se = math.sqrt(var_c / n_c + var_t / n_t) if (var_c + var_t) > 0 else 1e-10
    t_stat = (mean_t - mean_c) / se

    # Welch-Satterthwaite degrees of freedom
    num = (var_c / n_c + var_t / n_t) ** 2
    denom = ((var_c / n_c) ** 2 / max(n_c - 1, 1) +
             (var_t / n_t) ** 2 / max(n_t - 1, 1))
    df = num / denom if denom > 0 else 1

    # Approximate p-value using t-distribution (two-tailed)
    p_value = _t_test_p_value(abs(t_stat), df)

    improvement_pct = ((mean_t - mean_c) / mean_c * 100) if mean_c > 0 else 0

    if p_value < alpha:
        recommendation = "ADOPT" if mean_t > mean_c else "REJECT"
    else:
        recommendation = "INCONCLUSIVE"

    return {
        "significant": p_value < alpha,
        "p_value": round(p_value, 4),
        "improvement_pct": round(improvement_pct, 1),
        "recommendation": recommendation,
        "control_mean": round(mean_c, 1),
        "treatment_mean": round(mean_t, 1),
        "t_statistic": round(t_stat, 3),
        "degrees_of_freedom": round(df, 1),
        "samples_control": n_c,
        "samples_treatment": n_t,
    }


def detect_anomalies(
    series: list[dict],
    field: str = "kills_hr",
    direction: str = "down",
    threshold_sigma: float = 2.5,
    min_points: int = 4,
) -> list[dict]:
    """Detect anomalies in a time series using EWMA.

    Args:
        series: list of dicts with 'ts' and the target field
        field: which field to monitor
        direction: 'down' (detect drops) or 'up' (detect spikes)
        threshold_sigma: how many sigma to flag
        min_points: minimum data points before flagging

    Returns list of {ts, value, expected, z_score}.
    """
    if len(series) < min_points:
        return []

    # Build baseline from first (min_points - 1) data points
    warmup = [s.get(field, 0) for s in series[:min_points - 1]]
    baseline_mean = _mean(warmup)
    baseline_std = math.sqrt(_variance(warmup)) if len(warmup) >= 2 else 0

    alpha = 0.3
    ewma = baseline_mean
    ewma_var = baseline_std ** 2
    anomalies = []

    for i, point in enumerate(series):
        value = point.get(field, 0)
        residual = value - ewma

        # Compute z BEFORE updating variance (so anomaly doesn't inflate its own sigma)
        sigma = math.sqrt(ewma_var) if ewma_var > 0 else 1e-10
        z = residual / sigma

        # Now update EWMA for next iteration
        old_ewma = ewma
        ewma = alpha * value + (1 - alpha) * ewma
        ewma_var = alpha * residual ** 2 + (1 - alpha) * ewma_var

        if i < min_points - 1:
            continue
        is_anomaly = False
        if direction == "down" and z < -threshold_sigma:
            is_anomaly = True
        elif direction == "up" and z > threshold_sigma:
            is_anomaly = True

        if is_anomaly:
            anomalies.append({
                "ts": point.get("ts", ""),
                "value": value,
                "expected": round(ewma, 1),
                "z_score": round(z, 2),
            })

    return anomalies


def calc_supply_efficiency(stats: dict) -> dict:
    """Calculate supply run efficiency metrics.

    Returns {runs_per_hour, pct_time_supplying, avg_trip_minutes}.
    """
    bot_ms = stats.get("total_bot_ms", 0)
    runs = stats.get("total_supply_runs", 0)

    if bot_ms < MIN_SESSION_MS or runs == 0:
        return {"runs_per_hour": 0, "pct_time_supplying": 0, "avg_trip_minutes": 0}

    hours = bot_ms / 3_600_000
    runs_per_hour = runs / hours

    # Estimate: each supply run takes ~3 minutes (teleport + buy + return)
    est_trip_minutes = 3.0
    total_supply_minutes = runs * est_trip_minutes
    total_minutes = bot_ms / 60_000
    pct = (total_supply_minutes / total_minutes * 100) if total_minutes > 0 else 0

    return {
        "runs_per_hour": round(runs_per_hour, 2),
        "pct_time_supplying": round(pct, 1),
        "avg_trip_minutes": est_trip_minutes,
    }


def calc_risk_score(history: list[dict]) -> dict:
    """Calculate ban risk score (0-100) from account history.

    Signals: excessive uptime, high death rate, same location repetition,
    zero deaths with long sessions (suspiciously perfect play).
    """
    score = 0
    flags: list[str] = []

    if not history:
        return {"score": 0, "flags": [], "level": "UNKNOWN"}

    # 1. Excessive uptime (>18hr in a day)
    for d in history:
        day_hours = d.get("total_bot_ms", 0) / 3_600_000
        if day_hours > 20:
            score += 25
            flags.append(f"excessive_uptime={day_hours:.0f}hr")
        elif day_hours > 18:
            score += 15
            flags.append(f"long_uptime={day_hours:.0f}hr")

    # 2. Death rate
    total_deaths = sum(d.get("total_deaths", 0) for d in history)
    total_ms = sum(d.get("total_bot_ms", 0) for d in history)
    total_hours = total_ms / 3_600_000 if total_ms > 0 else 0
    if total_hours > 1:
        dph = total_deaths / total_hours
        if dph > 3:
            score += 20
            flags.append(f"very_high_deaths={dph:.1f}/hr")
        elif dph > 1.5:
            score += 10
            flags.append(f"high_deaths={dph:.1f}/hr")

    # 3. Same location 3+ consecutive days
    maps = [d.get("map_name", "") for d in sorted(history, key=lambda x: x.get("date", ""))]
    if len(maps) >= 3:
        consec = 1
        for i in range(1, len(maps)):
            if maps[i] == maps[i - 1] and maps[i]:
                consec += 1
            else:
                consec = 1
            if consec >= 3:
                score += 15
                flags.append(f"same_location_{consec}days={maps[i]}")
                break

    # 4. Zero deaths with long session (suspiciously perfect)
    for d in history:
        if d.get("total_bot_ms", 0) > 28_800_000 and d.get("total_deaths", 0) == 0:
            score += 10
            flags.append("zero_deaths_long_session")
            break

    # 5. Kill rate regularity (low variance = bot-like)
    if len(history) >= 3:
        kph_list = []
        for d in history:
            ms = d.get("total_bot_ms", 0)
            if ms > 3_600_000:
                kph_list.append(d.get("total_kills", 0) / (ms / 3_600_000))
        if len(kph_list) >= 3:
            avg = _mean(kph_list)
            if avg > 0:
                cv = math.sqrt(_variance(kph_list)) / avg
                if cv < 0.05:
                    score += 15
                    flags.append(f"suspicious_regularity_cv={cv:.3f}")

    score = min(score, 100)
    level = "HIGH" if score >= 40 else "MEDIUM" if score >= 20 else "LOW"

    return {"score": score, "flags": flags, "level": level}


def optimal_allocation(
    locations: dict[str, dict],
    total_bots: int,
    return_details: bool = False,
) -> dict:
    """Greedy resource allocation using marginal utility with diminishing returns.

    Each additional bot at a location yields less gold due to crowding.
    Greedily assigns each bot to the location with highest marginal gain.

    Args:
        locations: {name: {base_gold_hr, crowding_factor}} where
                   crowding_factor (0-1) controls how fast returns diminish.
                   E.g., 0.85 means each extra bot keeps 85% of previous bot's yield.
        total_bots: number of bots to allocate
        return_details: if True, include total_gold_hr estimate

    Returns dict of {location: bot_count} (or with total_gold_hr if return_details).
    """
    if not locations:
        return {}

    alloc = {loc: 0 for loc in locations}

    for _ in range(total_bots):
        best_loc = None
        best_marginal = -1.0
        for loc, info in locations.items():
            base = info.get("base_gold_hr", 0)
            cf = info.get("crowding_factor", 0.85)
            # Marginal gold of adding the (N+1)th bot
            marginal = base * (cf ** alloc[loc])
            if marginal > best_marginal:
                best_marginal = marginal
                best_loc = loc
        if best_loc is not None:
            alloc[best_loc] += 1

    if return_details:
        total = 0.0
        for loc, count in alloc.items():
            base = locations[loc].get("base_gold_hr", 0)
            cf = locations[loc].get("crowding_factor", 0.85)
            for i in range(count):
                total += base * (cf ** i)
        return {**alloc, "total_gold_hr": round(total, 0)}

    return alloc


def cusum_death_alert(
    death_timestamps: list[float],
    target_interval_s: float = 1800.0,
    threshold: float = 1.5,
    return_details: bool = False,
) -> bool | dict:
    """CUSUM change detection on death intervals.

    Detects when deaths are clustering (rate accelerating) compared to
    the target interval. Alerts when cumulative deviation exceeds threshold.

    Args:
        death_timestamps: list of timestamps (seconds) when deaths occurred
        target_interval_s: expected seconds between deaths (default 30 min)
        threshold: number of target_intervals of cumulative deviation to trigger
        return_details: if True, return dict with alert + cusum_max

    Returns bool (or dict if return_details).
    """
    if len(death_timestamps) < 3:
        result = {"alert": False, "cusum_max": 0.0, "intervals": []}
        return result if return_details else False

    sorted_ts = sorted(death_timestamps)
    intervals = [sorted_ts[i + 1] - sorted_ts[i] for i in range(len(sorted_ts) - 1)]

    cusum = 0.0
    cusum_max = 0.0
    allowance = target_interval_s * 0.5
    alert = False

    for interval in intervals:
        # Accumulate negative deviations (deaths faster than expected)
        cusum = max(0.0, cusum + (target_interval_s - interval) - allowance)
        cusum_max = max(cusum_max, cusum)
        if cusum > threshold * target_interval_s:
            alert = True

    if return_details:
        return {"alert": alert, "cusum_max": round(cusum_max, 1), "intervals": intervals}
    return alert


def build_heatmap(
    pos_log: list | None,
    grid_size: int = 8,
) -> list[dict]:
    """Build a 2D kill/gold heatmap from PosRecord data.

    Groups positions into grid cells and aggregates kills, gold, visits.

    Args:
        pos_log: list of [x, y, kills, gold] or [x, y, kills, gold, tick]
        grid_size: world units per grid cell (smaller = higher resolution)

    Returns list of {gx, gy, kills, gold, visits} per cell.
    """
    if not pos_log:
        return []

    cells: dict[tuple[int, int], dict] = {}

    for record in pos_log:
        if not isinstance(record, (list, tuple)) or len(record) < 4:
            continue
        x, y, kills, gold = record[0], record[1], record[2], record[3]
        gx = x // grid_size
        gy = y // grid_size
        key = (gx, gy)

        if key in cells:
            cells[key]["kills"] += kills
            cells[key]["gold"] += gold
            cells[key]["visits"] += 1
        else:
            cells[key] = {
                "gx": gx, "gy": gy,
                "kills": kills, "gold": gold, "visits": 1,
            }

    return list(cells.values())


def extract_hotspots(
    heatmap: list[dict],
    top_n: int = 10,
    min_kills: int = 0,
) -> list[dict]:
    """Extract top-N kill hotspots from a heatmap.

    Returns hotspots sorted by kills descending, with approximate
    world coordinates for navigation.

    Args:
        heatmap: output of build_heatmap()
        top_n: max hotspots to return
        min_kills: minimum kills to include
    """
    if not heatmap:
        return []

    filtered = [c for c in heatmap if c.get("kills", 0) >= min_kills]
    filtered.sort(key=lambda c: c["kills"], reverse=True)

    result = []
    for c in filtered[:top_n]:
        # grid_size is unknown here, but gx/gy * typical grid_size gives approximate world coords
        # We store the grid coords; caller can multiply by grid_size
        # For convenience, assume grid_size=8 (most common) for world_x/y approximation
        result.append({
            "gx": c["gx"],
            "gy": c["gy"],
            "kills": c["kills"],
            "gold": c["gold"],
            "visits": c["visits"],
            "world_x": c["gx"] * 8,  # approximate center
            "world_y": c["gy"] * 8,
        })

    return result


# ──────────────────────────────────────────────────────────────
#  A8: Hungarian Schedule Optimization
# ──────────────────────────────────────────────────────────────

def hungarian_schedule(gold_matrix: list[list[float]]) -> list[dict]:
    """Optimal account-to-slot assignment maximizing total gold/hr.

    Uses the Hungarian algorithm (Kuhn-Munkres) on a cost matrix.
    Handles rectangular matrices (more accounts than slots or vice versa).

    Args:
        gold_matrix: gold_matrix[i][j] = gold/hr of account i at slot j

    Returns list of {account, slot, gold_hr} for each assigned pair.
    """
    if not gold_matrix or not gold_matrix[0]:
        return []

    n_accounts = len(gold_matrix)
    n_slots = len(gold_matrix[0])

    # Pad to square matrix (fill with 0 = dummy)
    n = max(n_accounts, n_slots)
    # Convert to cost matrix (negate for minimization)
    cost = []
    for i in range(n):
        row = []
        for j in range(n):
            if i < n_accounts and j < n_slots:
                row.append(-gold_matrix[i][j])
            else:
                row.append(0)
        cost.append(row)

    # Hungarian algorithm (Kuhn-Munkres) — pure Python
    row_match, col_match = _hungarian(cost, n)

    # Extract real assignments (skip dummy rows/cols)
    result = []
    for i in range(n_accounts):
        j = row_match[i]
        if j < n_slots:
            result.append({
                "account": i,
                "slot": j,
                "gold_hr": gold_matrix[i][j],
            })

    # If more accounts than slots, pick the best n_slots assignments
    if n_accounts > n_slots:
        result.sort(key=lambda r: r["gold_hr"], reverse=True)
        result = result[:n_slots]

    return result


def _hungarian(cost: list[list[float]], n: int) -> tuple[list[int], list[int]]:
    """Kuhn-Munkres algorithm for n×n cost matrix. Returns (row_match, col_match)."""
    INF = float("inf")

    # u[i], v[j] = potentials
    u = [0.0] * (n + 1)
    v = [0.0] * (n + 1)
    # p[j] = row matched to column j (1-indexed internally)
    p = [0] * (n + 1)
    # way[j] = previous column in augmenting path
    way = [0] * (n + 1)

    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [INF] * (n + 1)
        used = [False] * (n + 1)

        while True:
            used[j0] = True
            i0 = p[j0]
            delta = INF
            j1 = -1

            for j in range(1, n + 1):
                if used[j]:
                    continue
                cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                if cur < minv[j]:
                    minv[j] = cur
                    way[j] = j0
                if minv[j] < delta:
                    delta = minv[j]
                    j1 = j

            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta

            j0 = j1
            if p[j0] == 0:
                break

        # Augment path
        while j0:
            p[j0] = p[way[j0]]
            j0 = way[j0]

    # Convert to 0-indexed
    row_match = [-1] * n
    col_match = [-1] * n
    for j in range(1, n + 1):
        if p[j] != 0:
            row_match[p[j] - 1] = j - 1
            col_match[j - 1] = p[j] - 1

    return row_match, col_match


# ──────────────────────────────────────────────────────────────
#  A9: Best-Response Game Equilibrium
# ──────────────────────────────────────────────────────────────

def best_response_equilibrium(
    accounts: list[dict],
    locations: dict[str, dict],
    move_threshold: float = 0.10,
    max_rounds: int = 20,
) -> list[dict]:
    """Iterative best-response dynamics for location allocation.

    Each bot checks if moving to another location yields >threshold% more
    gold. Repeats until no bot wants to move (Nash equilibrium).

    Args:
        accounts: [{name, current_location}]
        locations: {name: {base_gold_hr, crowding_factor}}
        move_threshold: min improvement % to justify a move (default 10%)
        max_rounds: max iteration rounds

    Returns list of {name, location, moved, gold_hr}.
    """
    if not accounts or not locations:
        return []

    loc_names = list(locations.keys())

    # Initialize assignments
    assignment: dict[str, str] = {}
    for acc in accounts:
        cur = acc.get("current_location", "")
        # If current location not in options, pick best
        if cur not in locations:
            assignment[acc["name"]] = loc_names[0]
        else:
            assignment[acc["name"]] = cur

    original = dict(assignment)

    for _round in range(max_rounds):
        moved_any = False
        for acc in accounts:
            name = acc["name"]
            cur_loc = assignment[name]

            # Count bots at each location
            loc_counts: dict[str, int] = {}
            for loc in loc_names:
                loc_counts[loc] = 0
            for a_name, a_loc in assignment.items():
                loc_counts[a_loc] = loc_counts.get(a_loc, 0) + 1

            # Current yield (as the Nth bot at this location)
            cur_n = loc_counts[cur_loc]
            cur_yield = _crowded_yield(locations[cur_loc], cur_n)

            # Check alternatives
            best_alt_loc = cur_loc
            best_alt_yield = cur_yield
            for alt_loc in loc_names:
                if alt_loc == cur_loc:
                    continue
                # Yield as the (N+1)th bot at alt location
                alt_n = loc_counts[alt_loc] + 1
                alt_yield = _crowded_yield(locations[alt_loc], alt_n)
                if alt_yield > best_alt_yield:
                    best_alt_yield = alt_yield
                    best_alt_loc = alt_loc

            # Move if improvement exceeds threshold
            if best_alt_loc != cur_loc:
                improvement = (best_alt_yield - cur_yield) / max(cur_yield, 1e-10)
                if improvement > move_threshold:
                    assignment[name] = best_alt_loc
                    moved_any = True

        if not moved_any:
            break

    # Build result
    loc_counts_final: dict[str, int] = {}
    for a_loc in assignment.values():
        loc_counts_final[a_loc] = loc_counts_final.get(a_loc, 0) + 1

    result = []
    for acc in accounts:
        name = acc["name"]
        loc = assignment[name]
        n = loc_counts_final[loc]
        yield_hr = _crowded_yield(locations[loc], n)
        result.append({
            "name": name,
            "location": loc,
            "moved": loc != original[name],
            "gold_hr": round(yield_hr, 0),
        })

    return result


def _crowded_yield(loc_info: dict, n_bots: int) -> float:
    """Gold/hr per bot at a location with n_bots present."""
    base = loc_info.get("base_gold_hr", 0)
    cf = loc_info.get("crowding_factor", 0.85)
    if n_bots <= 0:
        return base
    return base * (cf ** (n_bots - 1))


# ──────────────────────────────────────────────────────────────
#  A10: Patrol Path Generation from Kill Hotspots
# ──────────────────────────────────────────────────────────────

def generate_patrol_path(
    hotspots: list[dict],
    max_waypoints: int = 20,
    loop: bool = False,
) -> list[dict]:
    """Generate a patrol route from kill hotspots using greedy nearest-neighbor.

    Starts from the highest-kill hotspot, then visits the nearest unvisited
    hotspot. Optionally closes the loop back to start.

    Args:
        hotspots: [{world_x, world_y, kills, ...}]
        max_waypoints: max number of waypoints in the route
        loop: if True, append a return-to-start waypoint

    Returns list of {x, y, kills, distance_from_prev}.
    """
    if not hotspots:
        return []

    # Sort by kills descending, take top max_waypoints
    sorted_hs = sorted(hotspots, key=lambda h: h.get("kills", 0), reverse=True)
    candidates = sorted_hs[:max_waypoints]

    # Start from highest-kill hotspot
    visited = [candidates[0]]
    remaining = list(candidates[1:])

    # Greedy nearest-neighbor
    while remaining:
        last = visited[-1]
        lx, ly = last.get("world_x", 0), last.get("world_y", 0)

        best_idx = 0
        best_dist = float("inf")
        for i, h in enumerate(remaining):
            d = math.sqrt((h["world_x"] - lx) ** 2 + (h["world_y"] - ly) ** 2)
            if d < best_dist:
                best_dist = d
                best_idx = i

        visited.append(remaining.pop(best_idx))

    # Build path with distances
    path = []
    for i, h in enumerate(visited):
        x = h.get("world_x", 0)
        y = h.get("world_y", 0)
        if i == 0:
            dist = 0.0
        else:
            px, py = path[i - 1]["x"], path[i - 1]["y"]
            dist = math.sqrt((x - px) ** 2 + (y - py) ** 2)
        path.append({
            "x": x,
            "y": y,
            "kills": h.get("kills", 0),
            "distance_from_prev": round(dist, 1),
        })

    # Close loop if requested
    if loop and len(path) >= 2:
        sx, sy = path[0]["x"], path[0]["y"]
        lx, ly = path[-1]["x"], path[-1]["y"]
        dist = math.sqrt((sx - lx) ** 2 + (sy - ly) ** 2)
        path.append({
            "x": sx,
            "y": sy,
            "kills": path[0]["kills"],
            "distance_from_prev": round(dist, 1),
        })

    return path


# ──────────────────────────────────────────────────────────────
#  Internal helpers (no scipy dependency)
# ──────────────────────────────────────────────────────────────

def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0


def _variance(values: list[float]) -> float:
    if len(values) < 2:
        return 0
    m = _mean(values)
    return sum((x - m) ** 2 for x in values) / (len(values) - 1)


def _t_test_p_value(t: float, df: float) -> float:
    """Approximate two-tailed p-value for t-distribution.

    Uses the regularized incomplete beta function approximation.
    Good enough for df > 2 and practical significance testing.
    """
    if df <= 0:
        return 1.0
    x = df / (df + t * t)
    # Approximate using the normal distribution for large df
    if df > 30:
        z = t * (1 - 1 / (4 * df)) / math.sqrt(1 + t * t / (2 * df))
        p = math.erfc(abs(z) / math.sqrt(2))
        return p
    # For small df, use a simple approximation
    # Based on Abramowitz & Stegun 26.7.8
    g = math.lgamma((df + 1) / 2) - math.lgamma(df / 2)
    c = math.exp(g) / math.sqrt(df * math.pi)
    integrand_at_t = c * (1 + t * t / df) ** (-(df + 1) / 2)
    # Very rough: p ≈ 2 * integrand * effective_width
    # Better: use continued fraction expansion
    p = 2 * _betainc_approx(df / 2, 0.5, x)
    return min(p, 1.0)


def _betainc_approx(a: float, b: float, x: float) -> float:
    """Rough approximation of regularized incomplete beta function I_x(a, b).

    Uses the continued fraction representation (Lentz's method, 8 terms).
    Sufficient for t-test p-value estimation.
    """
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0

    # Front factor
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(a * math.log(x) + b * math.log(1 - x) - lbeta) / a

    # Continued fraction (simplified, 30 terms)
    # Using Lentz's algorithm
    f = 1.0
    c = 1.0
    d = 1.0 - (a + b) * x / (a + 1)
    if abs(d) < 1e-30:
        d = 1e-30
    d = 1 / d
    f = d

    for m in range(1, 31):
        # Even step
        num = m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m))
        d = 1 + num * d
        if abs(d) < 1e-30:
            d = 1e-30
        d = 1 / d
        c = 1 + num / c
        if abs(c) < 1e-30:
            c = 1e-30
        f *= d * c

        # Odd step
        num = -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))
        d = 1 + num * d
        if abs(d) < 1e-30:
            d = 1e-30
        d = 1 / d
        c = 1 + num / c
        if abs(c) < 1e-30:
            c = 1e-30
        f *= d * c

    return front * f
