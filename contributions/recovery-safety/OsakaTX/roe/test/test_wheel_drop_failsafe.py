"""
Tests for roe.wheel_drop_failsafe — measured wheel-drop switch fail-safe semantics.

Guards (all verified against primary source THIS run 2026-09-02):
  * the merged IKsares drive-wheel README (PR #61, upstream/main
    contributions/part-specs/IKsares/drive-wheel/README.md) documents an
    SPDT snap-action microswitch wired COM+NC (NO unused): at rest the
    harness is closed, lever pressed -> open, and "Firmware should treat
    open as wheel-dropped and stop" — the classic fail-safe arrangement;
  * the adapter polarity between the physical switch and the merged
    True-only ``oomwoo/safety/wheel_drop`` consumer is the missing link:
    open must map to True (assert), or a wire break silently defeats the
    fail-safe; the polarity is currently UNDEFINED (bridge unlanded).
"""

import os

import pytest

from roe.wheel_drop_failsafe import (
    ADAPTER_OPEN_TO_FALSE,
    ADAPTER_OPEN_TO_TRUE,
    SWITCH_AT_REST,
    SWITCH_OPEN_MEANS_DROPPED,
    SWITCH_PRESSED,
    TOPIC_FALSE,
    TOPIC_TRUE,
    WheelDropSwitchModel,
    evaluate_adapter_polarity,
    note_inverted_mechanical_correspondence,
    verify_drive_wheel_readme,
)

# ---------------------------------------------------------------------------
# Measured switch semantics (IKsares README §5, merged upstream/main)
# ---------------------------------------------------------------------------


def test_measured_switch_wiring_and_behaviour():
    # SPDT, COM+NC wired, NO unused: at rest closed, pressed -> open.
    assert WheelDropSwitchModel.harness_open(SWITCH_AT_REST) is False
    assert WheelDropSwitchModel.harness_open(SWITCH_PRESSED) is True


def test_open_is_the_safe_wheel_dropped_state():
    # IKsares (verbatim): "Firmware should treat open as wheel-dropped and
    # stop, which is the safe reading whichever way the mechanism turns out
    # to work." — the fail-safe direction.
    assert SWITCH_OPEN_MEANS_DROPPED is True
    assert WheelDropSwitchModel.safe_semantics_when(False) is False
    assert WheelDropSwitchModel.safe_semantics_when(True) is True


# ---------------------------------------------------------------------------
# Adapter polarity — the invariant that preserves fail-safe end-to-end
# ---------------------------------------------------------------------------


def test_preserve_polarity_maps_open_to_true():
    v = evaluate_adapter_polarity(ADAPTER_OPEN_TO_TRUE[SWITCH_PRESSED])
    assert v.preserves_failsafe is True
    assert v.open_maps_to is True
    assert ADAPTER_OPEN_TO_TRUE == {SWITCH_PRESSED: TOPIC_TRUE, SWITCH_AT_REST: TOPIC_FALSE}


def test_inverted_polarity_is_a_silent_break():
    v = evaluate_adapter_polarity(ADAPTER_OPEN_TO_FALSE[SWITCH_PRESSED])
    assert v.preserves_failsafe is False
    assert v.open_maps_to is False
    # open at rest + wire break both read "wheel present" -> node never
    # pauses -> silent (no alarm, no status change, no ack required)
    assert "silently" in v.note


def test_undefined_polarity_carries_no_guarantee():
    # Current stack state: oomwoo-one gz_bridge safety entries unlanded and
    # no physical adapter specified -> the hardware fail-safe does NOT yet
    # hold end-to-end.
    v = evaluate_adapter_polarity(None)
    assert v.preserves_failsafe is False
    assert v.open_maps_to is None
    assert "UNDEFINED" in v.note


def test_mechanical_correspondence_still_open():
    note = note_inverted_mechanical_correspondence()
    assert "UNMEASURED" in note
    assert "wheel-dropped" in note


# ---------------------------------------------------------------------------
# Drift-guard against the real in-repo IKsares README
# ---------------------------------------------------------------------------


def test_drive_wheel_readme_in_repo_supports_model(tmp_path):
    """Best-effort: if the upstream clone is present, verify the REAL README."""
    repo = os.environ.get("OOMWOO_REPO", str(tmp_path))
    readme = os.path.join(
        repo, "contributions/part-specs/IKsares/drive-wheel/README.md"
    )
    if not os.path.exists(readme):
        pytest.skip("upstream clone not present; IKsares README unavailable")
    with open(readme, encoding="utf-8") as fh:
        verify_drive_wheel_readme(fh.read())


def test_readme_guard_detects_wiring_change():
    # If the upstream doc were edited to a normally-OPEN arrangement, the
    # fail-safe model must flag it.
    sample = (
        "SPDT snap-action\nCOM and NC\nNO is left unused\n"
        "| At rest (not pressed) | **closed** | ...\n"
        "treat open as wheel-dropped and stop\nbroken wire ... read as *open*\n"
    )
    verify_drive_wheel_readme(sample)  # must not raise
    tampered = sample.replace("COM and NC", "COM and NO")
    with pytest.raises(Exception, match="COM\+NC"):
        verify_drive_wheel_readme(tampered)


def test_readme_guard_detects_guidance_change():
    sample = (
        "SPDT snap-action\nCOM and NC\nNO is left unused\n"
        "| At rest (not pressed) | **closed** | ...\n"
        "treat open as wheel-dropped and stop\nbroken wire ... read as *open*\n"
    )
    tampered = sample.replace(
        "treat open as wheel-dropped and stop", "treat closed as wheel-dropped"
    )
    with pytest.raises(Exception, match="treat open as wheel-dropped"):
        verify_drive_wheel_readme(tampered)
