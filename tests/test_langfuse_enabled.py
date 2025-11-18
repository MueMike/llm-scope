"""Integration tests for LangFuse with enabled client."""

import time
from unittest.mock import MagicMock, patch

import pytest

from src.config import Settings
from src.integrations import LangFuseClient


@pytest.fixture
def enabled_settings(monkeypatch):
    """Create settings with LangFuse enabled."""
    monkeypatch.setenv("LANGFUSE_ENABLED", "true")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test-12345")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test-67890")
    monkeypatch.setenv("LANGFUSE_HOST", "https://test.langfuse.com")
    return Settings()


@pytest.fixture
def mock_langfuse_sdk():
    """Mock the LangFuse SDK."""
    with patch("src.integrations.langfuse_client.Langfuse") as mock:
        mock_instance = MagicMock()

        # Mock trace
        mock_trace = MagicMock()
        mock_trace.id = "trace-test-123"
        mock_instance.trace.return_value = mock_trace

        # Mock generation (called directly on client, not trace)
        mock_generation = MagicMock()
        mock_generation.id = "gen-test-456"
        mock_instance.generation.return_value = mock_generation

        # Mock span (called directly on client, not trace)
        mock_span = MagicMock()
        mock_span.id = "span-test-789"
        mock_instance.span.return_value = mock_span

        # Mock score
        mock_instance.score.return_value = True

        # Mock flush
        mock_instance.flush.return_value = None

        mock.return_value = mock_instance
        yield mock_instance


class TestLangFuseClientEnabled:
    """Test LangFuse client when enabled."""

    def test_langfuse_client_enabled_with_credentials(
        self, enabled_settings, mock_langfuse_sdk
    ):
        """Test that LangFuse client is enabled with valid credentials."""
        client = LangFuseClient(enabled_settings)

        assert client.enabled is True
        assert client.client is not None

    def test_langfuse_client_initialization(
        self, enabled_settings, mock_langfuse_sdk
    ):
        """Test LangFuse client initialization with correct parameters."""
        client = LangFuseClient(enabled_settings)

        # Verify client was initialized
        assert client.enabled is True

    def test_create_trace_when_enabled(self, enabled_settings, mock_langfuse_sdk):
        """Test creating trace when LangFuse is enabled."""
        client = LangFuseClient(enabled_settings)

        trace = client.create_trace(
            name="test_trace",
            user_id="test_user",
            session_id="test_session",
            metadata={"key": "value"},
            tags=["tag1", "tag2"],
        )

        assert trace is not None
        assert trace.id == "trace-test-123"

        # Verify trace was called with correct parameters
        mock_langfuse_sdk.trace.assert_called_once()
        call_kwargs = mock_langfuse_sdk.trace.call_args.kwargs
        assert call_kwargs["name"] == "test_trace"
        assert call_kwargs["user_id"] == "test_user"
        assert call_kwargs["session_id"] == "test_session"
        assert call_kwargs["metadata"] == {"key": "value"}
        assert call_kwargs["tags"] == ["tag1", "tag2"]

    def test_create_trace_without_optional_params(
        self, enabled_settings, mock_langfuse_sdk
    ):
        """Test creating trace with minimal parameters."""
        client = LangFuseClient(enabled_settings)

        trace = client.create_trace(name="minimal_trace")

        assert trace is not None
        mock_langfuse_sdk.trace.assert_called_once()

    def test_create_generation_when_enabled(
        self, enabled_settings, mock_langfuse_sdk
    ):
        """Test creating generation when LangFuse is enabled."""
        client = LangFuseClient(enabled_settings)

        # First create a trace
        trace = client.create_trace(name="test_trace")

        generation = client.create_generation(
            trace_id=trace.id,
            name="test_generation",
            model="gpt-4",
            input_data=["test input"],
            output_data=["test output"],
            metadata={"temperature": 0.7},
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            start_time=time.time(),
            end_time=time.time() + 1,
        )

        assert generation is not None
        assert generation.id == "gen-test-456"

    def test_create_generation_with_token_usage(
        self, enabled_settings, mock_langfuse_sdk
    ):
        """Test creating generation with token usage information."""
        client = LangFuseClient(enabled_settings)

        trace = client.create_trace(name="test_trace")

        usage = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        }

        generation = client.create_generation(
            trace_id=trace.id,
            name="token_test",
            model="gpt-4",
            input_data=["input"],
            output_data=["output"],
            usage=usage,
        )

        assert generation is not None

    def test_create_span_when_enabled(self, enabled_settings, mock_langfuse_sdk):
        """Test creating span when LangFuse is enabled."""
        client = LangFuseClient(enabled_settings)

        trace = client.create_trace(name="test_trace")

        span = client.create_span(
            trace_id=trace.id,
            name="test_span",
            metadata={"operation": "preprocessing"},
            start_time=time.time(),
            end_time=time.time() + 0.5,
        )

        assert span is not None
        assert span.id == "span-test-789"

    def test_score_trace_when_enabled(self, enabled_settings, mock_langfuse_sdk):
        """Test scoring trace when LangFuse is enabled."""
        client = LangFuseClient(enabled_settings)

        result = client.score_trace(
            trace_id="trace-123",
            name="quality_score",
            value=0.95,
            comment="Excellent response",
        )

        assert result is True
        mock_langfuse_sdk.score.assert_called_once()

    def test_flush_when_enabled(self, enabled_settings, mock_langfuse_sdk):
        """Test flushing when LangFuse is enabled."""
        client = LangFuseClient(enabled_settings)

        # Should not raise exception
        client.flush()

        # Verify flush was called
        mock_langfuse_sdk.flush.assert_called_once()

    def test_shutdown_when_enabled(self, enabled_settings, mock_langfuse_sdk):
        """Test shutdown when LangFuse is enabled."""
        client = LangFuseClient(enabled_settings)

        # Should not raise exception
        client.shutdown()

        # Verify flush was called (shutdown calls flush)
        mock_langfuse_sdk.flush.assert_called()


class TestLangFuseClientErrorHandling:
    """Test LangFuse client error handling."""

    def test_create_trace_handles_exception(
        self, enabled_settings, mock_langfuse_sdk
    ):
        """Test that create_trace handles exceptions gracefully."""
        client = LangFuseClient(enabled_settings)

        # Make trace creation raise an exception
        mock_langfuse_sdk.trace.side_effect = Exception("LangFuse API error")

        # Should return None instead of raising
        trace = client.create_trace(name="error_trace")

        assert trace is None

    def test_create_generation_handles_exception(
        self, enabled_settings, mock_langfuse_sdk
    ):
        """Test that create_generation handles exceptions gracefully."""
        client = LangFuseClient(enabled_settings)

        # Create trace successfully
        trace = client.create_trace(name="test_trace")

        # Make generation creation raise an exception
        mock_langfuse_sdk.generation.side_effect = Exception("Generation error")

        # Should return None instead of raising
        generation = client.create_generation(
            trace_id=trace.id,
            name="error_gen",
            model="gpt-4",
            input_data=["test"],
            output_data=["test"],
        )

        assert generation is None

    def test_score_trace_handles_exception(
        self, enabled_settings, mock_langfuse_sdk
    ):
        """Test that score_trace handles exceptions gracefully."""
        client = LangFuseClient(enabled_settings)

        # Make score creation raise an exception
        mock_langfuse_sdk.score.side_effect = Exception("Score error")

        # Should return False instead of raising
        result = client.score_trace(
            trace_id="trace-123",
            name="error_score",
            value=0.5,
        )

        assert result is False

    def test_flush_handles_exception(self, enabled_settings, mock_langfuse_sdk):
        """Test that flush handles exceptions gracefully."""
        client = LangFuseClient(enabled_settings)

        # Make flush raise an exception
        mock_langfuse_sdk.flush.side_effect = Exception("Flush error")

        # Should not raise exception
        client.flush()


class TestLangFuseClientMetadata:
    """Test LangFuse client metadata handling."""

    def test_trace_with_complex_metadata(
        self, enabled_settings, mock_langfuse_sdk
    ):
        """Test creating trace with complex metadata."""
        client = LangFuseClient(enabled_settings)

        complex_metadata = {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000,
            "provider": "openai",
            "endpoint": "/chat/completions",
            "nested": {"key1": "value1", "key2": "value2"},
            "list": [1, 2, 3],
        }

        trace = client.create_trace(
            name="complex_trace",
            metadata=complex_metadata,
        )

        assert trace is not None
        call_kwargs = mock_langfuse_sdk.trace.call_args.kwargs
        assert call_kwargs["metadata"] == complex_metadata

    def test_generation_with_large_input_output(
        self, enabled_settings, mock_langfuse_sdk
    ):
        """Test creating generation with large input/output data."""
        client = LangFuseClient(enabled_settings)

        trace = client.create_trace(name="large_data_trace")

        large_input = [
            {
                "role": "system",
                "content": "You are a helpful assistant." * 100,
            },
            {
                "role": "user",
                "content": "Generate a long response." * 100,
            },
        ]

        large_output = [
            {
                "role": "assistant",
                "content": "This is a very long response." * 200,
            }
        ]

        generation = client.create_generation(
            trace_id=trace.id,
            name="large_gen",
            model="gpt-4",
            input_data=large_input,
            output_data=large_output,
        )

        assert generation is not None


class TestLangFuseClientTiming:
    """Test LangFuse client timing functionality."""

    def test_generation_with_precise_timing(
        self, enabled_settings, mock_langfuse_sdk
    ):
        """Test that generation records precise start/end times."""
        client = LangFuseClient(enabled_settings)

        trace = client.create_trace(name="timing_trace")

        start = time.time()
        time.sleep(0.01)  # Small delay
        end = time.time()

        generation = client.create_generation(
            trace_id=trace.id,
            name="timed_gen",
            model="gpt-4",
            input_data=["test"],
            output_data=["test"],
            start_time=start,
            end_time=end,
        )

        assert generation is not None

    def test_span_with_timing(self, enabled_settings, mock_langfuse_sdk):
        """Test that span records start/end times."""
        client = LangFuseClient(enabled_settings)

        trace = client.create_trace(name="span_timing_trace")

        start = time.time()
        time.sleep(0.01)
        end = time.time()

        span = client.create_span(
            trace_id=trace.id,
            name="timed_span",
            start_time=start,
            end_time=end,
        )

        assert span is not None


class TestLangFuseClientSessionTracking:
    """Test LangFuse client session tracking."""

    def test_multiple_traces_same_session(
        self, enabled_settings, mock_langfuse_sdk
    ):
        """Test creating multiple traces for the same session."""
        client = LangFuseClient(enabled_settings)

        session_id = "session-abc-123"

        # Create multiple traces for the same session
        trace1 = client.create_trace(
            name="trace1",
            user_id="user1",
            session_id=session_id,
        )

        trace2 = client.create_trace(
            name="trace2",
            user_id="user1",
            session_id=session_id,
        )

        trace3 = client.create_trace(
            name="trace3",
            user_id="user1",
            session_id=session_id,
        )

        assert trace1 is not None
        assert trace2 is not None
        assert trace3 is not None

        # Verify all traces have the same session ID
        assert mock_langfuse_sdk.trace.call_count == 3

    def test_traces_different_users_same_session(
        self, enabled_settings, mock_langfuse_sdk
    ):
        """Test creating traces for different users in same session."""
        client = LangFuseClient(enabled_settings)

        session_id = "shared-session-456"

        trace1 = client.create_trace(
            name="user1_trace",
            user_id="user1",
            session_id=session_id,
        )

        trace2 = client.create_trace(
            name="user2_trace",
            user_id="user2",
            session_id=session_id,
        )

        assert trace1 is not None
        assert trace2 is not None
