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

from .slip_odometry import (
    IMU_TOPIC,
    STREAM_TRUTH,
    STREAM_WHEEL,
    SlipAssessment,
    SlipAssessmentKind,
    SlipOdometryTracker,
    TRUTH_ODOM_TOPIC,
    WHEEL_ODOM_TOPIC,
)

from .safety_input_protocol import (
    ConsumerHardeningLatch,
    ConsumerHardeningLatchConfig,
    LatchState,
    MERGED_COMMAND_TOPIC,
    MERGED_EXHAUSTED_RECOVERABLE,
    MERGED_RESET_TOPIC,
    MERGED_SAFETY_PAUSED_RECOVERABLE,
    MERGED_SAFETY_REASON_CODES,
    MERGED_STATUS_TOPIC,
    MERGED_SUB_QOS_DEPTH,
    MergedInputSemantics,
    ProducerAssertionPolicy,
    ProducerAssertionPolicyConfig,
    ProducerDecision,
    SAFETY_EVENTS,
    SAFETY_TOPIC_PREFIX,
    SafetyInputOutcome,
    SafetyInputVerdict,
    TransportMode,
    is_post_reset_vulnerable,
)

from .pause_alert_ack import (
    PAUSE_ACK_REASON_CODES,
    AckEpisodesLog,
    AckState,
    AckVerdict,
    AlertAnnunciator,
    AlertLevel,
    AnnunciatorState,
    NodeSourceMismatch,
    PauseAlertConfig,
    PauseAckSupervisor,
    StatusState,
    builtin_alert_surface_source,
    classify_status,
    evaluate_ack_admission,
    reason_seen_paused_alert,
    verify_deployed_alert_surface,
)

from .wheel_drop_failsafe import (
    ADAPTER_OPEN_TO_FALSE,
    ADAPTER_OPEN_TO_TRUE,
    AdapterVerdict,
    DriveWheelDocMismatch,
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

from .status_emission_contract import (
    DEPLOYED_STATES,
    DEPLOYED_STATUS_KEYS,
    EMITTER_INIT_EMIT,
    EMITTER_EXECUTE_EMIT,
    EMITTER_PUBLISH_METHOD,
    EXTENDED_BLOCK_KEY,
    FrameCheck,
    FrameVerdict,
    Health,
    NO_KEEPALIVE_FACT,
    PUBLISH_TIME_KEY,
    ROBOT_TIME_KEY,
    STATUS_JSON_SORTED_KEYS,
    STATUS_TOPIC,
    StatusEmissionMonitor,
    check_frame,
    verify_emitter_shape,
)

from .status_observability_align import (
    KpiFireability,
    MERGED_STATE_VALUES,
    SourceMismatch,
    YUEQIN22_RECORD_STATUS_VERBATIM,
    evaluate_kpi_fireability,
    yueqin22_kpi_spec,
)

from .mcu_safety_state import (
    EVENTS_FULL,
    PR63_PROVENANCE,
    SAFETY_EVENT_MESSAGE_ID,
    SAFETY_STATE_MESSAGE_ID,
    SAFETY_STATE_STRUCT_FORMAT,
    ClearAdmission,
    NodeSafetyView,
    SafetyEvent,
    SafetyStateFrame,
    SafetyStateLiveness,
    active_events,
    admit_clear,
    event_by_name,
    flags_for,
    latched_events,
    node_pause_reason,
    parse_safety_state,
    project_to_node_inputs,
    recoverable,
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
    # slip_odometry
    "IMU_TOPIC", "STREAM_TRUTH", "STREAM_WHEEL", "SlipAssessment",
    "SlipAssessmentKind", "SlipOdometryTracker", "TRUTH_ODOM_TOPIC",
    "WHEEL_ODOM_TOPIC",
    # safety_input_protocol
    "ConsumerHardeningLatch", "ConsumerHardeningLatchConfig", "LatchState",
    "MERGED_COMMAND_TOPIC", "MERGED_EXHAUSTED_RECOVERABLE", "MERGED_RESET_TOPIC",
    "MERGED_SAFETY_PAUSED_RECOVERABLE", "MERGED_SAFETY_REASON_CODES",
    "MERGED_STATUS_TOPIC", "MERGED_SUB_QOS_DEPTH", "MergedInputSemantics",
    "ProducerAssertionPolicy", "ProducerAssertionPolicyConfig", "ProducerDecision",
    "SAFETY_EVENTS", "SAFETY_TOPIC_PREFIX", "SafetyInputOutcome",
    "SafetyInputVerdict", "TransportMode", "is_post_reset_vulnerable",
    # pause_alert_ack
    "PAUSE_ACK_REASON_CODES", "AckEpisodesLog", "AckState", "AckVerdict",
    "AlertAnnunciator", "AlertLevel", "AnnunciatorState", "NodeSourceMismatch",
    "PauseAlertConfig", "PauseAckSupervisor", "StatusState",
    "builtin_alert_surface_source", "classify_status", "evaluate_ack_admission",
    # wheel_drop_failsafe
    "ADAPTER_OPEN_TO_FALSE", "ADAPTER_OPEN_TO_TRUE", "AdapterVerdict",
    "DriveWheelDocMismatch", "SWITCH_AT_REST", "SWITCH_OPEN_MEANS_DROPPED",
    "SWITCH_PRESSED", "TOPIC_FALSE", "TOPIC_TRUE", "WheelDropSwitchModel",
    "evaluate_adapter_polarity", "note_inverted_mechanical_correspondence",
    "verify_drive_wheel_readme",
    # status_emission_contract
    "DEPLOYED_STATES", "DEPLOYED_STATUS_KEYS", "EMITTER_INIT_EMIT",
    "EMITTER_EXECUTE_EMIT", "EMITTER_PUBLISH_METHOD", "EXTENDED_BLOCK_KEY",
    "FrameCheck", "FrameVerdict", "Health", "NO_KEEPALIVE_FACT",
    "PUBLISH_TIME_KEY", "ROBOT_TIME_KEY", "STATUS_JSON_SORTED_KEYS",
    "STATUS_TOPIC", "StatusEmissionMonitor", "check_frame",
    "verify_emitter_shape",
    # status_observability_align
    "KpiFireability", "MERGED_STATE_VALUES", "SourceMismatch",
    "YUEQIN22_RECORD_STATUS_VERBATIM", "evaluate_kpi_fireability",
    "yueqin22_kpi_spec",
    "reason_seen_paused_alert", "verify_deployed_alert_surface",
    # mcu_safety_state
    "EVENTS_FULL", "PR63_PROVENANCE", "SAFETY_EVENT_MESSAGE_ID",
    "SAFETY_STATE_MESSAGE_ID", "SAFETY_STATE_STRUCT_FORMAT",
    "ClearAdmission", "NodeSafetyView", "SafetyEvent", "SafetyStateFrame",
    "SafetyStateLiveness", "active_events", "admit_clear", "event_by_name",
    "flags_for", "latched_events", "node_pause_reason",
    "parse_safety_state", "project_to_node_inputs", "recoverable",
]
