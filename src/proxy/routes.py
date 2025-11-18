"""API route definitions."""

import logging
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

import litellm

from ..integrations import LangFuseClient
from ..integrations.langfuse_enhanced import get_enhanced_langfuse_client
from ..integrations.llm_providers import get_model_provider
from ..monitoring import get_metrics_collector
from ..utils import calculate_cost, extract_metadata
from ..utils.code_quality import get_code_quality_analyzer

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatCompletionRequest(BaseModel):
    """Chat completion request model."""

    model: str
    messages: list
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    stream: Optional[bool] = False
    user: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatCompletionResponse(BaseModel):
    """Chat completion response model."""

    id: str
    object: str
    created: int
    model: str
    choices: list
    usage: Optional[Dict[str, int]] = None


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "litellm-proxy-langfuse"}


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    return {"status": "ready", "service": "litellm-proxy-langfuse"}


@router.post("/v1/chat/completions")
@router.post("/chat/completions")
async def chat_completions(
    request: Request,
    completion_request: ChatCompletionRequest,
):
    """
    Handle chat completion requests.
    
    Args:
        request: FastAPI request
        completion_request: Chat completion request data
        
    Returns:
        Chat completion response
    """
    start_time = time.time()
    metrics_collector = get_metrics_collector()
    
    # Extract metadata
    model = completion_request.model
    provider = get_model_provider(model)
    messages = completion_request.messages
    
    # Get trace info from request state
    trace_id = getattr(request.state, "trace_id", None)
    user_id = request.headers.get("X-User-ID", completion_request.user or "anonymous")
    session_id = request.headers.get("X-Session-ID", trace_id)
    
    # Get LangFuse client from request state
    langfuse_client = getattr(request.state, "langfuse_client", None)
    
    # Increment active requests
    metrics_collector.inc_active_requests(model, provider)
    
    try:
        # Get enhanced LangFuse client (fallback to basic if enhanced unavailable)
        enhanced_client = get_enhanced_langfuse_client()

        # Create LangFuse trace if enabled
        trace = None
        generation_id = None

        if langfuse_client and langfuse_client.enabled:
            # Prepare enhanced metadata
            metadata = extract_metadata(completion_request.dict())
            metadata.update({
                "endpoint": "/chat/completions",
                "provider": provider,
                "model": model,
                "trace_id": trace_id,
            })

            # Add custom metadata from request
            if completion_request.metadata:
                metadata.update(completion_request.metadata)

            # Use enhanced client if available, otherwise fallback to basic
            if enhanced_client and enhanced_client.enabled:
                trace = enhanced_client.create_trace(
                    name="chat_completion",
                    user_id=user_id,
                    session_id=session_id,
                    metadata=metadata,
                    tags=[provider, model, "chat"],
                    input_data={"messages": messages},
                )
            else:
                trace = langfuse_client.create_trace(
                    name="chat_completion",
                    user_id=user_id,
                    session_id=session_id,
                    metadata=metadata,
                    tags=[provider, model],
                )
        
        # Call LiteLLM
        logger.info(f"Calling LiteLLM with model: {model}")
        
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            temperature=completion_request.temperature,
            max_tokens=completion_request.max_tokens,
            top_p=completion_request.top_p,
            frequency_penalty=completion_request.frequency_penalty,
            presence_penalty=completion_request.presence_penalty,
            stream=completion_request.stream,
            user=user_id,
        )
        
        # Calculate metrics
        duration = time.time() - start_time
        
        # Extract usage info
        usage = response.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        # Calculate cost
        cost = calculate_cost(model, prompt_tokens, completion_tokens, provider)
        
        # Record metrics
        metrics_collector.record_request(
            model=model,
            provider=provider,
            status="success",
            duration=duration,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost,
        )
        
        # Create LangFuse generation if trace exists
        if trace and langfuse_client and langfuse_client.enabled:
            # Use enhanced client if available
            if enhanced_client and enhanced_client.enabled:
                generation = enhanced_client.create_generation(
                    trace_id=trace.id if hasattr(trace, "id") else trace_id,
                    name="llm_generation",
                    model=model,
                    input_data=messages,
                    output_data=response.get("choices", []),
                    metadata={
                        "provider": provider,
                        "temperature": completion_request.temperature,
                        "max_tokens": completion_request.max_tokens,
                        "cost_usd": cost,
                    },
                    usage={
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens,
                    },
                    start_time=start_time,
                    end_time=time.time(),
                )

                # Store generation ID for potential scoring
                if generation and hasattr(generation, "id"):
                    generation_id = generation.id

            else:
                langfuse_client.create_generation(
                    trace_id=trace.id if hasattr(trace, "id") else trace_id,
                    name="llm_generation",
                    model=model,
                    input_data=messages,
                    output_data=response.get("choices", []),
                    metadata={
                        "provider": provider,
                        "temperature": completion_request.temperature,
                        "max_tokens": completion_request.max_tokens,
                    },
                    usage={
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens,
                    },
                    start_time=start_time,
                    end_time=time.time(),
                )

        # Attempt to analyze code quality if response contains code
        if enhanced_client and enhanced_client.enabled and trace:
            try:
                # Extract generated text from response
                choices = response.get("choices", [])
                if choices:
                    generated_text = choices[0].get("message", {}).get("content", "")

                    # Check if response contains code (basic heuristic)
                    has_code = (
                        "```" in generated_text
                        or "def " in generated_text
                        or "function " in generated_text
                        or "class " in generated_text
                    )

                    if has_code and len(generated_text) > 20:
                        # Extract code blocks (simple extraction)
                        code_blocks = []
                        if "```" in generated_text:
                            parts = generated_text.split("```")
                            for i, part in enumerate(parts):
                                if i % 2 == 1:  # Odd indices are code blocks
                                    # Remove language identifier
                                    lines = part.strip().split("\n")
                                    if lines:
                                        # First line might be language, skip if it's short
                                        if len(lines[0]) < 20:
                                            code_blocks.append("\n".join(lines[1:]))
                                        else:
                                            code_blocks.append(part.strip())

                        # Analyze each code block
                        if code_blocks:
                            analyzer = get_code_quality_analyzer()

                            for idx, code in enumerate(code_blocks):
                                # Detect language from request metadata or code
                                language = "python"  # Default
                                if completion_request.metadata:
                                    language = completion_request.metadata.get("language", "python")

                                # Analyze quality
                                quality_score = analyzer.analyze(code, language)

                                # Create event for code analysis
                                enhanced_client.create_event(
                                    trace_id=trace.id if hasattr(trace, "id") else trace_id,
                                    name="code_quality_analysis",
                                    metadata={
                                        "block_index": idx,
                                        "language": language,
                                        "code_length": len(code),
                                        **quality_score.to_dict(),
                                    },
                                    parent_observation_id=generation_id,
                                )

                                # Add scores
                                if generation_id:
                                    enhanced_client.add_multi_dimensional_score(
                                        trace_id=trace.id if hasattr(trace, "id") else trace_id,
                                        observation_id=generation_id,
                                        scores=quality_score.get_scores_dict(),
                                        config_id="automated_code_quality_v1",
                                    )

                                logger.info(
                                    f"Code quality analysis: overall={quality_score.overall:.3f}, "
                                    f"syntax={quality_score.syntax_correctness:.3f}, "
                                    f"security={quality_score.security_score:.3f}"
                                )

            except Exception as e:
                # Don't fail the request if quality analysis fails
                logger.warning(f"Code quality analysis failed: {e}")

        logger.info(
            f"Chat completion successful: model={model}, "
            f"tokens={prompt_tokens + completion_tokens}, "
            f"cost=${cost:.6f}, duration={duration:.3f}s"
        )

        return response
        
    except Exception as e:
        duration = time.time() - start_time
        
        # Record error metrics
        metrics_collector.record_request(
            model=model,
            provider=provider,
            status="error",
            duration=duration,
        )
        metrics_collector.record_error(model, provider, type(e).__name__)
        
        logger.error(f"Chat completion failed: {e}", exc_info=True)
        
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Decrement active requests
        metrics_collector.dec_active_requests(model, provider)


@router.get("/v1/models")
@router.get("/models")
async def list_models():
    """
    List available models.
    
    Returns:
        List of available models
    """
    # This should be populated from config in production
    models = [
        {"id": "gpt-4-turbo-preview", "object": "model", "owned_by": "openai"},
        {"id": "gpt-4", "object": "model", "owned_by": "openai"},
        {"id": "gpt-3.5-turbo", "object": "model", "owned_by": "openai"},
        {"id": "claude-3-opus-20240229", "object": "model", "owned_by": "anthropic"},
        {"id": "claude-3-sonnet-20240229", "object": "model", "owned_by": "anthropic"},
        {"id": "claude-3-haiku-20240307", "object": "model", "owned_by": "anthropic"},
    ]
    
    return {"object": "list", "data": models}
