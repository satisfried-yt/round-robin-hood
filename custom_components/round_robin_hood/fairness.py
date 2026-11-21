"""Strategy-scoped fair accounting with anchored, *non-rolling* periods.

Period anchors are saved per profile and strategy on first activation, or on a
confirmed manual reset. The current fixed period is calculated from that anchor;
only runtime that overlaps the current cycle is considered. Lifetime totals
remain independent and are never discarded at an automatic period boundary.
Historical pre-upgrade segments cannot create retroactive period credit.
"""
from __future__ import annotations

import math
from typing import Any

from .model import UserError

FAIR_STRATEGIES = frozenset({'fair_runtime', 'fair_energy'})
WINDOWS = {'24h': 86400, '7d': 7 * 86400, '14d': 14 * 86400, '30d': 30 * 86400}
MAX_SEGMENTS = 20000


class FairLedger:
    def __init__(self, raw: Any = None, *, profiles=(), consumers=()) -> None:
        self.totals: dict[str, dict[str, dict[str, float]]] = {kind: {} for kind in FAIR_STRATEGIES}
        self.segments: list[list] = []
        self.anchors: dict[str, dict[str, float]] = {kind: {} for kind in FAIR_STRATEGIES}
        # Active start times are deliberately NOT persisted. A restart never
        # credits time while Home Assistant was offline or RRH paused.
        self.active: dict[tuple[str, str, str], tuple[float, float]] = {}
        if raw is None:
            return
        if not isinstance(raw, dict) or set(raw) not in ({'totals', 'segments'}, {'totals', 'segments', 'anchors'}):
            raise UserError('Ungültige Fairness-Statistik im Speicher.')
        valid_profiles = {p.id: set(p.consumer_ids) for p in profiles}
        valid_consumers = {c.id for c in consumers}
        totals = raw['totals']
        if not isinstance(totals, dict) or set(totals) != set(FAIR_STRATEGIES):
            raise UserError('Ungültige Fairness-Zähler im Speicher.')
        for kind, groups in totals.items():
            if not isinstance(groups, dict):
                raise UserError('Ungültige Fairness-Profilzähler.')
            for pid, counts in groups.items():
                if pid not in valid_profiles or not isinstance(counts, dict):
                    raise UserError('Ungültige Fairness-Profilkennung.')
                for cid, value in counts.items():
                    if (cid not in valid_profiles[pid] or cid not in valid_consumers or
                            type(value) not in (int, float) or not math.isfinite(value) or
                            not 0 <= value <= 1e15):
                        raise UserError('Ungültige Fairness-Verbraucherstatistik.')
                self.totals[kind][pid] = {cid: float(value) for cid, value in counts.items()}
        anchors = raw.get('anchors', {kind: {} for kind in FAIR_STRATEGIES})
        if not isinstance(anchors, dict) or set(anchors) != FAIR_STRATEGIES:
            raise UserError('Ungültige Fairness-Perioden im Speicher.')
        for kind, groups in anchors.items():
            if not isinstance(groups, dict):
                raise UserError('Ungültige Fairness-Perioden im Speicher.')
            for pid, started in groups.items():
                if (pid not in valid_profiles or type(started) not in (int, float) or
                        not math.isfinite(started) or not 0 <= started <= 1e12):
                    raise UserError('Ungültiger Fairness-Periodenbeginn.')
                self.anchors[kind][pid] = float(started)
        parts = raw['segments']
        if not isinstance(parts, list) or len(parts) > MAX_SEGMENTS:
            raise UserError('Ungültige Anzahl Fairness-Laufzeitabschnitte.')
        for part in parts:
            if not isinstance(part, (list, tuple)) or len(part) != 6:
                raise UserError('Ungültiger Fairness-Laufzeitabschnitt.')
            kind, pid, cid, start, end, watts = part
            if (kind not in FAIR_STRATEGIES or pid not in valid_profiles or
                    cid not in valid_profiles[pid] or cid not in valid_consumers or
                    any(type(v) not in (int, float) or not math.isfinite(v) for v in (start, end, watts)) or
                    not 0 <= start <= end <= 1e12 or not 0 < watts <= 1e7):
                raise UserError('Ungültige Fairness-Laufzeitdaten.')
            self.segments.append([kind, pid, cid, float(start), float(end), float(watts)])

    def document(self) -> dict:
        return {'totals': {kind: {pid: dict(counts) for pid, counts in groups.items()}
                           for kind, groups in self.totals.items()},
                'segments': [list(part) for part in self.segments],
                'anchors': {kind: dict(groups) for kind, groups in self.anchors.items()}}

    def _append(self, kind: str, pid: str, cid: str, start: float, end: float, watts: float) -> bool:
        duration = max(0.0, end - start)
        if duration <= 0:
            return False
        amount = duration if kind == 'fair_runtime' else duration * watts / 3600.0  # Wh
        counts = self.totals[kind].setdefault(pid, {})
        counts[cid] = counts.get(cid, 0.0) + amount
        for part in reversed(self.segments):
            if part[:3] == [kind, pid, cid]:
                if abs(part[4] - start) < 0.01 and part[5] == watts:
                    part[4] = end
                    break
                # Only an immediately adjacent segment may be coalesced.
                self.segments.append([kind, pid, cid, start, end, watts])
                break
        else:
            self.segments.append([kind, pid, cid, start, end, watts])
        return True

    def sync(self, current: dict[tuple[str, str, str], float], now: float) -> bool:
        """Checkpoint previous activity; start new confirmed activity at 'now'."""
        changed = False
        if now < 0 or not math.isfinite(now):
            return False
        for (kind, pid, cid), (start, watts) in list(self.active.items()):
            if now > start:
                changed |= self._append(kind, pid, cid, start, now, watts)
        self.active = {key: (now, watts) for key, watts in current.items()}
        cutoff = now - 31 * 86400
        old_len = len(self.segments)
        self.segments = [part for part in self.segments if part[4] >= cutoff]
        # Never silently drop still-relevant segments. This is an explicit
        # capacity error, not a guessed/partial 30-day fairness result.
        if len(self.segments) > MAX_SEGMENTS:
            raise UserError('Fairness-Historie ist zu groß. Betrieb pausieren und Statistik prüfen.')
        return changed or len(self.segments) != old_len

    def ensure_started(self, kind: str, pid: str, now: float) -> bool:
        """First *active* selection sets a durable origin, even with no loads ON."""
        if kind not in FAIR_STRATEGIES or not math.isfinite(now) or not 0 <= now <= 1e12:
            return False
        if pid in self.anchors[kind]:
            return False
        self.anchors[kind][pid] = float(now)
        return True

    def period(self, kind: str, pid: str, window: str, now: float) -> tuple[float | None, float | None, float | None]:
        """Return (origin, current period start, next boundary), UNIX seconds.

        A 24-hour period begins at the first activation timestamp, not midnight.
        A gap or pause never stops the period clock. All-time has no end.
        """
        anchor = self.anchors.get(kind, {}).get(pid)
        if anchor is None:
            return None, None, None
        if window not in WINDOWS:
            return anchor, anchor, None
        length = WINDOWS[window]
        cycle = max(0, math.floor((now - anchor) / length))
        start = anchor + cycle * length
        return anchor, start, start + length

    def value(self, kind: str, pid: str, cid: str, window: str, now: float) -> float:
        if kind not in FAIR_STRATEGIES or not math.isfinite(now):
            return 0.0
        if window == 'all':
            amount = self.totals[kind].get(pid, {}).get(cid, 0.0)
            cutoff = None
        else:
            # Until the profile's first fair-strategy activation, historical
            # rolling 0.3.3 segments must NOT leak into the new fixed window.
            _, cutoff, _ = self.period(kind, pid, window, now)
            if cutoff is None:
                return 0.0
            amount = 0.0
            for mode, group, consumer, start, end, watts in self.segments:
                if (mode, group, consumer) == (kind, pid, cid):
                    overlap = max(0.0, min(end, now) - max(start, cutoff))
                    amount += overlap if kind == 'fair_runtime' else overlap * watts / 3600.0
        opened = self.active.get((kind, pid, cid))
        if opened is not None:
            start, watts = opened
            overlap = max(0.0, now - max(start, cutoff)) if cutoff is not None else max(0.0, now - start)
            amount += overlap if kind == 'fair_runtime' else overlap * watts / 3600.0
        return max(0.0, amount)

    def reset(self, kind: str, pid: str, now: float | None = None) -> None:
        self.totals[kind].pop(pid, None)
        self.segments = [part for part in self.segments if not (part[0] == kind and part[1] == pid)]
        self.active = {key: val for key, val in self.active.items() if key[:2] != (kind, pid)}
        self.anchors[kind].pop(pid, None)
        # An explicit reset is itself a deliberate new period start.
        if now is not None:
            self.ensure_started(kind, pid, now)

    def restrict(self, profiles=(), consumers=()) -> None:
        allowed = {p.id: set(p.consumer_ids) for p in profiles}
        valid = {c.id for c in consumers}
        self.segments = [p for p in self.segments if p[1] in allowed and p[2] in allowed[p[1]] and p[2] in valid]
        self.active = {key: val for key, val in self.active.items() if key[1] in allowed and key[2] in allowed[key[1]] and key[2] in valid}
        for kind in FAIR_STRATEGIES:
            self.anchors[kind] = {pid: start for pid, start in self.anchors[kind].items() if pid in allowed}
            self.totals[kind] = {pid: {cid: value for cid, value in counts.items() if cid in allowed[pid] and cid in valid}
                                 for pid, counts in self.totals[kind].items() if pid in allowed}
