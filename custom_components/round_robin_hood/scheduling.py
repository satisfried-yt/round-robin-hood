"""HA-independent deterministic dispatch helpers for the optional strategies.

All watts are nominal estimates. Optimization never interprets an external switch
as RRH-owned and never uses grid export without subtracting the safety reserve.
"""
from __future__ import annotations

from bisect import bisect_right
import math

from .model import Consumer, Profile


def ranked_members(profile: Profile, members: list[Consumer], runtime_seconds: dict[str, float]) -> list[Consumer]:
    """The order of starts. Existing Classic remains controller-owned."""
    order = {cid: i for i, cid in enumerate(profile.consumer_ids)}
    strategy = profile.strategy
    if strategy in ("fair_runtime", "fair_energy"):
        return sorted(members, key=lambda c: (runtime_seconds.get(c.id, 0.0), order[c.id]))
    if strategy == "power_asc":
        return sorted(members, key=lambda c: (c.watts, order[c.id]))
    if strategy == "power_desc":
        return sorted(members, key=lambda c: (-c.watts, order[c.id]))
    return sorted(members, key=lambda c: order[c.id])


def efficient_subset(candidates: list[Consumer], capacity_w: float, currently_on: set[str]) -> set[str]:
    """Exact best-fill subset for up to 24 devices, with deterministic stable ties.

    Meet-in-the-middle instead of floating-point DP. Powers are conservatively
    rounded *up* to 0.001 W and the capacity *down* to 0.001 W, so approximate
    comparisons never deliberately exceed the nominal power budget. Ties
    retain running devices and prefer earlier configured devices.
    """
    if len(candidates) > 24:
        raise ValueError("Maximum Efficiency allows at most 24 devices")
    cap = max(0, math.floor(capacity_w * 1000 + 1e-7))
    n = len(candidates)
    amounts = [math.ceil(c.watts * 1000 - 1e-7) for c in candidates]
    current = sum(1 << i for i, c in enumerate(candidates) if c.id in currently_on)
    midpoint = n // 2

    def halves(start: int, stop: int):
        parts = [(0, 0, 0)]
        for pos in range(start, stop):
            bit = 1 << pos
            addition = amounts[pos]
            parts += [(power + addition, mask | bit, 0) for power, mask, _ in list(parts)]
        # The third value is the number of changed switches compared to now.
        own_bits = ((1 << stop) - 1) ^ ((1 << start) - 1)
        return [(power, mask, (mask ^ (current & own_bits)).bit_count())
                for power, mask, _ in parts if power <= cap]

    left, right = halves(0, midpoint), halves(midpoint, n)
    # For equal power prefer minimal change count, then earlier config bits.
    best_for_sum = {}
    for power, mask, change in right:
        prior = best_for_sum.get(power)
        if prior is None or (change, -sum((n - i) for i in range(n) if mask & (1 << i))) < (prior[2], -sum((n - i) for i in range(n) if prior[1] & (1 << i))):
            best_for_sum[power] = (power, mask, change)
    powers = sorted(best_for_sum)
    best = (-1, float("inf"), 0, 0)  # power, changes, tie, mask
    for lp, lm, lc in left:
        idx = bisect_right(powers, cap - lp) - 1
        if idx < 0:
            continue
        rp, rm, rc = best_for_sum[powers[idx]]
        mask = lm | rm
        tie = sum((n - i) for i in range(n) if mask & (1 << i))
        candidate = (lp + rp, lc + rc, tie, mask)
        if candidate[0] > best[0] or (candidate[0] == best[0] and (candidate[1], -candidate[2]) < (best[1], -best[2])):
            best = candidate
    return {c.id for i, c in enumerate(candidates) if best[3] & (1 << i)}
