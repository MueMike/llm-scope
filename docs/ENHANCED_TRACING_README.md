# Enhanced LangFuse Tracing for Agentic Coding

> **Version**: 1.0.0
> **Status**: Production Ready
> **Last Updated**: 2024-11-18

## Overview

This enhancement brings comprehensive **Agentic Coding Tracing** capabilities to the LiteLLM Proxy, enabling data-driven insights into AI coding assistant performance. The system automatically tracks, analyzes, and scores code generation quality while providing powerful analytics to answer critical questions about model performance, cost efficiency, and user satisfaction.

### Key Question This Solves

**"Which LLM models, prompts, and coding assistants deliver the best results for software development?"**

With these enhancements, you can now:
- ✅ Compare code quality across different models (Claude, GPT-4, GPT-3.5, etc.)
- ✅ Identify which prompts lead to successful outcomes
- ✅ Track cost vs quality tradeoffs
- ✅ Measure real-world coding assistant performance
- ✅ Optimize based on data, not intuition

## What's New

### 1. Automatic Code Quality Scoring ⭐

Every code generation is automatically analyzed for:

| Metric | Description | Weight |
|--------|-------------|---------|
| **Syntax Correctness** | Does the code compile/parse? | 30% |
| **Style Compliance** | Follows language conventions (PEP8, ESLint, etc.) | 20% |
| **Complexity** | Cyclomatic complexity, nesting depth | 25% |
| **Security** | Common vulnerabilities (OWASP issues) | 25% |

**Supported Languages**: Python, JavaScript, TypeScript (with basic support for Java, Go, Rust)

**Example Output**:
```json
{
  "code_quality_overall": 0.85,
  "code_quality_syntax": 1.0,
  "code_quality_style": 0.80,
  "code_quality_complexity": 0.75,
  "code_quality_security": 0.90
}
```

### 2. Enhanced Tracing Capabilities

#### Events (Point-in-Time Actions)
Track discrete actions like:
- `code_accepted` - User accepted the generated code
- `code_rejected` - User rejected the code
- `code_executed` - Code was run/tested
- `test_passed` - Tests executed successfully
- `user_feedback_given` - User provided feedback

#### Multi-Dimensional Scoring
Add multiple quality dimensions to any trace or generation:
```python
{
  "code_quality": 0.85,
  "readability": 0.90,
  "documentation": 0.75,
  "test_coverage": 0.80,
  "performance": 0.88
}
```

#### Hierarchical Spans
Track complex multi-step workflows:
```
Trace: Coding Session
  ├─ Span: Code Generation
  │   ├─ Generation: LLM Call
  │   ├─ Event: Code Analysis
  │   └─ Score: Quality Metrics
  ├─ Span: Code Review
  │   ├─ Generation: Review LLM Call
  │   └─ Event: Feedback Given
  └─ Span: Test Generation
      ├─ Generation: Test LLM Call
      └─ Event: Tests Executed
```

### 3. Analytics & Insights API

New endpoints to answer business questions:

#### `/analytics/models/compare`
**Question**: "Which model produces the best code for my use case?"

**Response**:
```json
{
  "comparison": {
    "claude-3-sonnet-20240229": {
      "avg_quality_score": 0.85,
      "avg_cost_usd": 0.023,
      "success_rate": 0.92,
      "user_satisfaction": 0.88
    },
    "gpt-4-turbo": {
      "avg_quality_score": 0.82,
      "avg_cost_usd": 0.045,
      "success_rate": 0.89,
      "user_satisfaction": 0.85
    }
  },
  "insights": [
    "Claude Sonnet shows 3.7% higher quality score",
    "Claude Sonnet is 49% more cost-effective",
    "Recommendation: Use Claude Sonnet for this task type"
  ]
}
```

#### `/analytics/prompts/effectiveness`
**Question**: "Which prompt version performs best?"

Track A/B test results and prompt optimization.

#### `/analytics/sessions/summary`
**Question**: "How productive are our coding sessions?"

Get session-level metrics: duration, completion rates, costs, language breakdown.

#### `/analytics/costs/breakdown`
**Question**: "Where can we reduce API costs?"

Identify optimization opportunities with potential savings.

#### `/analytics/quality/trends`
**Question**: "Is our code quality improving over time?"

Track quality scores over time with trend analysis.

#### `/analytics/assistants/comparison`
**Question**: "Which coding assistant performs best?"

Compare Cursor vs VSCode Copilot vs Claude Code vs others.

### 4. User Feedback Collection

Capture real user feedback:

```python
# Thumbs up/down
{
  "trace_id": "trace-123",
  "feedback_type": "thumbs_up",
  "value": true,
  "comment": "Perfect solution!"
}

# Star rating (1-5)
{
  "trace_id": "trace-123",
  "feedback_type": "rating",
  "value": 5,
  "comment": "Excellent code quality"
}

# Code acceptance
{
  "trace_id": "trace-123",
  "feedback_type": "code_accepted",
  "value": "full",  # full, partial, rejected
  "metadata": {
    "time_to_decision_ms": 3500,
    "modifications_needed": false
  }
}
```

## Architecture

### Data Flow

```
┌──────────────┐
│ IDE Request  │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────┐
│  LiteLLM Proxy                  │
│  ┌───────────────────────────┐  │
│  │ 1. Create Trace           │  │
│  │    - User, Session, Meta  │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ 2. LLM Generation         │  │
│  │    - Call Model           │  │
│  │    - Record Tokens/Cost   │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ 3. Code Quality Analysis  │  │
│  │    - Extract Code Blocks  │  │
│  │    - Analyze Quality      │  │
│  │    - Create Event         │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ 4. Add Scores             │  │
│  │    - Multi-dimensional    │  │
│  │    - Automated Metrics    │  │
│  └───────────────────────────┘  │
└─────────┬───────────────────────┘
          │
          ▼
    ┌─────────────┐
    │  LangFuse   │
    │  Dashboard  │
    └─────────────┘
```

### Trace Structure

```json
{
  "name": "chat_completion",
  "user_id": "developer@example.com",
  "session_id": "session-uuid",
  "metadata": {
    "endpoint": "/chat/completions",
    "provider": "anthropic",
    "model": "claude-3-sonnet-20240229",
    "language": "python",
    "task_type": "code_generation",
    "task_complexity": "medium"
  },
  "tags": ["anthropic", "claude-3-sonnet-20240229", "chat"],
  "observations": [
    {
      "type": "generation",
      "name": "llm_generation",
      "input": [...],
      "output": [...],
      "usage": {
        "prompt_tokens": 1500,
        "completion_tokens": 800,
        "total_tokens": 2300
      },
      "metadata": {
        "cost_usd": 0.0234
      },
      "scores": {
        "code_quality_overall": 0.85,
        "code_quality_syntax": 1.0,
        "code_quality_style": 0.80,
        "code_quality_complexity": 0.75,
        "code_quality_security": 0.90
      }
    },
    {
      "type": "event",
      "name": "code_quality_analysis",
      "metadata": {
        "language": "python",
        "num_issues": 2,
        "num_suggestions": 3
      }
    }
  ]
}
```

## Quick Start

### 1. Ensure LangFuse is Configured

```bash
# .env file
LANGFUSE_PUBLIC_KEY=pk_...
LANGFUSE_SECRET_KEY=sk_...
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_ENABLED=true
```

### 2. Start the Proxy

```bash
python main.py
```

### 3. Make a Chat Completion Request

```python
import requests

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    json={
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Write a Python function to sort a list"}
        ],
        "metadata": {
            "language": "python",
            "task_type": "code_generation"
        }
    },
    headers={
        "X-User-ID": "developer@example.com",
        "X-Session-ID": "session-123"
    }
)
```

**What happens automatically:**
1. ✅ Trace created in LangFuse
2. ✅ Code generated by LLM
3. ✅ Code quality analyzed (syntax, style, complexity, security)
4. ✅ Scores added to LangFuse
5. ✅ Events logged
6. ✅ All data available in LangFuse dashboard

### 4. Check LangFuse Dashboard

Navigate to https://cloud.langfuse.com and view:
- Traces with full context
- Code quality scores
- Token usage and costs
- Session analytics

### 5. Submit User Feedback

```python
import requests

requests.post(
    "http://localhost:8000/analytics/feedback",
    json={
        "trace_id": "trace-123",
        "feedback_type": "thumbs_up",
        "value": True,
        "comment": "Great code!"
    }
)
```

### 6. Query Analytics

```python
import requests

# Compare models
response = requests.post(
    "http://localhost:8000/analytics/models/compare",
    json={
        "models": ["claude-3-sonnet-20240229", "gpt-4-turbo"],
        "task_type": "code_generation",
        "language": "python",
        "metric": "quality"
    }
)

print(response.json()["insights"])
# Output:
# [
#   "Claude Sonnet shows 3.7% higher quality score",
#   "Claude Sonnet is 49% more cost-effective",
#   "Recommendation: Use Claude Sonnet for this task type"
# ]
```

## Usage Examples

See `/examples/enhanced_tracing_examples.py` for comprehensive examples:

1. **Code Generation with Quality Analysis** - Automatic scoring
2. **Submit User Feedback** - Thumbs up/down, ratings, acceptance
3. **Submit Custom Scores** - Manual quality dimensions
4. **Compare Models** - Which model is best?
5. **Analyze Prompt Effectiveness** - A/B testing results
6. **Get Session Summary** - Productivity metrics
7. **Get Cost Breakdown** - Optimization opportunities
8. **Compare Assistants** - Cursor vs VSCode Copilot vs others

Run all examples:
```bash
python examples/enhanced_tracing_examples.py
```

## API Reference

### Analytics Endpoints

#### POST `/analytics/feedback`
Submit user feedback on generated code.

**Request**:
```json
{
  "trace_id": "string",
  "feedback_type": "thumbs_up|thumbs_down|rating|code_accepted",
  "value": "boolean|number|string",
  "comment": "string (optional)",
  "metadata": {} (optional)
}
```

**Response**: `201 Created`

---

#### POST `/analytics/scores`
Submit manual quality scores.

**Request**:
```json
{
  "trace_id": "string",
  "observation_id": "string (optional)",
  "scores": {
    "score_name": number,
    ...
  },
  "config_id": "string (optional)"
}
```

**Response**: `201 Created`

---

#### POST `/analytics/models/compare`
Compare LLM model performance.

**Request**:
```json
{
  "models": ["string", ...] (optional),
  "task_type": "string (optional)",
  "language": "string (optional)",
  "start_date": "ISO 8601 (optional)",
  "end_date": "ISO 8601 (optional)",
  "metric": "quality|cost|speed|satisfaction"
}
```

**Response**: `200 OK` with comparison data and insights.

---

#### POST `/analytics/prompts/effectiveness`
Analyze prompt version effectiveness.

**Request**:
```json
{
  "prompt_name": "string (optional)",
  "min_version": number (optional),
  "max_version": number (optional),
  "task_type": "string (optional)"
}
```

**Response**: `200 OK` with performance data by prompt version.

---

#### POST `/analytics/sessions/summary`
Get session-level analytics.

**Request**:
```json
{
  "user_id": "string (optional)",
  "session_id": "string (optional)",
  "start_date": "ISO 8601 (optional)",
  "end_date": "ISO 8601 (optional)",
  "assistant_type": "string (optional)"
}
```

**Response**: `200 OK` with session statistics.

---

#### GET `/analytics/costs/breakdown`
Get cost breakdown and optimization insights.

**Query Parameters**:
- `start_date`: ISO 8601 date
- `end_date`: ISO 8601 date
- `group_by`: `model|provider|user|task_type`

**Response**: `200 OK` with cost data and optimization opportunities.

---

#### GET `/analytics/quality/trends`
Get code quality trends over time.

**Query Parameters**:
- `start_date`: ISO 8601 date
- `end_date`: ISO 8601 date
- `granularity`: `hour|day|week|month`
- `metric`: `overall|syntax|style|complexity|security`

**Response**: `200 OK` with time-series data.

---

#### GET `/analytics/assistants/comparison`
Compare coding assistant performance.

**Query Parameters**:
- `assistants`: Comma-separated list (e.g., `cursor,vscode-copilot`)
- `start_date`: ISO 8601 date
- `end_date`: ISO 8601 date

**Response**: `200 OK` with assistant comparison data.

## Code Quality Analyzer

### Scoring Algorithm

```python
overall_score = (
    syntax_correctness * 0.30 +
    style_compliance * 0.20 +
    complexity_score * 0.25 +
    security_score * 0.25
)
```

### Python Analysis

| Check | Tool | Description |
|-------|------|-------------|
| Syntax | AST Parser | Validates code compiles |
| Style | Regex Patterns | Basic PEP8 checks |
| Complexity | AST Analysis | Cyclomatic complexity, nesting |
| Security | Pattern Matching | OWASP common vulnerabilities |

**Security Patterns Detected**:
- `eval()` / `exec()` usage
- Hardcoded passwords/API keys
- SQL injection patterns
- Command injection (`os.system`, `subprocess`)
- Pickle deserialization
- And more...

### JavaScript/TypeScript Analysis

| Check | Tool | Description |
|-------|------|-------------|
| Syntax | Basic Validation | Brace/parenthesis matching |
| Style | Regex Patterns | `var` usage, `==` vs `===` |
| Complexity | Keyword Counting | Control flow complexity |
| Security | Pattern Matching | XSS, eval, innerHTML |

**Security Patterns Detected**:
- `eval()` usage
- `innerHTML` XSS risk
- `dangerouslySetInnerHTML`
- Command injection
- Hardcoded credentials

### Extending to Other Languages

Add support for new languages in `/src/utils/code_quality.py`:

```python
def _analyze_your_language(self, code: str) -> QualityScore:
    # Implement syntax checking
    # Implement style checking
    # Implement complexity analysis
    # Implement security scanning
    return QualityScore(...)
```

## Testing

### Run Tests

```bash
# All tests
pytest

# Enhanced features only
pytest tests/test_enhanced_features.py -v

# With coverage
pytest --cov=src tests/test_enhanced_features.py
```

### Test Coverage

The test suite includes:
- ✅ Code quality analyzer (syntax, style, complexity, security)
- ✅ Analytics endpoints (all 8 endpoints)
- ✅ Feedback submission
- ✅ Score submission
- ✅ Integration tests
- ✅ Performance tests

## Configuration

### Environment Variables

```bash
# LangFuse Configuration
LANGFUSE_PUBLIC_KEY=pk_...
LANGFUSE_SECRET_KEY=sk_...
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_ENABLED=true

# Feature Flags
CODE_QUALITY_ANALYSIS_ENABLED=true
ANALYTICS_ENABLED=true

# Logging
LOG_LEVEL=INFO
DEBUG_MODE=false
```

### Custom Quality Weights

Modify weights in `/src/utils/code_quality.py`:

```python
WEIGHTS = {
    "syntax_correctness": 0.30,   # Adjust as needed
    "style_compliance": 0.20,
    "complexity_score": 0.25,
    "security_score": 0.25,
}
```

## Best Practices

### 1. Always Include Metadata

```json
{
  "metadata": {
    "language": "python",
    "task_type": "code_generation",
    "task_complexity": "medium",
    "project_type": "web-app",
    "framework": "fastapi"
  }
}
```

This enables better filtering and analysis in analytics queries.

### 2. Use Consistent Session IDs

Group related requests with the same `X-Session-ID` header:

```python
headers = {
    "X-User-ID": "user@example.com",
    "X-Session-ID": "session-abc-123"  # Same for entire coding session
}
```

### 3. Collect User Feedback

Always submit feedback after code acceptance/rejection:

```python
# User accepted code
requests.post("/analytics/feedback", json={
    "trace_id": trace_id,
    "feedback_type": "code_accepted",
    "value": "full",
    "metadata": {"time_to_decision_ms": 3500}
})
```

### 4. Regular Analytics Review

Schedule regular reviews of:
- Model performance trends
- Cost optimization opportunities
- Quality score improvements
- User satisfaction metrics

### 5. A/B Test Prompts

Use prompt versioning to test improvements:

```python
# Version 1
{
  "metadata": {
    "prompt_name": "code_generation",
    "prompt_version": 1
  }
}

# Version 2 (improved)
{
  "metadata": {
    "prompt_name": "code_generation",
    "prompt_version": 2
  }
}

# Compare with /analytics/prompts/effectiveness
```

## Roadmap

### Planned Features

- [ ] **Machine Learning Predictions** - Predict code quality before generation
- [ ] **Automated Alerts** - Notify when quality drops or costs spike
- [ ] **Custom Analyzers** - Plugin system for domain-specific checks
- [ ] **IDE Extensions** - Native IDE integration for feedback
- [ ] **Dataset Creation** - Auto-create training datasets from traces
- [ ] **Experiment Tracking** - Full experiment management
- [ ] **Real-time Dashboards** - Live monitoring via Grafana/Streamlit
- [ ] **Advanced NLP Analysis** - Semantic code understanding
- [ ] **Performance Profiling** - Actual code execution performance

### Future Language Support

- [ ] Java (full AST analysis)
- [ ] Go (full analysis)
- [ ] Rust (full analysis)
- [ ] C/C++ (basic analysis)
- [ ] Ruby (basic analysis)
- [ ] PHP (basic analysis)

## Troubleshooting

### Issue: Code Quality Scores Not Appearing

**Solution**:
1. Ensure response contains code blocks (wrapped in ```)
2. Check logs for analysis errors
3. Verify language is supported
4. Check LangFuse dashboard for events

### Issue: Analytics Endpoints Return 503

**Solution**:
1. Verify `LANGFUSE_ENABLED=true`
2. Check LangFuse credentials
3. Ensure LangFuse host is accessible
4. Review startup logs for connection errors

### Issue: Scores Seem Inaccurate

**Solution**:
1. Review scoring weights (might need adjustment)
2. Check language-specific patterns
3. Verify code extraction is working correctly
4. Add more sophisticated analyzers for your language

## Contributing

We welcome contributions! Areas where help is needed:

1. **Language Analyzers** - Add support for more languages
2. **Security Patterns** - Expand security vulnerability detection
3. **Analytics Queries** - Implement actual LangFuse API queries
4. **Visualizations** - Create dashboards and reports
5. **Documentation** - Improve examples and guides

See `CONTRIBUTING.md` for guidelines.

## License

Same as main project.

## Support

- **Issues**: https://github.com/MueMike/llm-scope/issues
- **Discussions**: https://github.com/MueMike/llm-scope/discussions
- **Documentation**: https://github.com/MueMike/llm-scope/tree/main/docs

---

**Built with ❤️ for AI-powered software development**
