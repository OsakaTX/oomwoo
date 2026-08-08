# Reference Implementation (roe)
"""
OOMWOO recovery-safety reference logic — reactive bumper-pattern analyzer,
adaptive recovery ladder, safety handler, status reporter, and integration adapter.

This package complements xbattlax's oomwoo_recovery_safety package by providing
a bumper-contact history analyzer, an adaptive recovery ladder with re-entry
prevention, a safety-event arbitration handler, structured status reporting
with Home Assistant support, and the glue adapter to wire them all together.

Submodules:
    situation_analyzer   — BumperHistory, SituationClassifier, OdometryTracker
    adaptive_ladder      — AdaptiveLadder, ReentryMap, primary/panic ladders
    safety_handler       — SafetyHandler, SafetyEvent, SafetyArbitrationResult
    status_reporter      — FullStatus, StatusHistory, HA discovery configs
    integration_adapter  — RecoveryIntegrationAdapter, IntegrationDecision
    operator_override    — OperatorOverrideArbiter (RC/teleop takeover arbitration)
"""

from .situation_analyzer import (
    BumperHistory,
    BumperSide,
    ClassifierParams,
    ContactEvent,
    OdometryTracker,
    SituationAssessment,
    SituationClassifier,
    SituationType,
)

from .adaptive_ladder import (
    AdaptiveLadder,
    AdaptiveLadderParams,
    AttemptRecord,
    LadderStepCommand,
    PANIC_LADDERS,
    PRIMARY_LADDERS,
    RecoveryStep,
    ReentryMap,
)

from .safety_handler import (
    SafetyArbitrationResult,
    SafetyEvent,
    SafetyEventType,
    SafetyHandler,
    SafetyHandlerConfig,
    SafetySource,
    SafetyState,
    prioritize_events,
)

from .status_reporter import (
    ExtendedStatusFields,
    FullStatus,
    RecoveryBaseStatus,
    StatusHistory,
    StatusLevel,
    StatusReporterConfig,
    StatusSource,
    compute_level,
    generate_ha_discovery_configs,
    generate_ha_automation_suggestions,
    make_extended,
    make_status,
)

from .integration_adapter import (
    IntegrationAdapterLadderStep,
    IntegrationDecision,
    RecoveryIntegrationAdapter,
)

from .operator_override import (
    OperatorOverrideArbiter,
    OperatorOverrideConfig,
    OperatorOverrideState,
    OverrideArbiterDecision,
    OverrideReason,
)

__all__ = [
    # situation_analyzer
    "BumperHistory", "BumperSide", "ClassifierParams", "ContactEvent",
    "OdometryTracker", "SituationAssessment", "SituationClassifier", "SituationType",
    # adaptive_ladder
    "AdaptiveLadder", "AdaptiveLadderParams", "AttemptRecord", "LadderStepCommand",
    "PANIC_LADDERS", "PRIMARY_LADDERS", "RecoveryStep", "ReentryMap",
    # safety_handler
    "SafetyArbitrationResult", "SafetyEvent", "SafetyEventType", "SafetyHandler",
    "SafetyHandlerConfig", "SafetySource", "SafetyState", "prioritize_events",
    # status_reporter
    "ExtendedStatusFields", "FullStatus", "RecoveryBaseStatus", "StatusHistory",
    "StatusLevel", "StatusReporterConfig", "StatusSource", "compute_level",
    "generate_ha_discovery_configs", "generate_ha_automation_suggestions",
    "make_extended", "make_status",
    # integration_adapter
    "IntegrationAdapterLadderStep", "IntegrationDecision", "RecoveryIntegrationAdapter",
    # operator_override
    "OperatorOverrideArbiter", "OperatorOverrideConfig", "OperatorOverrideState",
    "OverrideArbiterDecision", "OverrideReason",
]
