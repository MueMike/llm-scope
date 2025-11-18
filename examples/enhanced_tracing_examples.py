"""
Examples demonstrating enhanced LangFuse tracing capabilities.

This file shows how to use the new features:
- Automatic code quality scoring
- User feedback submission
- Multi-dimensional scoring
- Analytics queries
- Model comparison
"""

import requests
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"  # If required

# Headers
HEADERS = {
    "Content-Type": "application/json",
    "X-User-ID": "developer@example.com",
    "X-Session-ID": "example-session-123",
}


# ==================== Basic Chat Completion with Enhanced Tracing ====================


def example_code_generation_with_quality_analysis():
    """
    Example: Generate code and get automatic quality analysis.

    The proxy now automatically:
    - Detects code in responses
    - Analyzes syntax, style, complexity, security
    - Adds quality scores to LangFuse traces
    """
    print("\n" + "=" * 60)
    print("Example 1: Code Generation with Quality Analysis")
    print("=" * 60)

    request_data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful coding assistant. Provide clean, well-documented code.",
            },
            {
                "role": "user",
                "content": "Write a Python function to calculate the Fibonacci sequence up to n terms.",
            },
        ],
        "temperature": 0.7,
        "metadata": {
            "language": "python",
            "task_type": "code_generation",
            "task_complexity": "medium",
        },
    }

    response = requests.post(f"{BASE_URL}/v1/chat/completions", json=request_data, headers=HEADERS)

    if response.status_code == 200:
        result = response.json()
        print("\n✓ Code generated successfully!")
        print(f"Model: {result['model']}")
        print(f"Tokens: {result['usage']['total_tokens']}")

        # The proxy automatically analyzed code quality and added scores to LangFuse
        print("\n✓ Code quality automatically analyzed and logged to LangFuse")
        print("  - Syntax correctness")
        print("  - Style compliance")
        print("  - Complexity score")
        print("  - Security analysis")

        print(f"\nGenerated Code:\n{result['choices'][0]['message']['content'][:200]}...")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")


# ==================== User Feedback ====================


def example_submit_user_feedback():
    """
    Example: Submit user feedback on generated code.

    Feedback types:
    - Thumbs up/down
    - Star ratings (1-5)
    - Acceptance (accepted/rejected/partial)
    - Custom feedback
    """
    print("\n" + "=" * 60)
    print("Example 2: Submit User Feedback")
    print("=" * 60)

    # First, generate some code to get a trace_id
    # In practice, you'd get the trace_id from response headers
    trace_id = "example-trace-id-123"

    # Example 1: Thumbs up
    feedback_thumbs_up = {
        "trace_id": trace_id,
        "feedback_type": "thumbs_up",
        "value": True,
        "comment": "Perfect! Code works exactly as expected.",
    }

    response = requests.post(f"{BASE_URL}/analytics/feedback", json=feedback_thumbs_up)

    if response.status_code == 201:
        print("✓ Thumbs up feedback submitted successfully")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

    # Example 2: Star rating
    feedback_rating = {
        "trace_id": trace_id,
        "feedback_type": "rating",
        "value": 5,
        "comment": "Excellent code quality and documentation",
        "metadata": {"helpful": True, "accurate": True, "well_documented": True},
    }

    response = requests.post(f"{BASE_URL}/analytics/feedback", json=feedback_rating)

    if response.status_code == 201:
        print("✓ Star rating feedback submitted successfully")

    # Example 3: Code acceptance
    feedback_acceptance = {
        "trace_id": trace_id,
        "feedback_type": "code_accepted",
        "value": "full",  # Options: full, partial, rejected
        "metadata": {
            "time_to_decision_ms": 3500,
            "modifications_needed": False,
            "tests_passing": True,
        },
    }

    response = requests.post(f"{BASE_URL}/analytics/feedback", json=feedback_acceptance)

    if response.status_code == 201:
        print("✓ Code acceptance feedback submitted successfully")


# ==================== Manual Scoring ====================


def example_submit_custom_scores():
    """
    Example: Submit custom quality scores.

    Use this for:
    - Manual code review scores
    - Test coverage metrics
    - Performance benchmarks
    - Custom quality dimensions
    """
    print("\n" + "=" * 60)
    print("Example 3: Submit Custom Quality Scores")
    print("=" * 60)

    trace_id = "example-trace-id-123"
    observation_id = "gen-456"

    # Multi-dimensional quality scoring
    scores_data = {
        "trace_id": trace_id,
        "observation_id": observation_id,
        "scores": {
            "code_readability": 0.90,
            "documentation_quality": 0.85,
            "test_coverage": 0.75,
            "performance_score": 0.88,
            "maintainability": 0.82,
            "edge_case_handling": 0.70,
        },
        "config_id": "manual_review_v1",
    }

    response = requests.post(f"{BASE_URL}/analytics/scores", json=scores_data)

    if response.status_code == 201:
        result = response.json()
        print(f"✓ {result['num_scores']} custom scores submitted successfully")
        print("  - Code readability: 0.90")
        print("  - Documentation quality: 0.85")
        print("  - Test coverage: 0.75")
        print("  - Performance score: 0.88")
        print("  - Maintainability: 0.82")
        print("  - Edge case handling: 0.70")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")


# ==================== Model Comparison ====================


def example_compare_models():
    """
    Example: Compare performance of different LLM models.

    Answers questions like:
    - Which model produces better code for Python?
    - Is GPT-4 worth the extra cost?
    - Which model is fastest?
    """
    print("\n" + "=" * 60)
    print("Example 4: Compare Models")
    print("=" * 60)

    comparison_request = {
        "models": ["claude-3-sonnet-20240229", "gpt-4-turbo", "gpt-3.5-turbo"],
        "task_type": "code_generation",
        "language": "python",
        "start_date": "2024-11-01T00:00:00Z",
        "end_date": "2024-11-18T23:59:59Z",
        "metric": "quality",
    }

    response = requests.post(f"{BASE_URL}/analytics/models/compare", json=comparison_request)

    if response.status_code == 200:
        result = response.json()
        print("\n✓ Model comparison completed")
        print("\nComparison Results:")

        if "comparison" in result and "example_data" in result["comparison"]:
            for model, metrics in result["comparison"]["example_data"].items():
                print(f"\n  {model}:")
                print(f"    - Quality Score: {metrics['avg_quality_score']:.3f}")
                print(f"    - Cost: ${metrics['avg_cost_usd']:.4f}")
                print(f"    - Speed: {metrics['avg_response_time_ms']:.0f}ms")
                print(f"    - Success Rate: {metrics['success_rate']:.1%}")
                print(f"    - User Satisfaction: {metrics['user_satisfaction']:.3f}")

        if "insights" in result:
            print("\nKey Insights:")
            for insight in result["insights"]:
                print(f"  • {insight}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")


# ==================== Prompt Effectiveness Analysis ====================


def example_analyze_prompt_effectiveness():
    """
    Example: Analyze which prompt versions perform best.

    Use this for:
    - A/B testing prompts
    - Optimizing prompt templates
    - Tracking prompt version performance
    """
    print("\n" + "=" * 60)
    print("Example 5: Analyze Prompt Effectiveness")
    print("=" * 60)

    analysis_request = {
        "prompt_name": "code_generation_v2",
        "min_version": 1,
        "max_version": 3,
        "task_type": "code_generation",
    }

    response = requests.post(
        f"{BASE_URL}/analytics/prompts/effectiveness", json=analysis_request
    )

    if response.status_code == 200:
        result = response.json()
        print("\n✓ Prompt effectiveness analysis completed")

        if "prompt_performance" in result and "example_data" in result["prompt_performance"]:
            print("\nPrompt Version Performance:")
            for prompt, metrics in result["prompt_performance"]["example_data"].items():
                print(f"\n  {prompt} (v{metrics['version']}):")
                print(f"    - Success Rate: {metrics['success_rate']:.1%}")
                print(f"    - Avg Quality: {metrics['avg_quality_score']:.3f}")
                print(f"    - Avg Iterations: {metrics['avg_iterations']:.1f}")
                print(f"    - User Satisfaction: {metrics['user_satisfaction']:.3f}")
                print(f"    - Total Uses: {metrics['total_uses']}")

        if "insights" in result:
            print("\nKey Insights:")
            for insight in result["insights"]:
                print(f"  • {insight}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")


# ==================== Session Summary ====================


def example_get_session_summary():
    """
    Example: Get summary analytics for coding sessions.

    Provides:
    - Total sessions and duration
    - Task completion rates
    - Cost breakdown
    - Language usage
    """
    print("\n" + "=" * 60)
    print("Example 6: Get Session Summary")
    print("=" * 60)

    summary_request = {
        "user_id": "developer@example.com",
        "start_date": "2024-11-01T00:00:00Z",
        "end_date": "2024-11-18T23:59:59Z",
        "assistant_type": "cursor",
    }

    response = requests.post(f"{BASE_URL}/analytics/sessions/summary", json=summary_request)

    if response.status_code == 200:
        result = response.json()
        print("\n✓ Session summary retrieved")

        if "summary" in result:
            summary = result["summary"]
            print("\nSession Statistics:")
            print(f"  - Total Sessions: {summary.get('total_sessions', 0)}")
            print(f"  - Total Requests: {summary.get('total_requests', 0)}")
            print(f"  - Total Duration: {summary.get('total_duration_hours', 0):.1f} hours")
            print(f"  - Avg Session: {summary.get('avg_session_duration_min', 0):.1f} minutes")
            print(f"  - Completion Rate: {summary.get('task_completion_rate', 0):.1%}")
            print(f"  - Avg Quality: {summary.get('avg_quality_score', 0):.3f}")
            print(f"  - Total Cost: ${summary.get('total_cost_usd', 0):.2f}")

        if "task_breakdown" in result:
            print("\nTask Breakdown:")
            for task, stats in result["task_breakdown"].items():
                print(
                    f"  - {task}: {stats['count']} requests ({stats['success_rate']:.1%} success)"
                )

        if "insights" in result:
            print("\nKey Insights:")
            for insight in result["insights"]:
                print(f"  • {insight}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")


# ==================== Cost Breakdown ====================


def example_get_cost_breakdown():
    """
    Example: Get detailed cost breakdown and optimization insights.
    """
    print("\n" + "=" * 60)
    print("Example 7: Get Cost Breakdown")
    print("=" * 60)

    params = {
        "start_date": "2024-11-01",
        "end_date": "2024-11-18",
        "group_by": "model",
    }

    response = requests.get(f"{BASE_URL}/analytics/costs/breakdown", params=params)

    if response.status_code == 200:
        result = response.json()
        print("\n✓ Cost breakdown retrieved")
        print(f"\nTotal Cost: ${result.get('total_cost_usd', 0):.2f}")

        if "breakdown" in result and "by_model" in result["breakdown"]:
            print("\nCost by Model:")
            for model, cost in result["breakdown"]["by_model"].items():
                print(f"  - {model}: ${cost:.2f}")

        if "optimization_opportunities" in result:
            print("\nOptimization Opportunities:")
            for opp in result["optimization_opportunities"]:
                print(f"\n  • {opp['description']}")
                print(f"    Potential Savings: ${opp['potential_savings_usd']:.2f}")
                print(f"    Impact: {opp['impact']}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")


# ==================== Assistant Comparison ====================


def example_compare_assistants():
    """
    Example: Compare different coding assistants (Cursor, VSCode Copilot, Claude Code).
    """
    print("\n" + "=" * 60)
    print("Example 8: Compare Coding Assistants")
    print("=" * 60)

    params = {
        "assistants": "cursor,vscode-copilot,claude-code",
        "start_date": "2024-11-01",
        "end_date": "2024-11-18",
    }

    response = requests.get(f"{BASE_URL}/analytics/assistants/comparison", params=params)

    if response.status_code == 200:
        result = response.json()
        print("\n✓ Assistant comparison completed")

        if "comparison" in result:
            print("\nAssistant Performance:")
            for assistant, metrics in result["comparison"].items():
                if assistant != "note":
                    print(f"\n  {assistant}:")
                    print(f"    - Success Rate: {metrics.get('success_rate', 0):.1%}")
                    print(f"    - Avg Speed: {metrics.get('avg_speed_ms', 0):.0f}ms")
                    print(f"    - Avg Cost: ${metrics.get('avg_cost_usd', 0):.4f}")
                    print(f"    - User Satisfaction: {metrics.get('user_satisfaction', 0):.3f}")

        if "insights" in result:
            print("\nKey Insights:")
            for insight in result["insights"]:
                print(f"  • {insight}")

        if "recommendations" in result:
            print("\nRecommendations:")
            for rec in result["recommendations"]:
                print(f"  • {rec}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")


# ==================== Main ====================


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("ENHANCED LANGFUSE TRACING EXAMPLES")
    print("=" * 60)
    print(
        "\nThese examples demonstrate the new agentic coding tracing capabilities."
    )
    print("Ensure the proxy server is running at:", BASE_URL)
    print("\nNote: Some examples require LangFuse to be properly configured.")
    print("=" * 60)

    try:
        # Example 1: Code generation with automatic quality analysis
        example_code_generation_with_quality_analysis()

        time.sleep(1)

        # Example 2: Submit user feedback
        example_submit_user_feedback()

        time.sleep(1)

        # Example 3: Submit custom scores
        example_submit_custom_scores()

        time.sleep(1)

        # Example 4: Compare models
        example_compare_models()

        time.sleep(1)

        # Example 5: Analyze prompt effectiveness
        example_analyze_prompt_effectiveness()

        time.sleep(1)

        # Example 6: Get session summary
        example_get_session_summary()

        time.sleep(1)

        # Example 7: Get cost breakdown
        example_get_cost_breakdown()

        time.sleep(1)

        # Example 8: Compare assistants
        example_compare_assistants()

        print("\n" + "=" * 60)
        print("✓ All examples completed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Check LangFuse dashboard for detailed traces")
        print("2. Review code quality scores in LangFuse")
        print("3. Use analytics endpoints to gain insights")
        print("4. Optimize based on data-driven recommendations")

    except requests.exceptions.ConnectionError:
        print(f"\n✗ Error: Could not connect to {BASE_URL}")
        print("Make sure the proxy server is running:")
        print("  python main.py")
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    main()
