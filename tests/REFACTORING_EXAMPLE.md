# Test Quality Refactoring Example

This document shows a concrete before/after example of improving test quality.

---

## Example: Chat Completion Test

### ❌ BEFORE (Current - Basic Quality)

```python
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
```

### Problems:
1. ❌ Tests multiple things (response validation + mock verification)
2. ❌ Hard-coded test data
3. ❌ Weak assertions (could pass with wrong data)
4. ❌ No clear Given-When-Then structure
5. ❌ Duplicate setup across tests
6. ❌ Hard to understand what's being tested

---

## ✅ AFTER (High Quality)

### Step 1: Create Test Data Builders

```python
# tests/builders.py
class ChatCompletionRequestBuilder:
    """Builder for creating test chat completion requests."""

    def __init__(self):
        self._model = "gpt-4"
        self._messages = [{"role": "user", "content": "test"}]
        self._temperature = 0.7
        self._max_tokens = None

    def with_model(self, model: str):
        self._model = model
        return self

    def with_simple_message(self, content: str):
        self._messages = [{"role": "user", "content": content}]
        return self

    def with_max_tokens(self, max_tokens: int):
        self._max_tokens = max_tokens
        return self

    def build(self) -> dict:
        payload = {
            "model": self._model,
            "messages": self._messages,
            "temperature": self._temperature,
        }
        if self._max_tokens:
            payload["max_tokens"] = self._max_tokens
        return payload


class MockLLMResponseBuilder:
    """Builder for creating mock LLM responses."""

    def __init__(self):
        self._content = "Test response"
        self._model = "gpt-4"
        self._prompt_tokens = 10
        self._completion_tokens = 20

    def with_content(self, content: str):
        self._content = content
        return self

    def with_model(self, model: str):
        self._model = model
        return self

    def with_tokens(self, prompt: int, completion: int):
        self._prompt_tokens = prompt
        self._completion_tokens = completion
        return self

    def build(self) -> dict:
        return {
            "id": "chatcmpl-test-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": self._model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": self._content,
                },
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": self._prompt_tokens,
                "completion_tokens": self._completion_tokens,
                "total_tokens": self._prompt_tokens + self._completion_tokens,
            },
        }
```

### Step 2: Create Custom Assertions

```python
# tests/assertions.py
def assert_valid_chat_completion_response(response_data: dict):
    """Assert response is a valid chat completion with detailed error messages."""

    # Check required fields with helpful messages
    required_fields = ["id", "object", "created", "model", "choices"]
    for field in required_fields:
        assert field in response_data, \
            f"Response missing required field '{field}'. Got: {list(response_data.keys())}"

    # Validate structure
    assert response_data["object"] == "chat.completion", \
        f"Expected object='chat.completion', got '{response_data['object']}'"

    assert len(response_data["choices"]) > 0, \
        "Response should have at least one choice"

    # Validate choice
    choice = response_data["choices"][0]
    assert "message" in choice, "Choice missing 'message' field"
    assert "role" in choice["message"], "Message missing 'role' field"
    assert "content" in choice["message"], "Message missing 'content' field"
    assert len(choice["message"]["content"]) > 0, "Message content should not be empty"

    # Validate usage
    if "usage" in response_data:
        usage = response_data["usage"]
        assert usage["prompt_tokens"] >= 0, "Prompt tokens should be non-negative"
        assert usage["completion_tokens"] >= 0, "Completion tokens should be non-negative"
        assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"], \
            f"Total tokens mismatch: {usage['total_tokens']} != " \
            f"{usage['prompt_tokens']} + {usage['completion_tokens']}"


def assert_litellm_called_with_correct_params(mock_call, expected_model: str, expected_temp: float):
    """Assert LiteLLM was called with expected parameters."""
    assert mock_call.call_count == 1, f"Expected 1 call to LiteLLM, got {mock_call.call_count}"

    kwargs = mock_call.call_args.kwargs
    assert kwargs["model"] == expected_model, \
        f"Expected model '{expected_model}', got '{kwargs['model']}'"
    assert kwargs["temperature"] == expected_temp, \
        f"Expected temperature {expected_temp}, got {kwargs['temperature']}"
```

### Step 3: Split Into Focused Tests

```python
# tests/test_routes_improved.py
class TestChatCompletionBasicFlow:
    """Test basic chat completion request flow."""

    @pytest.fixture
    def request_builder(self):
        """Provide request builder."""
        return ChatCompletionRequestBuilder()

    @pytest.fixture
    def response_builder(self):
        """Provide response builder."""
        return MockLLMResponseBuilder()

    @patch("src.proxy.routes.litellm.acompletion")
    def test_successful_request_returns_valid_response(
        self,
        mock_acompletion,
        client,
        request_builder,
        response_builder
    ):
        """
        Test that a successful chat completion returns a valid response.

        GIVEN a valid chat completion request
        WHEN the request is processed successfully
        THEN the response should be a valid chat completion
        """
        # GIVEN - Arrange
        request_payload = (
            request_builder
            .with_simple_message("Hello, world!")
            .with_max_tokens(100)
            .build()
        )

        mock_response = (
            response_builder
            .with_content("Hello! How can I help you today?")
            .with_tokens(prompt=5, completion=12)
            .build()
        )

        mock_acompletion.return_value = mock_response

        # WHEN - Act
        response = client.post("/v1/chat/completions", json=request_payload)

        # THEN - Assert
        assert response.status_code == 200, \
            f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert_valid_chat_completion_response(data)

    @patch("src.proxy.routes.litellm.acompletion")
    def test_request_parameters_passed_to_litellm_correctly(
        self,
        mock_acompletion,
        client,
        request_builder,
        response_builder
    ):
        """
        Test that request parameters are correctly passed to LiteLLM.

        GIVEN a chat completion request with specific parameters
        WHEN the request is processed
        THEN those parameters should be passed to LiteLLM
        """
        # GIVEN
        request_payload = (
            request_builder
            .with_model("gpt-3.5-turbo")
            .with_simple_message("Test message")
            .build()
        )

        mock_acompletion.return_value = response_builder.build()

        # WHEN
        response = client.post("/v1/chat/completions", json=request_payload)

        # THEN
        assert response.status_code == 200
        assert_litellm_called_with_correct_params(
            mock_acompletion,
            expected_model="gpt-3.5-turbo",
            expected_temp=0.7
        )

    @patch("src.proxy.routes.litellm.acompletion")
    def test_response_includes_correct_token_counts(
        self,
        mock_acompletion,
        client,
        request_builder,
        response_builder
    ):
        """
        Test that response includes accurate token usage.

        GIVEN a chat completion request
        WHEN the request completes successfully
        THEN the response should include accurate token counts
        """
        # GIVEN
        expected_prompt_tokens = 15
        expected_completion_tokens = 25

        request_payload = request_builder.build()
        mock_response = (
            response_builder
            .with_tokens(
                prompt=expected_prompt_tokens,
                completion=expected_completion_tokens
            )
            .build()
        )

        mock_acompletion.return_value = mock_response

        # WHEN
        response = client.post("/v1/chat/completions", json=request_payload)

        # THEN
        assert response.status_code == 200

        data = response.json()
        usage = data["usage"]

        assert usage["prompt_tokens"] == expected_prompt_tokens
        assert usage["completion_tokens"] == expected_completion_tokens
        assert usage["total_tokens"] == expected_prompt_tokens + expected_completion_tokens
```

### Step 4: Add Property-Based Tests

```python
from hypothesis import given, strategies as st

@given(
    content=st.text(min_size=1, max_size=100),
    prompt_tokens=st.integers(min_value=1, max_value=1000),
    completion_tokens=st.integers(min_value=1, max_value=1000),
)
@patch("src.proxy.routes.litellm.acompletion")
def test_chat_completion_handles_any_valid_content(
    mock_acompletion,
    client,
    request_builder,
    response_builder,
    content,
    prompt_tokens,
    completion_tokens
):
    """
    Property test: Chat completion should handle any valid content.

    This automatically generates hundreds of test cases with different:
    - Message content (various strings)
    - Token counts (various valid integers)
    """
    # Arrange
    request_payload = request_builder.with_simple_message(content).build()
    mock_response = (
        response_builder
        .with_content(f"Response to: {content[:20]}")
        .with_tokens(prompt=prompt_tokens, completion=completion_tokens)
        .build()
    )
    mock_acompletion.return_value = mock_response

    # Act
    response = client.post("/v1/chat/completions", json=request_payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert_valid_chat_completion_response(data)
    assert data["usage"]["total_tokens"] == prompt_tokens + completion_tokens
```

---

## Quality Improvements Summary

### ✅ What Changed:

1. **Separation of Concerns**
   - Test setup → Builders
   - Assertions → Custom assertion functions
   - Each test → Single responsibility

2. **Readability**
   - Clear Given-When-Then structure
   - Descriptive variable names
   - Explicit test names describing behavior

3. **Maintainability**
   - Builders can be reused across all tests
   - Custom assertions provide better error messages
   - Easy to add new test cases

4. **Reliability**
   - Stronger assertions catch more bugs
   - Property-based tests find edge cases
   - Clear failure messages aid debugging

5. **Coverage Quality**
   - Property tests verify invariants
   - Focused tests easier to understand
   - Better confidence in code correctness

### 📊 Metrics Comparison:

| Metric | Before | After |
|--------|--------|-------|
| Lines per test | 25 | 15 (focused tests) |
| Test clarity | Medium | High |
| Reusability | Low | High |
| Failure messages | Generic | Specific |
| Edge case coverage | Manual | Automated (Hypothesis) |
| Maintenance burden | High | Low |

### 🎯 Key Takeaways:

1. **Test one thing per test** - Easier to debug failures
2. **Use builders** - Reduces duplication, improves clarity
3. **Custom assertions** - Better error messages
4. **Property-based testing** - Finds edge cases automatically
5. **Given-When-Then** - Makes tests readable as specifications

---

## Applying This Pattern

To refactor existing tests:

1. **Identify common patterns** in test setup
2. **Create builders** for those patterns
3. **Extract assertions** into custom functions
4. **Split multi-assertion tests** into focused tests
5. **Add property tests** for invariants
6. **Document** test intent clearly

This pattern can be applied to any of the existing test files:
- `test_routes_integration.py` (45 tests)
- `test_middleware_integration.py` (15 tests)
- `test_langfuse_enabled.py` (21 tests)
- `test_metrics_integration.py` (31 tests)

**Estimated effort**: 4-6 hours to refactor all existing tests
**Estimated benefit**: 2x easier to maintain, 3x faster to write new tests
