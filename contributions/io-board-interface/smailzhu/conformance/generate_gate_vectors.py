#!/usr/bin/env python3
"""Generate / check the command-gate accept/reject vector corpus.

Each vector's EXPECTED outcome (``expect`` + ``reason``) is authored here by
hand from the firmware's gate rules -- it is NOT computed by
``oomwoo_command_gate.validate_command``. That independence is deliberate: the
test then checks the oracle against outcomes it did not produce, so an oracle
bug cannot hide by also corrupting the fixtures.

Payload bytes are derived from a ``pack`` (struct_format, values) or a literal
``raw`` hex string, so illegal values that the normal encoders refuse to build
are still representable.

Usage:
    generate_gate_vectors.py           # (re)write command_gate_vectors_v1.json
    generate_gate_vectors.py --check   # fail if the committed JSON is stale
"""

import argparse
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
OUTPUT = HERE / "command_gate_vectors_v1.json"

# Contract revision these vectors target.
TARGETS_CONTRACT = {
    "wire_version": 1,
    "contract_manifest": "contributions/io-board-interface/xbattlax/conformance/protocol_v1.json",
}

# Message ids (contract wire v1).
HEARTBEAT, ESTOP_SET, CLEAR_LATCHED_FAULT, IDENTIFY_REQUEST = 0x0001, 0x0002, 0x0003, 0x0004
DRIVE_SETPOINT, CLEANING_MOTORS_SET, LIDAR_MOTOR_SET, LED_SET = 0x0101, 0x0102, 0x0103, 0x0104
ACK, NACK = 0x7001, 0x7002
MCU_HELLO, FAST_TELEMETRY, SAFETY_EVENT = 0x8000, 0x8001, 0x8002
POWER_TELEMETRY, MCU_DIAGNOSTIC, SAFETY_STATE = 0x8003, 0x8004, 0x8005


def P(fmt, *values):
    return {"pack": [fmt, list(values)]}


def R(hexstr):
    return {"raw": hexstr}


# (name, message_type, version, payload_spec, expect, reason)
_SPECS = [
    # --- one accepted vector per command + ACK/NACK ---
    ("heartbeat_ok", HEARTBEAT, 1, P("<IB", 123456, 1), "OK", "OK"),
    ("estop_set_ok", ESTOP_SET, 1, P("<BH", 1, 0), "OK", "OK"),
    ("clear_latched_fault_ok", CLEAR_LATCHED_FAULT, 1, P("<H", 0x00FF), "OK", "OK"),
    ("identify_request_ok", IDENTIFY_REQUEST, 1, R(""), "OK", "OK"),
    ("drive_setpoint_ok", DRIVE_SETPOINT, 1, P("<hhH", -120, 500, 100), "OK", "OK"),
    ("cleaning_motors_ok", CLEANING_MOTORS_SET, 1, P("<BBBB", 50, 60, 70, 0), "OK", "OK"),
    ("lidar_motor_ok", LIDAR_MOTOR_SET, 1, P("<B", 80), "OK", "OK"),
    ("led_set_ok", LED_SET, 1, P("<BBB", 2, 3, 100), "OK", "OK"),
    ("ack_ok", ACK, 1, P("<HH", 0x0101, 0), "OK", "OK"),
    ("nack_ok", NACK, 1, P("<HH", 0x0101, 5), "OK", "OK"),

    # --- bad version (beats everything after it) ---
    ("bad_version_heartbeat", HEARTBEAT, 2, P("<IB", 0, 1), "REJECT", "BAD_VERSION"),
    ("bad_version_beats_unknown_type", 0x0999, 2, R(""), "REJECT", "BAD_VERSION"),
    ("bad_version_beats_value", DRIVE_SETPOINT, 0, P("<hhH", 9999, 0, 100), "REJECT", "BAD_VERSION"),
    ("bad_version_beats_length", HEARTBEAT, 2, R("01"), "REJECT", "BAD_VERSION"),

    # --- unknown type ---
    ("unknown_type", 0x0999, 1, R(""), "REJECT", "UNKNOWN_TYPE"),

    # --- wrong direction: MCU->CPU ids sent as commands ---
    ("wrong_dir_mcu_hello", MCU_HELLO, 1, R(""), "REJECT", "WRONG_DIRECTION"),
    ("wrong_dir_fast_telemetry", FAST_TELEMETRY, 1, R(""), "REJECT", "WRONG_DIRECTION"),
    ("wrong_dir_safety_event", SAFETY_EVENT, 1, R(""), "REJECT", "WRONG_DIRECTION"),
    ("wrong_dir_power_telemetry_open", POWER_TELEMETRY, 1, R(""), "REJECT", "WRONG_DIRECTION"),
    ("wrong_dir_mcu_diagnostic_open", MCU_DIAGNOSTIC, 1, R(""), "REJECT", "WRONG_DIRECTION"),
    ("wrong_dir_safety_state", SAFETY_STATE, 1, R(""), "REJECT", "WRONG_DIRECTION"),
    ("wrong_dir_beats_length", MCU_HELLO, 1, R("aabbcc"), "REJECT", "WRONG_DIRECTION"),

    # --- wrong payload length ---
    ("len_heartbeat_zero", HEARTBEAT, 1, R(""), "REJECT", "WRONG_PAYLOAD_LENGTH"),
    ("len_heartbeat_minus1", HEARTBEAT, 1, R("01020304"), "REJECT", "WRONG_PAYLOAD_LENGTH"),
    ("len_heartbeat_plus1", HEARTBEAT, 1, R("010203040506"), "REJECT", "WRONG_PAYLOAD_LENGTH"),
    ("len_heartbeat_overlong", HEARTBEAT, 1, R("00" * 20), "REJECT", "WRONG_PAYLOAD_LENGTH"),
    ("len_identify_plus1", IDENTIFY_REQUEST, 1, R("00"), "REJECT", "WRONG_PAYLOAD_LENGTH"),
    ("len_drive_minus1", DRIVE_SETPOINT, 1, R("0102030405"), "REJECT", "WRONG_PAYLOAD_LENGTH"),
    ("len_cleaning_plus1", CLEANING_MOTORS_SET, 1, R("0102030405"), "REJECT", "WRONG_PAYLOAD_LENGTH"),

    # --- heartbeat cpu_mode ---
    ("hb_mode0_ok", HEARTBEAT, 1, P("<IB", 0, 0), "OK", "OK"),
    ("hb_mode1_ok", HEARTBEAT, 1, P("<IB", 0, 1), "OK", "OK"),
    ("hb_mode2_oor", HEARTBEAT, 1, P("<IB", 0, 2), "REJECT", "VALUE_OUT_OF_RANGE"),

    # --- estop active ---
    ("estop_active0_ok", ESTOP_SET, 1, P("<BH", 0, 0), "OK", "OK"),
    ("estop_active1_ok", ESTOP_SET, 1, P("<BH", 1, 0), "OK", "OK"),
    ("estop_active2_oor", ESTOP_SET, 1, P("<BH", 2, 0), "REJECT", "VALUE_OUT_OF_RANGE"),

    # --- drive bounds (inclusive) ---
    ("drive_linear_max_ok", DRIVE_SETPOINT, 1, P("<hhH", 500, 0, 1), "OK", "OK"),
    ("drive_linear_over_oor", DRIVE_SETPOINT, 1, P("<hhH", 501, 0, 1), "REJECT", "VALUE_OUT_OF_RANGE"),
    ("drive_linear_min_ok", DRIVE_SETPOINT, 1, P("<hhH", -500, 0, 1), "OK", "OK"),
    ("drive_linear_under_oor", DRIVE_SETPOINT, 1, P("<hhH", -501, 0, 1), "REJECT", "VALUE_OUT_OF_RANGE"),
    ("drive_angular_max_ok", DRIVE_SETPOINT, 1, P("<hhH", 0, 4000, 1), "OK", "OK"),
    ("drive_angular_over_oor", DRIVE_SETPOINT, 1, P("<hhH", 0, 4001, 1), "REJECT", "VALUE_OUT_OF_RANGE"),
    ("drive_angular_min_ok", DRIVE_SETPOINT, 1, P("<hhH", 0, -4000, 1), "OK", "OK"),
    ("drive_angular_under_oor", DRIVE_SETPOINT, 1, P("<hhH", 0, -4001, 1), "REJECT", "VALUE_OUT_OF_RANGE"),
    ("drive_duration_min_ok", DRIVE_SETPOINT, 1, P("<hhH", 0, 0, 1), "OK", "OK"),
    ("drive_duration_max_ok", DRIVE_SETPOINT, 1, P("<hhH", 0, 0, 250), "OK", "OK"),
    ("drive_duration_zero_oor", DRIVE_SETPOINT, 1, P("<hhH", 0, 0, 0), "REJECT", "VALUE_OUT_OF_RANGE"),
    ("drive_duration_over_oor", DRIVE_SETPOINT, 1, P("<hhH", 0, 0, 251), "REJECT", "VALUE_OUT_OF_RANGE"),

    # --- cleaning motor percentages (each field) ---
    ("cleaning_all_max_ok", CLEANING_MOTORS_SET, 1, P("<BBBB", 100, 100, 100, 100), "OK", "OK"),
    ("cleaning_main_over_oor", CLEANING_MOTORS_SET, 1, P("<BBBB", 101, 0, 0, 0), "REJECT", "VALUE_OUT_OF_RANGE"),
    ("cleaning_side_over_oor", CLEANING_MOTORS_SET, 1, P("<BBBB", 0, 101, 0, 0), "REJECT", "VALUE_OUT_OF_RANGE"),
    ("cleaning_fan_over_oor", CLEANING_MOTORS_SET, 1, P("<BBBB", 0, 0, 101, 0), "REJECT", "VALUE_OUT_OF_RANGE"),
    ("cleaning_pump_over_oor", CLEANING_MOTORS_SET, 1, P("<BBBB", 0, 0, 0, 101), "REJECT", "VALUE_OUT_OF_RANGE"),

    # --- lidar percentage ---
    ("lidar_max_ok", LIDAR_MOTOR_SET, 1, P("<B", 100), "OK", "OK"),
    ("lidar_over_oor", LIDAR_MOTOR_SET, 1, P("<B", 101), "REJECT", "VALUE_OUT_OF_RANGE"),

    # --- led brightness (byte 3); id and mode unchecked ---
    ("led_brightness_max_ok", LED_SET, 1, P("<BBB", 0, 0, 100), "OK", "OK"),
    ("led_brightness_over_oor", LED_SET, 1, P("<BBB", 0, 0, 101), "REJECT", "VALUE_OUT_OF_RANGE"),
    ("led_id_mode_unchecked_ok", LED_SET, 1, P("<BBB", 255, 255, 50), "OK", "OK"),
]


def _payload_hex(spec):
    if "raw" in spec:
        return spec["raw"]
    fmt, values = spec["pack"]
    return struct.pack(fmt, *values).hex()


def render():
    vectors = []
    for name, mtype, version, spec, expect, reason in _SPECS:
        vectors.append(
            {
                "name": name,
                "message_type": mtype,
                "version": version,
                "payload_hex": _payload_hex(spec),
                "expect": expect,
                "reason": reason,
            }
        )
    return {
        "schema_version": 1,
        "targets_contract": TARGETS_CONTRACT,
        "vectors": vectors,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the committed JSON is stale")
    args = parser.parse_args(argv)

    payload = render()
    text = json.dumps(payload, indent=2) + "\n"

    if args.check:
        if not OUTPUT.exists():
            print(f"missing {OUTPUT.name}; run generate_gate_vectors.py", file=sys.stderr)
            return 1
        current = OUTPUT.read_text()
        if current != text:
            print(f"{OUTPUT.name} is stale; run generate_gate_vectors.py", file=sys.stderr)
            return 1
        print(f"{OUTPUT.name} is current ({len(payload['vectors'])} vectors)")
        return 0

    OUTPUT.write_text(text)
    print(f"wrote {OUTPUT.name} ({len(payload['vectors'])} vectors)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
