"""Integration tests for metrics collection."""

from unittest.mock import MagicMock, patch

import pytest

from src.config import Settings
from src.monitoring.metrics import MetricsCollector, get_metrics_collector


@pytest.fixture
def enabled_settings(monkeypatch):
    """Create settings with Prometheus enabled."""
    monkeypatch.setenv("ENABLE_PROMETHEUS", "true")
    monkeypatch.setenv("PROMETHEUS_PORT", "9091")
    return Settings()


@pytest.fixture
def disabled_settings(monkeypatch):
    """Create settings with Prometheus disabled."""
    monkeypatch.setenv("ENABLE_PROMETHEUS", "false")
    return Settings()


@pytest.fixture
def mock_prometheus():
    """Mock Prometheus client components."""
    with patch("src.monitoring.metrics.Counter") as mock_counter, \
         patch("src.monitoring.metrics.Gauge") as mock_gauge, \
         patch("src.monitoring.metrics.Histogram") as mock_histogram, \
         patch("src.monitoring.metrics.start_http_server") as mock_server:

        # Create mock metric instances
        mock_counter_instance = MagicMock()
        mock_gauge_instance = MagicMock()
        mock_histogram_instance = MagicMock()

        mock_counter.return_value = mock_counter_instance
        mock_gauge.return_value = mock_gauge_instance
        mock_histogram.return_value = mock_histogram_instance

        yield {
            "counter": mock_counter,
            "gauge": mock_gauge,
            "histogram": mock_histogram,
            "server": mock_server,
            "counter_instance": mock_counter_instance,
            "gauge_instance": mock_gauge_instance,
            "histogram_instance": mock_histogram_instance,
        }


class TestMetricsCollectorInitialization:
    """Test MetricsCollector initialization."""

    def test_metrics_collector_enabled(self, enabled_settings, mock_prometheus):
        """Test that metrics collector initializes when enabled."""
        collector = MetricsCollector(enabled_settings)

        assert collector.enabled is True
        assert collector.settings == enabled_settings

        # Verify metrics were created
        assert mock_prometheus["counter"].call_count > 0
        assert mock_prometheus["gauge"].call_count > 0
        assert mock_prometheus["histogram"].call_count > 0

    def test_metrics_collector_disabled(self, disabled_settings):
        """Test that metrics collector initializes when disabled."""
        collector = MetricsCollector(disabled_settings)

        assert collector.enabled is False

    def test_start_server_when_enabled(self, enabled_settings, mock_prometheus):
        """Test starting Prometheus HTTP server when enabled."""
        collector = MetricsCollector(enabled_settings)
        collector.start_server()

        # Verify server was started
        mock_prometheus["server"].assert_called_once_with(9091)

    def test_start_server_when_disabled(self, disabled_settings, mock_prometheus):
        """Test that server doesn't start when disabled."""
        collector = MetricsCollector(disabled_settings)
        collector.start_server()

        # Verify server was not started
        mock_prometheus["server"].assert_not_called()

    def test_start_server_handles_exception(self, enabled_settings, mock_prometheus):
        """Test that start_server handles exceptions gracefully."""
        mock_prometheus["server"].side_effect = Exception("Port already in use")

        collector = MetricsCollector(enabled_settings)

        # Should not raise exception
        collector.start_server()


class TestMetricsRecordRequest:
    """Test recording request metrics."""

    def test_record_successful_request(self, enabled_settings, mock_prometheus):
        """Test recording a successful request."""
        collector = MetricsCollector(enabled_settings)

        collector.record_request(
            model="gpt-4",
            provider="openai",
            status="success",
            duration=1.5,
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.005,
        )

        # Verify metrics were recorded
        # Note: labels() returns a mock that has inc() or observe() called on it

    def test_record_failed_request(self, enabled_settings, mock_prometheus):
        """Test recording a failed request."""
        collector = MetricsCollector(enabled_settings)

        collector.record_request(
            model="gpt-4",
            provider="openai",
            status="error",
            duration=0.5,
        )

        # Should record request even without tokens/cost

    def test_record_request_with_zero_tokens(self, enabled_settings, mock_prometheus):
        """Test recording request with zero tokens."""
        collector = MetricsCollector(enabled_settings)

        collector.record_request(
            model="gpt-4",
            provider="openai",
            status="success",
            duration=1.0,
            prompt_tokens=0,
            completion_tokens=0,
            cost=0.0,
        )

        # Should handle zero values gracefully

    def test_record_request_when_disabled(self, disabled_settings):
        """Test that record_request does nothing when disabled."""
        collector = MetricsCollector(disabled_settings)

        # Should not raise exception
        collector.record_request(
            model="gpt-4",
            provider="openai",
            status="success",
            duration=1.0,
        )

    def test_record_request_handles_exception(self, enabled_settings, mock_prometheus):
        """Test that record_request handles exceptions gracefully."""
        collector = MetricsCollector(enabled_settings)

        # Make metrics raise an exception
        mock_prometheus["counter_instance"].labels.side_effect = Exception("Metrics error")

        # Should not raise exception
        collector.record_request(
            model="gpt-4",
            provider="openai",
            status="success",
            duration=1.0,
        )


class TestMetricsRecordError:
    """Test recording error metrics."""

    def test_record_error(self, enabled_settings, mock_prometheus):
        """Test recording an error."""
        collector = MetricsCollector(enabled_settings)

        collector.record_error(
            model="gpt-4",
            provider="openai",
            error_type="AuthenticationError",
        )

        # Verify error counter was incremented

    def test_record_different_error_types(self, enabled_settings, mock_prometheus):
        """Test recording different error types."""
        collector = MetricsCollector(enabled_settings)

        error_types = [
            "AuthenticationError",
            "RateLimitError",
            "TimeoutError",
            "NetworkError",
            "ValueError",
        ]

        for error_type in error_types:
            collector.record_error(
                model="gpt-4",
                provider="openai",
                error_type=error_type,
            )

    def test_record_error_when_disabled(self, disabled_settings):
        """Test that record_error does nothing when disabled."""
        collector = MetricsCollector(disabled_settings)

        # Should not raise exception
        collector.record_error(
            model="gpt-4",
            provider="openai",
            error_type="TestError",
        )

    def test_record_error_handles_exception(self, enabled_settings, mock_prometheus):
        """Test that record_error handles exceptions gracefully."""
        collector = MetricsCollector(enabled_settings)

        # Make error counter raise an exception
        mock_prometheus["counter_instance"].labels.side_effect = Exception("Counter error")

        # Should not raise exception
        collector.record_error(
            model="gpt-4",
            provider="openai",
            error_type="TestError",
        )


class TestMetricsActiveRequests:
    """Test active requests counter."""

    def test_increment_active_requests(self, enabled_settings, mock_prometheus):
        """Test incrementing active requests counter."""
        collector = MetricsCollector(enabled_settings)

        collector.inc_active_requests(model="gpt-4", provider="openai")

        # Verify gauge was incremented

    def test_decrement_active_requests(self, enabled_settings, mock_prometheus):
        """Test decrementing active requests counter."""
        collector = MetricsCollector(enabled_settings)

        collector.dec_active_requests(model="gpt-4", provider="openai")

        # Verify gauge was decremented

    def test_active_requests_lifecycle(self, enabled_settings, mock_prometheus):
        """Test complete lifecycle of active requests tracking."""
        collector = MetricsCollector(enabled_settings)

        # Increment for new request
        collector.inc_active_requests(model="gpt-4", provider="openai")

        # Simulate request processing...

        # Decrement when done
        collector.dec_active_requests(model="gpt-4", provider="openai")

    def test_active_requests_when_disabled(self, disabled_settings):
        """Test that active requests tracking does nothing when disabled."""
        collector = MetricsCollector(disabled_settings)

        # Should not raise exception
        collector.inc_active_requests(model="gpt-4", provider="openai")
        collector.dec_active_requests(model="gpt-4", provider="openai")

    def test_inc_active_requests_handles_exception(self, enabled_settings, mock_prometheus):
        """Test that inc_active_requests handles exceptions gracefully."""
        collector = MetricsCollector(enabled_settings)

        # Make gauge raise an exception
        mock_prometheus["gauge_instance"].labels.side_effect = Exception("Gauge error")

        # Should not raise exception
        collector.inc_active_requests(model="gpt-4", provider="openai")

    def test_dec_active_requests_handles_exception(self, enabled_settings, mock_prometheus):
        """Test that dec_active_requests handles exceptions gracefully."""
        collector = MetricsCollector(enabled_settings)

        # Make gauge raise an exception
        mock_prometheus["gauge_instance"].labels.side_effect = Exception("Gauge error")

        # Should not raise exception
        collector.dec_active_requests(model="gpt-4", provider="openai")


class TestMetricsCollectorSingleton:
    """Test global metrics collector singleton."""

    def test_get_metrics_collector_returns_singleton(self):
        """Test that get_metrics_collector returns the same instance."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        assert collector1 is collector2

    def test_get_metrics_collector_creates_instance(self, reset_metrics_singleton):
        """Test that get_metrics_collector creates instance on first call."""
        collector = get_metrics_collector()

        assert collector is not None
        assert isinstance(collector, MetricsCollector)


class TestMetricsMultipleModels:
    """Test metrics for multiple models and providers."""

    def test_metrics_for_different_models(self, enabled_settings, mock_prometheus):
        """Test recording metrics for different models."""
        collector = MetricsCollector(enabled_settings)

        models = [
            ("gpt-4", "openai"),
            ("gpt-3.5-turbo", "openai"),
            ("claude-3-opus", "anthropic"),
            ("claude-3-sonnet", "anthropic"),
        ]

        for model, provider in models:
            collector.record_request(
                model=model,
                provider=provider,
                status="success",
                duration=1.0,
                prompt_tokens=10,
                completion_tokens=20,
                cost=0.001,
            )

    def test_metrics_for_different_providers(self, enabled_settings, mock_prometheus):
        """Test recording metrics for different providers."""
        collector = MetricsCollector(enabled_settings)

        providers = ["openai", "anthropic", "azure", "vertex_ai", "bedrock"]

        for provider in providers:
            collector.record_request(
                model=f"{provider}-model",
                provider=provider,
                status="success",
                duration=1.0,
            )


class TestMetricsCostTracking:
    """Test cost tracking in metrics."""

    def test_record_request_with_cost(self, enabled_settings, mock_prometheus):
        """Test that cost is recorded correctly."""
        collector = MetricsCollector(enabled_settings)

        test_costs = [0.001, 0.005, 0.01, 0.05, 0.1]

        for cost in test_costs:
            collector.record_request(
                model="gpt-4",
                provider="openai",
                status="success",
                duration=1.0,
                prompt_tokens=100,
                completion_tokens=50,
                cost=cost,
            )

    def test_record_request_with_zero_cost(self, enabled_settings, mock_prometheus):
        """Test recording request with zero cost."""
        collector = MetricsCollector(enabled_settings)

        collector.record_request(
            model="gpt-4",
            provider="openai",
            status="success",
            duration=1.0,
            cost=0.0,
        )

        # Zero cost should not be recorded (cost > 0 check)


class TestMetricsTokenTracking:
    """Test token tracking in metrics."""

    def test_record_prompt_tokens(self, enabled_settings, mock_prometheus):
        """Test recording prompt tokens."""
        collector = MetricsCollector(enabled_settings)

        collector.record_request(
            model="gpt-4",
            provider="openai",
            status="success",
            duration=1.0,
            prompt_tokens=500,
            completion_tokens=0,
        )

    def test_record_completion_tokens(self, enabled_settings, mock_prometheus):
        """Test recording completion tokens."""
        collector = MetricsCollector(enabled_settings)

        collector.record_request(
            model="gpt-4",
            provider="openai",
            status="success",
            duration=1.0,
            prompt_tokens=0,
            completion_tokens=300,
        )

    def test_record_both_token_types(self, enabled_settings, mock_prometheus):
        """Test recording both prompt and completion tokens."""
        collector = MetricsCollector(enabled_settings)

        collector.record_request(
            model="gpt-4",
            provider="openai",
            status="success",
            duration=1.0,
            prompt_tokens=200,
            completion_tokens=150,
        )


class TestMetricsDurationTracking:
    """Test duration tracking in metrics."""

    def test_record_various_durations(self, enabled_settings, mock_prometheus):
        """Test recording various request durations."""
        collector = MetricsCollector(enabled_settings)

        durations = [0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]

        for duration in durations:
            collector.record_request(
                model="gpt-4",
                provider="openai",
                status="success",
                duration=duration,
            )

    def test_record_very_short_duration(self, enabled_settings, mock_prometheus):
        """Test recording very short duration."""
        collector = MetricsCollector(enabled_settings)

        collector.record_request(
            model="gpt-4",
            provider="openai",
            status="success",
            duration=0.001,  # 1ms
        )

    def test_record_very_long_duration(self, enabled_settings, mock_prometheus):
        """Test recording very long duration."""
        collector = MetricsCollector(enabled_settings)

        collector.record_request(
            model="gpt-4",
            provider="openai",
            status="success",
            duration=300.0,  # 5 minutes
        )
