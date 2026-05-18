# ============================================
# Deep Research Platform - Feature Flag Unit Tests
# ============================================

from __future__ import annotations

from app.core.feature_flags import FeatureFlag, FeatureFlagManager


def test_flag_disabled_by_default():
    """Flags with no env-specific default should be disabled."""
    mgr = FeatureFlagManager(environment="development")
    # PDF export has no default entry → should default to False
    assert mgr.is_enabled(FeatureFlag.ENABLE_PDF_EXPORT) is False


def test_flag_env_specific_default():
    """Production-only flags should be off in development."""
    mgr = FeatureFlagManager(environment="development")
    assert mgr.is_enabled(FeatureFlag.ENABLE_RATE_LIMITING) is False

    mgr_prod = FeatureFlagManager(environment="production")
    assert mgr_prod.is_enabled(FeatureFlag.ENABLE_RATE_LIMITING) is True


def test_env_var_overrides_default(monkeypatch):
    """Environment variable should override the env-specific default."""
    monkeypatch.setenv("ENABLE_RATE_LIMITING", "true")
    mgr = FeatureFlagManager(environment="development")
    assert mgr.is_enabled(FeatureFlag.ENABLE_RATE_LIMITING) is True


def test_get_all_flags_returns_all():
    """get_all_flags() must return an entry for every FeatureFlag enum member."""
    mgr = FeatureFlagManager(environment="development")
    all_flags = mgr.get_all_flags()
    for flag in FeatureFlag:
        assert flag.value in all_flags


def test_get_enabled_flags():
    """get_enabled_flags() should only include flags that are True."""
    mgr = FeatureFlagManager(environment="development")
    enabled = mgr.get_enabled_flags()
    for flag_name in enabled:
        assert mgr.is_enabled(FeatureFlag(flag_name)) is True
