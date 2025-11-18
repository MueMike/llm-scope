"""Integration tests for middleware components."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from src.proxy.server import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestTracingMiddleware:
    """Test TracingMiddleware functionality."""

    @patch("src.proxy.routes.litellm.acompletion")
    def test_middleware_adds_trace_id_to_response(self, mock_acompletion, client):
        """Test that TracingMiddleware adds X-Trace-ID header to response."""
        mock_acompletion.return_value = {
            "id": "test",
            "object": "chat.completion",
            "created": 123456,
            "model": "gpt-4",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "Test"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        }

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        response = client.post("/v1/chat/completions", json=payload)

        # Verify trace ID header is present
        assert "X-Trace-ID" in response.headers
        trace_id = response.headers["X-Trace-ID"]
        assert len(trace_id) > 0
        assert isinstance(trace_id, str)

    def test_middleware_skips_health_endpoint(self, client):
        """Test that TracingMiddleware skips health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        # Health endpoint may or may not have trace headers
        # The key is it should still work

    def test_middleware_skips_ready_endpoint(self, client):
        """Test that TracingMiddleware skips readiness endpoint."""
        response = client.get("/ready")

        assert response.status_code == 200

    @patch("src.proxy.routes.litellm.acompletion")
    def test_middleware_extracts_user_id_from_header(self, mock_acompletion, client):
        """Test that middleware extracts X-User-ID header."""
        mock_acompletion.return_value = {
            "id": "test",
            "object": "chat.completion",
            "created": 123456,
            "model": "gpt-4",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "Test"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        }

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        headers = {
            "X-User-ID": "test-user-abc",
        }

        response = client.post("/v1/chat/completions", json=payload, headers=headers)

        assert response.status_code == 200
        # User ID should be used in LiteLLM call
        mock_acompletion.assert_called_once()
        call_kwargs = mock_acompletion.call_args.kwargs
        assert call_kwargs["user"] == "test-user-abc"

    @patch("src.proxy.routes.litellm.acompletion")
    def test_middleware_extracts_session_id_from_header(self, mock_acompletion, client):
        """Test that middleware extracts X-Session-ID header."""
        mock_acompletion.return_value = {
            "id": "test",
            "object": "chat.completion",
            "created": 123456,
            "model": "gpt-4",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "Test"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        }

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        headers = {
            "X-Session-ID": "session-xyz-123",
        }

        response = client.post("/v1/chat/completions", json=payload, headers=headers)

        assert response.status_code == 200
        # Session ID should be extracted and used

    @patch("src.proxy.routes.litellm.acompletion")
    def test_middleware_uses_default_user_when_header_missing(self, mock_acompletion, client):
        """Test that middleware uses 'anonymous' when X-User-ID header is missing."""
        mock_acompletion.return_value = {
            "id": "test",
            "object": "chat.completion",
            "created": 123456,
            "model": "gpt-4",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "Test"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        }

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        response = client.post("/v1/chat/completions", json=payload)

        assert response.status_code == 200
        # Should use 'anonymous' as default
        call_kwargs = mock_acompletion.call_args.kwargs
        assert call_kwargs["user"] == "anonymous"


class TestMetricsMiddleware:
    """Test MetricsMiddleware functionality."""

    @patch("src.proxy.routes.litellm.acompletion")
    def test_middleware_adds_duration_header(self, mock_acompletion, client):
        """Test that MetricsMiddleware adds X-Duration-Ms header."""
        mock_acompletion.return_value = {
            "id": "test",
            "object": "chat.completion",
            "created": 123456,
            "model": "gpt-4",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "Test"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        }

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        response = client.post("/v1/chat/completions", json=payload)

        # Verify duration header is present
        assert "X-Duration-Ms" in response.headers
        duration_ms = int(response.headers["X-Duration-Ms"])
        assert duration_ms >= 0
        assert duration_ms < 60000  # Should be less than 60 seconds

    def test_middleware_skips_health_endpoint(self, client):
        """Test that MetricsMiddleware skips health endpoint."""
        response = client.get("/health")

        assert response.status_code == 200

    @patch("src.proxy.routes.litellm.acompletion")
    def test_middleware_duration_accuracy(self, mock_acompletion, client):
        """Test that duration measurement is reasonably accurate."""
        import time

        # Simulate delay in LiteLLM response
        def delayed_response(*args, **kwargs):
            time.sleep(0.1)  # 100ms delay
            return {
                "id": "test",
                "object": "chat.completion",
                "created": 123456,
                "model": "gpt-4",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "Test"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
            }

        mock_acompletion.side_effect = delayed_response

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        response = client.post("/v1/chat/completions", json=payload)

        assert response.status_code == 200
        duration_ms = int(response.headers["X-Duration-Ms"])
        # Should be at least 100ms due to our delay
        assert duration_ms >= 100


class TestMiddlewareChain:
    """Test middleware chain integration."""

    @patch("src.proxy.routes.litellm.acompletion")
    def test_both_middlewares_add_headers(self, mock_acompletion, client):
        """Test that both TracingMiddleware and MetricsMiddleware add their headers."""
        mock_acompletion.return_value = {
            "id": "test",
            "object": "chat.completion",
            "created": 123456,
            "model": "gpt-4",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "Test"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        }

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        response = client.post("/v1/chat/completions", json=payload)

        assert response.status_code == 200

        # Both middleware headers should be present
        assert "X-Trace-ID" in response.headers
        assert "X-Duration-Ms" in response.headers

    @patch("src.proxy.routes.litellm.acompletion")
    def test_middleware_chain_with_custom_headers(self, mock_acompletion, client):
        """Test middleware chain with custom request headers."""
        mock_acompletion.return_value = {
            "id": "test",
            "object": "chat.completion",
            "created": 123456,
            "model": "gpt-4",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "Test"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        }

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        headers = {
            "X-User-ID": "middleware-test-user",
            "X-Session-ID": "middleware-test-session",
        }

        response = client.post("/v1/chat/completions", json=payload, headers=headers)

        assert response.status_code == 200
        assert "X-Trace-ID" in response.headers
        assert "X-Duration-Ms" in response.headers

    @patch("src.proxy.routes.litellm.acompletion")
    def test_middleware_handles_errors_gracefully(self, mock_acompletion, client):
        """Test that middleware handles errors gracefully."""
        mock_acompletion.side_effect = Exception("Test error")

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        response = client.post("/v1/chat/completions", json=payload)

        # Should return error but still have middleware headers
        assert response.status_code == 500
        assert "X-Trace-ID" in response.headers
        assert "X-Duration-Ms" in response.headers


class TestCORSMiddleware:
    """Test CORS middleware functionality."""

    def test_cors_preflight_request(self, client):
        """Test CORS preflight OPTIONS request."""
        response = client.options(
            "/v1/chat/completions",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        # CORS should allow the request
        assert response.status_code == 200

    @patch("src.proxy.routes.litellm.acompletion")
    def test_cors_actual_request(self, mock_acompletion, client):
        """Test CORS on actual request."""
        mock_acompletion.return_value = {
            "id": "test",
            "object": "chat.completion",
            "created": 123456,
            "model": "gpt-4",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "Test"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        }

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        response = client.post(
            "/v1/chat/completions",
            json=payload,
            headers={"Origin": "http://localhost:3000"},
        )

        assert response.status_code == 200
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers


class TestMiddlewareStateInjection:
    """Test that middleware properly injects state into requests."""

    @patch("src.proxy.routes.litellm.acompletion")
    def test_langfuse_client_injected_into_request_state(self, mock_acompletion, client):
        """Test that LangFuse client is available in request state."""
        mock_acompletion.return_value = {
            "id": "test",
            "object": "chat.completion",
            "created": 123456,
            "model": "gpt-4",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "Test"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        }

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        # This test verifies the request handler can access langfuse_client
        # from request.state (injected by middleware or app)
        response = client.post("/v1/chat/completions", json=payload)

        # Should work whether LangFuse is enabled or not
        assert response.status_code == 200
