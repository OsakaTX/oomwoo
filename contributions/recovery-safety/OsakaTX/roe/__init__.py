# Reference Implementation (roe)
"""
OOMWOO recovery-safety reference logic — bumper-pattern analyzer and adaptive recovery ladder.

This package complements xbattlax's oomwoo_recovery_safety package. It provides
a bumper-contact history analyzer that classifies stuck situations (wedge, confined
pocket, stuck/spinning, normal contact) and an adaptive ladder that adjusts recovery
step parameters based on escalation depth and recurrence tracking.

Usage:
    from roe import SituationClassifier, AdaptiveLadder, SituationType
"""
