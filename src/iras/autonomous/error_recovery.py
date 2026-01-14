"""
Error Recovery Mechanisms for Autonomous Agents

Provides comprehensive error handling and recovery strategies including:
- Retry strategies with exponential backoff and jitter
- Circuit breaker pattern for failing services
- Fallback mechanisms
- Checkpoint and rollback capabilities
- Graceful degradation

Features:
- Configurable retry policies
- Automatic circuit breaking
- State preservation and recovery
- Error pattern detection
- Recovery strategy selection
"""

from __future__ import annotations

import asyncio
import random
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Deque, Dict, List, Optional, TypeVar, Union
from uuid import UUID, uuid4

from loguru import logger
from pydantic import BaseModel, Field

T = TypeVar('T')


class RetryStrategy(str, Enum):
    """Retry strategy types"""

    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"


class CircuitState(str, Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class RecoveryAction(str, Enum):
    """Types of recovery actions"""

    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ESCALATE = "escalate"
    ROLLBACK = "rollback"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""

    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    jitter: bool = True
    jitter_range: float = 0.1  # ±10%
    exponential_base: float = 2.0
    backoff_multiplier: float = 1.5

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number"""
        if self.strategy == RetryStrategy.FIXED:
            delay = self.base_delay

        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = min(
                self.base_delay * (self.exponential_base ** (attempt - 1)),
                self.max_delay,
            )

        elif self.strategy == RetryStrategy.LINEAR:
            delay = min(
                self.base_delay * attempt,
                self.max_delay,
            )

        elif self.strategy == RetryStrategy.FIBONACCI:
            fib = self._fibonacci(attempt)
            delay = min(self.base_delay * fib, self.max_delay)

        else:
            delay = self.base_delay

        # Add jitter to prevent thundering herd
        if self.jitter:
            jitter_amount = delay * self.jitter_range
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)

    @staticmethod
    def _fibonacci(n: int) -> int:
        """Calculate nth Fibonacci number"""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return b


class ErrorRecord(BaseModel):
    """Record of an error occurrence"""

    id: UUID = Field(default_factory=uuid4)
    error_type: str
    error_message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    context: Dict[str, Any] = Field(default_factory=dict)
    stack_trace: Optional[str] = None
    recovery_action: Optional[RecoveryAction] = None
    recovered: bool = False


class Checkpoint(BaseModel):
    """State checkpoint for rollback"""

    id: UUID = Field(default_factory=uuid4)
    name: str
    state_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class CircuitBreaker:
    """
    Circuit breaker pattern implementation

    Prevents cascading failures by stopping requests to failing services.

    States:
    - CLOSED: Normal operation, requests allowed
    - OPEN: Too many failures, requests rejected
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
        half_open_max_calls: int = 1,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.half_open_max_calls = half_open_max_calls

        # State
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0

        # Statistics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.state_changes: List[tuple[CircuitState, datetime]] = []

        logger.info(f"Circuit breaker '{name}' initialized")

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        self.total_calls += 1

        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN"
                )

        # Check half-open call limit
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is HALF_OPEN and at call limit"
                )
            self.half_open_calls += 1

        # Execute function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """Handle successful call"""
        self.total_successes += 1

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self._transition_to_closed()
        else:
            # Reset failure count on success
            self.failure_count = 0

    def _on_failure(self) -> None:
        """Handle failed call"""
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            # Failure in half-open state immediately opens circuit
            self._transition_to_open()
        elif self.failure_count >= self.failure_threshold:
            self._transition_to_open()

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout

    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state"""
        logger.info(f"Circuit breaker '{self.name}': {self.state} -> CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.state_changes.append((CircuitState.CLOSED, datetime.now()))

    def _transition_to_open(self) -> None:
        """Transition to OPEN state"""
        logger.warning(f"Circuit breaker '{self.name}': {self.state} -> OPEN")
        self.state = CircuitState.OPEN
        self.success_count = 0
        self.half_open_calls = 0
        self.state_changes.append((CircuitState.OPEN, datetime.now()))

    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state"""
        logger.info(f"Circuit breaker '{self.name}': {self.state} -> HALF_OPEN")
        self.state = CircuitState.HALF_OPEN
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.state_changes.append((CircuitState.HALF_OPEN, datetime.now()))

    def get_state(self) -> CircuitState:
        """Get current circuit state"""
        return self.state

    def get_statistics(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.state,
            "total_calls": self.total_calls,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "failure_rate": (
                self.total_failures / self.total_calls
                if self.total_calls > 0
                else 0.0
            ),
            "current_failure_count": self.failure_count,
            "current_success_count": self.success_count,
            "state_changes": len(self.state_changes),
        }

    def reset(self) -> None:
        """Manually reset circuit breaker"""
        logger.info(f"Circuit breaker '{self.name}' manually reset")
        self._transition_to_closed()


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class ErrorRecoverySystem:
    """
    Comprehensive error recovery system

    Features:
    - Automatic retry with configurable strategies
    - Circuit breaker pattern
    - Checkpoint/rollback capabilities
    - Fallback mechanisms
    - Error pattern detection
    - Graceful degradation
    """

    def __init__(
        self,
        agent_id: UUID,
        default_retry_config: Optional[RetryConfig] = None,
        max_checkpoints: int = 100,
    ):
        self.agent_id = agent_id
        self.default_retry_config = default_retry_config or RetryConfig()
        self.max_checkpoints = max_checkpoints

        # Error tracking
        self.error_history: Deque[ErrorRecord] = deque(maxlen=1000)
        self.error_counts: Dict[str, int] = {}

        # Circuit breakers
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

        # Checkpoints
        self.checkpoints: Dict[str, Checkpoint] = {}
        self.checkpoint_order: Deque[str] = deque(maxlen=max_checkpoints)

        # Fallback handlers
        self.fallback_handlers: Dict[str, Callable] = {}

        # Recovery statistics
        self.total_errors = 0
        self.recovered_errors = 0
        self.failed_recoveries = 0

        logger.info(f"Error recovery system initialized for agent {agent_id}")

    async def execute_with_retry(
        self,
        func: Callable[..., T],
        *args,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker: Optional[str] = None,
        fallback: Optional[Callable] = None,
        **kwargs,
    ) -> T:
        """
        Execute function with automatic retry and recovery

        Args:
            func: Function to execute
            *args: Positional arguments
            retry_config: Custom retry configuration
            circuit_breaker: Name of circuit breaker to use
            fallback: Fallback function if all retries fail
            **kwargs: Keyword arguments

        Returns:
            Function result or fallback result
        """
        config = retry_config or self.default_retry_config
        last_error = None

        # Wrap with circuit breaker if specified
        if circuit_breaker:
            breaker = self.get_or_create_circuit_breaker(circuit_breaker)
            original_func = func

            async def wrapped_func(*a, **kw):
                return await breaker.call(original_func, *a, **kw)

            func = wrapped_func

        # Retry loop
        for attempt in range(1, config.max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Success
                if attempt > 1:
                    logger.info(
                        f"Successfully recovered after {attempt} attempts"
                    )
                    self.recovered_errors += 1

                return result

            except CircuitBreakerOpenError:
                # Circuit is open, don't retry
                logger.warning("Circuit breaker is open, skipping retries")
                last_error = CircuitBreakerOpenError(
                    "Circuit breaker prevented execution"
                )
                break

            except Exception as e:
                last_error = e
                self.total_errors += 1

                # Record error
                error_record = self._record_error(e, {
                    "attempt": attempt,
                    "max_attempts": config.max_attempts,
                })

                logger.warning(
                    f"Attempt {attempt}/{config.max_attempts} failed: {e}"
                )

                # Check if we should retry
                if attempt < config.max_attempts:
                    delay = config.calculate_delay(attempt)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {config.max_attempts} attempts failed"
                    )
                    self.failed_recoveries += 1

        # All retries failed, try fallback
        if fallback:
            try:
                logger.info("Executing fallback handler")
                if asyncio.iscoroutinefunction(fallback):
                    return await fallback(*args, **kwargs)
                else:
                    return fallback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Fallback also failed: {e}")
                last_error = e

        # No recovery possible
        raise last_error

    def _record_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
    ) -> ErrorRecord:
        """Record an error occurrence"""
        error_type = type(error).__name__
        error_record = ErrorRecord(
            error_type=error_type,
            error_message=str(error),
            context=context or {},
        )

        self.error_history.append(error_record)
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        return error_record

    def create_checkpoint(
        self,
        name: str,
        state_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Checkpoint:
        """
        Create a state checkpoint for potential rollback

        Args:
            name: Checkpoint name/identifier
            state_data: State data to save
            metadata: Optional metadata

        Returns:
            Created checkpoint
        """
        checkpoint = Checkpoint(
            name=name,
            state_data=state_data,
            metadata=metadata or {},
        )

        # Remove old checkpoint with same name if exists
        if name in self.checkpoints:
            self.checkpoint_order.remove(name)

        # Add new checkpoint
        self.checkpoints[name] = checkpoint
        self.checkpoint_order.append(name)

        # Remove oldest if over limit
        if len(self.checkpoints) > self.max_checkpoints:
            oldest_name = self.checkpoint_order[0]
            del self.checkpoints[oldest_name]

        logger.info(f"Checkpoint '{name}' created")
        return checkpoint

    def rollback_to_checkpoint(
        self,
        name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Rollback to a saved checkpoint

        Args:
            name: Checkpoint name

        Returns:
            Checkpoint state data if found, None otherwise
        """
        checkpoint = self.checkpoints.get(name)
        if not checkpoint:
            logger.warning(f"Checkpoint '{name}' not found")
            return None

        logger.info(f"Rolling back to checkpoint '{name}'")
        return checkpoint.state_data

    def get_or_create_circuit_breaker(
        self,
        name: str,
        **kwargs,
    ) -> CircuitBreaker:
        """Get existing circuit breaker or create new one"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, **kwargs)

        return self.circuit_breakers[name]

    def register_fallback(
        self,
        name: str,
        handler: Callable,
    ) -> None:
        """Register a fallback handler"""
        self.fallback_handlers[name] = handler
        logger.info(f"Fallback handler '{name}' registered")

    def get_fallback(self, name: str) -> Optional[Callable]:
        """Get fallback handler by name"""
        return self.fallback_handlers.get(name)

    def get_error_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns"""
        if not self.error_history:
            return {}

        # Count errors by type
        error_types = {}
        for error in self.error_history:
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1

        # Calculate recent error rate
        recent_window = datetime.now() - timedelta(minutes=5)
        recent_errors = [
            e for e in self.error_history
            if e.timestamp > recent_window
        ]

        return {
            "total_errors": len(self.error_history),
            "error_types": error_types,
            "most_common_error": max(error_types.items(), key=lambda x: x[1])[0]
            if error_types else None,
            "recent_errors_5min": len(recent_errors),
            "recovery_rate": (
                self.recovered_errors / self.total_errors
                if self.total_errors > 0
                else 0.0
            ),
        }

    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get comprehensive recovery statistics"""
        circuit_stats = {
            name: breaker.get_statistics()
            for name, breaker in self.circuit_breakers.items()
        }

        return {
            "agent_id": str(self.agent_id),
            "total_errors": self.total_errors,
            "recovered_errors": self.recovered_errors,
            "failed_recoveries": self.failed_recoveries,
            "recovery_rate": (
                self.recovered_errors / self.total_errors
                if self.total_errors > 0
                else 0.0
            ),
            "error_patterns": self.get_error_patterns(),
            "circuit_breakers": circuit_stats,
            "active_checkpoints": len(self.checkpoints),
            "registered_fallbacks": len(self.fallback_handlers),
        }

    def reset_statistics(self) -> None:
        """Reset recovery statistics"""
        self.total_errors = 0
        self.recovered_errors = 0
        self.failed_recoveries = 0
        logger.info("Recovery statistics reset")
