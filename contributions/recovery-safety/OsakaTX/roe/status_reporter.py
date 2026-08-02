"""
Structured status and error reporter for the recovery-safety module.

Implements the extended status schema defined in DESIGN.md §6, with
Home-Assistant-friendly JSON output. Complements xbattlax's RecoveryStatus
by adding extended telemetry fields, HA MQTT discovery config generation,
and status aggregation for multi-module reporting.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class StatusLevel(str, Enum):
    """Categorization of status severity."""

    OK = "ok"                       # Normal operation
    WARNING = "warning"             # Recoverable issue
    ERROR = "error"                 # Non-recoverable, needs human attention
    CRITICAL = "critical"           # E-stop or hardware fault


class StatusSource(str, Enum):
    """Which module produced the status."""

    RECOVERY = "oomwoo_recovery_safety"
    REACTIVE_LAYER = "oomwoo_reactive_layer"
    SAFETY_HANDLER = "oomwoo_safety_handler"
    INTEGRATION = "oomwoo_recovery_integration"


@dataclass
class StatusReporterConfig:
    """
    Configuration for the StatusReporter.

    Attributes:
        source: Module identifier published in every status payload.
        include_extended_fields: If True, include the _ext block.
        include_timestamps: If True, include robot_time and publish_time.
        ha_discovery_prefix: MQTT topic prefix for Home Assistant discovery.
            Set to None to disable HA discovery output.
        max_history: Number of status entries to retain in the rollup.
    """

    source: str = "oomwoo_recovery_safety"
    include_extended_fields: bool = True
    include_timestamps: bool = True
    ha_discovery_prefix: Optional[str] = "homeassistant"
    max_history: int = 100


@dataclass
class ExtendedStatusFields:
    """
    Extended telemetry fields for detailed status reporting.

    These supplement the base RecoveryStatus fields (state, reason_code,
    message, recoverable, source, situation, behavior, step_index, ladder_length).

    Serialized as a JSON object under the '_ext' key.
    """

    attempt_count: int = 0
    rapid_recurrences: int = 0
    elapsed_since_trigger: float = 0.0
    on_panic_ladder: bool = False
    odometry_during_recovery_m: float = 0.0
    additional_events: List[str] = field(default_factory=list)


@dataclass
class RecoveryBaseStatus:
    """
    Base status fields matching xbattlax's RecoveryStatus.
    """

    state: str
    reason_code: str
    message: str
    recoverable: bool
    source: str
    situation: Optional[str] = None
    behavior: Optional[str] = None
    step_index: Optional[int] = None
    ladder_length: Optional[int] = None


@dataclass
class FullStatus:
    """
    Complete status payload with base + extended fields + metadata.

    This is the top-level status object that gets serialized to JSON
    and published on /oomwoo/status.
    """

    base: RecoveryBaseStatus
    extended: Optional[ExtendedStatusFields] = None
    robot_time: Optional[float] = None
    publish_time: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to the wire format dict (suitable for JSON dump)."""
        d = asdict(self.base)
        if self.extended is not None:
            d["_ext"] = asdict(self.extended)
        if self.robot_time is not None:
            d["robot_time_s"] = self.robot_time
        if self.publish_time is not None:
            d["publish_time_s"] = self.publish_time
        return d

    def to_json(self) -> str:
        """Serialize to JSON string for /oomwoo/status publishing."""
        return json.dumps(self.to_dict(), sort_keys=True)

    def to_ha_payload(self) -> Dict[str, Any]:
        """
        Produce a Home Assistant MQTT sensor JSON attributes payload.

        This flattenes the structure for HA's value_template and
        json_attributes_template.
        """
        return self.to_dict()


def compute_level(status: FullStatus) -> StatusLevel:
    """
    Derive a status severity level from a FullStatus.

    Maps reason codes to severity:
    - E_STOP, E_STOP_LOCKED, SAFETY_CLIFF, SAFETY_WHEEL_DROP,
      RECOVERY_EXHAUSTED, RAPID_RECURRENCE → ERROR or CRITICAL
    - RECOVERY_ESCALATED, RECOVERY_STARTED, NO_RECOVERY_LADDER → WARNING
    - RECOVERED, READY, SAFETY_CLEAR, RECOVERY_ALREADY_ACTIVE → OK
    """
    reason = status.base.reason_code
    if reason.startswith("E_STOP"):
        return StatusLevel.CRITICAL
    if reason in ("SAFETY_CLIFF", "SAFETY_WHEEL_DROP", "SAFETY_PICKUP",
                   "RECOVERY_EXHAUSTED", "RAPID_RECURRENCE",
                   "UNKNOWN_SITUATION"):
        return StatusLevel.ERROR
    if reason in ("RECOVERY_ESCALATED", "RECOVERY_STARTED",
                   "NO_RECOVERY_LADDER", "RECOVERY_PAUSED",
                   "PENDING_CLEAR"):
        return StatusLevel.WARNING
    return StatusLevel.OK


# --- Home Assistant Discovery ---

_HATextSensor = {
    "name": None,
    "state_topic": "oomwoo/status",
    "value_template": None,
    "json_attributes_topic": "oomwoo/status",
    "json_attributes_template": "{{ value_json | tojson }}",
    "unique_id": None,
    "device": {
        "identifiers": ["oomwoo_robot"],
        "name": "OOMWOO Robot Vacuum",
        "manufacturer": "Maker's Pet",
        "model": "oomwoo-one",
    },
}


def generate_ha_discovery_configs(
    prefix: str = "homeassistant",
    status_topic: str = "oomwoo/status",
) -> List[Dict[str, Any]]:
    """
    Generate Home Assistant MQTT discovery configuration messages.

    Returns a list of dicts, each suitable for publishing to
    ``{prefix}/sensor/oomwoo_{name}/config``.

    Three sensors are defined:
    - ``oomwoo_recovery_state`` — the robot's current state string
    - ``oomwoo_recovery_reason`` — the reason_code string
    - ``oomwoo_recovery_level`` — the severity level (ok/warning/error/critical)
    """
    configs = []

    # 1. State sensor
    state_config = dict(_HATextSensor)
    state_config["name"] = "OOMWOO Recovery State"
    state_config["value_template"] = "{{ value_json.state }}"
    state_config["unique_id"] = "oomwoo_recovery_state"
    configs.append({
        "topic": f"{prefix}/sensor/oomwoo_recovery_state/config",
        "payload": state_config,
    })

    # 2. Reason code sensor
    reason_config = dict(_HATextSensor)
    reason_config["name"] = "OOMWOO Recovery Reason"
    reason_config["value_template"] = "{{ value_json.reason_code }}"
    reason_config["unique_id"] = "oomwoo_recovery_reason"
    configs.append({
        "topic": f"{prefix}/sensor/oomwoo_recovery_reason/config",
        "payload": reason_config,
    })

    # 3. Level sensor (severity aggregation)
    level_config = dict(_HATextSensor)
    level_config["name"] = "OOMWOO Recovery Level"
    level_config["value_template"] = "{{ value_json._ext.level }}"
    level_config["unique_id"] = "oomwoo_recovery_level"
    configs.append({
        "topic": f"{prefix}/sensor/oomwoo_recovery_level/config",
        "payload": level_config,
    })

    return configs


def generate_ha_automation_suggestions() -> Dict[str, str]:
    """
    Return Home Assistant automation YAML snippets for common alert scenarios.

    Each key is an alert scenario name; each value is the YAML/configuration
    snippet that a user can paste into Home Assistant.
    """
    return {
        "notify_on_critical": """
automation:
  - alias: "OOMWOO Critical Error Alert"
    trigger:
      - platform: mqtt
        topic: "oomwoo/status"
    condition:
      - condition: template
        value_template: "{{ 'critical' in value_json.get('_ext', {}).get('level', '') }}"
    action:
      - service: notify.mobile_app_phone
        data:
          title: "🚨 OOMWOO Critical Error"
          message: "{{ value_json.reason_code }}: {{ value_json.message }}"
""".strip(),
        "notify_on_exhausted": """
automation:
  - alias: "OOMWOO Recovery Exhausted"
    trigger:
      - platform: mqtt
        topic: "oomwoo/status"
        value_template: "{{ value_json.reason_code }}"
    condition:
      - condition: template
        value_template: "{{ value_json.reason_code == 'RECOVERY_EXHAUSTED' }}"
    action:
      - service: notify.mobile_app_phone
        data:
          title: "🧹 OOMWOO Stuck"
          message: "{{ value_json.message }}"
""".strip(),
        "notify_on_recovered": """
automation:
  - alias: "OOMWOO Recovered"
    trigger:
      - platform: mqtt
        topic: "oomwoo/status"
    condition:
      - condition: template
        value_template: "{{ value_json.reason_code == 'RECOVERED' }}"
    action:
      - service: notify.mobile_app_phone
        data:
          title: "✅ OOMWOO Recovered"
          message: "Robot freed itself and is resuming cleaning"
""".strip(),
    }


# --- History / Rollup ---


class StatusHistory:
    """
    Rolling history of status entries for diagnostic rollup.

    Maintains a bounded list of FullStatus entries in chronological order.
    Provides summary statistics for status reporting.
    """

    def __init__(self, max_entries: int = 100):
        self._max = max_entries
        self._entries: List[FullStatus] = []

    @property
    def entries(self) -> List[FullStatus]:
        return list(self._entries)

    def push(self, status: FullStatus) -> None:
        self._entries.append(status)
        if len(self._entries) > self._max:
            self._entries = self._entries[-self._max:]

    def last(self) -> Optional[FullStatus]:
        return self._entries[-1] if self._entries else None

    def summary(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Return the last `count` entries as dicts (for diagnostics).
        """
        return [s.to_dict() for s in self._entries[-count:]]

    def count_by_reason(self, reason_code: str) -> int:
        """Count how many entries have a specific reason_code."""
        return sum(1 for e in self._entries if e.base.reason_code == reason_code)

    def recent_errors(self, window_sec: float = 300.0) -> List[FullStatus]:
        """Return status entries within the last window_sec that are ERROR or CRITICAL."""
        now = time.time()
        result = []
        for entry in reversed(self._entries):
            ts = entry.robot_time or entry.publish_time or 0
            if now - ts > window_sec:
                break
            level = compute_level(entry)
            if level in (StatusLevel.ERROR, StatusLevel.CRITICAL):
                result.append(entry)
        return result

    def clear(self) -> None:
        self._entries.clear()


# --- Convenience builders ---


def make_status(
    state: str,
    reason_code: str,
    message: str,
    recoverable: bool,
    *,
    source: str = "oomwoo_recovery_safety",
    situation: Optional[str] = None,
    behavior: Optional[str] = None,
    step_index: Optional[int] = None,
    ladder_length: Optional[int] = None,
    extended: Optional[ExtendedStatusFields] = None,
    robot_time: Optional[float] = None,
) -> FullStatus:
    """Build a FullStatus from positional args (like xbattlax's RecoveryStatus)."""
    base = RecoveryBaseStatus(
        state=state,
        reason_code=reason_code,
        message=message,
        recoverable=recoverable,
        source=source,
        situation=situation,
        behavior=behavior,
        step_index=step_index,
        ladder_length=ladder_length,
    )
    return FullStatus(
        base=base,
        extended=extended,
        robot_time=robot_time,
        publish_time=time.time(),
    )


def make_extended(
    attempt_count: int = 0,
    rapid_recurrences: int = 0,
    elapsed_since_trigger: float = 0.0,
    on_panic_ladder: bool = False,
    odometry_during_recovery_m: float = 0.0,
    additional_events: Optional[List[str]] = None,
) -> ExtendedStatusFields:
    """Build ExtendedStatusFields with defaults."""
    return ExtendedStatusFields(
        attempt_count=attempt_count,
        rapid_recurrences=rapid_recurrences,
        elapsed_since_trigger=elapsed_since_trigger,
        on_panic_ladder=on_panic_ladder,
        odometry_during_recovery_m=odometry_during_recovery_m,
        additional_events=additional_events or [],
    )
