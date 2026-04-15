"""Constantes globales del Oraculo. Single source of truth."""
from __future__ import annotations
from pathlib import Path

API_VERSION = "1.0"
SCHEMA_VERSION = "1.0"

PROFILE_BASIC = "basic"
PROFILE_ENTERPRISE = "enterprise"
PROFILE_BANKING = "banking"
PROFILES_CANONICAL = (PROFILE_BASIC, PROFILE_ENTERPRISE, PROFILE_BANKING)

PROFILE_RANK = {PROFILE_BASIC: 1, PROFILE_ENTERPRISE: 2, PROFILE_BANKING: 3}

DEFAULT_DATA_DIR = "db_storage"
DEFAULT_PROFILE = PROFILE_ENTERPRISE

# Sentinels
DEGRADED_MODE_FILE = "degraded_state.json"
ACTIVE_PROFILE_FILE = "profiles/active.txt"
PROFILE_HISTORY_FILE = "profiles/history.jsonl"

# Trust tiers
TRUST_CANON = 1
TRUST_HIGH = 2
TRUST_CONTEXTUAL = 3
