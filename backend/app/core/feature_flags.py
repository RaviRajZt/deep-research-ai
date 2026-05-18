# ============================================
# Deep Research Platform - Feature Flag Management
# ============================================
# Core feature flagging engine for the platform.
# Handles environment-specific defaults, environment variable overrides,
# and runtime queries.
# ============================================

from __future__ import annotations

import os
from enum import StrEnum, unique
from typing import Any

from app.core.settings import get_settings


@unique
class FeatureFlag(StrEnum):
    """
    All platform feature flags.
    Must mirror the frontend contracts exactly (see shared/contracts/feature-flags.ts).
    """

    # Streaming
    ENABLE_SSE_STREAMING = "ENABLE_SSE_STREAMING"
    ENABLE_SSE_HEARTBEAT = "ENABLE_SSE_HEARTBEAT"

    # AI Agents
    ENABLE_PARALLEL_SUMMARIZATION = "ENABLE_PARALLEL_SUMMARIZATION"
    ENABLE_AGENT_TIMELINE = "ENABLE_AGENT_TIMELINE"
    ENABLE_AGENT_RETRY = "ENABLE_AGENT_RETRY"

    # Caching
    ENABLE_RESEARCH_CACHE = "ENABLE_RESEARCH_CACHE"
    ENABLE_QUERY_CACHE = "ENABLE_QUERY_CACHE"

    # Export
    ENABLE_MARKDOWN_EXPORT = "ENABLE_MARKDOWN_EXPORT"
    ENABLE_PDF_EXPORT = "ENABLE_PDF_EXPORT"

    # Observability
    ENABLE_OBSERVABILITY = "ENABLE_OBSERVABILITY"
    ENABLE_REQUEST_LOGGING = "ENABLE_REQUEST_LOGGING"
    ENABLE_SLOW_QUERY_LOG = "ENABLE_SLOW_QUERY_LOG"

    # Security
    ENABLE_RATE_LIMITING = "ENABLE_RATE_LIMITING"
    ENABLE_API_KEY_AUTH = "ENABLE_API_KEY_AUTH"


class FeatureFlagManager:
    """
    Evaluates state of feature flags based on:
    1. Environment variable overrides (highest priority)
    2. Environment-specific defaults (development, staging, production)
    3. Global fallback: False
    """

    def __init__(self, environment: str = "development") -> None:
        self.environment = environment

        # Environment-specific defaults.
        # "Flags with no env-specific default should be disabled (False)."
        self._defaults: dict[str, dict[FeatureFlag, bool]] = {
            "development": {
                FeatureFlag.ENABLE_SSE_STREAMING: True,
                FeatureFlag.ENABLE_SSE_HEARTBEAT: True,
                FeatureFlag.ENABLE_PARALLEL_SUMMARIZATION: True,
                FeatureFlag.ENABLE_AGENT_TIMELINE: True,
                FeatureFlag.ENABLE_AGENT_RETRY: True,
                FeatureFlag.ENABLE_RESEARCH_CACHE: True,
                FeatureFlag.ENABLE_QUERY_CACHE: True,
                FeatureFlag.ENABLE_MARKDOWN_EXPORT: True,
                FeatureFlag.ENABLE_OBSERVABILITY: True,
                FeatureFlag.ENABLE_REQUEST_LOGGING: True,
                FeatureFlag.ENABLE_SLOW_QUERY_LOG: True,
                FeatureFlag.ENABLE_RATE_LIMITING: False,
                FeatureFlag.ENABLE_API_KEY_AUTH: False,
                # Note: FeatureFlag.ENABLE_PDF_EXPORT has no dev-specific default entry -> defaults to False
            },
            "staging": {
                FeatureFlag.ENABLE_SSE_STREAMING: True,
                FeatureFlag.ENABLE_SSE_HEARTBEAT: True,
                FeatureFlag.ENABLE_PARALLEL_SUMMARIZATION: True,
                FeatureFlag.ENABLE_AGENT_TIMELINE: True,
                FeatureFlag.ENABLE_AGENT_RETRY: True,
                FeatureFlag.ENABLE_RESEARCH_CACHE: True,
                FeatureFlag.ENABLE_QUERY_CACHE: True,
                FeatureFlag.ENABLE_MARKDOWN_EXPORT: True,
                FeatureFlag.ENABLE_OBSERVABILITY: True,
                FeatureFlag.ENABLE_REQUEST_LOGGING: True,
                FeatureFlag.ENABLE_SLOW_QUERY_LOG: True,
                FeatureFlag.ENABLE_RATE_LIMITING: True,
                FeatureFlag.ENABLE_API_KEY_AUTH: False,
            },
            "production": {
                FeatureFlag.ENABLE_SSE_STREAMING: True,
                FeatureFlag.ENABLE_SSE_HEARTBEAT: True,
                FeatureFlag.ENABLE_PARALLEL_SUMMARIZATION: True,
                FeatureFlag.ENABLE_AGENT_TIMELINE: True,
                FeatureFlag.ENABLE_AGENT_RETRY: True,
                FeatureFlag.ENABLE_RESEARCH_CACHE: True,
                FeatureFlag.ENABLE_QUERY_CACHE: True,
                FeatureFlag.ENABLE_MARKDOWN_EXPORT: True,
                FeatureFlag.ENABLE_OBSERVABILITY: True,
                FeatureFlag.ENABLE_REQUEST_LOGGING: True,
                FeatureFlag.ENABLE_SLOW_QUERY_LOG: True,
                FeatureFlag.ENABLE_RATE_LIMITING: True,
                FeatureFlag.ENABLE_API_KEY_AUTH: True,
            },
        }

    def _parse_bool(self, val: str) -> bool:
        """Parse boolean string from environment variable."""
        return val.lower() in ("true", "1", "yes", "on")

    def is_enabled(self, flag: FeatureFlag | str) -> bool:
        """
        Check if a feature flag is enabled.
        Resolves overrides first, then env defaults, then global fallback.
        """
        # Convert string to FeatureFlag if needed (for safety and external integration)
        if isinstance(flag, str):
            try:
                flag = FeatureFlag(flag)
            except ValueError:
                return False

        # 1. Environment variable override
        env_val = os.getenv(flag.value)
        if env_val is not None:
            return self._parse_bool(env_val)

        # 2. Environment-specific default
        env_defaults = self._defaults.get(self.environment, {})
        if flag in env_defaults:
            return env_defaults[flag]

        # 3. Global fallback
        return False

    def get_all_flags(self) -> dict[str, bool]:
        """Get evaluated state of all defined feature flags."""
        return {flag.value: self.is_enabled(flag) for flag in FeatureFlag}

    def get_enabled_flags(self) -> list[str]:
        """Get list of values for all flags that are currently enabled."""
        return [flag.value for flag in FeatureFlag if self.is_enabled(flag)]

    def to_dict(self) -> dict[str, dict[str, bool]]:
        """Format flags as a dictionary matching frontend config expectations."""
        return {"flags": self.get_all_flags()}


# Initialize the application-wide singleton instance of the feature flags manager
try:
    _settings = get_settings()
    _env = _settings.app_env
except Exception:
    _env = "development"

feature_flags = FeatureFlagManager(environment=_env)
