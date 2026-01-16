"""
LLM Type Definitions

Common types used across all LLM providers.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LLMRole(str, Enum):
    """Message roles in conversation"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LLMMessage(BaseModel):
    """A single message in a conversation"""

    role: LLMRole
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """Response from an LLM"""

    content: str
    model: str
    provider: str
    usage: Dict[str, int] = Field(default_factory=dict)
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LLMProvider(str, Enum):
    """Supported LLM providers"""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
