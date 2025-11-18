"""Integration tests for API routes."""

import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from src.proxy.server import create_app


@pytest.fixture
def client():
    """Create test client with mocked dependencies."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_litellm_response():
    """Mock LiteLLM response."""
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "gpt-4",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a test response from the mocked LLM.",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        },
    }


@pytest.fixture
def mock_langfuse_client():
    """Mock LangFuse client."""
    client = MagicMock()
    client.enabled = True

    # Mock trace object
    trace = MagicMock()
    trace.id = "trace-test-123"
    client.create_trace.return_value = trace

    # Mock generation object
    generation = MagicMock()
    generation.id = "gen-test-123"
    client.create_generation.return_value = generation

    return client


class TestChatCompletionsSuccess:
    """Test successful chat completion scenarios."""

    @patch("src.proxy.routes.litellm.acompletion")
    def test_chat_completion_basic_success(self, mock_acompletion, client, mock_litellm_response):
        """Test basic chat completion request succeeds."""
        mock_acompletion.return_value = mock_litellm_response

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello, world!"}],
            "temperature": 0.7,
            "max_tokens": 100,
        }

        response = client.post("/v1/chat/completions", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert data["id"] == "chatcmpl-test123"
        assert data["object"] == "chat.completion"
        assert data["model"] == "gpt-4"
        assert len(data["choices"]) == 1
        assert data["choices"][0]["message"]["content"] == "This is a test response from the mocked LLM."
        assert data["usage"]["total_tokens"] == 30

        # Verify LiteLLM was called correctly
        mock_acompletion.assert_called_once()
        call_args = mock_acompletion.call_args
        assert call_args.kwargs["model"] == "gpt-4"
        assert call_args.kwargs["temperature"] == 0.7
        assert call_args.kwargs["max_tokens"] == 100

    @patch("src.proxy.routes.litellm.acompletion")
    def test_chat_completion_alternative_endpoint(self, mock_acompletion, client, mock_litellm_response):
        """Test chat completion on alternative endpoint /chat/completions."""
        mock_acompletion.return_value = mock_litellm_response

        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Test"}],
        }

        response = client.post("/chat/completions", json=payload)

        assert response.status_code == 200
        assert response.json()["model"] == "gpt-4"

    @patch("src.proxy.routes.litellm.acompletion")
    def test_chat_completion_with_custom_headers(self, mock_acompletion, client, mock_litellm_response):
        """Test chat completion with custom X-User-ID and X-Session-ID headers."""
        mock_acompletion.return_value = mock_litellm_response

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        headers = {
            "X-User-ID": "test-user-123",
            "X-Session-ID": "session-abc-456",
        }

        response = client.post("/v1/chat/completions", json=payload, headers=headers)

        assert response.status_code == 200

        # Verify headers are present in response
        assert "X-Trace-ID" in response.headers
        assert "X-Duration-Ms" in response.headers

    @patch("src.proxy.routes.litellm.acompletion")
    def test_chat_completion_with_metadata(self, mock_acompletion, client, mock_litellm_response):
        """Test chat completion with custom metadata."""
        mock_acompletion.return_value = mock_litellm_response

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
            "metadata": {
                "task_type": "code_generation",
                "language": "python",
            },
        }

        response = client.post("/v1/chat/completions", json=payload)

        assert response.status_code == 200

    @patch("src.proxy.routes.litellm.acompletion")
    def test_chat_completion_with_null_metadata(self, mock_acompletion, client, mock_litellm_response):
        """Test chat completion with null metadata (regression test)."""
        mock_acompletion.return_value = mock_litellm_response

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
            "metadata": None,
        }

        response = client.post("/v1/chat/completions", json=payload)

        # Should not raise "NoneType is not iterable" error
        assert response.status_code == 200

    @patch("src.proxy.routes.litellm.acompletion")
    def test_chat_completion_with_all_parameters(self, mock_acompletion, client, mock_litellm_response):
        """Test chat completion with all optional parameters."""
        mock_acompletion.return_value = mock_litellm_response

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
            "temperature": 0.8,
            "max_tokens": 500,
            "top_p": 0.9,
            "frequency_penalty": 0.5,
            "presence_penalty": 0.3,
            "stream": False,
            "user": "test-user",
        }

        response = client.post("/v1/chat/completions", json=payload)

        assert response.status_code == 200

        # Verify all parameters were passed to LiteLLM
        call_args = mock_acompletion.call_args
        assert call_args.kwargs["temperature"] == 0.8
        assert call_args.kwargs["max_tokens"] == 500
        assert call_args.kwargs["top_p"] == 0.9
        assert call_args.kwargs["frequency_penalty"] == 0.5
        assert call_args.kwargs["presence_penalty"] == 0.3
        assert call_args.kwargs["stream"] is False


class TestChatCompletionsWithLangFuse:
    """Test chat completion with LangFuse tracing."""

    @patch("src.proxy.routes.litellm.acompletion")
    def test_chat_completion_creates_langfuse_trace(
        self, mock_acompletion, client, mock_litellm_response, mock_langfuse_client
    ):
        """Test that chat completion creates LangFuse trace when enabled."""
        mock_acompletion.return_value = mock_litellm_response

        # Initialize app.state.langfuse_client first (set it before patching)
        client.app.state.langfuse_client = mock_langfuse_client

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        # Need to patch request.state to include langfuse_client
        with patch("src.proxy.routes.getattr", side_effect=lambda obj, name, default=None:
                  mock_langfuse_client if name == "langfuse_client" else default):
            response = client.post("/v1/chat/completions", json=payload)

        assert response.status_code == 200

    @patch("src.proxy.routes.litellm.acompletion")
    def test_chat_completion_langfuse_trace_with_metadata(
        self, mock_acompletion, client, mock_litellm_response, mock_langfuse_client
    ):
        """Test that LangFuse trace includes custom metadata."""
        mock_acompletion.return_value = mock_litellm_response

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
            "metadata": {
                "task_type": "code_review",
                "repository": "test-repo",
            },
        }

        with patch("src.proxy.routes.getattr", side_effect=lambda obj, name, default=None:
                  mock_langfuse_client if name == "langfuse_client" else default):
            response = client.post("/v1/chat/completions", json=payload)

        assert response.status_code == 200


class TestChatCompletionsErrors:
    """Test error handling in chat completions."""

    @patch("src.proxy.routes.litellm.acompletion")
    def test_chat_completion_litellm_error(self, mock_acompletion, client):
        """Test that LiteLLM errors are handled gracefully."""
        mock_acompletion.side_effect = Exception("API key not found")

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        response = client.post("/v1/chat/completions", json=payload)

        assert response.status_code == 500
        assert "API key not found" in response.json()["detail"]

    @patch("src.proxy.routes.litellm.acompletion")
    def test_chat_completion_authentication_error(self, mock_acompletion, client):
        """Test authentication error handling."""
        from openai import AuthenticationError
        from unittest.mock import MagicMock

        # Create mock response object for AuthenticationError
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.headers = {}

        mock_acompletion.side_effect = AuthenticationError(
            "Invalid API key",
            response=mock_response,
            body=None
        )

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        response = client.post("/v1/chat/completions", json=payload)

        assert response.status_code == 500
        assert "Invalid API key" in response.json()["detail"]

    def test_chat_completion_missing_required_fields(self, client):
        """Test validation error for missing required fields."""
        payload = {
            "model": "gpt-4",
            # Missing 'messages' field
        }

        response = client.post("/v1/chat/completions", json=payload)

        assert response.status_code == 422  # Validation error

    @patch("src.proxy.routes.litellm.acompletion")
    def test_chat_completion_empty_messages(self, mock_acompletion, client):
        """Test handling of empty messages array."""
        # LiteLLM will raise an error for empty messages
        mock_acompletion.side_effect = Exception("messages must not be empty")

        payload = {
            "model": "gpt-4",
            "messages": [],
        }

        response = client.post("/v1/chat/completions", json=payload)

        # Should return 500 error
        assert response.status_code == 500

    @patch("src.proxy.routes.litellm.acompletion")
    def test_chat_completion_invalid_model(self, mock_acompletion, client):
        """Test handling of invalid model name."""
        # LiteLLM will raise an error for invalid model
        mock_acompletion.side_effect = Exception("Invalid model specified")

        payload = {
            "model": "",
            "messages": [{"role": "user", "content": "Test"}],
        }

        response = client.post("/v1/chat/completions", json=payload)

        # Should return 500 error
        assert response.status_code == 500

    def test_chat_completion_malformed_json(self, client):
        """Test handling of malformed JSON."""
        response = client.post(
            "/v1/chat/completions",
            content='{"model": "gpt-4", "messages": [{"role": "user",}',
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422


class TestChatCompletionsMetrics:
    """Test metrics collection during chat completions."""

    @patch("src.proxy.routes.litellm.acompletion")
    @patch("src.proxy.routes.get_metrics_collector")
    def test_chat_completion_records_success_metrics(
        self, mock_get_metrics, mock_acompletion, client, mock_litellm_response
    ):
        """Test that successful requests record metrics."""
        mock_acompletion.return_value = mock_litellm_response
        mock_metrics = MagicMock()
        mock_get_metrics.return_value = mock_metrics

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        response = client.post("/v1/chat/completions", json=payload)

        assert response.status_code == 200

        # Verify metrics were recorded
        mock_metrics.inc_active_requests.assert_called_once_with("gpt-4", "openai")
        mock_metrics.dec_active_requests.assert_called_once_with("gpt-4", "openai")
        mock_metrics.record_request.assert_called_once()

        # Check that success metrics were recorded
        call_args = mock_metrics.record_request.call_args
        assert call_args.kwargs["model"] == "gpt-4"
        assert call_args.kwargs["provider"] == "openai"
        assert call_args.kwargs["status"] == "success"
        assert call_args.kwargs["prompt_tokens"] == 10
        assert call_args.kwargs["completion_tokens"] == 20
        assert call_args.kwargs["cost"] > 0

    @patch("src.proxy.routes.litellm.acompletion")
    @patch("src.proxy.routes.get_metrics_collector")
    def test_chat_completion_records_error_metrics(
        self, mock_get_metrics, mock_acompletion, client
    ):
        """Test that failed requests record error metrics."""
        mock_acompletion.side_effect = Exception("Test error")
        mock_metrics = MagicMock()
        mock_get_metrics.return_value = mock_metrics

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        response = client.post("/v1/chat/completions", json=payload)

        assert response.status_code == 500

        # Verify error metrics were recorded
        mock_metrics.record_error.assert_called_once()
        call_args = mock_metrics.record_error.call_args
        assert call_args[0][0] == "gpt-4"  # model
        assert call_args[0][1] == "openai"  # provider
        assert call_args[0][2] == "Exception"  # error type


class TestChatCompletionsCostCalculation:
    """Test cost calculation during chat completions."""

    @patch("src.proxy.routes.litellm.acompletion")
    @patch("src.proxy.routes.calculate_cost")
    def test_chat_completion_calculates_cost(
        self, mock_calculate_cost, mock_acompletion, client, mock_litellm_response
    ):
        """Test that cost is calculated for each request."""
        mock_acompletion.return_value = mock_litellm_response
        mock_calculate_cost.return_value = 0.00123

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        response = client.post("/v1/chat/completions", json=payload)

        assert response.status_code == 200

        # Verify cost calculation was called
        mock_calculate_cost.assert_called_once_with("gpt-4", 10, 20, "openai")

    @patch("src.proxy.routes.litellm.acompletion")
    def test_chat_completion_cost_for_different_models(
        self, mock_acompletion, client
    ):
        """Test cost calculation for different models."""
        models_to_test = [
            ("gpt-4", "openai"),
            ("gpt-3.5-turbo", "openai"),
            ("claude-3-opus", "anthropic"),
        ]

        for model, provider in models_to_test:
            mock_response = {
                "id": "test",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "Test"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            }
            mock_acompletion.return_value = mock_response

            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Test"}],
            }

            response = client.post("/v1/chat/completions", json=payload)

            # Should succeed for all models
            assert response.status_code == 200


class TestChatCompletionsResponseHeaders:
    """Test response headers in chat completions."""

    @patch("src.proxy.routes.litellm.acompletion")
    def test_chat_completion_includes_trace_id_header(
        self, mock_acompletion, client, mock_litellm_response
    ):
        """Test that response includes X-Trace-ID header."""
        mock_acompletion.return_value = mock_litellm_response

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        response = client.post("/v1/chat/completions", json=payload)

        assert response.status_code == 200
        assert "X-Trace-ID" in response.headers
        assert len(response.headers["X-Trace-ID"]) > 0

    @patch("src.proxy.routes.litellm.acompletion")
    def test_chat_completion_includes_duration_header(
        self, mock_acompletion, client, mock_litellm_response
    ):
        """Test that response includes X-Duration-Ms header."""
        mock_acompletion.return_value = mock_litellm_response

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
        }

        response = client.post("/v1/chat/completions", json=payload)

        assert response.status_code == 200
        assert "X-Duration-Ms" in response.headers
        assert int(response.headers["X-Duration-Ms"]) >= 0
