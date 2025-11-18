"""Analytics and feedback API routes for agentic coding insights."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from ..integrations.langfuse_enhanced import get_enhanced_langfuse_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ==================== Request/Response Models ====================


class FeedbackRequest(BaseModel):
    """User feedback submission."""

    trace_id: str = Field(..., description="Trace ID to provide feedback for")
    feedback_type: str = Field(..., description="Type of feedback (thumbs_up, thumbs_down, rating, etc.)")
    value: Any = Field(..., description="Feedback value (bool, int, float, or string)")
    comment: Optional[str] = Field(None, description="Optional user comment")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ScoreSubmission(BaseModel):
    """Manual score submission for code quality."""

    trace_id: str = Field(..., description="Trace ID")
    observation_id: Optional[str] = Field(None, description="Observation ID (None for trace-level)")
    scores: Dict[str, Any] = Field(..., description="Dictionary of score names and values")
    config_id: Optional[str] = Field(None, description="Score configuration ID")


class ModelComparisonRequest(BaseModel):
    """Request for model comparison analytics."""

    models: Optional[List[str]] = Field(None, description="List of models to compare (None for all)")
    task_type: Optional[str] = Field(None, description="Filter by task type")
    language: Optional[str] = Field(None, description="Filter by programming language")
    start_date: Optional[str] = Field(None, description="Start date (ISO format)")
    end_date: Optional[str] = Field(None, description="End date (ISO format)")
    metric: str = Field("quality", description="Primary metric to compare (quality, cost, speed, satisfaction)")


class PromptEffectivenessRequest(BaseModel):
    """Request for prompt effectiveness analysis."""

    prompt_name: Optional[str] = Field(None, description="Specific prompt name (None for all)")
    min_version: Optional[int] = Field(None, description="Minimum prompt version")
    max_version: Optional[int] = Field(None, description="Maximum prompt version")
    task_type: Optional[str] = Field(None, description="Filter by task type")


class SessionSummaryRequest(BaseModel):
    """Request for session summary analytics."""

    user_id: Optional[str] = Field(None, description="Filter by user ID")
    session_id: Optional[str] = Field(None, description="Specific session ID")
    start_date: Optional[str] = Field(None, description="Start date (ISO format)")
    end_date: Optional[str] = Field(None, description="End date (ISO format)")
    assistant_type: Optional[str] = Field(None, description="Filter by assistant type")


# ==================== Feedback Endpoints ====================


@router.post("/feedback", status_code=201)
async def submit_feedback(request: Request, feedback: FeedbackRequest):
    """
    Submit user feedback for a trace.

    This endpoint allows users to provide feedback on AI-generated code:
    - Thumbs up/down
    - Star ratings
    - Acceptance/rejection
    - Custom feedback with comments

    Example:
        ```json
        {
            "trace_id": "trace-123",
            "feedback_type": "thumbs_up",
            "value": true,
            "comment": "Perfect solution!"
        }
        ```
    """
    langfuse_client = get_enhanced_langfuse_client()

    if not langfuse_client.enabled:
        raise HTTPException(status_code=503, detail="LangFuse not configured")

    try:
        success = langfuse_client.add_user_feedback(
            trace_id=feedback.trace_id,
            feedback_type=feedback.feedback_type,
            value=feedback.value,
            comment=feedback.comment,
            metadata=feedback.metadata,
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to submit feedback")

        logger.info(f"Feedback submitted: trace={feedback.trace_id}, type={feedback.feedback_type}")

        return {
            "status": "success",
            "message": "Feedback submitted successfully",
            "trace_id": feedback.trace_id,
        }

    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scores", status_code=201)
async def submit_scores(request: Request, submission: ScoreSubmission):
    """
    Submit manual scores for code quality or other metrics.

    This endpoint allows manual scoring of generated code:
    - Code quality dimensions
    - Custom metrics
    - Multi-dimensional scoring

    Example:
        ```json
        {
            "trace_id": "trace-123",
            "observation_id": "gen-456",
            "scores": {
                "code_quality": 0.85,
                "readability": 0.9,
                "performance": 0.7
            }
        }
        ```
    """
    langfuse_client = get_enhanced_langfuse_client()

    if not langfuse_client.enabled:
        raise HTTPException(status_code=503, detail="LangFuse not configured")

    try:
        success = langfuse_client.add_multi_dimensional_score(
            trace_id=submission.trace_id,
            observation_id=submission.observation_id,
            scores=submission.scores,
            config_id=submission.config_id,
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to submit scores")

        logger.info(
            f"Scores submitted: trace={submission.trace_id}, "
            f"observation={submission.observation_id}, "
            f"num_scores={len(submission.scores)}"
        )

        return {
            "status": "success",
            "message": "Scores submitted successfully",
            "trace_id": submission.trace_id,
            "observation_id": submission.observation_id,
            "num_scores": len(submission.scores),
        }

    except Exception as e:
        logger.error(f"Failed to submit scores: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Analytics Endpoints ====================


@router.post("/models/compare")
async def compare_models(request: Request, comparison: ModelComparisonRequest):
    """
    Compare performance of different LLM models.

    This endpoint provides comparative analytics across models:
    - Code quality scores
    - Cost efficiency
    - Response speed
    - User satisfaction
    - Success rates

    Returns aggregated metrics for each model with statistical comparisons.

    Note: This endpoint requires LangFuse data to be available.
    Actual implementation would query LangFuse analytics API.
    """
    langfuse_client = get_enhanced_langfuse_client()

    if not langfuse_client.enabled:
        raise HTTPException(status_code=503, detail="LangFuse not configured")

    try:
        # Note: This is a placeholder for actual LangFuse analytics query
        # In production, this would query LangFuse's analytics API or database

        result = {
            "status": "success",
            "filters": {
                "models": comparison.models,
                "task_type": comparison.task_type,
                "language": comparison.language,
                "date_range": {
                    "start": comparison.start_date,
                    "end": comparison.end_date,
                },
            },
            "metric": comparison.metric,
            "comparison": {
                "note": "This is a placeholder. Implement actual LangFuse analytics query.",
                "example_data": {
                    "claude-3-sonnet-20240229": {
                        "avg_quality_score": 0.85,
                        "avg_cost_usd": 0.023,
                        "avg_response_time_ms": 2500,
                        "success_rate": 0.92,
                        "user_satisfaction": 0.88,
                        "total_requests": 1234,
                    },
                    "gpt-4-turbo": {
                        "avg_quality_score": 0.82,
                        "avg_cost_usd": 0.045,
                        "avg_response_time_ms": 3200,
                        "success_rate": 0.89,
                        "user_satisfaction": 0.85,
                        "total_requests": 987,
                    },
                },
            },
            "insights": [
                "Claude Sonnet shows 3.7% higher quality score",
                "Claude Sonnet is 49% more cost-effective",
                "Claude Sonnet is 28% faster on average",
                "Recommendation: Use Claude Sonnet for this task type",
            ],
        }

        logger.info(f"Model comparison requested: metric={comparison.metric}")
        return result

    except Exception as e:
        logger.error(f"Failed to compare models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompts/effectiveness")
async def analyze_prompt_effectiveness(request: Request, analysis: PromptEffectivenessRequest):
    """
    Analyze effectiveness of different prompt versions.

    This endpoint provides insights into prompt performance:
    - Success rates by prompt version
    - Quality scores by prompt
    - Cost efficiency
    - User satisfaction
    - A/B test results

    Helps identify which prompt templates and versions produce the best results.
    """
    langfuse_client = get_enhanced_langfuse_client()

    if not langfuse_client.enabled:
        raise HTTPException(status_code=503, detail="LangFuse not configured")

    try:
        result = {
            "status": "success",
            "filters": {
                "prompt_name": analysis.prompt_name,
                "version_range": {
                    "min": analysis.min_version,
                    "max": analysis.max_version,
                },
                "task_type": analysis.task_type,
            },
            "prompt_performance": {
                "note": "Placeholder for actual LangFuse prompt analytics",
                "example_data": {
                    "code_generation_v2": {
                        "version": "2.1",
                        "success_rate": 0.92,
                        "avg_quality_score": 0.87,
                        "avg_iterations": 1.2,
                        "user_satisfaction": 0.89,
                        "total_uses": 456,
                    },
                    "code_generation_v1": {
                        "version": "1.0",
                        "success_rate": 0.78,
                        "avg_quality_score": 0.72,
                        "avg_iterations": 1.8,
                        "user_satisfaction": 0.75,
                        "total_uses": 789,
                    },
                },
            },
            "insights": [
                "Version 2.1 shows 18% higher success rate",
                "Version 2.1 requires 33% fewer iterations",
                "User satisfaction improved by 19%",
                "Recommendation: Migrate all traffic to version 2.1",
            ],
        }

        logger.info(f"Prompt effectiveness analysis requested: prompt={analysis.prompt_name}")
        return result

    except Exception as e:
        logger.error(f"Failed to analyze prompt effectiveness: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/summary")
async def get_session_summary(request: Request, summary_req: SessionSummaryRequest):
    """
    Get summary analytics for coding sessions.

    This endpoint provides session-level insights:
    - Total sessions and duration
    - Task completion rates
    - Most common task types
    - Average quality scores
    - Cost breakdown
    - User patterns

    Useful for understanding overall coding assistant performance.
    """
    langfuse_client = get_enhanced_langfuse_client()

    if not langfuse_client.enabled:
        raise HTTPException(status_code=503, detail="LangFuse not configured")

    try:
        result = {
            "status": "success",
            "filters": {
                "user_id": summary_req.user_id,
                "session_id": summary_req.session_id,
                "date_range": {
                    "start": summary_req.start_date,
                    "end": summary_req.end_date,
                },
                "assistant_type": summary_req.assistant_type,
            },
            "summary": {
                "note": "Placeholder for actual LangFuse session analytics",
                "total_sessions": 156,
                "total_requests": 2347,
                "total_duration_hours": 42.5,
                "avg_session_duration_min": 16.3,
                "task_completion_rate": 0.89,
                "avg_quality_score": 0.84,
                "total_cost_usd": 127.45,
                "avg_cost_per_session": 0.82,
            },
            "task_breakdown": {
                "code_generation": {"count": 1234, "success_rate": 0.92},
                "debugging": {"count": 567, "success_rate": 0.85},
                "refactoring": {"count": 345, "success_rate": 0.91},
                "documentation": {"count": 201, "success_rate": 0.95},
            },
            "language_breakdown": {
                "python": 45.3,
                "javascript": 28.7,
                "typescript": 15.2,
                "other": 10.8,
            },
            "insights": [
                "Documentation tasks have highest success rate (95%)",
                "Python dominates usage (45% of requests)",
                "Average session duration trending down (more efficient)",
                "Cost per successful task: $0.92",
            ],
        }

        logger.info(
            f"Session summary requested: user={summary_req.user_id}, "
            f"session={summary_req.session_id}"
        )
        return result

    except Exception as e:
        logger.error(f"Failed to get session summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs/breakdown")
async def get_cost_breakdown(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    group_by: str = Query("model", description="Group by: model, provider, user, task_type"),
):
    """
    Get detailed cost breakdown and optimization insights.

    This endpoint provides cost analytics:
    - Total costs by model/provider
    - Cost per task type
    - Cost trends over time
    - Most expensive operations
    - Cost optimization recommendations

    Helps identify opportunities to reduce API costs.
    """
    langfuse_client = get_enhanced_langfuse_client()

    if not langfuse_client.enabled:
        raise HTTPException(status_code=503, detail="LangFuse not configured")

    try:
        result = {
            "status": "success",
            "filters": {
                "date_range": {"start": start_date, "end": end_date},
                "group_by": group_by,
            },
            "total_cost_usd": 127.45,
            "breakdown": {
                "note": "Placeholder for actual cost analytics",
                "by_model": {
                    "claude-3-sonnet-20240229": 45.23,
                    "gpt-4-turbo": 52.18,
                    "gpt-3.5-turbo": 18.34,
                    "claude-3-haiku-20240307": 11.70,
                },
                "by_task_type": {
                    "code_generation": 67.89,
                    "debugging": 32.45,
                    "refactoring": 18.23,
                    "documentation": 8.88,
                },
            },
            "insights": [
                "GPT-4 Turbo accounts for 41% of costs but only 32% of requests",
                "Switching debugging tasks to Claude Haiku could save $18/month",
                "Code generation tasks: 53% of cost, 43% of requests",
                "Recommendation: Use cheaper models for simpler tasks",
            ],
            "optimization_opportunities": [
                {
                    "description": "Use Claude Haiku for simple tasks",
                    "potential_savings_usd": 24.50,
                    "impact": "19% cost reduction",
                },
                {
                    "description": "Optimize prompts to reduce token usage",
                    "potential_savings_usd": 15.30,
                    "impact": "12% cost reduction",
                },
            ],
        }

        logger.info(f"Cost breakdown requested: group_by={group_by}")
        return result

    except Exception as e:
        logger.error(f"Failed to get cost breakdown: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/trends")
async def get_quality_trends(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    granularity: str = Query("day", description="Granularity: hour, day, week, month"),
    metric: str = Query("overall", description="Metric: overall, syntax, style, complexity, security"),
):
    """
    Get code quality trends over time.

    This endpoint provides trend analysis for:
    - Code quality scores over time
    - Improvement/degradation patterns
    - Model performance trends
    - User satisfaction trends

    Helps track whether code generation quality is improving.
    """
    langfuse_client = get_enhanced_langfuse_client()

    if not langfuse_client.enabled:
        raise HTTPException(status_code=503, detail="LangFuse not configured")

    try:
        result = {
            "status": "success",
            "filters": {
                "date_range": {"start": start_date, "end": end_date},
                "granularity": granularity,
                "metric": metric,
            },
            "trend_data": {
                "note": "Placeholder for actual trend data",
                "time_series": [
                    {"date": "2024-11-14", "avg_score": 0.78, "count": 145},
                    {"date": "2024-11-15", "avg_score": 0.82, "count": 167},
                    {"date": "2024-11-16", "avg_score": 0.85, "count": 156},
                    {"date": "2024-11-17", "avg_score": 0.87, "count": 178},
                    {"date": "2024-11-18", "avg_score": 0.89, "count": 189},
                ],
            },
            "statistics": {
                "overall_trend": "improving",
                "improvement_rate": "+14.1% over period",
                "best_day": "2024-11-18",
                "worst_day": "2024-11-14",
            },
            "insights": [
                "Quality scores improving steadily (+14% over 5 days)",
                "Prompt v2.1 rollout correlates with improvement",
                "Syntax scores remain consistently high (>95%)",
                "Security scores show room for improvement",
            ],
        }

        logger.info(f"Quality trends requested: metric={metric}, granularity={granularity}")
        return result

    except Exception as e:
        logger.error(f"Failed to get quality trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assistants/comparison")
async def compare_assistants(
    request: Request,
    assistants: Optional[str] = Query(None, description="Comma-separated assistant types"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
):
    """
    Compare different coding assistants (Cursor, VSCode Copilot, Claude Code, etc.).

    This endpoint provides comparative analytics:
    - Success rates by assistant
    - Speed comparisons
    - Cost comparisons
    - User preference
    - Task type suitability

    Helps determine which assistant performs best for different scenarios.
    """
    langfuse_client = get_enhanced_langfuse_client()

    if not langfuse_client.enabled:
        raise HTTPException(status_code=503, detail="LangFuse not configured")

    try:
        assistant_list = assistants.split(",") if assistants else None

        result = {
            "status": "success",
            "filters": {
                "assistants": assistant_list,
                "date_range": {"start": start_date, "end": end_date},
            },
            "comparison": {
                "note": "Placeholder for actual assistant comparison",
                "cursor": {
                    "success_rate": 0.91,
                    "avg_speed_ms": 2300,
                    "avg_cost_usd": 0.028,
                    "user_satisfaction": 0.89,
                    "total_sessions": 456,
                },
                "vscode-copilot": {
                    "success_rate": 0.87,
                    "avg_speed_ms": 2800,
                    "avg_cost_usd": 0.032,
                    "user_satisfaction": 0.85,
                    "total_sessions": 389,
                },
                "claude-code": {
                    "success_rate": 0.93,
                    "avg_speed_ms": 2100,
                    "avg_cost_usd": 0.025,
                    "avg_satisfaction": 0.91,
                    "total_sessions": 567,
                },
            },
            "insights": [
                "Claude Code shows highest success rate (93%)",
                "Claude Code is fastest (2100ms average)",
                "Claude Code is most cost-effective ($0.025/task)",
                "User satisfaction: Claude Code > Cursor > VSCode Copilot",
            ],
            "recommendations": [
                "Claude Code recommended for most tasks",
                "Cursor performs well for complex refactoring",
                "VSCode Copilot suitable for simple autocompletions",
            ],
        }

        logger.info(f"Assistant comparison requested: assistants={assistant_list}")
        return result

    except Exception as e:
        logger.error(f"Failed to compare assistants: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def analytics_health_check():
    """Health check for analytics service."""
    langfuse_client = get_enhanced_langfuse_client()

    return {
        "status": "healthy",
        "service": "analytics-api",
        "langfuse_enabled": langfuse_client.enabled,
    }
