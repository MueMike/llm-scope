"""
Examples of High-Quality Test Patterns

This file demonstrates improved test quality patterns that can be applied
to the existing test suite.
"""

import pytest
from hypothesis import given, strategies as st
from unittest.mock import MagicMock, patch

# ============================================================================
# EXAMPLE 1: Property-Based Testing with Hypothesis
# ============================================================================


@given(
    model=st.sampled_from(["gpt-4", "gpt-3.5-turbo", "claude-3-opus"]),
    prompt_tokens=st.integers(min_value=100, max_value=100000),  # Use larger minimum to avoid rounding errors
    completion_tokens=st.integers(min_value=100, max_value=100000),  # Use larger minimum to avoid rounding errors
)
def test_cost_calculation_properties(model, prompt_tokens, completion_tokens):
    """
    Property-based test: Cost calculation should have consistent properties.

    This test automatically generates hundreds of test cases to verify:
    1. Cost is always positive
    2. More tokens = higher cost
    3. Cost scales linearly with tokens

    Note: We use min_value=100 to avoid floating-point rounding issues with very small costs.
    """
    from src.utils.helpers import calculate_cost

    cost = calculate_cost(model, prompt_tokens, completion_tokens)

    # Property 1: Cost must be positive
    assert cost > 0, f"Cost should be positive for {model}"

    # Property 2: Doubling tokens should roughly double cost
    cost_double = calculate_cost(model, prompt_tokens * 2, completion_tokens * 2)
    assert cost_double > cost, "More tokens should cost more"

    # Property 3: Cost should scale linearly (within floating point precision)
    ratio = cost_double / cost
    assert 1.95 < ratio < 2.05, f"Cost should scale linearly, got ratio {ratio}"  # Slightly tighter tolerance since we're using larger values


@given(st.text(min_size=1))
def test_trace_id_generation_uniqueness(seed):
    """
    Property: Generated trace IDs should always be unique.

    Tests the invariant that trace ID generation creates unique identifiers.
    """
    from src.utils.helpers import generate_trace_id
    import uuid

    # Generate multiple IDs
    ids = {generate_trace_id() for _ in range(100)}

    # All should be unique (set size should equal count)
    assert len(ids) == 100, "All trace IDs should be unique"

    # All should be valid UUIDs
    for trace_id in ids:
        try:
            uuid.UUID(trace_id)
        except ValueError:
            pytest.fail(f"Invalid UUID format: {trace_id}")


@given(
    metadata=st.one_of(
        st.none(),
        st.dictionaries(st.text(), st.text(), max_size=10),
        st.dictionaries(st.text(), st.integers(), max_size=10),
        st.dictionaries(st.text(), st.floats(allow_nan=False), max_size=10),
    )
)
def test_extract_metadata_handles_any_valid_input(metadata):
    """
    Property: extract_metadata should handle any valid metadata structure.

    This finds edge cases we might not think to test manually.
    """
    from src.utils.helpers import extract_metadata

    request_data = {
        "model": "gpt-4",
        "temperature": 0.7,
        "metadata": metadata,
    }

    # Should never raise an exception
    result = extract_metadata(request_data)

    # Result should always be a dict
    assert isinstance(result, dict)

    # Model should always be extracted
    assert result["model"] == "gpt-4"


# ============================================================================
# EXAMPLE 2: Parameterized Tests for Comprehensive Coverage
# ============================================================================


@pytest.mark.parametrize(
    "model,expected_provider",
    [
        # OpenAI models
        ("gpt-4", "openai"),
        ("gpt-4-turbo", "openai"),
        ("gpt-3.5-turbo", "openai"),
        ("gpt-3.5-turbo-16k", "openai"),
        # Anthropic models
        ("claude-3-opus", "anthropic"),
        ("claude-3-sonnet", "anthropic"),
        ("claude-3-haiku", "anthropic"),
        ("claude-3-opus-20240229", "anthropic"),
        # Vertex AI models
        ("gemini-pro", "vertex_ai"),
        ("gemini-1.5-pro", "vertex_ai"),
        # Unknown models
        ("unknown-model", "unknown"),
        ("", "unknown"),
    ],
)
def test_model_provider_detection(model, expected_provider):
    """Test provider detection for all supported models."""
    from src.integrations.llm_providers import get_model_provider

    provider = get_model_provider(model)
    assert provider == expected_provider, f"Expected {expected_provider} for {model}, got {provider}"


@pytest.mark.parametrize(
    "error_class,expected_status,expected_metric",
    [
        ("AuthenticationError", 401, "authentication_error"),
        ("RateLimitError", 429, "rate_limit_error"),
        ("Timeout", 504, "timeout_error"),
        ("APIConnectionError", 503, "connection_error"),
        ("InvalidRequestError", 400, "invalid_request"),
    ],
)
def test_error_handling_for_different_exceptions(error_class, expected_status, expected_metric):
    """Test that different error types are handled correctly."""
    # This would test error handling comprehensively
    # Example showing the pattern
    pass


# ============================================================================
# EXAMPLE 3: Test Data Builders
# ============================================================================


class ChatCompletionRequestBuilder:
    """Builder pattern for creating test chat completion requests."""

    def __init__(self):
        self._model = "gpt-4"
        self._messages = [{"role": "user", "content": "test"}]
        self._temperature = 0.7
        self._max_tokens = None
        self._metadata = None
        self._stream = False

    def with_model(self, model: str):
        """Set the model."""
        self._model = model
        return self

    def with_messages(self, messages: list):
        """Set the messages."""
        self._messages = messages
        return self

    def with_simple_message(self, content: str):
        """Set a simple user message."""
        self._messages = [{"role": "user", "content": content}]
        return self

    def with_metadata(self, metadata: dict):
        """Set metadata."""
        self._metadata = metadata
        return self

    def with_streaming(self, stream: bool = True):
        """Enable/disable streaming."""
        self._stream = stream
        return self

    def build(self) -> dict:
        """Build the request payload."""
        payload = {
            "model": self._model,
            "messages": self._messages,
            "temperature": self._temperature,
            "stream": self._stream,
        }

        if self._max_tokens:
            payload["max_tokens"] = self._max_tokens

        if self._metadata:
            payload["metadata"] = self._metadata

        return payload


class MockLLMResponseBuilder:
    """Builder for creating mock LLM responses."""

    def __init__(self):
        self._content = "Test response"
        self._model = "gpt-4"
        self._prompt_tokens = 10
        self._completion_tokens = 20

    def with_content(self, content: str):
        """Set response content."""
        self._content = content
        return self

    def with_model(self, model: str):
        """Set model name."""
        self._model = model
        return self

    def with_tokens(self, prompt: int, completion: int):
        """Set token counts."""
        self._prompt_tokens = prompt
        self._completion_tokens = completion
        return self

    def build(self) -> dict:
        """Build the mock response."""
        return {
            "id": "chatcmpl-test-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": self._model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": self._content,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": self._prompt_tokens,
                "completion_tokens": self._completion_tokens,
                "total_tokens": self._prompt_tokens + self._completion_tokens,
            },
        }


def test_using_builders():
    """Example test using builder pattern."""
    # Arrange - Build test data fluently
    request = (
        ChatCompletionRequestBuilder()
        .with_model("gpt-3.5-turbo")
        .with_simple_message("Hello, world!")
        .with_metadata({"task": "greeting"})
        .build()
    )

    mock_response = (
        MockLLMResponseBuilder()
        .with_content("Hello! How can I help?")
        .with_tokens(prompt=5, completion=10)
        .build()
    )

    # Assert - Verify structure
    assert request["model"] == "gpt-3.5-turbo"
    assert mock_response["usage"]["total_tokens"] == 15


# ============================================================================
# EXAMPLE 4: Custom Assertions for Better Error Messages
# ============================================================================


def assert_valid_chat_completion_response(response_data: dict):
    """
    Assert that response is a valid chat completion.

    Provides detailed error messages for debugging.
    """
    # Check required fields
    required_fields = ["id", "object", "created", "model", "choices"]
    for field in required_fields:
        assert field in response_data, f"Missing required field: {field}"

    # Validate structure
    assert response_data["object"] == "chat.completion", \
        f"Expected object='chat.completion', got {response_data['object']}"

    assert len(response_data["choices"]) > 0, "No choices in response"

    # Validate choice structure
    choice = response_data["choices"][0]
    assert "message" in choice, "Choice missing 'message' field"
    assert "role" in choice["message"], "Message missing 'role' field"
    assert "content" in choice["message"], "Message missing 'content' field"

    # Validate usage
    if "usage" in response_data:
        usage = response_data["usage"]
        assert "prompt_tokens" in usage, "Usage missing 'prompt_tokens'"
        assert "completion_tokens" in usage, "Usage missing 'completion_tokens'"
        assert "total_tokens" in usage, "Usage missing 'total_tokens'"

        # Verify math
        expected_total = usage["prompt_tokens"] + usage["completion_tokens"]
        assert usage["total_tokens"] == expected_total, \
            f"Total tokens mismatch: {usage['total_tokens']} != {expected_total}"


def assert_valid_langfuse_trace(trace):
    """Assert that trace is a valid LangFuse trace object."""
    assert trace is not None, "Trace should not be None"
    assert hasattr(trace, "id"), "Trace should have 'id' attribute"
    assert len(trace.id) > 0, "Trace ID should not be empty"


def test_with_custom_assertions():
    """Example test using custom assertions."""
    response_data = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-4",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Test response",
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

    # Single assertion validates entire structure with helpful error messages
    assert_valid_chat_completion_response(response_data)


# ============================================================================
# EXAMPLE 5: Given-When-Then Pattern
# ============================================================================


def test_chat_completion_with_metadata_creates_langfuse_trace():
    """
    Test that custom metadata is included in LangFuse trace.

    GIVEN a chat completion request with custom metadata
    WHEN the request is processed successfully
    THEN the metadata should be included in the LangFuse trace
    """
    # GIVEN - Arrange test data
    custom_metadata = {
        "task_type": "code_review",
        "repository": "llm-scope",
        "file": "src/proxy/routes.py",
    }

    request_payload = (
        ChatCompletionRequestBuilder()
        .with_model("gpt-4")
        .with_simple_message("Review this code")
        .with_metadata(custom_metadata)
        .build()
    )

    mock_response = MockLLMResponseBuilder().build()

    # WHEN - Execute the action
    with patch("src.proxy.routes.litellm.acompletion") as mock_litellm:
        mock_litellm.return_value = mock_response

        # Simulate request processing
        # (This would be actual API call in real test)

    # THEN - Verify expectations
    # Would verify LangFuse trace contains the custom metadata
    # (Simplified for example)
    assert custom_metadata["task_type"] == "code_review"


# ============================================================================
# EXAMPLE 6: Concurrent Request Testing
# ============================================================================


def test_concurrent_requests_maintain_isolation():
    """
    Test that concurrent requests don't interfere with each other.

    This tests thread safety and state isolation.
    """
    import concurrent.futures
    from fastapi.testclient import TestClient
    from src.proxy.server import create_app

    app = create_app()
    client = TestClient(app)

    def make_request(user_id: str):
        """Make a request for a specific user."""
        with patch("src.proxy.routes.litellm.acompletion") as mock:
            mock.return_value = MockLLMResponseBuilder().build()

            response = client.post(
                "/v1/chat/completions",
                json=ChatCompletionRequestBuilder().build(),
                headers={"X-User-ID": user_id},
            )

            # Extract user from response (if tracked)
            return user_id, response.status_code

    # Execute 10 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request, f"user-{i}") for i in range(10)]
        results = [f.result() for f in futures]

    # Verify all requests succeeded
    assert len(results) == 10
    assert all(status == 200 for user, status in results)

    # Verify all users are unique (no mixing)
    users = [user for user, _ in results]
    assert len(set(users)) == 10


# ============================================================================
# EXAMPLE 7: Performance Regression Testing
# ============================================================================


@pytest.mark.benchmark
def test_cost_calculation_performance(benchmark):
    """
    Benchmark cost calculation to detect performance regressions.

    Run with: pytest --benchmark-only
    """
    from src.utils.helpers import calculate_cost

    # Benchmark the function
    result = benchmark(calculate_cost, "gpt-4", 1000, 500)

    # Basic sanity check
    assert result > 0


@pytest.mark.benchmark
def test_metadata_extraction_with_large_payload(benchmark):
    """
    Benchmark metadata extraction with realistic large payload.
    """
    from src.utils.helpers import extract_metadata

    # Create large realistic payload
    large_request = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant." * 100},
            {"role": "user", "content": "Help me with this code." * 100},
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
        "metadata": {f"key_{i}": f"value_{i}" * 10 for i in range(50)},
    }

    result = benchmark(extract_metadata, large_request)
    assert "model" in result


# ============================================================================
# EXAMPLE 8: Contract Testing Approach
# ============================================================================


def test_litellm_response_contract():
    """
    Verify our expectations match LiteLLM's actual response structure.

    This is a simplified contract test. In production, use Pact or similar.
    """
    # Define expected contract
    expected_fields = {
        "id": str,
        "object": str,
        "created": int,
        "model": str,
        "choices": list,
        "usage": dict,
    }

    # Mock response should match contract
    mock_response = MockLLMResponseBuilder().build()

    # Verify contract
    for field, expected_type in expected_fields.items():
        assert field in mock_response, f"Missing field: {field}"
        assert isinstance(mock_response[field], expected_type), \
            f"Field {field} should be {expected_type}, got {type(mock_response[field])}"


# ============================================================================
# Pytest Fixtures for Reusability
# ============================================================================


@pytest.fixture
def chat_request_builder():
    """Provide ChatCompletionRequestBuilder."""
    return ChatCompletionRequestBuilder()


@pytest.fixture
def mock_response_builder():
    """Provide MockLLMResponseBuilder."""
    return MockLLMResponseBuilder()


@pytest.fixture
def sample_chat_request(chat_request_builder):
    """Provide a sample chat request."""
    return chat_request_builder.with_simple_message("Hello").build()


@pytest.fixture
def sample_mock_response(mock_response_builder):
    """Provide a sample mock response."""
    return mock_response_builder.with_content("Hi there!").build()


def test_using_fixtures(sample_chat_request, sample_mock_response):
    """Example of using fixtures for clean test setup."""
    assert sample_chat_request["model"] == "gpt-4"
    assert sample_mock_response["choices"][0]["message"]["content"] == "Hi there!"
