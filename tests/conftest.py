"""Shared pytest fixtures and configuration."""

import pytest
from prometheus_client import REGISTRY


@pytest.fixture(autouse=True)
def cleanup_prometheus_registry():
    """Clean up Prometheus registry between tests to avoid duplication errors."""
    # Get all registered collectors
    collectors_to_unregister = list(REGISTRY._collector_to_names.keys())

    # Unregister all non-default collectors
    for collector in collectors_to_unregister:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            # Ignore errors for collectors that can't be unregistered
            pass

    yield

    # Clean up after test
    collectors_to_unregister = list(REGISTRY._collector_to_names.keys())
    for collector in collectors_to_unregister:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass


@pytest.fixture
def reset_metrics_singleton():
    """Reset the global metrics collector singleton."""
    import src.monitoring.metrics as metrics_module

    original_collector = metrics_module._metrics_collector
    metrics_module._metrics_collector = None

    yield

    metrics_module._metrics_collector = original_collector
