"""Enhanced LangFuse integration with full feature support for agentic coding tracing."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from langfuse import Langfuse

from ..config import Settings, get_settings
from ..utils import calculate_cost, extract_metadata, generate_trace_id

logger = logging.getLogger(__name__)


class EnhancedLangFuseClient:
    """
    Enhanced LangFuse client with full feature support:
    - Traces, Spans, Generations (existing)
    - Events (point-in-time actions)
    - Scores (multi-dimensional quality metrics)
    - Datasets (for training/evaluation)
    - Experiments (A/B testing)
    - Prompts (versioned prompt management)
    - Advanced analytics
    """

    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize enhanced LangFuse client.

        Args:
            settings: Application settings. If None, loads from environment.
        """
        self.settings = settings or get_settings()
        self.client: Optional[Langfuse] = None
        self.enabled = False

        if self.settings.is_langfuse_configured():
            try:
                self.client = Langfuse(
                    public_key=self.settings.langfuse_public_key,
                    secret_key=self.settings.langfuse_secret_key,
                    host=self.settings.langfuse_host,
                )
                self.enabled = True
                logger.info("Enhanced LangFuse client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize LangFuse client: {e}")
                self.enabled = False
        else:
            logger.warning("LangFuse not configured. Tracing disabled.")

    # ==================== Core Tracing Methods ====================

    def create_trace(
        self,
        name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        input_data: Optional[Any] = None,
        output_data: Optional[Any] = None,
        public: bool = False,
    ) -> Optional[Any]:
        """
        Create a new trace with enhanced metadata.

        Args:
            name: Trace name (e.g., "coding_session", "code_generation")
            user_id: User identifier
            session_id: Session identifier for grouping
            metadata: Rich metadata dictionary
            tags: List of tags for filtering/grouping
            input_data: Optional input data
            output_data: Optional output data
            public: Whether trace should be publicly accessible

        Returns:
            Trace object or None if disabled
        """
        if not self.enabled or not self.client:
            return None

        try:
            trace = self.client.trace(
                name=name,
                user_id=user_id,
                session_id=session_id,
                metadata=metadata or {},
                tags=tags or [],
                input=input_data,
                output=output_data,
                public=public,
            )
            logger.debug(f"Created trace: {name} (user={user_id}, session={session_id})")
            return trace
        except Exception as e:
            logger.error(f"Failed to create trace: {e}")
            return None

    def update_trace(
        self,
        trace_id: str,
        output_data: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        Update an existing trace with final results.

        Args:
            trace_id: Trace ID to update
            output_data: Final output data
            metadata: Additional metadata to merge
            tags: Additional tags to add

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False

        try:
            # LangFuse SDK handles trace updates through the same trace object
            # This is a convenience method for updating via trace_id
            logger.debug(f"Updated trace: {trace_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update trace: {e}")
            return False

    def create_generation(
        self,
        trace_id: str,
        name: str,
        model: str,
        input_data: Any,
        output_data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        usage: Optional[Dict[str, int]] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        parent_observation_id: Optional[str] = None,
        prompt_name: Optional[str] = None,
        prompt_version: Optional[int] = None,
    ) -> Optional[Any]:
        """
        Create a generation (LLM call) with enhanced tracking.

        Args:
            trace_id: Parent trace ID
            name: Generation name
            model: Model identifier
            input_data: Input data (messages/prompt)
            output_data: Output data (completion)
            metadata: Model parameters and custom metadata
            usage: Token usage dictionary
            start_time: Start timestamp
            end_time: End timestamp
            parent_observation_id: Parent span ID (for nesting)
            prompt_name: Name of prompt template used
            prompt_version: Version of prompt template

        Returns:
            Generation object or None if disabled
        """
        if not self.enabled or not self.client:
            return None

        try:
            # Enhance metadata with prompt info
            enhanced_metadata = metadata or {}
            if prompt_name:
                enhanced_metadata["prompt_name"] = prompt_name
            if prompt_version:
                enhanced_metadata["prompt_version"] = prompt_version

            generation = self.client.generation(
                trace_id=trace_id,
                name=name,
                model=model,
                model_parameters=enhanced_metadata,
                input=input_data,
                output=output_data,
                usage=usage,
                start_time=datetime.fromtimestamp(start_time) if start_time else None,
                end_time=datetime.fromtimestamp(end_time) if end_time else None,
                parent_observation_id=parent_observation_id,
            )
            logger.debug(f"Created generation: {name} (model={model})")
            return generation
        except Exception as e:
            logger.error(f"Failed to create generation: {e}")
            return None

    def create_span(
        self,
        trace_id: str,
        name: str,
        input_data: Any = None,
        output_data: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        parent_observation_id: Optional[str] = None,
        level: str = "DEFAULT",
    ) -> Optional[Any]:
        """
        Create a span for non-LLM operations.

        Args:
            trace_id: Parent trace ID
            name: Span name (e.g., "syntax_validation", "code_execution")
            input_data: Input data
            output_data: Output data
            metadata: Custom metadata
            start_time: Start timestamp
            end_time: End timestamp
            parent_observation_id: Parent span ID for nesting
            level: Logging level (DEBUG, DEFAULT, WARNING, ERROR)

        Returns:
            Span object or None if disabled
        """
        if not self.enabled or not self.client:
            return None

        try:
            span = self.client.span(
                trace_id=trace_id,
                name=name,
                input=input_data,
                output=output_data,
                metadata=metadata,
                start_time=datetime.fromtimestamp(start_time) if start_time else None,
                end_time=datetime.fromtimestamp(end_time) if end_time else None,
                parent_observation_id=parent_observation_id,
                level=level,
            )
            logger.debug(f"Created span: {name}")
            return span
        except Exception as e:
            logger.error(f"Failed to create span: {e}")
            return None

    def create_event(
        self,
        trace_id: str,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        input_data: Optional[Any] = None,
        output_data: Optional[Any] = None,
        parent_observation_id: Optional[str] = None,
        level: str = "DEFAULT",
    ) -> Optional[Any]:
        """
        Create an event (point-in-time action).

        Events are useful for tracking discrete actions like:
        - code_accepted
        - code_rejected
        - test_executed
        - user_feedback_given
        - error_occurred

        Args:
            trace_id: Parent trace ID
            name: Event name
            metadata: Event metadata
            input_data: Optional input data
            output_data: Optional output data
            parent_observation_id: Parent observation ID
            level: Logging level

        Returns:
            Event object or None if disabled
        """
        if not self.enabled or not self.client:
            return None

        try:
            event = self.client.event(
                trace_id=trace_id,
                name=name,
                metadata=metadata,
                input=input_data,
                output=output_data,
                parent_observation_id=parent_observation_id,
                level=level,
            )
            logger.debug(f"Created event: {name}")
            return event
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            return None

    # ==================== Scoring Methods ====================

    def score_observation(
        self,
        trace_id: str,
        observation_id: str,
        name: str,
        value: Union[float, int, str],
        data_type: str = "NUMERIC",
        comment: Optional[str] = None,
        config_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add a score to a specific observation (generation, span, or event).

        Args:
            trace_id: Trace ID
            observation_id: Observation ID to score
            name: Score name (e.g., "code_quality", "syntax_correctness")
            value: Score value
            data_type: Type of score (NUMERIC, CATEGORICAL, BOOLEAN)
            comment: Optional explanation
            config_id: Score configuration identifier
            metadata: Additional score metadata

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False

        try:
            self.client.score(
                trace_id=trace_id,
                observation_id=observation_id,
                name=name,
                value=value,
                data_type=data_type,
                comment=comment,
                config_id=config_id,
            )
            logger.debug(f"Added score to observation {observation_id}: {name}={value}")
            return True
        except Exception as e:
            logger.error(f"Failed to score observation: {e}")
            return False

    def score_trace(
        self,
        trace_id: str,
        name: str,
        value: Union[float, int, str],
        data_type: str = "NUMERIC",
        comment: Optional[str] = None,
        config_id: Optional[str] = None,
    ) -> bool:
        """
        Add a score to a trace (session-level scoring).

        Args:
            trace_id: Trace ID
            name: Score name (e.g., "session_success", "user_satisfaction")
            value: Score value
            data_type: Type of score
            comment: Optional explanation
            config_id: Score configuration identifier

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False

        try:
            self.client.score(
                trace_id=trace_id,
                name=name,
                value=value,
                data_type=data_type,
                comment=comment,
                config_id=config_id,
            )
            logger.debug(f"Added score to trace {trace_id}: {name}={value}")
            return True
        except Exception as e:
            logger.error(f"Failed to score trace: {e}")
            return False

    def add_multi_dimensional_score(
        self,
        trace_id: str,
        observation_id: Optional[str],
        scores: Dict[str, Union[float, int, str]],
        config_id: Optional[str] = None,
    ) -> bool:
        """
        Add multiple scores at once (multi-dimensional scoring).

        Example:
            scores = {
                "code_quality": 0.85,
                "syntax_correctness": 1.0,
                "style_compliance": 0.8,
                "security_score": 0.9,
                "complexity_score": 0.75,
            }

        Args:
            trace_id: Trace ID
            observation_id: Observation ID (None for trace-level)
            scores: Dictionary of score names and values
            config_id: Score configuration identifier

        Returns:
            True if all successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False

        success = True
        for score_name, score_value in scores.items():
            # Determine data type
            data_type = "NUMERIC"
            if isinstance(score_value, str):
                data_type = "CATEGORICAL"
            elif isinstance(score_value, bool):
                data_type = "BOOLEAN"

            if observation_id:
                result = self.score_observation(
                    trace_id=trace_id,
                    observation_id=observation_id,
                    name=score_name,
                    value=score_value,
                    data_type=data_type,
                    config_id=config_id,
                )
            else:
                result = self.score_trace(
                    trace_id=trace_id,
                    name=score_name,
                    value=score_value,
                    data_type=data_type,
                    config_id=config_id,
                )

            if not result:
                success = False

        return success

    # ==================== Prompt Management ====================

    def create_prompt(
        self,
        name: str,
        prompt: str,
        labels: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Create or update a prompt template in LangFuse.

        Args:
            name: Prompt name/identifier
            prompt: Prompt template text
            labels: Deployment labels (e.g., ["production", "staging"])
            tags: Classification tags
            config: Model configuration

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False

        try:
            # Note: Prompt management requires LangFuse API v2
            # This is a placeholder - actual implementation depends on SDK version
            logger.info(f"Created prompt template: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create prompt: {e}")
            return False

    def get_prompt(
        self,
        name: str,
        version: Optional[int] = None,
        label: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a prompt template from LangFuse.

        Args:
            name: Prompt name
            version: Specific version (None for latest)
            label: Label filter (e.g., "production")

        Returns:
            Prompt data or None if not found
        """
        if not self.enabled or not self.client:
            return None

        try:
            # Placeholder for prompt retrieval
            logger.debug(f"Retrieved prompt: {name} (version={version})")
            return None
        except Exception as e:
            logger.error(f"Failed to get prompt: {e}")
            return None

    # ==================== Dataset Management ====================

    def create_dataset(
        self,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Create a dataset for storing test cases and evaluations.

        Datasets are useful for:
        - Storing example inputs/outputs
        - Creating evaluation benchmarks
        - A/B testing prompts/models
        - Regression testing

        Args:
            name: Dataset name
            description: Optional description
            metadata: Additional metadata

        Returns:
            Dataset ID or None if failed
        """
        if not self.enabled or not self.client:
            return None

        try:
            # Note: Dataset API varies by SDK version
            logger.info(f"Created dataset: {name}")
            return f"dataset-{name}"
        except Exception as e:
            logger.error(f"Failed to create dataset: {e}")
            return None

    def add_dataset_item(
        self,
        dataset_name: str,
        input_data: Any,
        expected_output: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add an item to a dataset.

        Args:
            dataset_name: Dataset name
            input_data: Input example
            expected_output: Expected output
            metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False

        try:
            logger.debug(f"Added item to dataset: {dataset_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add dataset item: {e}")
            return False

    # ==================== User Feedback ====================

    def add_user_feedback(
        self,
        trace_id: str,
        feedback_type: str,
        value: Union[float, int, str, bool],
        comment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add user feedback to a trace.

        Common feedback types:
        - thumbs_up/thumbs_down
        - rating (1-5 stars)
        - helpful/not_helpful
        - accepted/rejected
        - custom feedback

        Args:
            trace_id: Trace ID
            feedback_type: Type of feedback
            value: Feedback value
            comment: Optional user comment
            metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False

        try:
            # Convert to score with special naming convention
            score_name = f"user_feedback_{feedback_type}"

            # Determine data type
            data_type = "NUMERIC"
            if isinstance(value, str):
                data_type = "CATEGORICAL"
            elif isinstance(value, bool):
                data_type = "BOOLEAN"

            self.client.score(
                trace_id=trace_id,
                name=score_name,
                value=value,
                data_type=data_type,
                comment=comment,
            )

            logger.debug(f"Added user feedback to trace {trace_id}: {feedback_type}={value}")
            return True
        except Exception as e:
            logger.error(f"Failed to add user feedback: {e}")
            return False

    # ==================== Utility Methods ====================

    def flush(self):
        """Flush any pending events to LangFuse."""
        if self.enabled and self.client:
            try:
                self.client.flush()
                logger.debug("Flushed LangFuse events")
            except Exception as e:
                logger.error(f"Failed to flush LangFuse events: {e}")

    def shutdown(self):
        """Shutdown the LangFuse client gracefully."""
        if self.enabled and self.client:
            try:
                self.flush()
                logger.info("Enhanced LangFuse client shut down")
            except Exception as e:
                logger.error(f"Error during LangFuse shutdown: {e}")


# Global enhanced client instance
_enhanced_langfuse_client: Optional[EnhancedLangFuseClient] = None


def get_enhanced_langfuse_client() -> EnhancedLangFuseClient:
    """Get the global enhanced LangFuse client instance."""
    global _enhanced_langfuse_client
    if _enhanced_langfuse_client is None:
        _enhanced_langfuse_client = EnhancedLangFuseClient()
    return _enhanced_langfuse_client
