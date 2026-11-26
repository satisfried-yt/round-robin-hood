# rrh-origin:60a87ab54ee9f1b35be11c34c1b5f0fd
"""Single-flight controller, independent of HA transport and storage.

Only two injected async operations: send a switch command, persist one document.
Observation is synchronous on one event loop; all writes/commands are serialized.
Pause is synchronous so it can stop a queued action even during slow storage.
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from copy import deepcopy
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, tzinfo
import logging
import math
import time
from typing import Any
from uuid import uuid4

from .const import API_VERSION, CONFIRM_TIMEOUT, VERSION
from .model import Config, Consumer, Profile, ConditionSet, NumericCondition, UserError, grid_watts, next_consumer
from .scheduling import ranked_members, efficient_subset
from .fairness import FairLedger, FAIR_STRATEGIES
from .statistics import EnergyLedger

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class Reading:
    raw: Any = None
    unit: str | None = None
    at: float | None = None
    sequence: int = 0
    restored: bool = False


@dataclass(slots=True)
class Pending:
    consumer: Consumer
    target: str
    token: str = field(default_factory=lambda: uuid4().hex)
    sent: bool = False
    observed: asyncio.Event = field(default_factory=asyncio.Event)
    observed_sequence: int = -1
    problem: str | None = None
    phase: str = "vor Dienstaufruf"
    service_completed: bool = False
    group_ids: tuple[str, ...] = ()
    target_watts: float | None = None


class Controller:
    """No background retries, no power rotation, no implicit adoption of loads."""

    def __init__(self, saved: dict | None, *,
                 send: Callable[[str, str, str], Awaitable[None]],
                 save: Callable[[dict], Awaitable[None]],
                 send_all_off: Callable[[list[str]], Awaitable[None]] | None = None,
                 send_level: Callable[[Consumer, float, str], Awaitable[None]] | None = None,
                 clock: Callable[[], float] = time.monotonic,
                 wall_clock: Callable[[], float] = time.time,
                 confirmation_timeout: float = CONFIRM_TIMEOUT, timezone: tzinfo = UTC) -> None:
        self.send = send
        self.send_level = send_level or self._unsupported_level
        self.save = save
        self.send_all_off = send_all_off or self._send_off_individually
        self.clock = clock
        self.wall_clock = wall_clock
        self.timezone = timezone
        self.timeout = confirmation_timeout
        self.config = Config()
        self.revision = 0
        self.cursor: str | None = None
        self.profile_cursors: dict[str, str] = {}
        self.owned: list[str] = []
        self.started_at: dict[str, float] = {}
        self.runtime_totals_s: dict[str, float] = {}
        self.runtime_segments: list[tuple[str, float, float]] = []
        self.fairness = FairLedger()
        self._efficiency_goals: dict[str, set[str]] = {}
        self._efficiency_last_swap: dict[str, float] = {}
        self.cooldown_until: dict[str, float] = {}
        self.condition_latches: dict[str, bool] = {}
        self.power_levels: dict[str, float] = {}
        self._last_level_change: dict[str, float] = {}
        self._regulation_off: tuple[str, int] | None = None
        self.condition_states: dict[str, tuple[str | None, bool]] = {}
        self.incomplete: dict | None = None
        self.emergency_unresolved = False
        self.resume_mode = "stopped"  # last deliberate state; persisted separately from transient mode
        if saved is not None:
            self._load(saved)
        self.statistics = EnergyLedger(saved.get("statistics") if saved else None, timezone=timezone)
        if self.config.energy.currency != self.statistics.money_currency:
            raise UserError("Statistik und Tarifwährung widersprechen sich. Speicherung unverändert lassen und Sicherung prüfen.")
        self.stat_sources: dict = {}
        self.states: dict[str, str] = {}
        self.reading = Reading()
        # The standalone controller initializes paused; HA runtime applies
        # the configured startup policy only after binding known entity states.
        self.mode = "paused"
        self.reason = "Nach Start pausiert. Einstellungen prüfen und bewusst aktivieren."
        self._startup_restore = self.config.startup_mode == "on" or (self.config.startup_mode == "last" and self.resume_mode == "running")
        if self.config.startup_mode == "last" and self.resume_mode == "paused":
            self.mode = "paused"
            self.reason = "Letzter Zustand: pausiert. Laufende Verbraucher bleiben unverändert."
        if self._startup_restore:
            self.reason = "Automatischer Start vorgesehen. Warte auf gültige aktuelle Netzmessung und Verbraucherzustände."
        if self.incomplete or self.emergency_unresolved:
            self._startup_restore = False
        if self.emergency_unresolved:
            self.reason = "Pausiert: Vorheriger Hauptschalter-Aus-Befehl nicht vollständig bestätigt. Erneut ausschalten und kontrollieren."
        elif self.incomplete:
            self.reason = "Pausiert: Ein fr\u00fcherer Schaltauftrag wurde nicht vollst\u00e4ndig abgeschlossen."
        self.pending: Pending | None = None
        self.deficit_since: float | None = None
        self.wait_after_sequence: int | None = None
        self.last_action = "Noch keine Schaltung in dieser Sitzung."
        self._lock = asyncio.Lock()
        self._task: asyncio.Task | None = None
        self._dirty = False
        # Commit the upgraded 0.1.5 document once on startup, including
        # start timestamps for already managed loads, without changing cursor.
        legacy_storage = saved is not None and (
            "started_at" not in saved or "cooldown_until" not in saved or
            "profile_cursors" not in saved or "profiles" not in saved.get("config", {}) or
            "condition_latches" not in saved or
            "runtime_totals_s" not in saved or "runtime_segments" not in saved or
            "fairness" not in saved or
            not isinstance(saved.get("fairness"), dict) or
            "anchors" not in saved["fairness"] or "power_levels" not in saved or
            "statistics" not in saved or "resume_mode" not in saved
        )
        self._generation = 1 if legacy_storage else 0
        self._persisted_generation = 0
        self.closed = False
        self._has_confirmed_all_off = False
        self._startup_grid_sequence = None
        self._stop_epoch = 0
        self._emergency_epoch = 0
        self._storage_failed = False
        self._emergency_active = False
        self._emergency_lock = asyncio.Lock()
        self._dispatch_lock = asyncio.Lock()
        self._emergency_change = asyncio.Event()

    async def _unsupported_level(self, consumer: Consumer, level: float, token: str) -> None:
        raise UserError("Diese Installation unterstützt keine Leistungsregelung.")

    async def _send_off_individually(self, entities: list[str]) -> None:
        for entity_id in entities:
            await self.send(entity_id, "off", uuid4().hex)

    def _load(self, data: dict) -> None:
        if not isinstance(data, dict) or data.get("schema") != 1:
            raise UserError("Unbekanntes Speicherformat. Daten wurden nicht ver\u00e4ndert.")
        self.config = Config.parse(data.get("config"))
        revision = data.get("revision")
        cursor, owned, incomplete = data.get("cursor"), data.get("owned"), data.get("incomplete")
        if type(revision) is not int or revision < 0:
            raise UserError("Ung\u00fcltige gespeicherte Konfigurationsrevision.")
        if cursor is not None and (not isinstance(cursor, str) or len(cursor) > 64):
            raise UserError("Ung\u00fcltiger gespeicherter Vergabezeiger.")
        ids = {c.id for c in self.config.consumers}
        if not isinstance(owned, list) or any(not isinstance(i, str) or i not in ids for i in owned) or len(set(owned)) != len(owned):
            raise UserError("Ung\u00fcltige gespeicherte Ger\u00e4tezuordnung.")
        if incomplete is not None and (not isinstance(incomplete, dict) or set(incomplete) != {"id", "target"} or incomplete["id"] not in ids or incomplete["target"] not in ("on", "off", "level")):
            raise UserError("Ung\u00fcltiger gespeicherter Schaltauftrag.")
        unresolved = data.get("emergency_unresolved", False)
        if type(unresolved) is not bool:
            raise UserError("Ungültiger gespeicherter Not-Aus-Zustand.")
        self.emergency_unresolved = unresolved
        resume = data.get("resume_mode", "stopped")
        if resume not in ("running", "paused", "stopped") or not isinstance(resume, str):
            raise UserError("Ungültiger gespeicherter Neustartzustand.")
        self.resume_mode = resume
        self.revision, self.cursor = revision, cursor
        raw_cursors = data.get("profile_cursors")
        if raw_cursors is None:
            # 0.1.6 had a single global Classic cursor. Preserve its position
            # when the legacy consumers are put in the new Standard profile.
            group = next((p for p in self.config.profiles if cursor in p.consumer_ids), None)
            raw_cursors = {group.id: cursor} if group is not None else {}
        if not isinstance(raw_cursors, dict) or any(
            not isinstance(k, str) or k not in {p.id for p in self.config.profiles} or
            not isinstance(v, str) or len(v) > 64
            for k, v in raw_cursors.items()
        ):
            raise UserError("Ungültige gespeicherte Profil-Vergabezeiger.")
        self.profile_cursors = dict(raw_cursors)
        self.owned, self.incomplete = list(owned), deepcopy(incomplete)
        raw_latches = data.get("condition_latches", {})
        known = self._condition_keys()
        if not isinstance(raw_latches, dict) or any(
            not isinstance(k, str) or k not in known or type(v) is not bool
            for k, v in raw_latches.items()
        ):
            raise UserError("Ungültiger gespeicherter Bedingungszustand.")
        self.condition_latches = dict(raw_latches)
        def timestamps(key: str) -> dict[str, float]:
            value = data.get(key, {})
            if not isinstance(value, dict) or any(
                k not in ids or type(v) not in (float, int) or not math.isfinite(v) or v < 0 or v > 1e12
                for k, v in value.items()
            ):
                raise UserError(f"Ungültige gespeicherte Zeitpunkte: {key}.")
            return dict(value)
        self.started_at = timestamps("started_at")
        raw_levels = data.get("power_levels", {})
        if not isinstance(raw_levels, dict) or any(
            cid not in ids or type(level) not in (float, int) or not math.isfinite(level) or level < 0 or level > 100000
            for cid, level in raw_levels.items()
        ):
            raise UserError("Ungültige gespeicherte Leistungsstufen.")
        self.power_levels = {cid:float(value) for cid, value in raw_levels.items()}
        self.cooldown_until = timestamps("cooldown_until")
        # A v0.2.1 storage document has no runtime history; start at zero
        # rather than inventing past runtime from old switch history.
        self.runtime_totals_s = timestamps("runtime_totals_s")
        raw_segments = data.get("runtime_segments", [])
        if not isinstance(raw_segments, list) or len(raw_segments) > 20000 or any(
            not isinstance(part, (list, tuple)) or len(part) != 3 or not isinstance(part[0], str) or part[0] not in ids or
            any(type(t) not in (float, int) or not math.isfinite(t) or not 0 <= t <= 1e12 for t in part[1:]) or
            part[1] > part[2]
            for part in raw_segments
        ):
            raise UserError("Ungültige Laufzeitaufzeichnungen.")
        self.runtime_segments = [(cid, float(start), float(end)) for cid, start, end in raw_segments]
        # Never inherit the general runtime history into strategy-specific totals.
        self.fairness = FairLedger(data.get("fairness"), profiles=self.config.profiles, consumers=self.config.consumers)
        # Historical ownership from 0.1.5 had no start times. Do not invent
        # an earlier confirmation; start the safety interval conservatively.
        for cid in owned:
            self.started_at.setdefault(cid, self.wall_clock())

    def document(self) -> dict:
        return {"schema": 1, "config": self.config.to_dict(), "revision": self.revision,
                "cursor": self.cursor, "profile_cursors": dict(self.profile_cursors),
                "owned": list(self.owned), "incomplete": deepcopy(self.incomplete),
                "emergency_unresolved": self.emergency_unresolved,
                "started_at": dict(self.started_at), "cooldown_until": dict(self.cooldown_until),
                "condition_latches": dict(self.condition_latches),
                "runtime_totals_s": dict(self.runtime_totals_s),
                "power_levels": dict(self.power_levels),
                "runtime_segments": [list(item) for item in self.runtime_segments],
                "fairness": self.fairness.document(),
                "statistics":self.statistics.document(), "resume_mode":self.resume_mode}

    def _changed(self) -> None:
        self._generation += 1

    async def _persist(self) -> None:
        # Observations can remove ownership while an atomic HA Store write awaits I/O.
        # Flush again rather than accidentally resurrecting stale ownership in storage.
        while self._persisted_generation != self._generation:
            self._fair_refresh()
            generation = self._generation
            try:
                await self.save(self.document())
            except Exception:
                self._storage_failed = True
                raise
            self._persisted_generation = generation
        self._storage_failed = False

    def wake(self) -> None:
        if self.closed:
            return
        self._dirty = True
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._drain(), name="rrh-control")

    async def settle(self) -> None:
        """Wait for the current finite evaluation, not for future source events."""
        while self._task is not None and not self._task.done():
            await asyncio.shield(self._task)

    async def _drain(self) -> None:
        try:
            while self._dirty and not self.closed:
                self._dirty = False
                async with self._lock:
                    if self._storage_failed:
                        return  # Retry storage only on an explicit user operation or unload.
                    await self._persist()
                    await self._evaluate()
        except asyncio.CancelledError:
            raise
        except Exception:
            _LOGGER.exception("RRH evaluation/storage failed; pausing without further commands")
            self._fault("Interner oder Speicherfehler. Keine weiteren Schaltbefehle. HA-Protokoll pr\u00fcfen.")

    def _fault(self, reason: str) -> None:
        self._fair_refresh()
        self._stop_epoch += 1
        self.mode, self.reason, self.deficit_since = "error", reason, None
        self.resume_mode = "stopped"
        self._changed()
        self._fair_refresh()

    def pause(self, *, persist_intent: bool = True) -> None:
        self._startup_restore = False
        self._startup_grid_sequence = None
        self._fair_refresh()
        # Sampling stops at the moment of pause; HA tick never backfills it.
        self.statistics.last_snapshot = None
        self._stop_epoch += 1
        self._regulation_off = None
        self.mode = "paused"
        if persist_intent:
            self.resume_mode = "paused"
            self._changed()
            self.wake()
        self.reason = "Pausiert. Keine weiteren Schaltbefehle; laufende Verbraucher bleiben unver\u00e4ndert."
        self.deficit_since = None
        self._efficiency_goals.clear()
        self._fair_refresh()

    def observe_condition(self, entity_id: str, raw: Any, *, restored: bool = False) -> None:
        """A sensor report, including unavailable/unknown, immediately reevaluates eligibility."""
        value = None if raw is None else str(raw)
        self.condition_states[entity_id] = (value, restored)
        for scope, items in (("profile", self.config.profiles), ("consumer", self.config.consumers)):
            for item in items:
                if item.conditions.enabled and any(rule.entity_id == entity_id for rule in item.conditions.rules):
                    self._condition_report(scope, item)
        self.wake()

    def _condition_keys(self) -> set[str]:
        return {f"{scope}:{item.id}:{rule.id}"
                for scope, items in (("profile", self.config.profiles), ("consumer", self.config.consumers))
                for item in items for rule in item.conditions.rules}

    def _condition_sensor_ids(self) -> set[str]:
        return {rule.entity_id for item in (*self.config.profiles, *self.config.consumers)
                if item.conditions.enabled for rule in item.conditions.rules}

    def _test_numeric(self, rule: NumericCondition, value: float, previously: bool) -> bool:
        """For <21 and 1-degree hysteresis: enable below 20, disable at 21."""
        op, limit, margin = rule.operator, rule.value, rule.hysteresis
        if op == "<":
            return value < (limit if previously else limit - margin)
        if op == "<=":
            return value <= (limit if previously else limit - margin)
        if op == ">":
            return value > (limit if previously else limit + margin)
        if op == ">=":
            return value >= (limit if previously else limit + margin)
        if op == "==":
            return value == limit
        return value != limit

    def _condition_report(self, scope: str, item: Profile | Consumer) -> dict:
        settings: ConditionSet = item.conditions
        if not settings.enabled:
            return {"allowed": True, "reason": "", "checks": []}
        checks = []
        for rule in settings.rules:
            key = f"{scope}:{item.id}:{rule.id}"
            raw, restored = self.condition_states.get(rule.entity_id, (None, False))
            reading = None
            invalid = raw in (None, "unknown", "unavailable", "") or restored
            if not invalid:
                try:
                    reading = float(raw)
                    invalid = not math.isfinite(reading)
                except (ValueError, TypeError, OverflowError):
                    invalid = True
            passed = False if invalid else self._test_numeric(rule, reading, self.condition_latches.get(key, False))
            if self.condition_latches.get(key, False) != passed:
                self.condition_latches[key] = passed
                self._changed()
                self.wake()
            if invalid:
                reason = f"{rule.entity_id}: Sensorwert fehlt/ungültig/nicht verfügbar"
            elif not passed:
                reason = f"{rule.entity_id}: {reading:g} erfüllt {rule.operator} {rule.value:g} nicht (Hysterese {rule.hysteresis:g})"
            else:
                reason = ""
            checks.append({"entity_id": rule.entity_id, "reading": reading, "operator": rule.operator,
                           "threshold": rule.value, "hysteresis": rule.hysteresis,
                           "passed": passed, "invalid": invalid, "reason": reason})
        allowed = (all(x["passed"] for x in checks) if settings.logic == "all"
                   else any(x["passed"] for x in checks))
        if allowed:
            reason = ""
        else:
            failed = [x["reason"] for x in checks if not x["passed"]]
            reason = "; ".join(failed[:3])
            if len(failed) > 3:
                reason += f" (+{len(failed)-3} weitere)"
        return {"allowed": allowed, "reason": reason, "checks": checks}


    def _schedule_report(self, item: Profile | Consumer) -> dict:
        schedule = item.schedule
        if not schedule.enabled:
            return {"allowed": True, "reason": "", "next_start": None}
        now = self.wall_clock()
        permitted = schedule.allows(datetime.fromtimestamp(now, self.timezone))
        return {"allowed": permitted,
                "reason": "" if permitted else "Außerhalb der erlaubten Zeitfenster",
                "next_start": None if permitted else schedule.next_start(now, self.timezone)}

    def _eligible(self, scope: str, item: Profile | Consumer) -> bool:
        # Sensor rules AND weekly schedule; neither can override a denial.
        return (self._condition_report(scope, item)["allowed"] and
                self._schedule_report(item)["allowed"])

    def _eligibility_reason(self, scope: str, item: Profile | Consumer) -> str:
        sensor = self._condition_report(scope, item)
        window = self._schedule_report(item)
        failures = []
        if not sensor["allowed"]:
            failures.append(sensor["reason"])
        if not window["allowed"]:
            failures.append(window["reason"])
        return "; ".join(failures)

    def _consumer_permitted(self, consumer: Consumer) -> bool:
        if not consumer.enabled or not consumer.virtual_confirmed or not self._eligible("consumer", consumer):
            return False
        profile = self._profile_for(consumer)
        if profile is not None:
            return profile.enabled and self._eligible("profile", profile)
        return consumer.id == self.config.residual_consumer_id

    def _profile_for(self, c: Consumer) -> Profile | None:
        return next((p for p in self.config.profiles if c.id in p.consumer_ids), None)

    def _blocked_condition_groups(self) -> list[tuple[Profile, list[Consumer], str]]:
        by_id = {c.id: c for c in self.config.consumers}
        result = []
        for profile in self.config.profiles:
            if self._eligible("profile", profile):
                continue
            members = [by_id[cid] for cid in profile.consumer_ids if cid in self.owned and
                       cid in by_id and self.states.get(by_id[cid].entity_id) == "on"]
            if members:
                result.append((profile, members, self._eligibility_reason("profile", profile)))
        return result

    def observe_grid(self, raw: Any, unit: str | None, *, age_s: float = 0,
                     restored: bool = False) -> None:
        at = self.clock() - age_s if math.isfinite(age_s) and age_s >= 0 else None
        self.reading = Reading(raw, unit, at, self.reading.sequence + 1, restored)
        self._maybe_restore_startup()
        value, error, _ = self.power()
        if error:
            self.deficit_since = None
            if self.mode == "running":
                self._fault(error)
        elif value is not None and value >= self.config.reserve_w:
            self.deficit_since = None
        # Periodically checkpoint fair accounting; adjacent intervals are
        # coalesced, so fixed-period history does not grow on every grid sample.
        if self.mode == "running" and any(
            self.wall_clock() - opened[0] >= 60 for opened in self.fairness.active.values()
        ):
            self._fair_refresh()
        self.wake()

    def seed_switch(self, entity_id: str, state: str) -> None:
        """Initial observation never means that RRH acquired a device."""
        self._fair_refresh()
        self.states[entity_id] = state
        self._fair_refresh()
        c = next((c for c in self.config.consumers if c.entity_id == entity_id), None)
        if c and state == "off" and c.id in self.owned:
            # The end time of a device stopped while HA was offline is
            # unknown; do not invent its runtime here.
            self.owned.remove(c.id)
            self.started_at.pop(c.id, None)
            self.power_levels.pop(c.id, None)
            if c.cooldown_s:
                self.cooldown_until[c.id] = self.wall_clock() + c.cooldown_s
            self._changed()

    def observe_switch(self, entity_id: str, state: str, *,
                       command_token: str | None = None, explicit_external: bool = False) -> None:
        self._fair_refresh()
        previous = self.states.get(entity_id)
        self.states[entity_id] = state
        self._fair_refresh()
        if previous == "on" and state == "off":
            c_off = next((c for c in self.config.consumers if c.entity_id == entity_id), None)
            if c_off:
                if c_off.id in self.owned:
                    self._record_runtime(c_off.id)
                self.started_at.pop(c_off.id, None)
                self.power_levels.pop(c_off.id, None)
                if c_off.cooldown_s:
                    self.cooldown_until[c_off.id] = self.wall_clock() + c_off.cooldown_s
                self._changed()
        if self._emergency_active:
            self._emergency_change.set()
            p = self.pending
            if p is not None and p.consumer.entity_id == entity_id:
                p.problem = "Hauptschalter AUS hat den vorherigen Auftrag abgebrochen."
                p.observed.set()
            if previous != state:
                self.wake()
            return
        # Group-condition OFF is a single HA service call; confirmations of its
        # members must not be mistaken for external interference.
        group = self.pending
        if group is not None and group.group_ids and group.sent:
            member = next((c for c in self.config.consumers if c.entity_id == entity_id), None)
            if member and member.id in group.group_ids:
                if explicit_external and command_token is None:
                    group.problem = f"{member.name}: Externe Zustandsänderung während der Gruppenabschaltung."
                    group.observed.set()
                elif state not in ("off", "on"):
                    group.problem = f"{member.name}: Status während Profilabschaltung unbekannt."
                    group.observed.set()
                elif all(self.states.get(c.entity_id) == "off" for c in self.config.consumers if c.id in group.group_ids):
                    group.observed.set()
                self.wake()
                return
        if previous == state:
            self._maybe_restore_startup()
            return
        c = next((c for c in self.config.consumers if c.entity_id == entity_id), None)
        if c is None:
            return
        if self.mode == "stopped" and self._has_confirmed_all_off and state != "off":
            self.emergency_unresolved = True
            self._changed()
            self._fault(f"{c.name} ist nach Hauptschalter AUS nicht mehr ausgeschaltet. Geräte prüfen und AUS erneut ausführen.")
            self.wake()
            return
        p = self.pending
        is_target = p is not None and p.consumer.id == c.id and p.sent
        if is_target:
            _LOGGER.info("RRH Schalt-Rueckmeldung: %s Zustand=%s erwartet=%s Kontext_zugeordnet=%s Benutzerkontext=%s", entity_id, state, p.target, command_token == p.token, explicit_external)
        if is_target and state == p.target and not (explicit_external and command_token != p.token):
            p.observed_sequence = self.reading.sequence
            p.observed.set()
        else:
            self.wait_after_sequence = self.reading.sequence
            if c.id in self.owned:
                self.owned.remove(c.id)
                self.started_at.pop(c.id, None)
                self._changed()
            if is_target:
                p.problem = "Widerspr\u00fcchliche oder fremde R\u00fcckmeldung w\u00e4hrend des Schaltauftrags."
                p.observed.set()
                self._fault(p.problem)
            elif self.mode == "running" and (state in ("on", "off") or previous == "on"):
                self._fault(f"Externe Zustands\u00e4nderung bei {c.name}. Automatik pausiert; keine \u00dcbernahme.")
        # Complete startup AFTER classifying the report as normal initialization,
        # not before (otherwise a late HA state could look like external tampering).
        self._maybe_restore_startup()
        self.wake()

    def power(self) -> tuple[float | None, str | None, float | None]:
        r = self.reading
        age = None if r.at is None else max(0.0, self.clock() - r.at)
        if not self.config.grid_entity:
            return None, "Bitte zuerst eine Netzleistungsentit\u00e4t ausw\u00e4hlen.", age
        try:
            value = grid_watts(r.raw, r.unit, self.config.export_positive)
        except UserError as err:
            return None, str(err), age
        if r.restored:
            return value, "Die Netzquelle ist nur ein wiederhergestellter Wert. Neue Meldung abwarten.", age
        if age is None:
            return value, "Das Meldungsalter der Netzquelle ist nicht bestimmbar.", age
        if age > self.config.max_age_s:
            return value, f"Netzmessung veraltet ({age:.0f} s). Keine weiteren Schaltbefehle.", age
        return value, None, age

    def _revision_check(self, expected: int) -> None:
        if type(expected) is not int or expected != self.revision:
            raise UserError("Einstellungen wurden inzwischen ge\u00e4ndert. Neu laden, dann erneut bearbeiten.")

    async def configure(self, config: dict, expected_revision: int, *, currency_tariffs_confirmed: bool = False) -> None:
        proposed = Config.parse(config)
        if self.emergency_unresolved or self._emergency_active:
            raise UserError("Vor der Bearbeitung den unbestätigten Hauptschalter-Aus-Befehl erneut ausführen.")
        if self.pending is not None or self.mode == "running":
            raise UserError("Zum Bearbeiten zuerst pausieren und den offenen Auftrag abwarten.")
        async with self._lock:
            self._revision_check(expected_revision)
            if self.closed or self.pending is not None or self.mode == "running" or self._emergency_active:
                raise UserError("Die Anwendung ist besch\u00e4ftigt oder wurde entladen.")
            if proposed.energy.currency != self.config.energy.currency and self.statistics.totals["valued_kwh"] > 0:
                raise UserError("Währungswechsel würde historische Beträge verfälschen. Exportieren und Gesamtstatistik bewusst zurücksetzen, dann die Währung wechseln.")
            if proposed.energy.currency != self.config.energy.currency:
                prior_pricing = any(source.value is not None or source.entity_id
                                    for source in (self.config.energy.import_price, self.config.energy.feed_in_price))
                if prior_pricing and currency_tariffs_confirmed is not True:
                    raise UserError("Währungswechsel: Bezugspreis und Einspeisevergütung müssen ausdrücklich in der neuen Währung bestätigt werden.")
                if prior_pricing and any(source.mode == "fixed" and source.value is None
                                         for source in (proposed.energy.import_price, proposed.energy.feed_in_price)):
                    raise UserError("Währungswechsel: Beide Tarife in neuer Währung erfassen oder passende Tarif-Sensoren auswählen.")
            old_map, new_map = ({c.id: c for c in cfg.consumers} for cfg in (self.config, proposed))
            for cid, c in old_map.items():
                removed_or_replaced = cid not in new_map or new_map[cid].entity_id != c.entity_id
                if removed_or_replaced and (cid in self.owned or (self.incomplete and self.incomplete["id"] == cid)) and self.states.get(c.entity_id) != "off":
                    raise UserError(f"{c.name}: Vor Entfernen oder Schalterwechsel in HA ausschalten und R\u00fcckmeldung abwarten.")
            self._fair_refresh()
            previous = self.document()
            source_changed = proposed.grid_entity != self.config.grid_entity
            self.config = proposed
            # An explicit edit of configuration overrides an armed autostart.
            self._startup_restore = False
            self._startup_grid_sequence = None
            self.statistics.money_currency = proposed.energy.currency
            # Edited thresholds, operators and sensors must not inherit an old
            # hysteresis latch, which could otherwise permit an unsafe start.
            self.condition_latches = {}
            self.profile_cursors = {
                profile.id: self.profile_cursors[profile.id]
                for profile in proposed.profiles
                if profile.id in self.profile_cursors and self.profile_cursors[profile.id] in profile.consumer_ids
            }
            self.revision += 1
            self.owned = [cid for cid in self.owned if cid in new_map and old_map[cid].entity_id == new_map[cid].entity_id]
            self.started_at = {i: t for i, t in self.started_at.items() if i in self.owned}
            kept = {i for i in new_map if i in old_map and old_map[i].entity_id == new_map[i].entity_id}
            self.cooldown_until = {i: t for i, t in self.cooldown_until.items() if i in kept}
            self.runtime_totals_s = {i: t for i, t in self.runtime_totals_s.items() if i in kept}
            self.power_levels = {i: v for i, v in self.power_levels.items() if i in kept}
            self.runtime_segments = [part for part in self.runtime_segments if part[0] in kept]
            self.fairness.restrict(profiles=proposed.profiles, consumers=proposed.consumers)
            self._fair_refresh()
            self._efficiency_goals.clear()
            self._efficiency_last_swap.clear()
            if self.incomplete and (self.incomplete["id"] not in new_map or self.states.get(old_map[self.incomplete["id"]].entity_id) == "off"):
                self.incomplete = None
            self._changed()
            try:
                await self._persist()
            except Exception as err:
                relinquished = set(previous["owned"]) - set(self.owned)
                self._load(previous)
                self.statistics.money_currency = previous["statistics"].get("money_currency", "EUR")
                self.owned = [i for i in self.owned if i not in relinquished]
                self._changed()
                self._fault("Einstellungen konnten nicht gespeichert werden. Keine Aktivierung.")
                raise UserError(self.reason) from err
            if source_changed:
                self.reading = Reading(sequence=self.reading.sequence)
            self.wait_after_sequence = None
            self.reason = "Einstellungen gespeichert. Automatik bleibt pausiert."

    async def factory_reset(self, expected_revision: int, confirmation: str) -> None:
        """Irreversible, admin-confirmed reset *only after verified all-off*.

        Never delete the HA storage file, external devices or HA recorder data.
        The replacement document is durably verified before changing memory.
        """
        if confirmation != "RESET ROUND ROBIN HOOD":
            raise UserError("Vollständiger Reset nicht bestätigt.")
        if self.mode != "stopped" or not self._has_confirmed_all_off or self.emergency_unresolved or self._emergency_active:
            raise UserError("Reset nur nach vollständig bestätigtem Alle AUS möglich.")
        if self.pending is not None or self.incomplete is not None or self.closed:
            raise UserError("Reset gesperrt: unbestätigter Auftrag oder Integration entladen.")
        async with self._lock:
            self._revision_check(expected_revision)
            if (self.closed or self.mode != "stopped" or not self._has_confirmed_all_off or self.pending is not None or
                    self.emergency_unresolved or self._emergency_active or self.incomplete is not None):
                raise UserError("Reset gesperrt: Schaltzustand hat sich geändert.")
            if (self.owned or any(self.states.get(c.entity_id) != "off" for c in self.config.consumers)):
                raise UserError("Reset gesperrt: Nicht alle RRH-Verbraucher sind als AUS bestätigt.")
            # The storage writer performs its own read-after-write verification.
            fresh = {
                "schema": 1, "config": Config().to_dict(), "revision": self.revision + 1,
                "cursor": None, "profile_cursors": {}, "owned": [], "incomplete": None,
                "emergency_unresolved": False, "started_at": {}, "cooldown_until": {},
                "condition_latches": {}, "runtime_totals_s": {}, "power_levels": {},
                "runtime_segments": [], "fairness": FairLedger().document(),
                "statistics": EnergyLedger(timezone=self.statistics.timezone).document(), "resume_mode": "stopped",
            }
            try:
                await self.save(fresh)
            except Exception as err:
                # Disk durability may be ambiguous after an I/O error. Never
                # silently retry with the former configuration after a reset.
                self._storage_failed = True
                self._fault("Reset-Speicherprüfung fehlgeschlagen. HA-Protokoll und Sicherung prüfen; nicht erneut starten.")
                raise UserError(self.reason) from err
            self._load(fresh)
            self._has_confirmed_all_off = False
            self.statistics = EnergyLedger(fresh["statistics"], timezone=self.statistics.timezone)
            self.states.clear()
            self.condition_states.clear()
            self.reading = Reading()
            self.stat_sources.clear()
            self._efficiency_goals.clear()
            self._efficiency_last_swap.clear()
            self._last_level_change.clear()
            self._regulation_off = None
            self.wait_after_sequence = self.reading.sequence
            self.deficit_since = None
            self.mode = "stopped"
            self.reason = "RRH vollständig zurückgesetzt. Einrichtungsassistent starten; Automatik bleibt AUS."
            self.last_action = "RRH-Daten vollständig zurückgesetzt; HA-Geräte und HA-Historie unverändert."
            self._storage_failed = False
            self._changed()
            self._persisted_generation = self._generation
        self.wake()

    async def dismiss_notice(self, dismissed: bool) -> None:
        """Persist UI-only acknowledgment on the LIVE controller, never in demo.

        This is not an actuator authorization and may not start an appliance.
        """
        if type(dismissed) is not bool:
            raise UserError("Ungültige Hinweisbestätigung.")
        async with self._lock:
            if self.closed:
                raise UserError("Integration wurde entladen.")
            old_config, old_revision = self.config, self.revision
            self.config = replace(self.config, notice_dismissed=dismissed)
            self.revision += 1
            self._changed()
            try:
                await self._persist()
            except Exception as err:
                self.config, self.revision = old_config, old_revision
                self._changed()
                raise UserError("Hinweisbestätigung konnte nicht gespeichert werden.") from err

    async def participation(self, consumer_id: str, enabled: bool, expected_revision: int) -> None:
        if type(enabled) is not bool:
            raise UserError("Ung\u00fcltiger Teilnahmestatus.")
        if self.pending is not None:
            raise UserError("Bitte die laufende Schaltbest\u00e4tigung abwarten.")
        async with self._lock:
            self._revision_check(expected_revision)
            if self.closed or self.pending is not None or self._emergency_active:
                raise UserError("Die Anwendung ist besch\u00e4ftigt oder wurde entladen.")
            if not any(c.id == consumer_id for c in self.config.consumers):
                raise UserError("Verbraucher nicht gefunden.")
            self._fair_refresh()
            old_config, old_revision = self.config, self.revision
            self.config = replace(self.config, consumers=tuple(replace(c, enabled=enabled) if c.id == consumer_id else c for c in self.config.consumers))
            self._fair_refresh()
            self.revision += 1
            self._changed()
            try:
                await self._persist()
            except Exception as err:
                self.config, self.revision = old_config, old_revision
                self._changed()
                self._fault("Teilnahme konnte nicht gespeichert werden.")
                raise UserError(self.reason) from err
        self.wake()

    async def profile_participation(self, profile_id: str, enabled: bool, expected_revision: int) -> None:
        """Activate/deactivate one profile without interrupting the other profiles.

        Deactivation triggers confirmed OFF commands for RRH-owned members,
        regardless of min-runtime. Externally controlled switches are not adopted.
        """
        if type(enabled) is not bool:
            raise UserError("Ungültiger Profilstatus.")
        if self.pending is not None or self._emergency_active or self.emergency_unresolved:
            raise UserError("Bitte den laufenden Schalt- oder AUS-Auftrag abwarten.")
        async with self._lock:
            self._revision_check(expected_revision)
            if self.closed or self.pending is not None or self._emergency_active:
                raise UserError("Die Anwendung ist beschäftigt oder wurde entladen.")
            if not any(p.id == profile_id for p in self.config.profiles):
                raise UserError("Profil nicht gefunden.")
            self._fair_refresh()
            old_config, old_revision = self.config, self.revision
            self.config = replace(self.config, profiles=tuple(
                replace(p, enabled=enabled) if p.id == profile_id else p
                for p in self.config.profiles
            ))
            self._fair_refresh()
            self.revision += 1
            self._changed()
            try:
                await self._persist()
            except Exception as err:
                self.config, self.revision = old_config, old_revision
                self._changed()
                self._fault("Profilstatus konnte nicht gespeichert werden.")
                raise UserError(self.reason) from err
        self.wake()

    def restore_startup(self) -> None:
        """Arm a safe restart, but never depend on the UI setup wizard flag.

        HA integrations restore their entities asynchronously. A missing state at
        integration setup is NOT a permanent startup failure. We retain the
        requested restart intent until both the actuator feedback and a fresh
        (post-bind) grid sample have been received. No commands are issued while
        pending, and no old ON commands are replayed.
        """
        if not self._startup_restore:
            if self.config.startup_mode == "off" or (self.config.startup_mode == "last" and self.resume_mode == "stopped"):
                self.mode = "stopped"
                self.reason = "Startverhalten: RRH bleibt AUS. Keine automatische Schaltung."
            return
        if self.incomplete or self.emergency_unresolved:
            self._startup_restore = False
            self.mode = "paused"
            self.reason = "Autostart blockiert: unvollständiger Schaltauftrag oder unbestätigtes Alle AUS. Bitte prüfen."
            return
        if not self.config.grid_entity or not self.config.consumers:
            self._startup_restore = False
            self.mode = "stopped"
            self.reason = "Autostart nicht möglich: Netzquelle oder Verbraucher fehlen."
            return
        active = {cid for profile in self.config.profiles if profile.enabled for cid in profile.consumer_ids}
        if self.config.residual_consumer_id:
            active.add(self.config.residual_consumer_id)
        if not any(c.enabled and c.id in active for c in self.config.consumers):
            self._startup_restore = False
            self.mode = "stopped"
            self.reason = "Autostart nicht möglich: kein aktiver Profil-Verbraucher."
            return
        # A manual configuration is valid even when the optional UI wizard was
        # skipped; setup_complete is an onboarding flag, not a safety gate.
        self.mode = "paused"
        self._startup_grid_sequence = self.reading.sequence
        self.reason = "Autostart vorgemerkt: warte auf neue Netzmessung und bekannte Verbraucherzustände."
        self._maybe_restore_startup()

    def _maybe_restore_startup(self) -> None:
        """Complete auto-start only when all runtime prerequisites are verified."""
        if not self._startup_restore or self.closed or self.incomplete or self.emergency_unresolved:
            return
        if any(self.states.get(c.entity_id) not in ("on", "off") for c in self.config.consumers):
            self.reason = "Autostart wartet auf Rückmeldungen aller konfigurierten Verbraucher."
            return
        if self._startup_grid_sequence is None or self.reading.sequence <= self._startup_grid_sequence:
            self.reason = "Autostart wartet auf eine neue Netzleistungsmeldung nach dem Neustart."
            return
        value, error, _ = self.power()
        if error or value is None:
            self.reason = f"Autostart wartet auf gültige Netzleistung: {error or 'kein Messwert'}."
            return
        self._startup_restore = False
        self._startup_grid_sequence = None
        self.mode = "running"
        self.resume_mode = "running"
        # The current report was accepted AFTER the boot barrier and the
        # actuator checks. It is safe to evaluate without an extra stale sample.
        self.wait_after_sequence = self.reading.sequence - 1
        self.deficit_since = None
        self.reason = "Neustartprüfung bestanden: automatische Steuerung aktiviert."
        self._changed()  # _drain persists before invoking any HA service.
        self.wake()

    async def activate(self) -> None:
        if self.emergency_unresolved or self._emergency_active:
            raise UserError("Hauptschalter AUS ist nicht abgeschlossen. Zuerst alle Verbraucher ausschalten und bestätigen.")
        if self.mode == "running":
            return
        if self.pending is not None:
            raise UserError("Ein bereits versandter Schaltauftrag ist noch offen.")
        async with self._lock:
            if self.closed or self._emergency_active:
                raise UserError("Integration wurde entladen oder wird gestoppt.")
            stop_epoch = self._stop_epoch
            _, error, _ = self.power()
            if error:
                raise UserError(error)
            active = {cid for p in self.config.profiles if p.enabled for cid in p.consumer_ids}
            if self.config.residual_consumer_id:
                active.add(self.config.residual_consumer_id)
            if not any(c.enabled and c.id in active for c in self.config.consumers):
                raise UserError("Mindestens ein aktives Profil mit teilnehmendem Verbraucher erforderlich.")
            for c in self.config.consumers:
                if c.id in self.owned and self.states.get(c.entity_id) not in ("on", "off"):
                    raise UserError(f"{c.name}: Zustand eines verwalteten Verbrauchers ist unbekannt.")
            # A failed/unfinished ON never silently becomes owned on explicit recovery.
            if self.incomplete and self.incomplete["target"] == "on":
                self.owned = [i for i in self.owned if i != self.incomplete["id"]]
            self.incomplete = None
            self._changed()
            try:
                await self._persist()
            except Exception as err:
                self._fault("Speicherung fehlgeschlagen. Betrieb bleibt gestoppt.")
                raise UserError(self.reason) from err
            # A pause or invalid source during slow storage must not be lost.
            if self._stop_epoch != stop_epoch or self.closed:
                raise UserError("Aktivierung durch Pause oder Fehler abgebrochen.")
            _, error, _ = self.power()
            if error:
                raise UserError(error)
            self.mode, self.reason = "running", "Automatik aktiviert."
            self._startup_restore = False
            self._startup_grid_sequence = None
            self.resume_mode = "running"
            self._changed()
            try:
                await self._persist()
            except Exception as err:
                self._fault("Startzustand konnte nicht gespeichert werden. Keine automatische Steuerung.")
                raise UserError(self.reason) from err
            self._fair_refresh()
            self.deficit_since = None
        self.wake()

    def sample_statistics(self, *, values: dict | None = None) -> None:
        """Record one fresh-meter sample. Called only by the HA timer, never
        by frontend polling. Demo samples are synthetic and unpersisted.
        """
        if self.closed:
            return
        values=values or {}
        export, error, _ = self.power()
        valid_export = export if error is None else None
        loads={c.id:self._load_w(c) for c in self.config.consumers
               if c.id in self.owned and self.states.get(c.entity_id)=="on"}
        self.stat_sources={k:v for k,v in values.items() if k in ("pv_size_kwp", "pv_power_w", "import_price", "feed_in_price", "warnings")}
        if self.statistics.sample(self.wall_clock(),mode=self.mode,export_w=valid_export,
                                  managed_w=sum(loads.values()),loads=loads,
                                  buy_price=values.get("import_price"),feed_price=values.get("feed_in_price"),
                                  pv_meter_kwh=values.get("pv_meter_kwh"),
                                  export_meter_kwh=values.get("export_meter_kwh")):
            self._changed()

    async def reset_statistics(self, expected_revision: int) -> None:
        if self.mode == "running" or self.pending is not None or self._emergency_active:
            raise UserError("Gesamtstatistik nur im pausierten Betrieb zurücksetzen.")
        async with self._lock:
            self._revision_check(expected_revision)
            previous=self.statistics.document()
            self.statistics.reset(self.wall_clock())
            self._changed()
            try:
                await self._persist()
            except Exception as err:
                self.statistics=EnergyLedger(previous, timezone=self.statistics.timezone)
                self._changed()
                self._fault("Gesamtstatistik konnte nicht gespeichert werden.")
                raise UserError(self.reason) from err

    def _fair_refresh(self) -> None:
        """Reconcile confirmed live ownership with strategy-specific credit."""
        current = {}
        if self.mode == "running":
            by_id = {c.id: c for c in self.config.consumers}
            for profile in self.config.profiles:
                if not profile.enabled or profile.strategy not in FAIR_STRATEGIES:
                    continue
                if self.fairness.ensure_started(profile.strategy, profile.id, self.wall_clock()):
                    self._changed()
                for cid in profile.consumer_ids:
                    c = by_id.get(cid)
                    if (c is not None and c.enabled and cid in self.owned and
                            self.states.get(c.entity_id) == "on"):
                        current[(profile.strategy, profile.id, cid)] = self._load_w(c)
        if self.fairness.sync(current, self.wall_clock()):
            self._changed()

    def _load_w(self, consumer: Consumer) -> float:
        """Confirmed load estimate; smart consumers use their last observed output level."""
        if consumer.power_mode != "fixed" and consumer.id in self.owned:
            return self.power_levels.get(consumer.id, consumer.watts)
        return consumer.watts

    def seed_power_level(self, consumer_id: str, watts: float | None) -> None:
        # Startup never adopts a device. Only restore measured setpoints to
        # previously confirmed ownership; another device is ignored.
        if consumer_id in self.owned and watts is not None and math.isfinite(watts):
            self.power_levels[consumer_id] = max(0.0, watts)

    def observe_power_level(self, consumer_id: str, watts: float | None, *, explicit_external: bool = False) -> None:
        """HA feedback of a setpoint/option, not assumed device consumption."""
        if watts is None or not math.isfinite(watts) or watts < 0:
            if consumer_id in self.owned and self.mode == "running":
                self._fault("Unbekannte Leistungsstufe eines verwalteten Verbrauchers.")
            return
        old = self.power_levels.get(consumer_id)
        if old is not None and abs(old - watts) < 0.001:
            pending = self.pending
            if pending and pending.consumer.id == consumer_id and pending.target == "level" and pending.sent and abs(watts - (pending.target_watts or 0)) < 0.001:
                pending.observed.set()
            return
        self._fair_refresh()
        self.power_levels[consumer_id] = watts
        self._fair_refresh()
        pending = self.pending
        if pending and pending.consumer.id == consumer_id and pending.target == "level" and pending.sent:
            if abs(watts - (pending.target_watts or 0)) < 0.001 and not explicit_external:
                pending.observed.set()
            else:
                pending.problem = "Leistungsrückmeldung weicht vom Sollwert ab oder wurde extern verändert."
                pending.observed.set()
        elif consumer_id in self.owned and self.mode == "running" and not (pending and pending.consumer.id == consumer_id and pending.target in ("on", "off")):
            self._fault("Leistungsstufe extern geändert. Automatik pausiert.")
        self._changed()
        self.wake()

    def _fair_value(self, kind: str, profile: Profile, consumer_id: str) -> float:
        return self.fairness.value(kind, profile.id, consumer_id, profile.runtime_window, self.wall_clock())

    async def reset_fair(self, profile_id: str, kind: str, expected_revision: int) -> None:
        """Explicit, administrator-confirmed profile statistic reset (not global runtime)."""
        if kind not in FAIR_STRATEGIES:
            raise UserError("Unbekannte Fairness-Statistik.")
        if self.mode == "running" or self.pending is not None or self._emergency_active:
            raise UserError("Für das Zurücksetzen zuerst RRH pausieren.")
        async with self._lock:
            self._revision_check(expected_revision)
            if self.closed or self.mode == "running" or self.pending is not None:
                raise UserError("Automatik ist beschäftigt. Zuerst pausieren.")
            if not any(p.id == profile_id for p in self.config.profiles):
                raise UserError("Profil nicht gefunden.")
            previous = self.document()
            self.fairness.reset(kind, profile_id, self.wall_clock())
            self.revision += 1
            self._changed()
            try:
                await self._persist()
            except Exception as err:
                self._load(previous)
                self._changed()
                self._fault("Fairness-Statistik konnte nicht gespeichert werden.")
                raise UserError(self.reason) from err
            self.reason = "Fairness-Statistik des Profils zurückgesetzt."

    def _record_runtime(self, consumer_id: str) -> None:
        """Log a confirmed, RRH-owned run exactly once on observed OFF."""
        start = self.started_at.get(consumer_id)
        end = self.wall_clock()
        if start is None or start <= 0 or start >= end:
            return
        seconds = end - start
        self.runtime_totals_s[consumer_id] = self.runtime_totals_s.get(consumer_id, 0.0) + seconds
        self.runtime_segments.append((consumer_id, start, end))
        cutoff = end - 31 * 86400
        self.runtime_segments = [part for part in self.runtime_segments if part[2] >= cutoff][-20000:]
        self._changed()

    def _runtime_seconds(self, consumer_id: str, window: str) -> float:
        now = self.wall_clock()
        live_start = self.started_at.get(consumer_id)
        c = next((x for x in self.config.consumers if x.id == consumer_id), None)
        live = max(0, now - live_start) if (c is not None and live_start is not None and
                    live_start > 0 and consumer_id in self.owned and self.states.get(c.entity_id) == "on") else 0.0
        if window == "all":
            return self.runtime_totals_s.get(consumer_id, 0.0) + live
        days = {"24h": 1, "7d": 7, "14d": 14, "30d": 30}[window]
        cutoff = now - days * 86400
        seconds = sum(max(0.0, min(end, now) - max(start, cutoff))
                      for cid, start, end in self.runtime_segments if cid == consumer_id)
        if live_start is not None and live:
            seconds += max(0.0, now - max(cutoff, live_start))
        return seconds

    def _can_preempt(self, c: Consumer) -> bool:
        if c.id not in self.owned or self.states.get(c.entity_id) != "on":
            return False
        # Scheduled optimization/rotation must always respect a configured
        # minimum run. The strict flag only changes deficit-triggered shedding.
        return not (c.min_on_s and self.started_at.get(c.id, 0) > 0
                    and self.wall_clock() < self.started_at[c.id] + c.min_on_s)

    def _profile_members(self, profile: Profile) -> list[Consumer]:
        mapping = {c.id: c for c in self.config.consumers}
        return [mapping[cid] for cid in profile.consumer_ids if cid in mapping and cid != self.config.residual_consumer_id]

    def _ranked_members(self, profile: Profile) -> list[Consumer]:
        members = self._profile_members(profile)
        runtime = ({c.id: self._fair_value(profile.strategy, profile, c.id) for c in members}
                   if profile.strategy in FAIR_STRATEGIES else {})
        return ranked_members(profile, members, runtime)

    def _cooldown_remaining(self, c: Consumer) -> float:
        return max(0.0, self.cooldown_until.get(c.id, 0) - self.wall_clock())

    def _eligible_waiting(self, profile: Profile) -> list[Consumer]:
        """Start candidates in strategy order, ignoring ineligible sensor states.

        Power shortage alone does not exclude a device. A configured cooldown
        with cooldown_wait=True blocks the order; otherwise it is skipped.
        """
        if not profile.enabled or not self._eligible("profile", profile):
            return []
        items = self._ranked_members(profile)
        if profile.strategy == "classic" and items:
            cursor = self.profile_cursors.get(profile.id)
            index = next((i for i, c in enumerate(items) if c.id == cursor), -1)
            items = items[index + 1:] + items[:index + 1]
        return [c for c in items if c.id != self.config.residual_consumer_id and c.enabled and c.virtual_confirmed and
                self.states.get(c.entity_id) == "off" and
                self._eligible("consumer", c) and
                (not self._cooldown_remaining(c) or c.cooldown_wait)]

    def _profile_candidate(self, profile: Profile) -> Consumer | None:
        return next(iter(self._eligible_waiting(profile)), None)

    def _efficiency_proposal(self, profile: Profile, export: float) -> tuple[set[str], set[str]]:
        """Compute a profile-local optimal set without stealing another profile's budget.

        All running managed loads are added back to measured grid export,
        *only once*. Other profiles' loads remain in the measurement.
        """
        members = self._profile_members(profile)
        running = {c.id for c in members if c.id in self.owned and self.states.get(c.entity_id) == "on"}
        locked = {c.id for c in members if c.id in running and not self._can_preempt(c)}
        choices = [c for c in members if c.id not in locked and c.enabled and c.virtual_confirmed and
                   self._eligible("consumer", c) and
                   (c.id in running or (self.states.get(c.entity_id) == "off" and not self._cooldown_remaining(c)))]
        current_w = sum(self._load_w(c) for c in members if c.id in running)
        locked_w = sum(self._load_w(c) for c in members if c.id in locked)
        budget = max(0.0, export - self.config.reserve_w - profile.efficiency_start_margin_w + current_w - locked_w)
        chosen = efficient_subset(choices, budget, running)
        return locked | chosen, running

    def _efficiency_action(self, profile: Profile, export: float) -> tuple[Consumer, str] | None:
        desired, running = self._efficiency_proposal(profile, export)
        mapping = {c.id: c for c in self._profile_members(profile)}
        off = [mapping[i] for i in profile.consumer_ids if i in running - desired]
        on = [mapping[i] for i in profile.consumer_ids if i in desired - running]
        active_goal = self._efficiency_goals.get(profile.id)
        if active_goal is not None and active_goal != desired:
            # Sensor, condition or power changes can invalidate an in-flight
            # optimization. Never continue a stale plan without requalification.
            self._efficiency_goals.pop(profile.id, None)
            active_goal = None
        if not off and not on:
            if active_goal is not None:
                self._efficiency_goals.pop(profile.id, None)
                self._efficiency_last_swap[profile.id] = self.clock()
            return None
        # An optimization may start extra devices freely. Replacing already
        # running ones is deliberately less eager to prevent contactor wear.
        if off and active_goal is None:
            benefit = sum(mapping[i].watts for i in desired) - sum(mapping[i].watts for i in running)
            if benefit + 1e-6 < profile.efficiency_min_gain_w:
                self.reason = f"{profile.name}: Optimierung unter Mindestverbesserung ({benefit:g} W)."
                return None
            if self.clock() - self._efficiency_last_swap.get(profile.id, -1e12) < profile.efficiency_interval_s:
                self.reason = f"{profile.name}: Optimierung wartet auf das Wechselintervall."
                return None
            self._efficiency_goals[profile.id] = set(desired)
        if off:
            # One confirmed OFF at a time; a fresh grid report is required
            # before another OFF or subsequent ON.
            self.reason = f"{profile.name}: Optimierung gibt {off[0].name} frei."
            return off[0], "off"
        if on:
            # The measured export already includes all managed ON loads.
            available = export - self.config.reserve_w
            if available - profile.efficiency_start_margin_w + 1e-7 >= on[0].watts:
                self.reason = f"{profile.name}: Optimierung startet {on[0].name}."
                return on[0], "on"
        return None

    def _fair_rotation_choice(self, profile: Profile, available: float,
                              candidates: list[Consumer]) -> tuple[Consumer, Consumer] | None:
        """Find an achievable fairness swap, not merely the first waiting ID.

        A waiting device may overtake a power-infeasible candidate only if the
        profile explicitly allows skipping. Rotation never bypasses a minimum
        run, restart cooldown, or the configured rotation interval / fair gap.
        No OFF is sent unless an ON will fit after freeing eligible managed loads.
        """
        if profile.strategy not in FAIR_STRATEGIES:
            return None
        now = self.wall_clock()
        ranked_running = [c for c in self._ranked_members(profile)
                          if c.id in self.owned and self.states.get(c.entity_id) == "on"
                          and self._can_preempt(c)
                          and now - self.started_at.get(c.id, now) >= profile.fair_rotation_s]
        if not ranked_running:
            return None
        gap = profile.fair_min_gap_s if profile.strategy == "fair_runtime" else profile.fair_min_gap_wh
        for candidate in (candidates if profile.allow_power_skip else candidates[:1]):
            if self._cooldown_remaining(candidate):
                # An explicit cooldown wait is a real barrier, not a power skip.
                if candidate.cooldown_wait:
                    return None
                continue
            if available + 1e-7 >= candidate.watts:
                continue  # No replacement needed; ordinary scheduling starts it.
            candidate_credit = self._fair_value(profile.strategy, profile, candidate.id)
            replaceable = [c for c in ranked_running
                           if self._fair_value(profile.strategy, profile, c.id) >= candidate_credit + gap]
            replaceable.sort(key=lambda c: (-self._fair_value(profile.strategy, profile, c.id), -c.watts))
            if available + sum(self._load_w(c) for c in replaceable) + 1e-7 >= candidate.watts:
                return candidate, replaceable[0]
        return None

    def _strategy_action(self, profile: Profile, export: float) -> tuple[tuple[Consumer, str] | None, bool]:
        """Return an optional action and whether this profile blocks lower ones.

        Only an ineligible device (sensor/participation/cooldown without wait)
        may be silently bypassed in strict mode. Lack of watts never skips the
        head unless this profile explicitly allows power-based overtaking.
        """
        if not profile.enabled or not self._eligible("profile", profile):
            self._efficiency_goals.pop(profile.id, None)
            return None, False
        if profile.strategy == "maximum_efficiency":
            result = self._efficiency_action(profile, export)
            return result, bool(result)
        available = export - self.config.reserve_w
        eligible = self._eligible_waiting(profile)
        if not eligible:
            return None, False

        # A deliberately waiting cooldown remains a hard barrier. Neither the
        # strict nor flexible power setting changes configured cooldown policy.
        first = eligible[0]
        remaining = self._cooldown_remaining(first)
        if remaining:
            self.reason = f"{profile.name}: {first.name} Wiedereinschaltsperre noch {remaining:.0f} s."
            return None, True

        candidate = first
        can_skip_power = profile.allow_power_skip or profile.strategy == "stable_operation"
        if can_skip_power:
            fitting = next((c for c in eligible if not self._cooldown_remaining(c) and
                            available + 1e-7 >= c.watts), None)
            if fitting is not None:
                return (fitting, "on"), True
        elif available + 1e-7 >= candidate.watts:
            return (candidate, "on"), True

        if profile.strategy in ("classic", "stable_operation"):
            self.reason = (f"{profile.name}: {candidate.name} wartet auf Überschuss."
                           if can_skip_power else
                           f"{profile.name}: {candidate.name} wartet auf Überschuss. Kein Überholen.")
            return None, True

        ranked = self._ranked_members(profile)
        running = [c for c in ranked if c.id in self.owned and self.states.get(c.entity_id) == "on"]
        if profile.strategy in ("fixed_priority", "power_asc", "power_desc"):
            order = {c.id: i for i, c in enumerate(ranked)}
            replaceable = [c for c in running if order[c.id] > order[candidate.id] and self._can_preempt(c)]
            replaceable.reverse()  # Lowest priority in this profile first.
        else:  # Fairness: skip unfittable candidates *also for rotations*.
            swap = self._fair_rotation_choice(profile, available, eligible)
            if swap is not None:
                target, victim = swap
                self.reason = f"{profile.name}: Fairness-Rotation: {victim.name} macht Platz für {target.name}."
                return (victim, "off"), True
            self.reason = f"{profile.name}: Fairness wartet auf Leistung, Mindestvorsprung oder Schutzzeit."
            return None, True
        if replaceable and available + sum(self._load_w(c) for c in replaceable) + 1e-7 >= candidate.watts:
            self.reason = f"{profile.name}: {replaceable[0].name} macht Platz für {candidate.name}."
            return (replaceable[0], "off"), True
        self.reason = f"{profile.name}: {candidate.name} wartet auf Leistung oder geschützte Laufzeit."
        return None, True

    def _priority_rebalance_action(self, export: float, running: list[Consumer]) -> tuple[Consumer, str] | None:
        """Give an activated higher-priority group power currently used below it.

        Preempt only if an eligible higher-priority device can actually start
        after releasing unprotected lower-priority managed loads. Never take
        over external switches, bypass protection timers or shed speculatively
        when the desired consumer cannot fit even after reclaiming all loads.
        """
        profiles = self.config.profiles
        positions = {c.id: idx for idx, profile in enumerate(profiles) for c in self._profile_members(profile)}
        available = export - self.config.reserve_w
        for idx, profile in enumerate(profiles[:-1]):
            if not profile.enabled or not self._eligible("profile", profile):
                continue
            lower = [c for c in running if positions.get(c.id, -1) > idx and self._can_preempt(c)]
            if not lower:
                continue
            # Lower priority groups relinquish first; within a group prefer
            # the largest load so a single OFF can free sufficient headroom.
            lower.sort(key=lambda c: (-positions[c.id], -c.watts))
            reclaimable = sum(self._load_w(c) for c in lower)
            if profile.strategy == "maximum_efficiency":
                desired, currently_on = self._efficiency_proposal(profile, export + reclaimable)
                candidates = [c for c in self._profile_members(profile) if c.id in desired - currently_on]
            else:
                candidates = self._eligible_waiting(profile)
                if candidates and self._cooldown_remaining(candidates[0]):
                    continue
                if profile.strategy != "stable_operation" and not profile.allow_power_skip:
                    candidates = candidates[:1]
            margin = profile.efficiency_start_margin_w if profile.strategy == "maximum_efficiency" else 0
            target = next((c for c in candidates if not self._cooldown_remaining(c) and
                           available - margin + 1e-7 < c.watts and
                           available + reclaimable - margin + 1e-7 >= c.watts), None)
            if target is None:
                continue
            # Free one lower-priority load at a time. The next step is only
            # evaluated after a fresh grid reading; there is no stale swap plan.
            first = lower[0]
            self.reason = f"Priorität: {first.name} macht Platz für {target.name} ({profile.name})."
            return (first, "off")
        return None

    def _status_candidate(self, profile: Profile, export: float | None, error: str | None) -> Consumer | None:
        candidates = self._eligible_waiting(profile)
        candidate = next(iter(candidates), None)
        if not profile.enabled or error or export is None:
            return candidate
        if profile.strategy == "maximum_efficiency":
            desired, running = self._efficiency_proposal(profile, export)
            return next((c for c in self._profile_members(profile) if c.id in desired - running), candidate)
        if (profile.allow_power_skip or profile.strategy == "stable_operation") and candidates:
            available = export - self.config.reserve_w
            immediately_fitting = next((c for c in candidates if not self._cooldown_remaining(c) and
                                        c.watts <= available + 1e-7), None)
            if immediately_fitting is not None:
                return immediately_fitting
            if profile.strategy in FAIR_STRATEGIES:
                # Include safely reclaimable managed power so the next feasible
                # rotational candidate is displayed, rather than a perpetually
                # unfittable lower-credit load.
                running_w = sum(self._load_w(c) for c in self._profile_members(profile)
                                if c.id in self.owned and self.states.get(c.entity_id) == "on"
                                and self._can_preempt(c))
                return next((c for c in candidates if not self._cooldown_remaining(c) and
                             c.watts <= available + running_w + 1e-7), candidate)
            return candidate
        return candidate

    def _candidate_with_profile(self) -> tuple[Profile, Consumer] | None:
        # The first active group in config order wins the next power budget.
        # In particular, a high-priority candidate that lacks enough power
        # blocks lower profiles instead of being overtaken.
        export, error, _ = self.power()
        for profile in self.config.profiles:
            candidate = self._status_candidate(profile, export, error)
            if candidate is not None:
                return profile, candidate
        return None

    def _next_candidate(self) -> Consumer | None:
        choice = self._candidate_with_profile()
        return choice[1] if choice else None

    def _active_member_ids(self) -> set[str]:
        return {i for p in self.config.profiles if p.enabled for i in p.consumer_ids} | ({self.config.residual_consumer_id} if self.config.residual_consumer_id else set())

    def _deficit_delay(self, c: Consumer) -> float:
        """Explicit consumer override wins; disabled global default means immediate shedding."""
        if c.shutdown_delay_s is not None:
            return c.shutdown_delay_s
        return self.config.shutdown_delay_s if self.config.global_shutdown_delay_enabled else 0.0

    async def skip_timer(self, consumer_id: str, timer: str, expected_revision: int) -> None:
        """Expire a single timer; scheduling still makes all subsequent decisions."""
        if timer not in ("cooldown", "minimum"):
            raise UserError("Unbekannte Zeitregel.")
        if self.pending is not None or self._emergency_active or self.emergency_unresolved:
            raise UserError("Laufenden Schaltauftrag zuerst abschließen.")
        async with self._lock:
            self._revision_check(expected_revision)
            if self.closed or self.pending is not None or self._emergency_active:
                raise UserError("Die Anwendung ist beschäftigt.")
            c = next((x for x in self.config.consumers if x.id == consumer_id), None)
            if c is None:
                raise UserError("Verbraucher nicht gefunden.")
            previous = self.document()
            if timer == "cooldown":
                if self._cooldown_remaining(c) <= 0:
                    raise UserError("Keine laufende Wiedereinschaltsperre.")
                self.cooldown_until.pop(c.id, None)
            else:
                if c.id not in self.owned or self.states.get(c.entity_id) != "on" or not c.min_on_s or self.started_at.get(c.id, 0) + c.min_on_s <= self.wall_clock():
                    raise UserError("Keine laufende Mindestlaufzeit.")
                self.started_at[c.id] = 0.0  # persisted sentinel: explicitly released minimum
            self._changed()
            try:
                await self._persist()
            except Exception as err:
                self._load(previous)
                self._changed()
                self._fault("Zeitregel konnte nicht gespeichert werden.")
                raise UserError(self.reason) from err
            self.reason = f"{c.name}: {timer} manuell beendet; normale Steuerungsregeln gelten weiter."
        self.wake()

    def _decision(self) -> tuple[Consumer, str] | None:
        if self.mode != "running" or self.closed:
            return None
        by_id = {c.id: c for c in self.config.consumers}
        owned_on = [by_id[i] for i in self.owned if i in by_id and self.states.get(by_id[i].entity_id) == "on"]
        for c in self.config.consumers:
            if c.id in self.owned and self.states.get(c.entity_id) not in ("on", "off"):
                self._fault(f"{c.name}: Zustand eines verwalteten Verbrauchers ist unbekannt.")
                return None
        active_members = self._active_member_ids()
        # Eligibility loss is a stop condition, not an energy shortage. It must
        # preempt strict minimum runtime, cooldown and the post-command grid barrier.
        disabled = next((c for c in owned_on if not c.enabled or c.id not in active_members), None)
        if disabled:
            self.reason = f"Teilnahme/Profil deaktiviert: {disabled.name} wird ausgeschaltet."
            return disabled, "off"
        for c in owned_on:
            profile = self._profile_for(c)
            if profile and not self._eligible("profile", profile):
                self.reason = f"Profilbedingung/Zeitplan {profile.name} nicht erfüllt: {c.name} wird sofort ausgeschaltet."
                return c, "off"
            check = self._condition_report("consumer", c)
            window = self._schedule_report(c)
            if not check["allowed"] or not window["allowed"]:
                explanation = "; ".join(reason for reason in (check["reason"], window["reason"]) if reason)
                self.reason = f"Bedingung/Zeitplan {c.name} nicht erfüllt: {explanation}. Sofort abschalten."
                return c, "off"
        value, error, _ = self.power()
        if error or value is None:
            self._fault(error or "Kein Netzleistungswert.")
            return None
        if self.wait_after_sequence is not None and self.reading.sequence <= self.wait_after_sequence:
            self.reason = "Warte auf eine neue Netzmessung nach der Schaltbestätigung."
            return None
        self.wait_after_sequence = None
        if value < self.config.reserve_w:
            if self.deficit_since is None:
                self.deficit_since = self.clock()
            elapsed = self.clock() - self.deficit_since
            priorities = {cid: index for index, profile in enumerate(self.config.profiles) for cid in profile.consumer_ids}
            # Lower profile priority sheds first; within one profile FIFO.
            indexed = list(enumerate(owned_on))
            def shed_key(pair):
                i, c = pair
                profile = self._profile_for(c)
                if profile is None or profile.strategy == "classic":
                    return (-priorities.get(c.id, 999), i)
                rank = {x.id: j for j, x in enumerate(self._ranked_members(profile))}
                if profile.strategy in FAIR_STRATEGIES:
                    return (-priorities.get(c.id, 999), -self._fair_value(profile.strategy, profile, c.id))
                if profile.strategy == "stable_operation":
                    return (-priorities.get(c.id, 999), -self.started_at.get(c.id, 0))
                if profile.strategy == "maximum_efficiency":
                    return (-priorities.get(c.id, 999), -c.watts)
                return (-priorities.get(c.id, 999), -rank.get(c.id, 0))
            shed_order = [c for _, c in sorted(indexed, key=shed_key)]
            due = [c for c in shed_order if
                   elapsed >= self._deficit_delay(c)
                   and not (c.min_on_strict and c.min_on_s and
                            self.started_at.get(c.id, 0) > 0 and
                            self.wall_clock() - self.started_at[c.id] < c.min_on_s)]
            if due:
                self.reason = f"Reserve unterschritten: {due[0].name} wird nach Profilpriorität/FIFO ausgeschaltet."
                return due[0], "off"
            if owned_on:
                remaining = [max(0, self._deficit_delay(c) - elapsed) for c in owned_on]
                if min(remaining, default=0) > 0:
                    self.reason = f"Reserve unterschritten; nächste Abschaltverzögerung noch {min(remaining):.0f} s."
                else:
                    self.reason = "Reserve unterschritten; erzwungene Mindestlaufzeiten schützen die noch laufenden Verbraucher. Netzbezug möglich."
            else:
                self.reason = "Reserve unterschritten. Kein von RRH verwalteter Verbraucher zum Abschalten."
            return None
        self.deficit_since = None
        # Rebalance even when a higher-priority profile was enabled while a
        # lower-priority strategy already held all the available PV capacity.
        rebalance = self._priority_rebalance_action(value, owned_on)
        if rebalance is not None:
            return rebalance
        for profile in self.config.profiles:
            action, blocks_lower = self._strategy_action(profile, value)
            if action is not None:
                return action
            if blocks_lower:
                return None
        self.reason = "Kein verfügbarer Profil-Verbraucher zur Vergabe."
        return None

    def _quantized(self, c: Consumer, maximum: float) -> float:
        if maximum + 1e-7 < c.watts:
            return 0.0
        if c.power_mode == "staged":
            return next((step.watts for step in reversed(c.power_steps) if step.watts <= maximum + 1e-7), 0.0)
        if c.power_mode == "variable":
            steps = max(0, math.floor((min(maximum, c.max_watts) - c.watts + 1e-7) / c.power_step_w))
            return round(min(c.max_watts, c.watts + steps*c.power_step_w), 5)
        return c.watts

    def _running_flexible(self) -> list[Consumer]:
        eligible = [c for c in self.config.consumers if c.power_mode != "fixed" and c.id in self.owned
                    and self.states.get(c.entity_id) == "on"]
        priorities = {cid: idx for idx, p in enumerate(self.config.profiles) for cid in p.consumer_ids}
        # Residual is always the first sacrificed load. Lower profiles next.
        return sorted(eligible, key=lambda c: (-1 if c.id == self.config.residual_consumer_id else 0,
                       -priorities.get(c.id, 999)))

    def _down_plan(self, export: float) -> tuple[Consumer, float] | None:
        """Release adjustable watts before shedding fixed loads or starving a regular load."""
        available = export - self.config.reserve_w
        flexible = self._running_flexible()
        if not flexible:
            return None
        needed = max(0., -available)
        if needed <= 0.00001:
            # A regular candidate must be able to displace the residual sink.
            for profile in self.config.profiles:
                if not profile.enabled or not self._eligible("profile", profile):
                    continue
                eligible = self._eligible_waiting(profile)
                if not eligible:
                    continue
                candidate = eligible[0]
                if self._cooldown_remaining(candidate):
                    return None
                if profile.allow_power_skip:
                    candidate = next((c for c in eligible if not self._cooldown_remaining(c)
                                     and c.watts <= available + sum(self._load_w(x) for x in flexible) + 1e-7), candidate)
                if candidate.watts <= available + 1e-7:
                    return None  # Normal scheduler can start directly.
                if candidate.watts <= available + sum(self._load_w(x) for x in flexible) + 1e-7:
                    needed = candidate.watts - available
                break
        if needed <= 0:
            return None
        for c in flexible:
            current = self._load_w(c)
            if current <= 0:
                continue
            reduced = self._quantized(c, current - needed)
            if reduced + 1e-6 < current:
                if reduced == 0 and not self._can_preempt(c):
                    continue
                return c, reduced
        return None

    def _up_plan(self, export: float) -> tuple[Consumer, float] | None:
        if self.mode != "running" or self.wait_after_sequence is not None or export <= self.config.reserve_w:
            return None
        available = export - self.config.reserve_w
        flexible = self._running_flexible()
        # First top up normal loads (by profile order), residual last.
        priorities = {cid: idx for idx, p in enumerate(self.config.profiles) for cid in p.consumer_ids}
        flexible.sort(key=lambda c: (c.id == self.config.residual_consumer_id, priorities.get(c.id, 999)))
        for c in flexible:
            if not self._consumer_permitted(c):
                continue
            current = self._load_w(c)
            desired = self._quantized(c, current + available)
            if desired > current and desired - current >= c.power_hysteresis_w and self.clock() - self._last_level_change.get(c.id, -1e12) >= c.power_interval_s:
                return c, desired
        residual = next((c for c in self.config.consumers if c.id == self.config.residual_consumer_id), None)
        if (residual and residual.enabled and self.states.get(residual.entity_id) == "off" and
                self._consumer_permitted(residual) and
                self._cooldown_remaining(residual) <= 0 and residual.watts <= available + 1e-7):
            return residual, residual.watts
        return None

    async def _execute_level(self, c: Consumer, target_w: float) -> None:
        """Confirmed setpoint transaction, protected by the same dispatch/storage barriers as ON/OFF."""
        old = self._load_w(c)
        if self.mode != "running" or self.pending is not None or self.states.get(c.entity_id) != "on" or c.id not in self.owned:
            return
        p = self.pending = Pending(c, "level", target_watts=target_w)
        epoch = self._emergency_epoch
        self.incomplete = {"id":c.id,"target":"level"}
        self._changed()
        try:
            await self._persist()
            if self.mode != "running" or self.closed or self._emergency_active or epoch != self._emergency_epoch:
                return
            if not self._consumer_permitted(c):
                self.incomplete = None
                self._changed()
                await self._persist()
                return
            p.sent = True
            async with asyncio.timeout(self.timeout):
                async with self._dispatch_lock:
                    if self._emergency_active or epoch != self._emergency_epoch:
                        raise UserError("Leistungsänderung durch AUS abgebrochen.")
                    await self.send_level(c, target_w, p.token)
                p.service_completed = True
                # Verify a freshly read HA setpoint only; the adapter may have
                # already delivered an event before its service call returned.
                await p.observed.wait()
            if p.problem or abs(self.power_levels.get(c.id, -1.) - target_w) > 0.001:
                raise UserError(p.problem or "Leistungsstufe nicht bestätigt.")
            self.incomplete = None
            self._last_level_change[c.id] = self.clock()
            self._changed()
            await self._persist()
            self.wait_after_sequence = self.reading.sequence
            self.last_action = f"{c.name}: Leistung {old:g} W → {target_w:g} W bestätigt."
            self._fair_refresh()
            self._dirty = True
        except asyncio.CancelledError:
            self._fault("Leistungsänderung unterbrochen.")
            raise
        except Exception:
            _LOGGER.exception("RRH power level confirmation failed for %s", c.entity_id)
            self._fault(f"{c.name}: Leistungsstufe nicht bestätigt; Automatik pausiert.")
        finally:
            self.pending = None

    async def _evaluate(self) -> None:
        if self.mode == "running" and self._startup_grid_sequence is not None:
            # Block ALL dispatch paths, including condition-driven OFF, until a
            # new post-restart meter report has been accepted and vetted.
            if self.reading.sequence <= self._startup_grid_sequence:
                return
            self._startup_grid_sequence = None
            value, error, _ = self.power()
            if error or value is None:
                self._fault(error or "Neustart: Netzquelle nicht verfügbar.")
                return
            if any(self.states.get(c.entity_id) not in ("on", "off") for c in self.config.consumers):
                self._fault("Neustart: Verbraucherrückmeldung nicht verfügbar.")
                return
        if self.mode == "running" and not self.closed:
            for profile, members, explanation in self._blocked_condition_groups():
                if len(members) > 1:
                    await self._execute_group_condition_off(profile, members, explanation)
                    return
            # Time-window expiry preempts adjustable-power optimization and
            # deficit barriers. Never defer an OFF because a watt plan was ready.
            for c in self.config.consumers:
                if c.id not in self.owned or self.states.get(c.entity_id) != "on":
                    continue
                profile = self._profile_for(c)
                if not self._schedule_report(c)["allowed"] or (profile and not self._schedule_report(profile)["allowed"]):
                    await self._execute(c, "off")
                    return
            # Invalid data/conditions are processed by the ordinary decision path.
            export, error, _ = self.power()
            if error is None and export is not None and (self.wait_after_sequence is None or self.reading.sequence > self.wait_after_sequence):
                down = self._down_plan(export)
                if down is not None:
                    c, level = down
                    if level <= 0:
                        self._regulation_off = (c.id, self.reading.sequence)
                        try:
                            await self._execute(c, "off")
                        finally:
                            self._regulation_off = None
                    else:
                        await self._execute_level(c, level)
                    return
        action = self._decision()
        if action is not None:
            await self._execute(*action)
            return
        if self.mode == "running" and not self.closed:
            export, error, _ = self.power()
            if error is None and export is not None:
                up = self._up_plan(export)
                if up is not None:
                    c, level = up
                    if self.states.get(c.entity_id) == "off":
                        # The residual load is intentionally excluded from
                        # regular profiles, so this is its only start path.
                        self._regulation_off = (c.id, self.reading.sequence)
                        try:
                            await self._execute(c, "on")
                        finally:
                            self._regulation_off = None
                    else:
                        await self._execute_level(c, level)

    async def _execute_group_condition_off(self, profile: Profile, consumers: list[Consumer], explanation: str) -> None:
        """Switch all owned, running members off with one HA bulk service call."""
        epoch = self._emergency_epoch
        p = self.pending = Pending(consumers[0], "off", group_ids=tuple(c.id for c in consumers))
        self.incomplete = {"id": consumers[0].id, "target": "off"}
        self._changed()
        try:
            await self._persist()  # crash marker before any real command
            still_blocked = not self._eligible("profile", profile)
            if self.mode != "running" or self.closed or not still_blocked or self._emergency_active:
                self.incomplete = None
                self._changed()
                await self._persist()
                return
            p.sent = True
            self.reason = f"Profil {profile.name}: Bedingung/Zeitplan nicht erfüllt ({explanation}). Alle verwalteten Profilgeräte sofort ausschalten."
            async with asyncio.timeout(self.timeout):
                async with self._dispatch_lock:
                    if self._emergency_epoch != epoch or self._emergency_active:
                        raise UserError("Profilabschaltung durch Hauptschalter AUS abgebrochen.")
                    await self.send_all_off([c.entity_id for c in consumers])
                p.service_completed = True
                if all(self.states.get(c.entity_id) == "off" for c in consumers):
                    p.observed.set()
                await p.observed.wait()
            if self._emergency_epoch != epoch or self._emergency_active:
                return
            if p.problem or any(self.states.get(c.entity_id) != "off" for c in consumers):
                raise UserError(p.problem or "Nicht alle Profil-Verbraucher haben AUS bestätigt.")
            for c in consumers:
                if c.id in self.owned:
                    self.owned.remove(c.id)
                self.started_at.pop(c.id, None)
            self.incomplete = None
            self._changed()
            await self._persist()
            self.wait_after_sequence = self.reading.sequence
            self.last_action = f"{profile.name}: {len(consumers)} Verbraucher gemeinsam ausgeschaltet, bestätigt."
            self._fair_refresh()
            self._dirty = True
        except asyncio.CancelledError:
            if not self._emergency_active:
                self._fault("Profilabschaltung unterbrochen; keine automatische Wiederholung.")
            raise
        except Exception:
            if self._emergency_active or self._emergency_epoch != epoch:
                return
            _LOGGER.exception("RRH group condition OFF failed: %s", profile.id)
            self._fault(f"{profile.name}: Gruppenabschaltung nicht vollständig bestätigt. Geräte prüfen; keine automatische Wiederholung.")
        finally:
            self.pending = None

    async def _execute(self, consumer: Consumer, target: str) -> None:
        start_epoch = self._emergency_epoch
        p = self.pending = Pending(consumer, target)
        self.incomplete = {"id": consumer.id, "target": target}
        self._changed()
        try:
            # Persist a single crash marker BEFORE sending, then re-check live safety.
            await self._persist()
            regulation_ok = (self._regulation_off == (consumer.id, self.reading.sequence)
                             and consumer.power_mode != "fixed" and self.mode == "running" and
                             self.power()[1] is None and self.states.get(consumer.entity_id) == ("off" if target == "on" else "on"))
            if (target == "on" and not self._consumer_permitted(consumer)) or (not regulation_ok and self._decision() != (consumer, target)):
                self.incomplete = None
                self._changed()
                await self._persist()
                return
            p.sent = True
            p.phase = "HA-Schaltaktion"
            _LOGGER.info("RRH Schaltauftrag gestartet: %s -> %s", consumer.entity_id, target)
            self.reason = f"{consumer.name}: Warte auf {'Ein' if target == 'on' else 'Aus'}-Best\u00e4tigung."
            async with asyncio.timeout(self.timeout):
                async with self._dispatch_lock:
                    if self._emergency_epoch != start_epoch or self._emergency_active:
                        raise UserError("Auftrag durch Hauptschalter AUS abgebrochen.")
                    if target == "on" and not self._consumer_permitted(consumer):
                        p.sent = False
                        self.incomplete = None
                        self._changed()
                        await self._persist()
                        return
                    await self.send(consumer.entity_id, target, p.token)
                p.service_completed = True
                p.phase = "Zustandsbestaetigung"
                _LOGGER.info("RRH HA-Schaltaktion zurueckgekehrt: %s -> %s; Zustand=%s; Bestaetigung=%s", consumer.entity_id, target, self.states.get(consumer.entity_id), p.observed.is_set())
                await p.observed.wait()
            if self._emergency_epoch != start_epoch or self._emergency_active:
                raise UserError("Schaltauftrag durch Stopp unterbrochen.")
            if p.problem or self.states.get(consumer.entity_id) != target:
                raise UserError(p.problem or "Der Schalter hat den angeforderten Zustand nicht best\u00e4tigt.")
            old_cursor, old_owned = self.cursor, list(self.owned)
            old_profile_cursors = dict(self.profile_cursors)
            old_started = dict(self.started_at)
            if target == "on":
                self.cursor = consumer.id
                profile = next((p for p in self.config.profiles if consumer.id in p.consumer_ids), None)
                if profile is not None:
                    self.profile_cursors[profile.id] = consumer.id
                self.owned = [i for i in self.owned if i != consumer.id] + [consumer.id]
                self.started_at[consumer.id] = self.wall_clock()
            else:
                self.owned = [i for i in self.owned if i != consumer.id]
                self.started_at.pop(consumer.id, None)
                self.power_levels.pop(consumer.id, None)
            self.incomplete = None
            self._changed()
            try:
                await self._persist()
            except Exception:
                self.cursor = old_cursor
                self.profile_cursors = old_profile_cursors
                self.owned = [i for i in old_owned if i in self.owned]
                self.started_at = {i: t for i, t in old_started.items() if i in self.owned}
                self.incomplete = {"id": consumer.id, "target": target}
                self._changed()
                raise
            self.wait_after_sequence = p.observed_sequence
            self.last_action = f"{consumer.name}: {'eingeschaltet' if target == 'on' else 'ausgeschaltet'}, best\u00e4tigt und gespeichert."
            self._fair_refresh()
            self._dirty = True
        except asyncio.CancelledError:
            if not self._emergency_active:
                self._fault("Schaltauftrag durch Entladen unterbrochen. Keine automatische Wiederholung.")
            raise
        except TimeoutError:
            if self._emergency_active or self._emergency_epoch != start_epoch:
                return
            self.wait_after_sequence = self.reading.sequence
            _LOGGER.warning("RRH Schaltauftrag Timeout: %s -> %s; Phase=%s; Dienst_fertig=%s; Rueckmeldung=%s; beobachtet=%s", consumer.entity_id, target, p.phase, p.service_completed, p.observed.is_set(), self.states.get(consumer.entity_id))
            detail = "HA-Dienstaufruf nicht abgeschlossen" if not p.service_completed else "HA-Dienstaufruf abgeschlossen, aber keine gueltige Zustandsbestaetigung"
            self._fault(f"{consumer.name}: Innerhalb von {self.timeout:g} s keine vollst\u00e4ndige Best\u00e4tigung ({detail}). Keine automatische Wiederholung.")
        except Exception:
            if self._emergency_active or self._emergency_epoch != start_epoch:
                return
            if p.sent:
                self.wait_after_sequence = self.reading.sequence
            _LOGGER.exception("RRH command/confirmation/storage failed for %s", consumer.entity_id)
            self._fault(f"{consumer.name}: Schalt- oder Speicherfehler. Kein unbest\u00e4tigter Zeigerfortschritt; keine automatische Wiederholung.")
        finally:
            self.pending = None

    async def emergency_off(self) -> None:
        """Explicit user stop: dispatch one bulk OFF for *all* configured consumers.

        In contrast to pause, this includes disabled, unowned and unknown switches.
        Never wait for the ordinary scheduling lock before dispatching the OFF.
        The HA adapter orders this call after any already dispatched ON service call.
        No automatic retries. The stored cursor never changes.
        """
        if self.closed:
            raise UserError("Integration wurde entladen.")
        if self._emergency_active:
            raise UserError("Hauptschalter AUS läuft bereits.")
        # Stop decisions synchronously before waiting for the emergency lock.
        self._emergency_epoch += 1
        self._stop_epoch += 1
        self.mode = "stopped"
        self._startup_restore = False
        self._startup_grid_sequence = None
        self.resume_mode = "stopped"
        self.deficit_since = None
        self._efficiency_goals.clear()
        self.reason = "Hauptschalter AUS: Abschaltung aller konfigurierten Verbraucher l\u00e4uft."
        self.emergency_unresolved = True
        self._emergency_active = True
        self._changed()
        if self.pending is not None:
            self.pending.problem = "Hauptschalter AUS hat den laufenden Auftrag unterbrochen."
            self.pending.observed.set()
        async with self._emergency_lock:
            entities = [c.entity_id for c in self.config.consumers]
            issue = None
            confirmed = False
            try:
                # One HA service call for all configured consumers; wait for *each* OFF observation.
                async with asyncio.timeout(self.timeout):
                    if entities:
                        async with self._dispatch_lock:
                            await self.send_all_off(entities)
                        while any(self.states.get(entity_id) != "off" for entity_id in entities):
                            self._emergency_change.clear()
                            if all(self.states.get(entity_id) == "off" for entity_id in entities):
                                break
                            await self._emergency_change.wait()
                    confirmed = True
            except TimeoutError:
                issue = "HA hat das Ausschalten nicht innerhalb der Frist vollst\u00e4ndig best\u00e4tigt."
            except Exception:
                _LOGGER.exception("RRH main switch OFF service call failed")
                issue = "Der Ausschaltbefehl ist fehlgeschlagen oder wurde nicht vollst\u00e4ndig ausgef\u00fchrt."
            # Complete any interrupted ordinary allocation; it must not commit a cursor.
            if self._task is not None and self._task is not asyncio.current_task():
                try:
                    await asyncio.wait_for(asyncio.shield(self._task), timeout=self.timeout)
                except (Exception, asyncio.CancelledError):
                    issue = issue or "Ein vorheriger Auftrag ist noch nicht abgeschlossen."
                    confirmed = False
            if self._task is not None and not self._task.done():
                # Avoid waiting forever on _lock held by a stalled normal write.
                # Unresolved marker remains set; no success is reported.
                self.mode = "error"
                self.reason = "Hauptschalter AUS: Vorheriger Auftrag blockiert die Abschlusspr\u00fcfung. Zustand kontrollieren."
                self.last_action = "Hauptschalter AUS nicht vollst\u00e4ndig best\u00e4tigt."
                self._emergency_active = False
                self._changed()
                raise UserError(self.reason)
            missing = [c.name for c in self.config.consumers if self.states.get(c.entity_id) != "off"]
            confirmed = confirmed and not missing and issue is None
            async with self._lock:
                if confirmed:
                    self.owned.clear()
                    self.started_at.clear()
                    self.incomplete = None
                else:
                    # Keep the incomplete marker and ownership conservatively.
                    self.owned = [i for i in self.owned if any(c.id == i and self.states.get(c.entity_id) != "off" for c in self.config.consumers)]
                self.emergency_unresolved = not confirmed
                self._changed()
                try:
                    await self._persist()
                except Exception as err:
                    self.emergency_unresolved = True
                    self._fault("Hauptschalter AUS: Speicherfehler. Schaltzust\u00e4nde und HA-Protokoll kontrollieren.")
                    self._emergency_active = False
                    raise UserError(self.reason) from err
            self._emergency_active = False
            if not confirmed:
                self.mode = "error"
                details = "; ".join(missing) if missing else "nicht sicher abgeschlossen"
                self.reason = f"Hauptschalter AUS unvollst\u00e4ndig: {issue or details}. Nicht best\u00e4tigt: {details}."
                self.last_action = "Hauptschalter AUS: Nicht alle Verbraucher best\u00e4tigt. Keine automatische Wiederholung."
                raise UserError(self.reason)
            self.mode = "stopped"
            self._has_confirmed_all_off = True
            self.reason = "Hauptschalter AUS: Alle konfigurierten Verbraucher best\u00e4tigt ausgeschaltet. RRH gestoppt."
            self.last_action = "Hauptschalter AUS: Alle konfigurierten Verbraucher ausgeschaltet."

    def _consumer_wait_reason(self, c: Consumer, candidate: Consumer | None,
                              export: float | None, error: str | None) -> str:
        membership = self._profile_for(c)
        if not c.enabled:
            return "Teilnahme deaktiviert"
        if membership is None:
            return "Keinem Profil zugeordnet"
        if not membership.enabled:
            return "Profil manuell deaktiviert"
        check = self._condition_report("profile", membership)
        if not check["allowed"]:
            return f"Profilbedingung gesperrt: {check['reason']}"
        window = self._schedule_report(membership)
        if not window["allowed"]:
            return "Profilzeitplan gesperrt: " + window["reason"]
        check = self._condition_report("consumer", c)
        if not check["allowed"]:
            return f"Verbraucherbedingung gesperrt: {check['reason']}"
        window = self._schedule_report(c)
        if not window["allowed"]:
            return "Verbraucherzeitplan gesperrt: " + window["reason"]
        if self.states.get(c.entity_id) == "on":
            return ""
        if self.states.get(c.entity_id) != "off":
            return "Schalter nicht verfügbar"
        if self._cooldown_remaining(c) > 0:
            return "Wiedereinschaltsperre läuft"
        if candidate is not None and candidate.id != c.id:
            return "Wartet auf seinen Round-Robin-Turn"
        if error or export is None:
            return "Netzmessung nicht verfügbar"
        if export - self.config.reserve_w < c.watts:
            return "Wartet auf ausreichend Überschuss"
        return "Bereit für die Vergabe"

    def _deficit_remaining(self, c: Consumer, export: float | None) -> float | None:
        if self.mode != "running" or export is None or export >= self.config.reserve_w or self.deficit_since is None:
            return None
        if c.id not in self.owned or self.states.get(c.entity_id) != "on":
            return None
        return max(0.0, self._deficit_delay(c) - (self.clock() - self.deficit_since))

    def status(self) -> dict:
        value, error, age = self.power()
        choice = self._candidate_with_profile()
        candidate = choice[1] if choice else None
        now = self.wall_clock()
        profiles = []
        for profile in self.config.profiles:
            period_origin, period_start, period_end = (self.fairness.period(
                profile.strategy, profile.id, profile.runtime_window, now)
                if profile.strategy in FAIR_STRATEGIES else (None, None, None))
            profile_candidate = self._status_candidate(profile, value, error)
            # Display mode is separate from strategy. Allocation mode starts
            # with running members and a strategy-selected candidate.
            members = list(profile.consumer_ids)
            started = [i for i in self.owned if i in members and
                       any(c.id == i and self.states.get(c.entity_id) == "on" for c in self.config.consumers)]
            cursor = self.profile_cursors.get(profile.id)
            anchor = members.index(cursor) if cursor in members else -1
            cyclic = members[anchor + 1:] + members[:anchor + 1] if profile.strategy == "classic" else [c.id for c in self._ranked_members(profile)]
            if profile.strategy in ("fixed_priority", "power_asc", "power_desc"):
                display_ids = [c.id for c in self._ranked_members(profile)]
            else:
                display_ids = list(dict.fromkeys(started + ([profile_candidate.id] if profile_candidate else []) + cyclic))
            report = self._condition_report("profile", profile)
            window = self._schedule_report(profile)
            profiles.append({"id": profile.id, "name": profile.name,
                "enabled": profile.enabled, "conditions": profile.conditions.to_dict(),
                "conditions_allowed": report["allowed"],
                "conditions_reason": report["reason"], "condition_checks": report["checks"],
                "schedule": profile.schedule.to_dict(), "schedule_allowed": window["allowed"],
                "schedule_reason": window["reason"], "schedule_next_start": window["next_start"],
                "strategy": profile.strategy,
                "allow_power_skip": profile.allow_power_skip,
                "runtime_window": profile.runtime_window,
                "fair_period_origin": period_origin,
                "fair_period_start": period_start,
                "fair_period_end": period_end,
                "fair_values": {cid: round(self._fair_value(profile.strategy, profile, cid), 3)
                                for cid in profile.consumer_ids} if profile.strategy in FAIR_STRATEGIES else {},
                "fair_unit": "s" if profile.strategy == "fair_runtime" else "Wh" if profile.strategy == "fair_energy" else None,
                "fair_rotation_s": profile.fair_rotation_s,
                "fair_min_gap_s": profile.fair_min_gap_s,
                "fair_min_gap_wh": profile.fair_min_gap_wh,
                "efficiency_min_gain_w": profile.efficiency_min_gain_w,
                "efficiency_interval_s": profile.efficiency_interval_s,
                "efficiency_start_margin_w": profile.efficiency_start_margin_w,
                "consumer_ids": members, "dashboard_order": profile.dashboard_order,
                "next_id": profile_candidate.id if profile_candidate else None,
                "cursor": cursor, "display_ids": display_ids,
                "running_count": sum(1 for i in members if i in self.owned and any(c.id == i and self.states.get(c.entity_id) == "on" for c in self.config.consumers))})
        return {"api_version": API_VERSION, "version": VERSION, "mode": self.mode, "reason": self.reason,
                "config": self.config.to_dict(), "revision": self.revision,
                "power": {"raw": self.reading.raw, "unit": self.reading.unit, "export_w": value,
                          "available_w": None if error or value is None else max(0, value - self.config.reserve_w),
                          "total_usable_w": None if error or value is None else max(0, value - self.config.reserve_w + sum(self._load_w(c) for c in self.config.consumers if c.id in self.owned and self.states.get(c.entity_id) == "on")),
                          "age_s": None if age is None else round(age, 1), "error": error},
                "consumers": [{**c_dict, "state": self.states.get(c.entity_id, "unavailable"), "owned": c.id in self.owned,
                               "min_remaining_s": round(max(0, self.started_at.get(c.id, now) + c.min_on_s - now), 1) if c.id in self.owned and self.states.get(c.entity_id) == "on" and c.min_on_s and self.started_at.get(c.id, 0) > 0 else 0,
                               "cooldown_remaining_s": round(self._cooldown_remaining(c), 1),
                               "deficit_remaining_s": self._deficit_remaining(c, value),
                               "condition_checks": self._condition_report("consumer", c)["checks"],
                               "conditions_allowed": self._eligible("consumer", c),
                               "conditions_reason": self._condition_report("consumer", c)["reason"],
                               "schedule_allowed": self._schedule_report(c)["allowed"],
                               "schedule_reason": self._schedule_report(c)["reason"],
                               "schedule_next_start": self._schedule_report(c)["next_start"],
                               "wait_reason": self._consumer_wait_reason(c, candidate, value, error),
                               "active_watts": self._load_w(c) if self.states.get(c.entity_id) == "on" else 0}
                              for c, c_dict in zip(self.config.consumers, self.config.to_dict()["consumers"], strict=True)],
                "profiles": profiles, "next_id": candidate.id if candidate else None,
                "next_profile_id": choice[0].id if choice else None,
                "cursor": self.cursor, "profile_cursors": dict(self.profile_cursors),
                "pending": None if self.pending is None else {"id": self.pending.consumer.id, "target": self.pending.target, "sent": self.pending.sent},
                "incomplete": deepcopy(self.incomplete), "emergency_unresolved": self.emergency_unresolved,
                "emergency_active": self._emergency_active, "startup_pending": self._startup_restore,
                "last_action": self.last_action,
                "managed_w": sum(self._load_w(c) for c in self.config.consumers if c.id in self.owned and self.states.get(c.entity_id) == "on"),
                "residual_consumer_id": self.config.residual_consumer_id,
                "statistics":{**self.statistics.status(),"sensors":self.stat_sources}}

    async def close(self) -> None:
        self._changed()  # Persist partial accounting since the last 30-second checkpoint.
        self.pause(persist_intent=False)
        self.closed = True
        if self._task is not None and not self._task.done():
            # Already dispatched commands may still finish and be recorded, never retried.
            await asyncio.shield(self._task)
        async with self._lock:
            await self._persist()
