"""Host-side reference oracle for the CPU->MCU command gate.

The STM32 I/O board fail-closes on every CPU->MCU command: it rejects the wrong
wire version, unknown message IDs, MCU->CPU messages sent as commands, wrong
payload lengths, and out-of-range field values. That gate lives in firmware
(``oomwoo_cpu_ingress_validate_frame`` in makerspet/oomwoo-firmware).

This module restates the *same decision rules* in host Python so they become an
executable spec. It is a reference oracle, not the safety gate itself, and it
operates on an already-decoded frame (message_type, version, payload). It does
NOT cover wire framing or CRC -- that is the StreamDecoder's job.

Design notes:
- The message structure (id, direction, struct_format) is restated here from the
  contract manifest ``protocol_v1.json`` (wire version 1). It is deliberately
  self-contained: it does not import any other contributor's codec at runtime.
  A drift check against the committed manifest lives in the tests.
- Semantic limits mirror the firmware's ``oomwoo_message_validate``.
- Gate precedence matches the firmware exactly:
  version -> known type -> direction -> payload length -> field values.
"""

import struct
from enum import IntEnum


WIRE_VERSION = 1

# Frozen semantic limits (mirror include/oomwoo_messages.h in the firmware).
MAX_LINEAR_MM_S = 500
MAX_ANGULAR_MRAD_S = 4000
MAX_SETPOINT_DURATION_MS = 250
MAX_PERCENT = 100
CPU_MODE_DISARMED = 0
CPU_MODE_STACK_HEALTHY = 1


class GateResult(IntEnum):
    """Mirrors the applicable ``oomwoo_cpu_ingress_result_t`` reason codes.

    NULL_ARGUMENT and CODEC_ERROR describe C-API/internal failures and do not
    apply to this decoded-frame API. PAYLOAD_UNDEFINED is unreachable for the
    two open MCU->CPU payloads because the direction check rejects them first.
    """

    OK = 0
    BAD_VERSION = 1
    UNKNOWN_TYPE = 2
    WRONG_DIRECTION = 3
    WRONG_PAYLOAD_LENGTH = 4
    VALUE_OUT_OF_RANGE = 5


# name -> (id, direction, struct_format)
#   direction: "cpu_to_mcu" | "mcu_to_cpu" | "both"
#   struct_format: little-endian layout, or None for open/undefined payloads
_MESSAGES = {
    "HEARTBEAT": (0x0001, "cpu_to_mcu", "<IB"),
    "ESTOP_SET": (0x0002, "cpu_to_mcu", "<BH"),
    "CLEAR_LATCHED_FAULT": (0x0003, "cpu_to_mcu", "<H"),
    "IDENTIFY_REQUEST": (0x0004, "cpu_to_mcu", ""),
    "DRIVE_SETPOINT": (0x0101, "cpu_to_mcu", "<hhH"),
    "CLEANING_MOTORS_SET": (0x0102, "cpu_to_mcu", "<BBBB"),
    "LIDAR_MOTOR_SET": (0x0103, "cpu_to_mcu", "<B"),
    "LED_SET": (0x0104, "cpu_to_mcu", "<BBB"),
    "ACK": (0x7001, "both", "<HH"),
    "NACK": (0x7002, "both", "<HH"),
    "MCU_HELLO": (0x8000, "mcu_to_cpu", None),
    "FAST_TELEMETRY": (0x8001, "mcu_to_cpu", None),
    "SAFETY_EVENT": (0x8002, "mcu_to_cpu", None),
    "POWER_TELEMETRY": (0x8003, "mcu_to_cpu", None),
    "MCU_DIAGNOSTIC": (0x8004, "mcu_to_cpu", None),
    "SAFETY_STATE": (0x8005, "mcu_to_cpu", None),
}

_BY_ID = {mid: (name, direction, fmt) for name, (mid, direction, fmt) in _MESSAGES.items()}


def message_name(message_type):
    """Return the contract name for an id, or None if unknown."""
    entry = _BY_ID.get(message_type)
    return entry[0] if entry else None


def expected_length(struct_format):
    """Payload length implied by a struct format ("" -> 0)."""
    return struct.calcsize(struct_format) if struct_format else 0


def _reject(reason, detail):
    return reason, detail


def _validate_values(name, fmt, payload):
    """Apply the frozen field-value rules. Returns (GateResult, detail)."""
    fields = struct.unpack(fmt, payload) if fmt else ()

    if name == "HEARTBEAT":
        _cpu_time_ms, cpu_mode = fields
        if cpu_mode not in (CPU_MODE_DISARMED, CPU_MODE_STACK_HEALTHY):
            return _reject(GateResult.VALUE_OUT_OF_RANGE, f"cpu_mode={cpu_mode} not in {{0,1}}")
    elif name == "ESTOP_SET":
        active, _reserved = fields
        if active > 1:
            return _reject(GateResult.VALUE_OUT_OF_RANGE, f"active={active} > 1")
    elif name == "DRIVE_SETPOINT":
        linear, angular, duration = fields
        if not (-MAX_LINEAR_MM_S <= linear <= MAX_LINEAR_MM_S):
            return _reject(GateResult.VALUE_OUT_OF_RANGE, f"linear_mm_s={linear} out of +/-{MAX_LINEAR_MM_S}")
        if not (-MAX_ANGULAR_MRAD_S <= angular <= MAX_ANGULAR_MRAD_S):
            return _reject(GateResult.VALUE_OUT_OF_RANGE, f"angular_mrad_s={angular} out of +/-{MAX_ANGULAR_MRAD_S}")
        if not (1 <= duration <= MAX_SETPOINT_DURATION_MS):
            return _reject(GateResult.VALUE_OUT_OF_RANGE, f"duration_ms={duration} not in [1,{MAX_SETPOINT_DURATION_MS}]")
    elif name == "CLEANING_MOTORS_SET":
        for label, value in zip(("main_brush", "side_brush", "fan", "pump"), fields):
            if value > MAX_PERCENT:
                return _reject(GateResult.VALUE_OUT_OF_RANGE, f"{label}={value} > {MAX_PERCENT}")
    elif name == "LIDAR_MOTOR_SET":
        (pct,) = fields
        if pct > MAX_PERCENT:
            return _reject(GateResult.VALUE_OUT_OF_RANGE, f"pwm_pct={pct} > {MAX_PERCENT}")
    elif name == "LED_SET":
        _led_id, _mode, brightness = fields  # led id and mode are NOT range-checked
        if brightness > MAX_PERCENT:
            return _reject(GateResult.VALUE_OUT_OF_RANGE, f"brightness_pct={brightness} > {MAX_PERCENT}")
    # CLEAR_LATCHED_FAULT, IDENTIFY_REQUEST, ACK, NACK: no field-value rules.
    return GateResult.OK, "accepted"


def validate_command(message_type, version, payload):
    """Decide how the MCU command gate would treat this decoded frame.

    Args:
        message_type: 16-bit message id.
        version: wire version byte.
        payload: decoded payload bytes (no magic/header/CRC).

    Returns:
        (GateResult, detail_str). GateResult.OK means the gate accepts it.

    Raises:
        TypeError: if payload is not bytes-like.
    """
    if not isinstance(payload, (bytes, bytearray, memoryview)):
        raise TypeError(f"payload must be bytes-like, got {type(payload).__name__}")
    if version != WIRE_VERSION:
        return _reject(GateResult.BAD_VERSION, f"version={version} != {WIRE_VERSION}")

    entry = _BY_ID.get(message_type)
    if entry is None:
        return _reject(GateResult.UNKNOWN_TYPE, f"unknown message_type={message_type:#06x}")
    name, direction, fmt = entry

    if direction not in ("cpu_to_mcu", "both"):
        return _reject(GateResult.WRONG_DIRECTION, f"{name} is {direction}, not a command")

    exp = expected_length(fmt)
    if len(payload) != exp:
        return _reject(
            GateResult.WRONG_PAYLOAD_LENGTH,
            f"{name} expects {exp} payload bytes, got {len(payload)}",
        )

    return _validate_values(name, fmt, payload)
