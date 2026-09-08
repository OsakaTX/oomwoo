"""Tests for the safety handler module."""

import time

from roe.safety_handler import (
    SafetyArbitrationResult,
    SafetyEvent,
    SafetyEventType,
    SafetyHandler,
    SafetyHandlerConfig,
    SafetySource,
    SafetyState,
    prioritize_events,
)


class TestSafetyEvent:
    def test_e_stop_factory(self):
        event = SafetyEvent.e_stop(100.0)
        assert event.event_type == SafetyEventType.E_STOP
        assert event.reason_code == "E_STOP"
        assert event.recoverable is False
        assert event.requires_hardware_reset is True

    def test_cliff_factory(self):
        event = SafetyEvent.cliff(100.0)
        assert event.event_type == SafetyEventType.CLIFF
        assert event.reason_code == "SAFETY_CLIFF"
        assert event.recoverable is False
        assert event.requires_hardware_reset is False

    def test_cliff_with_side(self):
        event = SafetyEvent.cliff(100.0, side="left")
        assert event.side == "left"
        assert "left" in event.message

    def test_wheel_drop_factory(self):
        event = SafetyEvent.wheel_drop(100.0)
        assert event.event_type == SafetyEventType.WHEEL_DROP
        assert event.reason_code == "SAFETY_WHEEL_DROP"

    def test_pickup_factory(self):
        event = SafetyEvent.pickup(100.0)
        assert event.event_type == SafetyEventType.PICKUP
        assert event.recoverable is True

    def test_bumper_jam_factory(self):
        event = SafetyEvent.bumper_jam(100.0, "left", 4.5)
        assert event.event_type == SafetyEventType.BUMPER_JAM
        assert event.source == SafetySource.INFERRED
        assert "4.5" in event.message


class TestPrioritizeEvents:
    def test_empty_returns_none(self):
        assert prioritize_events([]) is None

    def test_single_event(self):
        e = SafetyEvent.e_stop(0.0)
        assert prioritize_events([e]) is e

    def test_e_stop_highest_priority(self):
        cliff = SafetyEvent.cliff(0.0)
        estop = SafetyEvent.e_stop(0.0)
        pickup = SafetyEvent.pickup(0.0)
        assert prioritize_events([cliff, estop, pickup]) is estop

    def test_cliff_over_pickup(self):
        cliff = SafetyEvent.cliff(0.0)
        pickup = SafetyEvent.pickup(0.0)
        assert prioritize_events([pickup, cliff]) is cliff

    def test_wheel_drop_over_pickup(self):
        wd = SafetyEvent.wheel_drop(0.0)
        pickup = SafetyEvent.pickup(0.0)
        assert prioritize_events([pickup, wd]) is wd

    def test_bumper_jam_lowest(self):
        jam = SafetyEvent.bumper_jam(0.0, "left", 5.0)
        pickup = SafetyEvent.pickup(0.0)
        assert prioritize_events([jam, pickup]) is pickup


class TestSafetyHandler:
    def test_initial_state_clear(self):
        handler = SafetyHandler()
        result = handler.arbitrate(0.0)
        assert result.state == SafetyState.CLEAR
        assert result.is_safe

    def test_trigger_estop(self):
        handler = SafetyHandler()
        result = handler.trigger(SafetyEvent.e_stop(1.0))
        assert result.state == SafetyState.HARD_LOCKED
        assert result.primary_event.event_type == SafetyEventType.E_STOP
        assert result.is_locked

    def test_trigger_cliff(self):
        handler = SafetyHandler()
        result = handler.trigger(SafetyEvent.cliff(1.0))
        assert result.state == SafetyState.ACTIVE
        assert result.primary_event.reason_code == "SAFETY_CLIFF"
        assert not result.is_safe

    def test_trigger_pickup(self):
        handler = SafetyHandler()
        result = handler.trigger(SafetyEvent.pickup(1.0))
        assert result.state == SafetyState.ACTIVE
        assert result.reason_code == "SAFETY_PICKUP"

    def test_clear_returns_pending(self):
        handler = SafetyHandler()
        handler.trigger(SafetyEvent.cliff(1.0))
        result = handler.clear(2.0)
        assert result.state == SafetyState.PENDING_CLEAR
        assert result.reason_code == "PENDING_CLEAR"

    def test_confirm_clear_returns_clear(self):
        handler = SafetyHandler()
        handler.trigger(SafetyEvent.cliff(1.0))
        handler.clear(2.0)
        result = handler.confirm_clear(3.0)
        assert result.state == SafetyState.CLEAR
        assert result.is_safe
        assert result.reason_code == "SAFETY_CLEAR"

    def test_hard_lock_survives_clear(self):
        handler = SafetyHandler()
        handler.trigger(SafetyEvent.e_stop(1.0))
        result = handler.clear(2.0)
        assert result.state == SafetyState.HARD_LOCKED
        assert result.reason_code == "E_STOP_LOCKED"

    def test_hard_lock_survives_confirm(self):
        handler = SafetyHandler()
        handler.trigger(SafetyEvent.e_stop(1.0))
        result = handler.confirm_clear(2.0)
        assert result.state == SafetyState.HARD_LOCKED

    def test_hard_reset_clears_estop(self):
        handler = SafetyHandler()
        handler.trigger(SafetyEvent.e_stop(1.0))
        result = handler.hard_reset(2.0)
        assert result.state == SafetyState.CLEAR
        assert result.is_safe

    def test_highest_priority_wins_in_multi_event(self):
        handler = SafetyHandler()
        handler.trigger(SafetyEvent.pickup(1.0))
        result = handler.trigger(SafetyEvent.cliff(2.0))
        # Cliff is higher priority than pickup
        assert result.primary_event.event_type == SafetyEventType.CLIFF
        assert result.state == SafetyState.ACTIVE

    def test_estop_overrides_pickup(self):
        handler = SafetyHandler()
        handler.trigger(SafetyEvent.pickup(1.0))
        result = handler.trigger(SafetyEvent.e_stop(2.0))
        assert result.primary_event.event_type == SafetyEventType.E_STOP
        assert result.state == SafetyState.HARD_LOCKED

    def test_history_records_events(self):
        handler = SafetyHandler()
        handler.trigger(SafetyEvent.cliff(1.0))
        handler.trigger(SafetyEvent.pickup(2.0))
        assert len(handler.history) == 2
        assert handler.history[0].reason_code == "SAFETY_CLIFF"

    def test_history_bounded(self):
        handler = SafetyHandler(config=SafetyHandlerConfig(max_events_logged=3))
        for i in range(10):
            handler.trigger(SafetyEvent.pickup(float(i)))
        assert len(handler.history) == 3

    def test_reset_history(self):
        handler = SafetyHandler()
        handler.trigger(SafetyEvent.cliff(1.0))
        handler.reset_history()
        assert len(handler.history) == 0

    def test_clear_specific_event_type(self):
        handler = SafetyHandler()
        handler.trigger(SafetyEvent.cliff(1.0))
        handler.trigger(SafetyEvent.pickup(2.0))
        # Clear just the cliff event
        handler.clear(3.0, SafetyEventType.CLIFF)
        result = handler.arbitrate(3.0)
        assert result.primary_event.event_type == SafetyEventType.PICKUP

    def test_pickup_auto_clear(self):
        handler = SafetyHandler(config=SafetyHandlerConfig(auto_clear_pickup=True))
        handler.trigger(SafetyEvent.pickup(1.0))
        # Pickup is still active
        assert handler.state == SafetyState.ACTIVE

    def test_all_events_in_result(self):
        handler = SafetyHandler()
        handler.trigger(SafetyEvent.pickup(1.0))
        result = handler.trigger(SafetyEvent.cliff(2.0))
        assert len(result.all_events) == 2

    def test_active_events_property(self):
        handler = SafetyHandler()
        handler.trigger(SafetyEvent.cliff(1.0))
        assert len(handler.active_events) == 1
        handler.clear(2.0)
        assert len(handler.active_events) == 0

    def test_is_safe_when_clear(self):
        handler = SafetyHandler()
        result = handler.arbitrate(0.0)
        assert result.is_safe
        assert not result.is_locked

    def test_is_locked_when_estop(self):
        handler = SafetyHandler()
        result = handler.trigger(SafetyEvent.e_stop(1.0))
        assert result.is_locked
        assert not result.is_safe
