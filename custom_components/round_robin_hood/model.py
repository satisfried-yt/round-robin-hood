# rrh-origin:ca5844cf35dbbae0878c6a666eb4b28c
"""Validated configuration and pure surplus-allocation decision functions.

No Home Assistant dependency; this is also the code exercised by the unit tests.
Positive normalized grid power is export. Rated powers are estimates, not meters.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import base64
import binascii
import math
import re
from typing import Any


STRATEGIES = frozenset({"classic", "fair_runtime", "fair_energy", "fixed_priority", "maximum_efficiency",
                        "power_asc", "power_desc", "stable_operation"})
RUNTIME_WINDOWS = frozenset({"24h", "7d", "14d", "30d", "all"})


class UserError(ValueError):
    """A validation/operating error that can be displayed in the panel."""


def number(value: Any, label: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise UserError(f"{label}: Bitte eine Zahl eingeben.")
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise UserError(f"{label}: Erlaubt sind {minimum:g} bis {maximum:g}.")
    return float(value)


def entity(value: Any, domain: str, *, optional: bool = False) -> str:
    if value == "" and optional:
        return ""
    if not isinstance(value, str) or len(value) > 255 or not re.fullmatch(
        rf"{domain}\.[a-z0-9_]+", value
    ):
        raise UserError(f"Bitte eine g\u00fcltige {domain}-Entit\u00e4t ausw\u00e4hlen.")
    return value


def exact_keys(data: Any, keys: set[str], label: str) -> None:
    if not isinstance(data, dict) or set(data) != keys:
        raise UserError(f"{label}: Unvollst\u00e4ndige oder unbekannte Felder.")


@dataclass(frozen=True, slots=True)
class NumericCondition:
    """Numeric Home Assistant state comparison with optional release hysteresis."""

    id: str
    entity_id: str
    operator: str
    value: float
    hysteresis: float = 0.0

    @classmethod
    def parse(cls, data: Any) -> NumericCondition:
        if not isinstance(data, dict) or set(data) != {"id", "entity_id", "operator", "value", "hysteresis"}:
            raise UserError("Bedingung: Ungültige oder unvollständige Felder.")
        if not isinstance(data["id"], str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", data["id"]):
            raise UserError("Bedingung: Ungültige Kennung.")
        eid = data["entity_id"]
        if not isinstance(eid, str) or not re.fullmatch(r"(?:sensor|number|input_number)\.[a-z0-9_]+", eid):
            raise UserError("Bedingung: Bitte einen numerischen HA-Sensor auswählen.")
        if data["operator"] not in ("<", "<=", ">", ">=", "==", "!="):
            raise UserError("Bedingung: Ungültiger Vergleichsoperator.")
        threshold = number(data["value"], "Grenzwert", -1e9, 1e9)
        hyst = number(data["hysteresis"], "Hysterese", 0, 1e6)
        if data["operator"] in ("==", "!=") and hyst:
            raise UserError("Bei Gleichheit/Ungleichheit ist die Hysterese auf 0 zu setzen.")
        return cls(data["id"], eid, data["operator"], threshold, hyst)


@dataclass(frozen=True, slots=True)
class ConditionSet:
    enabled: bool = False
    logic: str = "all"
    rules: tuple[NumericCondition, ...] = ()

    @classmethod
    def parse(cls, data: Any) -> ConditionSet:
        if data is None:
            return cls()
        if not isinstance(data, dict) or set(data) != {"enabled", "logic", "rules"}:
            raise UserError("Bedingungen: Unvollständige oder unbekannte Felder.")
        if type(data["enabled"]) is not bool or data["logic"] not in ("all", "any"):
            raise UserError("Bedingungen: Ungültige Aktivierung oder Verknüpfung.")
        raw = data["rules"]
        if not isinstance(raw, list) or len(raw) > 12:
            raise UserError("Bedingungen: Maximal zwölf Regeln erlaubt.")
        rules = tuple(NumericCondition.parse(item) for item in raw)
        if len({rule.id for rule in rules}) != len(rules):
            raise UserError("Bedingungen: Kennungen müssen eindeutig sein.")
        if data["enabled"] and not rules:
            raise UserError("Aktivierte Bedingungen benötigen mindestens eine Regel.")
        return cls(data["enabled"], data["logic"], rules)

    def to_dict(self) -> dict:
        return {"enabled": self.enabled, "logic": self.logic,
                "rules": [asdict(rule) for rule in self.rules]}


@dataclass(frozen=True, slots=True)
class PowerStep:
    watts: float
    option: str

    @classmethod
    def parse(cls, raw: Any) -> PowerStep:
        exact_keys(raw, {"watts", "option"}, "Leistungsstufe")
        watts = number(raw["watts"], "Leistungsstufe", 1, 100000)
        option = raw["option"]
        if not isinstance(option, str) or not 1 <= len(option) <= 80 or option.strip() != option:
            raise UserError("Leistungsstufe: Option muss ein gültiger HA-Auswahlwert sein.")
        return cls(watts, option)


@dataclass(frozen=True, slots=True)
class Consumer:
    id: str
    name: str
    entity_id: str
    watts: float
    enabled: bool
    virtual_confirmed: bool
    min_on_s: int = 0
    min_on_strict: bool = False
    cooldown_s: int = 0
    cooldown_wait: bool = False
    shutdown_delay_s: float | None = None
    icon: str = "mdi:power-plug"
    icon_image: str | None = None
    conditions: ConditionSet = ConditionSet()
    power_mode: str = "fixed"
    power_steps: tuple[PowerStep, ...] = ()
    stage_entity_id: str = ""
    off_option: str = "off"
    max_watts: float = 0.0
    power_step_w: float = 10.0
    power_hysteresis_w: float = 100.0
    power_interval_s: int = 10

    @classmethod
    def parse(cls, data: Any) -> Consumer:
        base = {"id", "name", "entity_id", "watts", "enabled", "virtual_confirmed"}
        extras = {"min_on_s", "min_on_strict", "cooldown_s", "cooldown_wait", "shutdown_delay_s", "icon", "icon_image", "conditions", "power_mode", "power_steps", "stage_entity_id", "off_option", "max_watts", "power_step_w", "power_hysteresis_w", "power_interval_s"}
        if not isinstance(data, dict) or not base <= set(data) or not set(data) <= base | extras:
            raise UserError("Verbraucher: Unvollständige oder unbekannte Felder.")
        for key in ("min_on_strict", "cooldown_wait"):
            if type(data.get(key, False)) is not bool:
                raise UserError(f"{key}: Bitte eine gültige Auswahl treffen.")
        def seconds(key):
            value = data.get(key, 0)
            if type(value) is not int or not 0 <= value <= 86400:
                raise UserError(f"{key}: Erlaubt sind 0 bis 86400 Sekunden.")
            return value
        if not isinstance(data["id"], str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", data["id"]):
            raise UserError("Ung\u00fcltige Verbraucherkennung.")
        name = data["name"]
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
            raise UserError("Der Name muss 1 bis 80 Zeichen lang sein.")
        if type(data["enabled"]) is not bool or data["virtual_confirmed"] is not True:
            raise UserError("Nur ausdr\u00fccklich freigegebene HA-Steuerentit\u00e4ten sind erlaubt.")
        delay = data.get("shutdown_delay_s")
        if delay is not None:
            delay = number(delay, "Geräte-Abschaltverzögerung", 0, 600)
        icon = data.get("icon", "mdi:power-plug")
        if not isinstance(icon, str) or not re.fullmatch(r"mdi:[a-z0-9-]{1,70}", icon):
            raise UserError("Nur Home-Assistant-Symbole mit mdi: sind erlaubt.")
        icon_image = data.get("icon_image")
        if icon_image is not None:
            if not isinstance(icon_image, str) or len(icon_image) > 90000:
                raise UserError("Eigenes Symbol: Datei zu groß oder ungültig.")
            match = re.fullmatch(r"data:image/(png|webp);base64,([A-Za-z0-9+/]+={0,2})", icon_image)
            if not match:
                raise UserError("Eigenes Symbol: Nur PNG oder WebP erlaubt.")
            try:
                raw = base64.b64decode(match.group(2), validate=True)
            except (ValueError, binascii.Error) as err:
                raise UserError("Eigenes Symbol: Ungültige Bilddaten.") from err
            if len(raw) > 48 * 1024 or not (
                (match.group(1) == "png" and raw.startswith(b"\x89PNG\r\n\x1a\n")) or
                (match.group(1) == "webp" and raw.startswith(b"RIFF") and raw[8:12] == b"WEBP")
            ):
                raise UserError("Eigenes Symbol: maximal 48 KB, gültiges PNG oder WebP.")
        mode = data.get("power_mode", "fixed")
        if mode not in ("fixed", "staged", "variable"):
            raise UserError("Unbekannter Verbrauchertyp.")
        eid = data["entity_id"]
        if not isinstance(eid, str) or not re.fullmatch(r"(?:switch|select|climate|number)\.[a-z0-9_]+", eid):
            raise UserError("Ungültige Steuerentität.")
        domain = eid.split(".", 1)[0]
        if (mode == "fixed" and domain != "switch") or (mode == "variable" and domain != "number") or (mode == "staged" and domain not in ("switch", "select", "climate")):
            raise UserError("Der Verbrauchertyp passt nicht zur Steuerentität.")
        base_w = number(data["watts"], "Nenn-/Mindestleistung", 1, 100000)
        raw_steps = data.get("power_steps", [])
        if not isinstance(raw_steps, (list, tuple)):
            raise UserError("Leistungsstufen müssen eine Liste sein.")
        steps = tuple(PowerStep.parse(step) for step in raw_steps)
        stage_entity = data.get("stage_entity_id", "")
        off_option = data.get("off_option", "off")
        if not isinstance(off_option, str) or not 1 <= len(off_option) <= 80:
            raise UserError("AUS-Option ungültig.")
        max_watts = number(data.get("max_watts", 0), "Maximalleistung", 0, 100000)
        resolution = number(data.get("power_step_w", 10), "Regelauflösung", 1, 10000)
        hysteresis = number(data.get("power_hysteresis_w", 100), "Regelhysterese", 0, 10000)
        interval = data.get("power_interval_s", 10)
        if type(interval) is not int or not 5 <= interval <= 3600:
            raise UserError("Regelintervall: 5 bis 3600 Sekunden.")
        if mode == "fixed" and (steps or stage_entity):
            raise UserError("Ein/Aus-Verbraucher dürfen keine Leistungsstufen enthalten.")
        if mode == "staged":
            if len(steps) < 2 or len(steps) > 16 or any(steps[i].watts >= steps[i+1].watts for i in range(len(steps)-1)):
                raise UserError("Leistungsstufen: 2–16 aufsteigende Wattwerte erforderlich.")
            if len({step.option for step in steps}) != len(steps) or abs(steps[0].watts - base_w) > 0.001:
                raise UserError("Leistungsstufen: erste Stufe muss der Mindestleistung entsprechen; Optionen eindeutig.")
            stage_entity = stage_entity or (eid if domain in ("select", "climate") else "")
            if not re.fullmatch(r"(?:select|climate)\.[a-z0-9_]+", stage_entity):
                raise UserError("Leistungsstufen benötigen eine select- oder climate-Entität.")
            if stage_entity.startswith("select.") and eid == stage_entity and off_option in {x.option for x in steps}:
                raise UserError("AUS-Option darf nicht mit einer Leistungsstufe übereinstimmen.")
        if mode == "variable":
            if steps or stage_entity or max_watts <= base_w:
                raise UserError("Stufenlose Regelung benötigt eine Maximalleistung über der Mindestleistung.")
        return cls(data["id"], name.strip(), eid,
                   base_w, data["enabled"], True,
                   seconds("min_on_s"), data.get("min_on_strict", False),
                   seconds("cooldown_s"), data.get("cooldown_wait", False),
                   delay, icon, icon_image, ConditionSet.parse(data.get("conditions")),
                   mode, steps, stage_entity, off_option, max_watts, resolution, hysteresis, interval)


@dataclass(frozen=True, slots=True)
class Profile:
    id: str
    name: str
    enabled: bool
    strategy: str
    consumer_ids: tuple[str, ...]
    dashboard_order: str = "fixed"
    conditions: ConditionSet = ConditionSet()
    runtime_window: str = "7d"
    fair_rotation_s: int = 900
    efficiency_min_gain_w: float = 200.0
    efficiency_interval_s: int = 60
    allow_power_skip: bool = False
    efficiency_start_margin_w: float = 50.0
    fair_min_gap_s: float = 60.0
    fair_min_gap_wh: float = 10.0

    @classmethod
    def parse(cls, data: Any) -> Profile:
        if not isinstance(data, dict):
            raise UserError("Profil: Ungültige Daten.")
        base = {"id", "name", "enabled", "strategy", "consumer_ids", "dashboard_order"}
        optional = {"conditions", "runtime_window", "fair_rotation_s", "efficiency_min_gain_w", "efficiency_interval_s", "allow_power_skip", "efficiency_start_margin_w", "fair_min_gap_s", "fair_min_gap_wh"}
        if not base <= set(data) or not set(data) <= base | optional:
            raise UserError("Profil: Unvollständige oder unbekannte Felder.")
        if not isinstance(data["id"], str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", data["id"]):
            raise UserError("Ungültige Profilkennung.")
        if not isinstance(data["name"], str) or not 1 <= len(data["name"].strip()) <= 80:
            raise UserError("Profilname muss 1 bis 80 Zeichen lang sein.")
        if type(data["enabled"]) is not bool:
            raise UserError("Profilstatus muss aktiviert oder deaktiviert sein.")
        strategy = data["strategy"]
        if not isinstance(strategy, str) or strategy not in STRATEGIES:
            raise UserError("Profil: Unbekannte Verteilstrategie.")
        window = data.get("runtime_window", "7d")
        if not isinstance(window, str) or window not in RUNTIME_WINDOWS:
            raise UserError("Fair Runtime: Unbekannter Vergleichszeitraum.")
        rotation = data.get("fair_rotation_s", 900)
        interval = data.get("efficiency_interval_s", 60)
        if type(rotation) is not int or not 60 <= rotation <= 86400:
            raise UserError("Fair Runtime: Rotation muss zwischen 60 und 86400 Sekunden liegen.")
        if type(interval) is not int or not 10 <= interval <= 3600:
            raise UserError("Maximum Efficiency: Optimierungsintervall muss 10 bis 3600 Sekunden betragen.")
        gain = number(data.get("efficiency_min_gain_w", 200), "Mindestverbesserung", 0, 100000)
        # 0.3.0 power strategies already skipped unfittable loads. Preserve that
        # for migrated profiles; all newly created profiles explicitly choose.
        legacy_skip = strategy in ("power_asc", "power_desc")
        allow_skip = data.get("allow_power_skip", legacy_skip)
        if type(allow_skip) is not bool:
            raise UserError("Überholregel: Bitte Strikt oder Überspringen auswählen.")
        if allow_skip and strategy not in ("classic", "fair_runtime", "fair_energy", "fixed_priority", "power_asc", "power_desc"):
            raise UserError("Überholregel: Bei dieser Strategie nicht verfügbar.")
        margin = number(data.get("efficiency_start_margin_w", 50), "Start-Sicherheitsabstand", 0, 10000)
        fair_gap_s = number(data.get("fair_min_gap_s", 60), "Mindestvorsprung Laufzeit (s)", 1, 86400)
        fair_gap_wh = number(data.get("fair_min_gap_wh", 10), "Mindestvorsprung Energie (Wh)", 0.001, 100000)
        if data["dashboard_order"] not in ("fixed", "allocation"):
            raise UserError("Unbekannte Dashboard-Reihenfolge.")
        ids = data["consumer_ids"]
        if not isinstance(ids, list) or len(ids) > 100 or any(
            not isinstance(i, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", i) for i in ids
        ) or len(set(ids)) != len(ids):
            raise UserError("Profil-Verbraucher müssen eindeutig sein (maximal 100).")
        if strategy == "maximum_efficiency" and len(ids) > 24:
            raise UserError("Maximum Efficiency unterstützt maximal 24 Verbraucher pro Profil.")
        return cls(data["id"], data["name"].strip(), data["enabled"], strategy, tuple(ids),
                   data["dashboard_order"], ConditionSet.parse(data.get("conditions")), window,
                   rotation, gain, interval, allow_skip, margin, fair_gap_s, fair_gap_wh)


# Energy sources deliberately reuse HA Energy Dashboard compatible sensors and
# numerical helpers. PV capacity is informational; grid-meter decisions remain
# independent of energy tariffs and analytics.
CARD_KEYS = frozenset({"grid", "budget", "managed", "live_chart", "rate", "total_net", "total_energy", "capture", "pipeline", "pv_power"})
CHART_TYPES = frozenset({"gauge", "line", "bar", "area", "donut", "stacked", "sparkline"})
LANGUAGES = frozenset({"auto", "de", "en", "fr", "es", "pt", "it"})
CURRENCIES = frozenset({"EUR", "CHF", "USD", "GBP"})


@dataclass(frozen=True, slots=True)
class ValueSource:
    mode: str = "fixed"
    value: float | None = None
    entity_id: str = ""

    @classmethod
    def parse(cls, data: Any, *, label: str, maximum: float) -> ValueSource:
        if not isinstance(data, dict) or set(data) != {"mode", "value", "entity_id"}:
            raise UserError(f"{label}: Bitte Datenquelle vollständig angeben.")
        mode = data["mode"]
        if mode not in ("fixed", "entity"):
            raise UserError(f"{label}: Feste Zahl oder HA-Entität auswählen.")
        eid = data["entity_id"]
        if not isinstance(eid, str) or (eid and not re.fullmatch(r"(?:sensor|number|input_number)\.[a-z0-9_]+", eid)):
            raise UserError(f"{label}: Ungültige HA-Entität.")
        if mode == "entity" and not eid:
            raise UserError(f"{label}: Bitte eine HA-Entität angeben.")
        v = data["value"]
        if v is not None:
            v = number(v, label, 0, maximum)
        if mode == "fixed" and eid:
            raise UserError(f"{label}: Für eine feste Zahl darf keine Entität gesetzt sein.")
        return cls(mode, v, eid)


@dataclass(frozen=True, slots=True)
class EnergyOptions:
    pv_size: ValueSource = ValueSource()
    import_price: ValueSource = ValueSource()
    feed_in_price: ValueSource = ValueSource()
    pv_power_entity: str = ""
    pv_energy_entity: str = ""
    grid_export_energy_entity: str = ""
    currency: str = "EUR"

    @classmethod
    def parse(cls, data: Any) -> EnergyOptions:
        if data is None:
            return cls()
        if not isinstance(data, dict) or not {"pv_size", "import_price", "feed_in_price", "pv_power_entity", "pv_energy_entity", "grid_export_energy_entity"} <= set(data) or not set(data) <= {"pv_size", "import_price", "feed_in_price", "pv_power_entity", "pv_energy_entity", "grid_export_energy_entity", "currency"}:
            raise UserError("Energie und Kosten: Ungültige oder fehlende Angaben.")
        extras = []
        for key in ("pv_power_entity", "pv_energy_entity", "grid_export_energy_entity"):
            eid = data[key]
            if not isinstance(eid, str) or (eid and not re.fullmatch(r"sensor\.[a-z0-9_]+", eid)):
                raise UserError(f"Energiesensor {key}: Ungültige Sensorentität.")
            extras.append(eid)
        currency = data.get("currency", "EUR")
        if not isinstance(currency, str) or currency not in CURRENCIES:
            raise UserError("Energie und Kosten: Ungültige Währung.")
        return cls(ValueSource.parse(data["pv_size"], label="PV-Größe (kWp)", maximum=100000),
                   ValueSource.parse(data["import_price"],label="Strompreis (€/kWh)",maximum=1000),
                   ValueSource.parse(data["feed_in_price"],label="Einspeisevergütung (€/kWh)",maximum=1000), *extras, currency)


@dataclass(frozen=True, slots=True)
class DashboardOptions:
    visible: dict[str,bool] = field(default_factory=lambda:{key:True for key in CARD_KEYS})
    chart_type: str = "gauge"
    language: str = "auto"
    show_donation: bool = True

    def to_dict(self):
        return {"visible":dict(self.visible if self.visible is not None else {key:True for key in CARD_KEYS}),
                "chart_type":self.chart_type,"language":self.language,"show_donation":self.show_donation}

    @classmethod
    def parse(cls, data: Any) -> DashboardOptions:
        if data is None:
            return cls({key:True for key in CARD_KEYS})
        if not isinstance(data, dict) or not {"visible", "chart_type", "language"} <= set(data) or not set(data) <= {"visible", "chart_type", "language", "show_donation"}:
            raise UserError("Dashboard: Ungültige Einstellungen.")
        if type(data.get("show_donation", True)) is not bool:
            raise UserError("Dashboard: Spendenlink muss ein Ja/Nein-Wert sein.")
        visible=data["visible"]
        if not isinstance(visible, dict) or set(visible) != CARD_KEYS or any(type(v) is not bool for v in visible.values()):
            raise UserError("Dashboard: Karten müssen einzeln ein- oder ausgeschaltet werden.")
        if data["chart_type"] not in CHART_TYPES or data["language"] not in LANGUAGES:
            raise UserError("Dashboard: Ungültige Diagramm- oder Sprachauswahl.")
        return cls(dict(visible),data["chart_type"],data["language"],data.get("show_donation", True))


@dataclass(frozen=True, slots=True)
class Config:
    grid_entity: str = ""
    export_positive: bool = True
    reserve_w: float = 100.0
    shutdown_delay_s: float = 30.0
    global_shutdown_delay_enabled: bool = True
    confirm_timer_skip: bool = True
    confirm_profile_toggle: bool = True
    data_quality_visible: bool = True
    max_age_s: float = 60.0
    consumers: tuple[Consumer, ...] = ()
    profiles: tuple[Profile, ...] = ()
    residual_consumer_id: str = ""
    energy: EnergyOptions = EnergyOptions()
    dashboard: DashboardOptions = DashboardOptions()
    notice_dismissed: bool = False
    setup_complete: bool = False
    startup_mode: str = "off"  # off | on | last; old configurations migrate safely to off

    def to_dict(self) -> dict:
        result = asdict(self)
        result["consumers"] = [{**asdict(c), "conditions": c.conditions.to_dict(), "power_steps": [asdict(step) for step in c.power_steps]} for c in self.consumers]
        result["profiles"] = [{**asdict(p), "consumer_ids": list(p.consumer_ids), "conditions": p.conditions.to_dict()} for p in self.profiles]
        result["dashboard"] = self.dashboard.to_dict()
        return result

    @classmethod
    def parse(cls, data: Any) -> Config:
        if not isinstance(data, dict):
            raise UserError("Einstellungen: Ungültige Daten.")
        legacy = "profiles" not in data
        allowed = {"grid_entity", "export_positive", "reserve_w", "shutdown_delay_s", "max_age_s", "consumers"} | (set() if legacy else {"profiles"})
        if not isinstance(data, dict) or not allowed <= set(data) or not set(data) <= allowed | {"global_shutdown_delay_enabled", "confirm_timer_skip", "confirm_profile_toggle", "data_quality_visible", "residual_consumer_id", "energy", "dashboard", "notice_dismissed", "setup_complete", "startup_mode"}:
            raise UserError("Einstellungen: Unvollständige oder unbekannte Felder.")
        if type(data.get("global_shutdown_delay_enabled", True)) is not bool:
            raise UserError("Globale Unterlastverzögerung: Bitte eine gültige Auswahl treffen.")
        for key in ("confirm_timer_skip", "confirm_profile_toggle", "data_quality_visible"):
            if type(data.get(key, True)) is not bool:
                raise UserError(f"{key}: Bitte eine gültige Auswahl treffen.")
        for key in ("notice_dismissed", "setup_complete"):
            if type(data.get(key, False)) is not bool:
                raise UserError(f"{key}: Ungültige Einstellung.")
        if data.get("startup_mode", "off") not in ("off", "on", "last") or not isinstance(data.get("startup_mode", "off"), str):
            raise UserError("Startverhalten: Bitte AUS, EIN oder letzten Zustand auswählen.")
        if type(data["export_positive"]) is not bool:
            raise UserError("Die Vorzeichenrichtung fehlt.")
        if not isinstance(data["consumers"], list) or len(data["consumers"]) > 100:
            raise UserError("Erlaubt sind bis zu 100 Verbraucher.")
        consumers = tuple(Consumer.parse(c) for c in data["consumers"])
        if len({c.id for c in consumers}) != len(consumers):
            raise UserError("Verbraucherkennungen m\u00fcssen eindeutig sein.")
        if len({c.entity_id for c in consumers}) != len(consumers):
            raise UserError("Eine HA-Steuerentität darf nur einem Verbraucher zugeordnet sein.")
        # One HA actuator must never be shared across RRH consumers. A separate
        # stage select/climate endpoint cannot simultaneously belong to another
        # consumer's primary control or another stage controller.
        primary = {c.entity_id for c in consumers}
        stages = [c.stage_entity_id for c in consumers if c.power_mode == "staged" and c.stage_entity_id != c.entity_id]
        if len(stages) != len(set(stages)) or set(stages) & primary:
            raise UserError("Stufensteuerung: dieselbe HA-Entität ist mehreren Verbrauchern zugeordnet.")
        # Transparent 0.1.6 migration: retain all existing consumers and order.
        # An explicitly supplied value must be a list (not None/dict/etc.).
        if not legacy and not isinstance(data["profiles"], list):
            raise UserError("Profile müssen als Liste angegeben werden.")
        if legacy or not data["profiles"]:
            # A non-empty integration always has a safe default allocation
            # group unless explicit profile assignments have been supplied.
            profiles = (Profile("standard", "Standard", True, "classic", tuple(c.id for c in consumers)),) if consumers else ()
        else:
            if not isinstance(data["profiles"], list) or len(data["profiles"]) > 30:
                raise UserError("Erlaubt sind maximal 30 Profile.")
            profiles = tuple(Profile.parse(p) for p in data["profiles"])
        if len({p.id for p in profiles}) != len(profiles):
            raise UserError("Profilkennungen müssen eindeutig sein.")
        if len({p.name.casefold() for p in profiles}) != len(profiles):
            raise UserError("Profilnamen müssen eindeutig sein.")
        members = [cid for p in profiles for cid in p.consumer_ids]
        consumer_ids = {c.id for c in consumers}
        if any(cid not in consumer_ids for cid in members):
            raise UserError("Ein Profil enthält einen nicht vorhandenen Verbraucher.")
        if len(set(members)) != len(members):
            raise UserError("Ein Verbraucher darf ausschließlich einem Profil zugeordnet sein.")
        residual = data.get("residual_consumer_id", "")
        if not isinstance(residual, str) or (residual and residual not in consumer_ids):
            raise UserError("Restüberschussverbraucher nicht gefunden.")
        if residual and next(c for c in consumers if c.id == residual).power_mode == "fixed":
            raise UserError("Restüberschussverbraucher muss mehrstufig oder stufenlos regelbar sein.")
        return cls(entity(data["grid_entity"], "sensor", optional=True), data["export_positive"],
                   number(data["reserve_w"], "Reserve", 0, 100000),
                   number(data["shutdown_delay_s"], "Abschaltverzögerung", 0, 600),
                   data.get("global_shutdown_delay_enabled", True),
                   data.get("confirm_timer_skip", True), data.get("confirm_profile_toggle", True),
                   data.get("data_quality_visible", True), number(data["max_age_s"], "Maximales Meldungsalter", 5, 3600), consumers, profiles, residual, EnergyOptions.parse(data.get("energy")), DashboardOptions.parse(data.get("dashboard")),
                   data.get("notice_dismissed", False), data.get("setup_complete", False), data.get("startup_mode", "off"))


def grid_watts(raw: Any, unit: str | None, export_positive: bool) -> float:
    """Never coerce missing/non-finite data or energy units into zero power."""
    if unit not in ("W", "kW"):
        raise UserError("Die Netzquelle muss eine Leistung in W oder kW liefern.")
    if isinstance(raw, bool):
        raise UserError("Die Netzquelle liefert keine g\u00fcltige Zahl.")
    try:
        value = float(raw)
    except (ValueError, TypeError, OverflowError) as err:
        raise UserError("Die Netzquelle liefert keinen nutzbaren Messwert.") from err
    value *= 1000 if unit == "kW" else 1
    if not math.isfinite(value):
        raise UserError("Die Netzquelle liefert keine endliche Zahl.")
    return value if export_positive else -value


def next_consumer(config: Config, cursor: str | None, states: dict[str, str]) -> Consumer | None:
    """Choose BEFORE checking power. Lack of power must never allow overtaking.

    A removed cursor is kept as historical fact; search then starts at list start.
    Disabled, on, missing and unavailable consumers are not eligible for a start.
    """
    items = config.consumers
    if not items:
        return None
    index = next((i for i, c in enumerate(items) if c.id == cursor), -1)
    for offset in range(1, len(items) + 1):
        c = items[(index + offset) % len(items)]
        if c.enabled and c.virtual_confirmed and states.get(c.entity_id) == "off":
            return c
    return None
