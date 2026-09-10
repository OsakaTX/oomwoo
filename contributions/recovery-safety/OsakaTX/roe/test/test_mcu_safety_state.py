"""Tests for roe.mcu_safety_state (PR #63 SAFETY_STATE -> ROS view).

Provenance: constants were read on 2026-09-10 from makers-pet/oomwoo PR #63
head 629b60245a22f78929749f9dcf0a7090ad5be844 -- docs/cpu_mcu_serial_contract.md
and conformance/protocol_v1.json. The manifest/sample-derived assertions below
re-derive every number from the module's public surface so a merged-PR content
change breaks them loudly instead of silently drifting.
"""

from __future__ import annotations

import inspect

import pytest

from roe import mcu_safety_state as m
from roe.mcu_safety_state import (
    EVENTS_FULL,
    SAFETY_EVENT_MESSAGE_ID,
    SAFETY_STATE_MESSAGE_ID,
    SAFETY_STATE_STRUCT_FORMAT,
    SafetyStateFrame,
    SafetyStateLiveness,
    admit_clear,
    active_events,
    event_by_name,
    flags_for,
    latched_events,
    node_pause_reason,
    parse_safety_state,
    project_to_node_inputs,
    recoverable,
)

# ---------------------------------------------------------------------------
# manifest / struct identity
# ---------------------------------------------------------------------------


def test_struct_format_is_i_h_h():
    assert SAFETY_STATE_STRUCT_FORMAT == "<IHH"


def test_message_ids_match_pr_manifest():
    assert SAFETY_STATE_MESSAGE_ID == 32773
    assert SAFETY_EVENT_MESSAGE_ID == 32770


def test_parse_roundtrip_manifest_sample():
    f = parse_safety_state(23, [151, 256, 768])
    assert (f.timestamp_ms, f.active_flags, f.latched_flags) == (151, 256, 768)


def test_parse_rejects_wrong_arity():
    with pytest.raises(ValueError, match="3 values"):
        parse_safety_state(1, [1, 2])


def test_parse_rejects_negative():
    with pytest.raises(ValueError, match="nonnegative"):
        parse_safety_state(1, [-1, 0, 0])


def test_parse_rejects_mask_over_u16():
    with pytest.raises(ValueError, match="u16"):
        parse_safety_state(1, [0, 0x10000, 0])


def test_parse_rejects_ts_over_u32():
    with pytest.raises(ValueError, match="u32"):
        parse_safety_state(1, [0x100000000, 0, 0])


# ---------------------------------------------------------------------------
# event table + bit mapping (PR doc 'Safety events' / 'SAFETY_STATE')
# ---------------------------------------------------------------------------


def test_table_has_ten_codes_in_order():
    assert [e.code for e in EVENTS_FULL] == list(range(1, 11))


def test_event_names_match_pr_table():
    assert [e.name for e in EVENTS_FULL] == [
        "BUMPER_LEFT", "BUMPER_RIGHT", "CLIFF_LEFT", "CLIFF_RIGHT",
        "WHEEL_DROP_LEFT", "WHEEL_DROP_RIGHT", "BRUSH_OVERCURRENT",
        "FAN_OVERCURRENT", "CPU_HEARTBEAT_TIMEOUT", "ESTOP",
    ]


def test_bit_mapping_is_code_minus_one():
    for ev in EVENTS_FULL:
        assert ev.bit == ev.code - 1


def test_verbatim_behavior_cells_for_latching_events():
    by = {e.name: e for e in EVENTS_FULL}
    assert "latch until wheel contact returns." in \
        by["WHEEL_DROP_LEFT"].mcu_behavior
    assert "latch until explicit clear." in by["ESTOP"].mcu_behavior


def test_flags_for_selected_members():
    assert flags_for(["ESTOP"]) == 1 << 9
    assert flags_for(["CLIFF_LEFT", "CLIFF_RIGHT"]) == 0b1100
    assert flags_for(["WHEEL_DROP_LEFT", "WHEEL_DROP_RIGHT"]) == 0b110000


def test_events_1_to_10_fit_u16_exactly_as_pr_doc_claims():
    assert flags_for(e.name for e in EVENTS_FULL) == 0x3FF


def test_manifest_sample_151_256_768_decodes_named():
    f = parse_safety_state(23, [151, 256, 768])
    # field order <IHH: ts=151 ms; active=256 bit 8 -> code 9;
    # latched=768 bits {8,9} -> codes 9,10 (N -> bit N-1)
    assert f.timestamp_ms == 151
    assert active_events(f) == frozenset({"CPU_HEARTBEAT_TIMEOUT"})
    assert latched_events(f) == frozenset(
        {"CPU_HEARTBEAT_TIMEOUT", "ESTOP"})


def test_unknown_bit_raises_with_flags_detail():
    f = parse_safety_state(1, [0, 0, 1 << 15])
    with pytest.raises(ValueError, match="no event code"):
        latched_events(f)


def test_event_by_name_roundtrip_and_miss():
    assert event_by_name("ESTOP").code == 10
    with pytest.raises(KeyError):
        event_by_name("NOPE")


def test_provenance_string_pins_head_sha():
    assert "629b60245a22f78929749f9dcf0a7090ad5be844" in m.PR63_PROVENANCE
    assert "2026-09-10" in m.PR63_PROVENANCE


# ---------------------------------------------------------------------------
# projection onto the deployed node's input view
# ---------------------------------------------------------------------------


def _frame(active, latched=0, ts=1000):
    return parse_safety_state(1, [ts, active, latched])


def test_estop_only_view():
    v = project_to_node_inputs(_frame(flags_for(["ESTOP"])))
    assert v.estop is True
    assert v.cliff is False and v.wheel_drop is False
    assert v.bumper_contact is False and v.pickup is False


def test_left_cliff_and_right_wheel_drop():
    v = project_to_node_inputs(
        _frame(flags_for(["CLIFF_LEFT", "WHEEL_DROP_RIGHT"])))
    assert v.cliff is True and v.wheel_drop is True
    assert v.estop is False and v.bumper_contact is False


def test_bumper_sets_only_contact_flag():
    v = project_to_node_inputs(_frame(flags_for(["BUMPER_LEFT", "BUMPER_RIGHT"])))
    assert v.bumper_contact is True
    assert not (v.estop or v.cliff or v.wheel_drop)


def test_pickup_not_represented_in_mcu_table():
    assert "PICKUP" not in [e.name for e in EVENTS_FULL]
    v = project_to_node_inputs(_frame(0x3FF))
    assert v.pickup is False  # modeled NOT REPRESENTED, not as a bit


def test_latched_only_does_not_assert_inputs():
    v = project_to_node_inputs(_frame(0, latched=flags_for(["ESTOP"])))
    assert v.estop is False  # active mask drives the view, not the latch


def test_projection_is_deterministic():
    a = project_to_node_inputs(_frame(0b1111111111))
    b = project_to_node_inputs(_frame(0b1111111111, ts=999))
    assert a == b


# ---------------------------------------------------------------------------
# node pause-reason vocabulary + recoverable
# ---------------------------------------------------------------------------


def test_reason_map():
    assert node_pause_reason("ESTOP") == "E_STOP"
    assert node_pause_reason("CLIFF_LEFT") == "SAFETY_CLIFF"
    assert node_pause_reason("CLIFF_RIGHT") == "SAFETY_CLIFF"
    assert node_pause_reason("WHEEL_DROP_LEFT") == "SAFETY_WHEEL_DROP"
    assert node_pause_reason("WHEEL_DROP_RIGHT") == "SAFETY_WHEEL_DROP"


def test_overcurrent_and_heartbeat_unmapped_by_design():
    for name in ("BRUSH_OVERCURRENT", "FAN_OVERCURRENT",
                 "CPU_HEARTBEAT_TIMEOUT"):
        assert node_pause_reason(name) is None


def test_unknown_mnemonic_is_none_not_raise():
    assert node_pause_reason("NOT_A_THING") is None


def test_all_safety_pauses_nonrecoverable():
    for reason in ("E_STOP", "SAFETY_CLIFF", "SAFETY_WHEEL_DROP",
                   "SAFETY_PICKUP"):
        assert recoverable(reason) is False


def test_recoverable_unknown_is_none():
    assert recoverable("whatever") is None


# ---------------------------------------------------------------------------
# latch-aware clear admission
# ---------------------------------------------------------------------------

CLEAN = project_to_node_inputs(_frame(0))


def test_clean_state_admits():
    r = admit_clear(CLEAN, False, now_ms=10_000, last_active_ms=None)
    assert r.admitted is True and r.blockers == frozenset()


def test_active_estop_blocks():
    v = project_to_node_inputs(_frame(flags_for(["ESTOP"])))
    r = admit_clear(v, False, 10_000, None)
    assert r.admitted is False
    assert r.blockers == frozenset({"estop_active"})


def test_active_cliff_blocks_as_environment():
    v = project_to_node_inputs(_frame(flags_for(["CLIFF_RIGHT"])))
    assert "environment_unstable" in admit_clear(
        v, False, 10_000, None).blockers


def test_active_wheel_drop_blocks_as_environment():
    v = project_to_node_inputs(_frame(flags_for(["WHEEL_DROP_LEFT"])))
    assert "environment_unstable" in admit_clear(
        v, False, 10_000, None).blockers


def test_unacked_latch_blocks_even_when_quiet():
    r = admit_clear(CLEAN, True, 10_000, 5_000)
    assert r.admitted is False and "latch_unacked" in r.blockers


def test_quiet_window_inside_blocks():
    r = admit_clear(CLEAN, False, 3_000, last_active_ms=1_500,
                    quiet_window_ms=2_000)
    assert r.admitted is False and "quiet_window" in r.blockers


def test_quiet_window_after_expires_admits():
    r = admit_clear(CLEAN, False, 3_500, last_active_ms=1_500,
                    quiet_window_ms=2_000)
    assert r.admitted is True  # boundary: exactly 2000 ms elapsed


def test_never_active_no_window_blocker():
    r = admit_clear(CLEAN, False, 1, None)
    assert r.admitted is True and "quiet_window" not in r.blockers


def test_all_blockers_and_together():
    v = project_to_node_inputs(_frame(flags_for(["ESTOP", "CLIFF_LEFT"])))
    r = admit_clear(v, True, 100, 99)
    assert r.admitted is False
    assert r.blockers == frozenset(
        {"estop_active", "environment_unstable", "latch_unacked",
         "quiet_window"})


def test_default_window_docstring_carries_estimate_marker():
    src = inspect.getsource(m.admit_clear)
    assert "(estimate)" in src


# ---------------------------------------------------------------------------
# stream liveness
# ---------------------------------------------------------------------------


def test_liveness_never_current_stale():
    w = SafetyStateLiveness(stale_after_ms=100)
    assert w.evaluate(0) == "never"
    w.observe(_frame(0), 1_000)
    assert w.evaluate(1_100) == "current"  # boundary inclusive (<= window)
    assert w.evaluate(1_101) == "stale"
    assert w.frames_seen == 1


def test_liveness_window_tracks_last_frame():
    w = SafetyStateLiveness(stale_after_ms=100)
    w.observe(_frame(0), 1_000)
    w.observe(_frame(0), 1_050)
    assert w.evaluate(1_150) == "current"  # boundary inclusive
    assert w.evaluate(1_151) == "stale"


def test_liveness_rejects_nonpositive_window():
    with pytest.raises(ValueError, match="positive"):
        SafetyStateLiveness(stale_after_ms=0)


def test_default_window_is_documented_estimate():
    assert SafetyStateLiveness.STALE_DEFAULT_MS == 2500


def test_liveness_ignores_frame_content():
    a, b = SafetyStateLiveness(), SafetyStateLiveness()
    a.observe(_frame(0x3FF, 0xFFFF, ts=7), 5)
    b.observe(_frame(0, 0, ts=9), 5)
    assert a.evaluate(6) == b.evaluate(6) == "current"
    assert a.frames_seen == b.frames_seen == 1
