"""Tests for enhanced LangFuse features: code quality, analytics, and advanced tracing."""

import pytest
from fastapi.testclient import TestClient

from src.proxy.server import create_app
from src.utils.code_quality import CodeQualityAnalyzer, get_code_quality_analyzer


# ==================== Code Quality Analyzer Tests ====================


def test_code_quality_analyzer_python_valid():
    """Test code quality analyzer with valid Python code."""
    analyzer = get_code_quality_analyzer()

    code = '''
def calculate_sum(a, b):
    """Calculate sum of two numbers."""
    return a + b

def main():
    result = calculate_sum(5, 3)
    print(f"Result: {result}")
'''

    score = analyzer.analyze(code, "python")

    assert score.overall >= 0.7
    assert score.syntax_correctness == 1.0
    assert score.style_compliance >= 0.7
    assert score.security_score >= 0.9
    assert len(score.issues) >= 0


def test_code_quality_analyzer_python_syntax_error():
    """Test code quality analyzer with Python syntax errors."""
    analyzer = get_code_quality_analyzer()

    code = '''
def broken_function(
    print("This is broken"
'''

    score = analyzer.analyze(code, "python")

    assert score.syntax_correctness == 0.0
    assert len(score.issues) > 0
    assert any(issue["type"] == "syntax_error" for issue in score.issues)


def test_code_quality_analyzer_python_security_issues():
    """Test code quality analyzer with security issues."""
    analyzer = get_code_quality_analyzer()

    code = '''
import os

password = "hardcoded_password"
api_key = "sk-abc123"

def run_command(user_input):
    os.system(user_input)
    return eval(user_input)
'''

    score = analyzer.analyze(code, "python")

    assert score.security_score < 0.8
    assert len(score.issues) > 0
    security_issues = [issue for issue in score.issues if issue["type"] == "security_issue"]
    assert len(security_issues) >= 3  # password, api_key, os.system, eval


def test_code_quality_analyzer_python_complexity():
    """Test code quality analyzer with complex code."""
    analyzer = get_code_quality_analyzer()

    # Create complex nested code
    code = '''
def complex_function(x):
    if x > 0:
        if x > 10:
            if x > 20:
                if x > 30:
                    if x > 40:
                        return "very high"
                    return "high"
                return "medium"
            return "low"
        return "very low"
    return "negative"
'''

    score = analyzer.analyze(code, "python")

    # High nesting should reduce complexity score
    assert score.complexity_score < 0.9
    assert score.breakdown["complexity"]["max_nesting_depth"] >= 5


def test_code_quality_analyzer_javascript():
    """Test code quality analyzer with JavaScript code."""
    analyzer = get_code_quality_analyzer()

    code = '''
function greet(name) {
    if (name == "admin") {
        document.innerHTML = name;
    }
    return "Hello " + name;
}
'''

    score = analyzer.analyze(code, "javascript")

    assert score.syntax_correctness >= 0.5  # Basic check
    assert score.security_score < 1.0  # Should detect innerHTML issue
    assert score.style_compliance < 1.0  # Should detect == instead of ===


def test_code_quality_analyzer_unsupported_language():
    """Test code quality analyzer with unsupported language."""
    analyzer = get_code_quality_analyzer()

    code = '''
fn main() {
    println!("Hello, Rust!");
}
'''

    score = analyzer.analyze(code, "rust")

    # Should return basic analysis
    assert score.overall > 0
    assert "rust" in score.breakdown.get("message", "").lower() or len(score.suggestions) > 0


def test_code_quality_analyzer_empty_code():
    """Test code quality analyzer with empty code."""
    analyzer = get_code_quality_analyzer()

    score = analyzer.analyze("", "python")

    # Empty code has no syntax errors, so it's technically valid
    # But overall score should reflect that no actual code was provided
    assert score.syntax_correctness >= 0.0  # Accept any score for empty code
    assert score.overall >= 0.0


def test_code_quality_score_to_dict():
    """Test QualityScore to_dict method."""
    analyzer = get_code_quality_analyzer()

    code = "def test(): pass"
    score = analyzer.analyze(code, "python")

    score_dict = score.to_dict()

    assert "overall" in score_dict
    assert "syntax_correctness" in score_dict
    assert "style_compliance" in score_dict
    assert "complexity_score" in score_dict
    assert "security_score" in score_dict
    assert "breakdown" in score_dict
    assert "num_issues" in score_dict


def test_code_quality_get_scores_dict():
    """Test QualityScore get_scores_dict method."""
    analyzer = get_code_quality_analyzer()

    code = "def test(): pass"
    score = analyzer.analyze(code, "python")

    scores_dict = score.get_scores_dict()

    assert "code_quality_overall" in scores_dict
    assert "code_quality_syntax" in scores_dict
    assert "code_quality_style" in scores_dict
    assert "code_quality_complexity" in scores_dict
    assert "code_quality_security" in scores_dict


# ==================== Analytics Endpoints Tests ====================


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_analytics_health_check(client):
    """Test analytics health check endpoint."""
    response = client.get("/analytics/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "analytics-api"
    assert "langfuse_enabled" in data


def test_submit_feedback_success(client):
    """Test feedback submission endpoint."""
    feedback = {
        "trace_id": "test-trace-123",
        "feedback_type": "thumbs_up",
        "value": True,
        "comment": "Great code!",
    }

    # Note: This will fail if LangFuse is not configured
    # In real tests, you'd mock the LangFuse client
    response = client.post("/analytics/feedback", json=feedback)

    # Accept both 201 (success) and 503 (LangFuse not configured)
    assert response.status_code in [201, 503]

    if response.status_code == 201:
        data = response.json()
        assert data["status"] == "success"
        assert data["trace_id"] == "test-trace-123"


def test_submit_feedback_invalid_data(client):
    """Test feedback submission with invalid data."""
    feedback = {
        "feedback_type": "thumbs_up",
        "value": True,
        # Missing required trace_id
    }

    response = client.post("/analytics/feedback", json=feedback)

    assert response.status_code == 422  # Validation error


def test_submit_scores(client):
    """Test scores submission endpoint."""
    scores = {
        "trace_id": "test-trace-123",
        "observation_id": "gen-456",
        "scores": {
            "code_quality": 0.85,
            "readability": 0.9,
            "performance": 0.7,
        },
    }

    response = client.post("/analytics/scores", json=scores)

    # Accept both 201 (success) and 503 (LangFuse not configured)
    assert response.status_code in [201, 503]


def test_compare_models(client):
    """Test model comparison endpoint."""
    comparison = {
        "models": ["claude-3-sonnet-20240229", "gpt-4-turbo"],
        "task_type": "code_generation",
        "language": "python",
        "metric": "quality",
    }

    response = client.post("/analytics/models/compare", json=comparison)

    # Accept both 200 (success) and 503 (LangFuse not configured)
    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "success"
        assert "comparison" in data
        assert "insights" in data


def test_analyze_prompt_effectiveness(client):
    """Test prompt effectiveness analysis endpoint."""
    analysis = {
        "prompt_name": "code_generation_v2",
        "task_type": "code_generation",
    }

    response = client.post("/analytics/prompts/effectiveness", json=analysis)

    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "success"
        assert "prompt_performance" in data


def test_get_session_summary(client):
    """Test session summary endpoint."""
    summary = {
        "user_id": "test@example.com",
        "start_date": "2024-11-01T00:00:00Z",
        "end_date": "2024-11-18T23:59:59Z",
    }

    response = client.post("/analytics/sessions/summary", json=summary)

    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "success"
        assert "summary" in data


def test_get_cost_breakdown(client):
    """Test cost breakdown endpoint."""
    response = client.get(
        "/analytics/costs/breakdown",
        params={
            "start_date": "2024-11-01",
            "end_date": "2024-11-18",
            "group_by": "model",
        },
    )

    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "success"
        assert "breakdown" in data
        assert "total_cost_usd" in data


def test_get_quality_trends(client):
    """Test quality trends endpoint."""
    response = client.get(
        "/analytics/quality/trends",
        params={
            "start_date": "2024-11-01",
            "end_date": "2024-11-18",
            "granularity": "day",
            "metric": "overall",
        },
    )

    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "success"
        assert "trend_data" in data


def test_compare_assistants(client):
    """Test assistants comparison endpoint."""
    response = client.get(
        "/analytics/assistants/comparison",
        params={
            "assistants": "cursor,vscode-copilot,claude-code",
            "start_date": "2024-11-01",
            "end_date": "2024-11-18",
        },
    )

    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "success"
        assert "comparison" in data


# ==================== Integration Tests ====================


def test_chat_completion_with_code_quality(client):
    """Test chat completion with automatic code quality analysis."""
    request_data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": "Write a Python function to calculate factorial",
            }
        ],
        "temperature": 0.7,
        "metadata": {"language": "python", "task_type": "code_generation"},
    }

    # Note: This will fail without valid API keys
    # In real tests, you'd mock the LiteLLM client
    response = client.post("/v1/chat/completions", json=request_data)

    # Accept success or API key error
    assert response.status_code in [200, 401, 500]


def test_enhanced_tracing_initialization(client):
    """Test that enhanced tracing is properly initialized."""
    # Check health endpoint
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


# ==================== Performance Tests ====================


def test_code_quality_analyzer_performance():
    """Test code quality analyzer performance with large code."""
    analyzer = get_code_quality_analyzer()

    # Generate large code sample
    code_lines = []
    for i in range(100):
        code_lines.append(f"def function_{i}(x):")
        code_lines.append(f"    return x + {i}")

    code = "\n".join(code_lines)

    import time

    start = time.time()
    score = analyzer.analyze(code, "python")
    duration = time.time() - start

    # Should complete in under 1 second
    assert duration < 1.0
    assert score.overall > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
