"""
Unified LLM Client

Provides a single interface for multiple LLM providers.
Automatically handles provider-specific API differences.
"""

import os
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, Field

from iras.llm.types import LLMMessage, LLMProvider, LLMResponse, LLMRole


class LLMConfig(BaseModel):
    """LLM configuration from environment or explicit settings"""

    provider: LLMProvider = Field(
        default_factory=lambda: LLMProvider(os.getenv("LLM_PROVIDER", "anthropic"))
    )
    model: str = Field(
        default_factory=lambda: os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")
    )
    temperature: float = Field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.7")))
    max_tokens: int = Field(default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "4096")))

    # API Keys
    anthropic_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY")
    )
    openai_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    gemini_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))

    # Advanced options
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stop_sequences: List[str] = Field(default_factory=list)


class LLMClient:
    """
    Unified LLM client supporting multiple providers

    Usage:
        config = LLMConfig(provider=LLMProvider.ANTHROPIC)
        client = LLMClient(config)
        response = await client.generate("What is 2+2?")
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._client = None
        self._initialize_client()

        logger.info(
            f"LLM Client initialized: provider={self.config.provider.value}, model={self.config.model}"
        )

    def _initialize_client(self) -> None:
        """Initialize the appropriate LLM provider client"""

        if self.config.provider == LLMProvider.ANTHROPIC:
            self._initialize_anthropic()
        elif self.config.provider == LLMProvider.OPENAI:
            self._initialize_openai()
        elif self.config.provider == LLMProvider.GEMINI:
            self._initialize_gemini()
        else:
            raise ValueError(f"Unknown provider: {self.config.provider}")

    def _initialize_anthropic(self) -> None:
        """Initialize Anthropic client"""
        if not self.config.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. Please set it in environment or config."
            )

        try:
            from anthropic import AsyncAnthropic

            self._client = AsyncAnthropic(api_key=self.config.anthropic_api_key)
        except ImportError:
            raise ImportError(
                "Anthropic package not installed. Install with: pip install anthropic"
            )

    def _initialize_openai(self) -> None:
        """Initialize OpenAI client"""
        if not self.config.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set. Please set it in environment or config.")

        try:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=self.config.openai_api_key)
        except ImportError:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")

    def _initialize_gemini(self) -> None:
        """Initialize Google Gemini client"""
        if not self.config.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not set. Please set it in environment or config.")

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.config.gemini_api_key)
            self._client = genai
        except ImportError:
            raise ImportError(
                "Google Generative AI package not installed. Install with: pip install google-generativeai"
            )

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        messages: Optional[List[LLMMessage]] = None,
    ) -> LLMResponse:
        """
        Generate text using the configured LLM

        Args:
            prompt: User prompt (ignored if messages provided)
            system: System prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            messages: Full conversation history (overrides prompt/system)

        Returns:
            LLMResponse with generated text and metadata
        """

        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens

        # Build messages if not provided
        if messages is None:
            messages = []
            if system:
                messages.append(LLMMessage(role=LLMRole.SYSTEM, content=system))
            messages.append(LLMMessage(role=LLMRole.USER, content=prompt))

        # Route to appropriate provider
        if self.config.provider == LLMProvider.ANTHROPIC:
            return await self._generate_anthropic(messages, temp, tokens)
        elif self.config.provider == LLMProvider.OPENAI:
            return await self._generate_openai(messages, temp, tokens)
        elif self.config.provider == LLMProvider.GEMINI:
            return await self._generate_gemini(messages, temp, tokens)

    async def _generate_anthropic(
        self, messages: List[LLMMessage], temperature: float, max_tokens: int
    ) -> LLMResponse:
        """Generate using Anthropic Claude"""

        # Separate system message from conversation
        system_content = None
        conversation = []

        for msg in messages:
            if msg.role == LLMRole.SYSTEM:
                system_content = msg.content
            else:
                conversation.append({"role": msg.role.value, "content": msg.content})

        # Call Anthropic API
        response = await self._client.messages.create(
            model=self.config.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_content or "You are a helpful AI assistant.",
            messages=conversation,
        )

        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            provider="anthropic",
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
            metadata={"response_id": response.id},
        )

    async def _generate_openai(
        self, messages: List[LLMMessage], temperature: float, max_tokens: int
    ) -> LLMResponse:
        """Generate using OpenAI GPT"""

        # Convert messages to OpenAI format
        openai_messages = [{"role": msg.role.value, "content": msg.content} for msg in messages]

        # Call OpenAI API
        response = await self._client.chat.completions.create(
            model=self.config.model,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            provider="openai",
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            finish_reason=response.choices[0].finish_reason,
            metadata={"response_id": response.id},
        )

    async def _generate_gemini(
        self, messages: List[LLMMessage], temperature: float, max_tokens: int
    ) -> LLMResponse:
        """Generate using Google Gemini"""

        # Get model
        model = self._client.GenerativeModel(self.config.model)

        # Gemini uses a different message format
        # System messages become part of the configuration
        system_instruction = None
        chat_history = []
        user_message = None

        for msg in messages:
            if msg.role == LLMRole.SYSTEM:
                system_instruction = msg.content
            elif msg.role == LLMRole.USER:
                user_message = msg.content
            elif msg.role == LLMRole.ASSISTANT:
                chat_history.append({"role": "model", "parts": [msg.content]})

        # Start chat with history
        chat = model.start_chat(history=chat_history)

        # Generate response
        response = await chat.send_message_async(
            user_message,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )

        return LLMResponse(
            content=response.text,
            model=self.config.model,
            provider="gemini",
            usage={
                "input_tokens": response.usage_metadata.prompt_token_count,
                "output_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count,
            },
            finish_reason=str(response.candidates[0].finish_reason),
            metadata={"response_id": response.candidates[0].index},
        )

    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate structured output (JSON) conforming to a schema

        Args:
            prompt: User prompt
            schema: JSON schema for the output
            system: System prompt
            **kwargs: Additional generation parameters

        Returns:
            Parsed JSON object
        """
        import json

        # Enhance prompt with schema instruction
        enhanced_prompt = f"""{prompt}

Please respond with valid JSON matching this schema:
{json.dumps(schema, indent=2)}

Respond with ONLY the JSON, no other text."""

        response = await self.generate(prompt=enhanced_prompt, system=system, **kwargs)

        # Parse JSON from response
        try:
            # Try to extract JSON from markdown code blocks
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            logger.error(f"Response was: {response.content}")
            raise ValueError(f"LLM did not return valid JSON: {e}")

    def update_config(self, **kwargs) -> None:
        """Update configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        logger.info(f"LLM config updated: {kwargs}")
