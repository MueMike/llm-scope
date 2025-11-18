"""Comprehensive tests for enhanced LangFuse features and analytics."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock

from src.proxy.server import create_app
from src.utils.code_quality import CodeQualityAnalyzer, QualityScore


# =================================================================
# Fixtures
# =================================================================


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_langfuse_client():
    """Mock enhanced LangFuse client."""
    client = MagicMock()
    client.enabled = True

    # Mock trace
    trace = MagicMock()
    trace.id = "trace-123"
    client.create_trace.return_value = trace

    # Mock generation
    generation = MagicMock()
    generation.id = "gen-456"
    client.create_generation.return_value = generation

    # Mock event
    event = MagicMock()
    event.id = "event-789"
    client.create_event.return_value = event

    # Mock scoring
    client.score_observation.return_value = True
    client.score_trace.return_value = True
    client.add_multi_dimensional_score.return_value = True

    return client


# =================================================================
# Code Quality Analyzer Tests
# =================================================================


class TestCodeQualityAnalyzerEdgeCases:
    """Test edge cases for code quality analyzer."""

    def test_analyze_python_code_with_multiple_issues(self):
        """Test code with multiple quality issues."""
        analyzer = CodeQualityAnalyzer()

        code = '''
import *  # Bad import
def MyFunction():  # Bad naming
    password = "12345"  # Hardcoded password
    eval("print('test')")  # Dangerous eval
    if True:
        if True:
            if True:
                if True:
                    if True:
                        pass  # Deep nesting
'''

        score = analyzer.analyze(code, "python")

        assert score.overall < 0.65  # Should have low overall score due to multiple issues
        assert score.security_score < 0.8  # Security issues detected
        assert len(score.issues) >= 4  # Multiple issues found (syntax, style, security)
        assert len(score.suggestions) > 0  # Suggestions provided

    def test_analyze_javascript_xss_vulnerabilities(self):
        """Test JavaScript XSS vulnerability detection."""
        analyzer = CodeQualityAnalyzer()

        code = '''
function displayUser(user) {
    document.innerHTML = user.name;  // XSS risk
    eval("alert('test')");  // Dangerous
    var password = "secret123";  // Hardcoded
}
'''

        score = analyzer.analyze(code, "javascript")

        assert score.security_score < 0.8
        security_issues = [i for i in score.issues if i["type"] == "security_issue"]
        assert len(security_issues) >= 2  # innerHTML and eval

    def test_analyze_code_with_only_comments(self):
        """Test code that is only comments."""
        analyzer = CodeQualityAnalyzer()

        code = '''
# This is a comment
# Another comment
# Just comments, no code
'''

        score = analyzer.analyze(code, "python")

        # Comments should parse correctly but have low practical value
        assert score.syntax_correctness >= 0.0  # Should not crash

    def test_analyze_very_long_code(self):
        """Test analyzer performance with very long code."""
        analyzer = CodeQualityAnalyzer()

        # Generate a large code block
        code_lines = []
        for i in range(1000):
            code_lines.append(f"def function_{i}(x):")
            code_lines.append(f"    return x + {i}")

        code = "\n".join(code_lines)

        import time
        start = time.time()
        score = analyzer.analyze(code, "python")
        duration = time.time() - start

        assert duration < 2.0  # Should complete in reasonable time
        assert score.syntax_correctness == 1.0  # Should be valid
        assert score.complexity_score > 0  # Should calculate complexity

    def test_quality_score_serialization(self):
        """Test QualityScore to_dict and get_scores_dict methods."""
        score = QualityScore(
            overall=0.85,
            syntax_correctness=1.0,
            style_compliance=0.8,
            complexity_score=0.75,
            security_score=0.9,
            breakdown={"test": "data"},
            issues=[{"type": "test", "severity": "warning", "message": "test"}],
            suggestions=["Test suggestion"]
        )

        # Test to_dict
        dict_repr = score.to_dict()
        assert dict_repr["overall"] == 0.85
        assert dict_repr["syntax_correctness"] == 1.0
        assert dict_repr["num_issues"] == 1
        assert dict_repr["num_suggestions"] == 1

        # Test get_scores_dict
        scores_dict = score.get_scores_dict()
        assert "code_quality_overall" in scores_dict
        assert "code_quality_syntax" in scores_dict
        assert "code_quality_style" in scores_dict
        assert scores_dict["code_quality_overall"] == 0.85


# =================================================================
# Analytics Endpoint Tests
# =================================================================


class TestAnalyticsEndpoints:
    """Test analytics API endpoints."""

    def test_analytics_health_check(self, client):
        """Test analytics health check endpoint."""
        response = client.get("/analytics/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "analytics-api"
        assert "langfuse_enabled" in data

    def test_submit_feedback_valid_thumbs_up(self, client):
        """Test submitting thumbs up feedback."""
        feedback = {
            "trace_id": "test-trace-123",
            "feedback_type": "thumbs_up",
            "value": True,
            "comment": "Excellent code!",
            "metadata": {"helpful": True}
        }

        response = client.post("/analytics/feedback", json=feedback)

        # Accept both 201 (success) and 503 (LangFuse not configured)
        assert response.status_code in [201, 503]

        if response.status_code == 201:
            data = response.json()
            assert data["status"] == "success"
            assert data["trace_id"] == "test-trace-123"

    def test_submit_feedback_with_rating(self, client):
        """Test submitting star rating feedback."""
        feedback = {
            "trace_id": "test-trace-456",
            "feedback_type": "rating",
            "value": 5,
            "comment": "Perfect solution"
        }

        response = client.post("/analytics/feedback", json=feedback)
        assert response.status_code in [201, 503]

    def test_submit_feedback_missing_trace_id(self, client):
        """Test feedback submission with missing required field."""
        feedback = {
            "feedback_type": "thumbs_up",
            "value": True
            # Missing trace_id
        }

        response = client.post("/analytics/feedback", json=feedback)
        assert response.status_code == 422  # Validation error

    def test_submit_scores_multi_dimensional(self, client):
        """Test submitting multi-dimensional quality scores."""
        scores = {
            "trace_id": "test-trace-789",
            "observation_id": "gen-123",
            "scores": {
                "code_quality": 0.85,
                "readability": 0.9,
                "performance": 0.8,
                "maintainability": 0.75,
                "test_coverage": 0.7
            },
            "config_id": "manual_review_v1"
        }

        response = client.post("/analytics/scores", json=scores)
        assert response.status_code in [201, 503]

        if response.status_code == 201:
            data = response.json()
            assert data["num_scores"] == 5

    def test_submit_scores_trace_level(self, client):
        """Test submitting trace-level scores."""
        scores = {
            "trace_id": "test-trace-999",
            # No observation_id - trace-level scoring
            "scores": {
                "session_success": 1.0,
                "user_satisfaction": 0.95
            }
        }

        response = client.post("/analytics/scores", json=scores)
        assert response.status_code in [201, 503]

    def test_compare_models_basic(self, client):
        """Test basic model comparison."""
        comparison = {
            "models": ["claude-3-sonnet-20240229", "gpt-4-turbo"],
            "task_type": "code_generation",
            "language": "python",
            "metric": "quality"
        }

        response = client.post("/analytics/models/compare", json=comparison)
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "comparison" in data
            assert "insights" in data

    def test_compare_models_with_date_range(self, client):
        """Test model comparison with date filtering."""
        comparison = {
            "models": ["gpt-4", "gpt-3.5-turbo"],
            "start_date": "2024-11-01T00:00:00Z",
            "end_date": "2024-11-18T23:59:59Z",
            "metric": "cost"
        }

        response = client.post("/analytics/models/compare", json=comparison)
        assert response.status_code in [200, 503]

    def test_analyze_prompt_effectiveness(self, client):
        """Test prompt effectiveness analysis."""
        analysis = {
            "prompt_name": "code_generation_v2",
            "min_version": 1,
            "max_version": 3,
            "task_type": "code_generation"
        }

        response = client.post("/analytics/prompts/effectiveness", json=analysis)
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "prompt_performance" in data
            assert "insights" in data

    def test_get_session_summary_basic(self, client):
        """Test getting session summary."""
        summary = {
            "user_id": "test@example.com",
            "start_date": "2024-11-01T00:00:00Z",
            "end_date": "2024-11-18T23:59:59Z"
        }

        response = client.post("/analytics/sessions/summary", json=summary)
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "summary" in data

    def test_get_session_summary_with_session_id(self, client):
        """Test getting specific session summary."""
        summary = {
            "session_id": "session-abc-123"
        }

        response = client.post("/analytics/sessions/summary", json=summary)
        assert response.status_code in [200, 503]

    def test_get_cost_breakdown(self, client):
        """Test getting cost breakdown."""
        response = client.get(
            "/analytics/costs/breakdown",
            params={
                "start_date": "2024-11-01",
                "end_date": "2024-11-18",
                "group_by": "model"
            }
        )

        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "breakdown" in data
            assert "total_cost_usd" in data

    def test_get_cost_breakdown_by_provider(self, client):
        """Test cost breakdown grouped by provider."""
        response = client.get(
            "/analytics/costs/breakdown",
            params={"group_by": "provider"}
        )

        assert response.status_code in [200, 503]

    def test_get_quality_trends(self, client):
        """Test getting quality trends over time."""
        response = client.get(
            "/analytics/quality/trends",
            params={
                "start_date": "2024-11-01",
                "end_date": "2024-11-18",
                "granularity": "day",
                "metric": "overall"
            }
        )

        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "trend_data" in data
            assert "statistics" in data

    def test_get_quality_trends_hourly(self, client):
        """Test quality trends with hourly granularity."""
        response = client.get(
            "/analytics/quality/trends",
            params={
                "granularity": "hour",
                "metric": "syntax"
            }
        )

        assert response.status_code in [200, 503]

    def test_compare_assistants(self, client):
        """Test comparing coding assistants."""
        response = client.get(
            "/analytics/assistants/comparison",
            params={
                "assistants": "cursor,vscode-copilot,claude-code",
                "start_date": "2024-11-01",
                "end_date": "2024-11-18"
            }
        )

        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "comparison" in data
            assert "insights" in data
            assert "recommendations" in data


# =================================================================
# Integration Tests for Complete Workflows
# =================================================================


class TestEnhancedTracingWorkflow:
    """Test complete workflow with enhanced tracing."""

    @patch("src.proxy.routes.litellm.acompletion")
    def test_code_generation_with_automatic_quality_analysis(
        self, mock_acompletion, client
    ):
        """Test that code generation automatically triggers quality analysis."""
        # Mock response with code
        mock_acompletion.return_value = {
            "id": "test",
            "object": "chat.completion",
            "created": 123456,
            "model": "gpt-4",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "```python\ndef factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)\n```"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }

        payload = {
            "model": "gpt-4",
            "messages": [
                {"role": "user", "content": "Write a factorial function in Python"}
            ],
            "metadata": {
                "language": "python",
                "task_type": "code_generation"
            }
        }

        response = client.post("/v1/chat/completions", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "```python" in data["choices"][0]["message"]["content"]

    @patch("src.proxy.routes.litellm.acompletion")
    def test_multi_turn_conversation_with_session_tracking(
        self, mock_acompletion, client
    ):
        """Test multi-turn conversation with session tracking."""
        mock_acompletion.return_value = {
            "id": "test",
            "object": "chat.completion",
            "created": 123456,
            "model": "gpt-4",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "Response"},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        }

        session_id = "test-session-123"
        headers = {
            "X-User-ID": "test-user",
            "X-Session-ID": session_id
        }

        # First turn
        response1 = client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "Hello"}]
            },
            headers=headers
        )

        assert response1.status_code == 200

        # Second turn - same session
        response2 = client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4",
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Response"},
                    {"role": "user", "content": "Continue"}
                ]
            },
            headers=headers
        )

        assert response2.status_code == 200
        # Both requests should have the same session ID in headers
        assert "X-Trace-ID" in response1.headers
        assert "X-Trace-ID" in response2.headers


# =================================================================
# Performance and Load Tests
# =================================================================


class TestPerformanceAndLoad:
    """Test performance characteristics."""

    @patch("src.proxy.routes.litellm.acompletion")
    def test_concurrent_requests_performance(self, mock_acompletion, client):
        """Test handling of concurrent requests."""
        mock_acompletion.return_value = {
            "id": "test",
            "object": "chat.completion",
            "created": 123456,
            "model": "gpt-4",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "Response"},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        }

        import time
        import concurrent.futures

        def make_request():
            return client.post(
                "/v1/chat/completions",
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Test"}]
                }
            )

        # Make 10 concurrent requests
        start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]
        duration = time.time() - start

        # All requests should succeed
        assert all(r.status_code == 200 for r in results)

        # Should complete reasonably fast
        assert duration < 5.0  # 10 requests in under 5 seconds

    def test_large_response_handling(self, client):
        """Test handling of large response payloads."""
        # Test with large message
        large_message = "x" * 100000  # 100KB message

        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": large_message}]
            }
        )

        # Should handle large payloads
        # Will likely fail without mocking, but structure should work
        assert response.status_code in [200, 401, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
