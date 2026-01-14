"""
Context Compression Module

Implements various compression techniques to reduce context size:
- Extractive summarization (select key sentences)
- Abstractive summarization (generate concise summaries)
- Chunking strategies (split long contexts)
- Token counting and estimation
"""

from __future__ import annotations

import asyncio
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger
from pydantic import BaseModel, Field


class CompressionStrategy(str, Enum):
    """Available compression strategies"""

    EXTRACTIVE = "extractive"
    ABSTRACTIVE = "abstractive"
    CHUNKING = "chunking"
    HYBRID = "hybrid"


class CompressionConfig(BaseModel):
    """Configuration for compression operations"""

    strategy: CompressionStrategy = CompressionStrategy.HYBRID
    target_ratio: float = Field(default=0.5, ge=0.1, le=0.9)  # Target compression ratio
    max_chunk_size: int = Field(default=512, ge=100)
    chunk_overlap: int = Field(default=50, ge=0)
    preserve_structure: bool = True
    min_sentence_length: int = Field(default=10, ge=1)
    extractive_top_k: int = Field(default=5, ge=1)


@dataclass
class CompressionResult:
    """Result of compression operation"""

    original_text: str
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    strategy_used: CompressionStrategy
    chunks: Optional[List[str]] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TokenCounter:
    """
    Token counting and estimation utilities

    In production, this would use tiktoken or similar for accurate counting
    """

    # Approximate tokens per word for different models
    TOKENS_PER_WORD = {
        "gpt-4": 1.3,
        "claude": 1.3,
        "default": 1.3,
    }

    @classmethod
    def count_tokens(
        cls,
        text: str,
        model: str = "default",
    ) -> int:
        """
        Estimate token count for text

        In production, use actual tokenizer (e.g., tiktoken)
        """
        if not text:
            return 0

        # Simple word-based estimation
        words = len(text.split())
        ratio = cls.TOKENS_PER_WORD.get(model, cls.TOKENS_PER_WORD["default"])

        return int(words * ratio)

    @classmethod
    def split_by_tokens(
        cls,
        text: str,
        max_tokens: int,
        overlap_tokens: int = 0,
        model: str = "default",
    ) -> List[str]:
        """
        Split text into chunks by token count

        Args:
            text: Text to split
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Number of overlapping tokens between chunks
            model: Model name for token counting

        Returns:
            List of text chunks
        """
        if not text:
            return []

        # Split into sentences
        sentences = cls._split_sentences(text)
        chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = cls.count_tokens(sentence, model)

            # If single sentence exceeds max, split it by words
            if sentence_tokens > max_tokens:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_tokens = 0

                # Split long sentence
                word_chunks = cls._split_by_words(sentence, max_tokens, model)
                chunks.extend(word_chunks)
                continue

            # Check if adding sentence exceeds limit
            if current_tokens + sentence_tokens > max_tokens:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))

                # Handle overlap
                if overlap_tokens > 0 and current_chunk:
                    overlap_chunk = []
                    overlap_count = 0
                    for sent in reversed(current_chunk):
                        sent_tokens = cls.count_tokens(sent, model)
                        if overlap_count + sent_tokens <= overlap_tokens:
                            overlap_chunk.insert(0, sent)
                            overlap_count += sent_tokens
                        else:
                            break
                    current_chunk = overlap_chunk
                    current_tokens = overlap_count
                else:
                    current_chunk = []
                    current_tokens = 0

            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        # Add remaining chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting (can be improved with NLTK/spaCy)
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    @classmethod
    def _split_by_words(
        cls,
        text: str,
        max_tokens: int,
        model: str = "default",
    ) -> List[str]:
        """Split text by words when sentence is too long"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_tokens = 0

        for word in words:
            word_tokens = cls.count_tokens(word, model)

            if current_tokens + word_tokens > max_tokens:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_tokens = word_tokens
            else:
                current_chunk.append(word)
                current_tokens += word_tokens

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks


class BaseCompressor(ABC):
    """Base class for all compression strategies"""

    def __init__(self, config: CompressionConfig):
        self.config = config

    @abstractmethod
    async def compress(self, text: str) -> CompressionResult:
        """
        Compress text

        Args:
            text: Text to compress

        Returns:
            Compression result with metadata
        """
        pass

    def _calculate_ratio(self, original_tokens: int, compressed_tokens: int) -> float:
        """Calculate compression ratio"""
        if original_tokens == 0:
            return 0.0
        return compressed_tokens / original_tokens


class ExtractiveSummarizer(BaseCompressor):
    """
    Extractive summarization

    Selects most important sentences from original text
    """

    async def compress(self, text: str) -> CompressionResult:
        """Perform extractive summarization"""
        if not text:
            return CompressionResult(
                original_text=text,
                compressed_text=text,
                original_tokens=0,
                compressed_tokens=0,
                compression_ratio=1.0,
                strategy_used=CompressionStrategy.EXTRACTIVE,
            )

        # Split into sentences
        sentences = TokenCounter._split_sentences(text)

        if not sentences:
            return CompressionResult(
                original_text=text,
                compressed_text=text,
                original_tokens=TokenCounter.count_tokens(text),
                compressed_tokens=TokenCounter.count_tokens(text),
                compression_ratio=1.0,
                strategy_used=CompressionStrategy.EXTRACTIVE,
            )

        # Score sentences
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = self._score_sentence(sentence, i, len(sentences))
            scored_sentences.append((score, sentence))

        # Sort by score and select top-k
        scored_sentences.sort(key=lambda x: x[0], reverse=True)

        # Calculate how many sentences to keep
        target_count = max(
            1,
            int(len(sentences) * self.config.target_ratio),
        )
        target_count = min(target_count, self.config.extractive_top_k)

        # Select top sentences and maintain order
        selected_sentences = [s for _, s in scored_sentences[:target_count]]

        # Restore original order
        selected_sentences_ordered = [
            s for s in sentences if s in selected_sentences
        ]

        # Combine
        compressed_text = " ".join(selected_sentences_ordered)

        original_tokens = TokenCounter.count_tokens(text)
        compressed_tokens = TokenCounter.count_tokens(compressed_text)

        logger.debug(
            f"Extractive compression: {original_tokens} -> {compressed_tokens} tokens "
            f"({len(sentences)} -> {len(selected_sentences_ordered)} sentences)"
        )

        return CompressionResult(
            original_text=text,
            compressed_text=compressed_text,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=self._calculate_ratio(original_tokens, compressed_tokens),
            strategy_used=CompressionStrategy.EXTRACTIVE,
            metadata={
                "original_sentences": len(sentences),
                "selected_sentences": len(selected_sentences_ordered),
            },
        )

    def _score_sentence(
        self,
        sentence: str,
        position: int,
        total_sentences: int,
    ) -> float:
        """
        Score sentence importance

        Factors:
        - Length (prefer moderate length)
        - Position (prefer beginning and end)
        - Keyword presence
        - Named entities (simplified detection)
        """
        if len(sentence) < self.config.min_sentence_length:
            return 0.0

        score = 0.0

        # Length score (prefer 20-50 words)
        word_count = len(sentence.split())
        if 20 <= word_count <= 50:
            score += 1.0
        elif word_count < 20:
            score += word_count / 20.0
        else:
            score += 50.0 / word_count

        # Position score (prefer beginning and end)
        if position == 0:
            score += 0.5  # First sentence bonus
        elif position == total_sentences - 1:
            score += 0.3  # Last sentence bonus
        else:
            # Middle sentences get lower score
            relative_pos = position / total_sentences
            score += 0.2 * (1.0 - abs(0.5 - relative_pos))

        # Keyword score (simple heuristic)
        important_words = [
            "important", "critical", "key", "main", "primary",
            "significant", "essential", "crucial", "fundamental",
            "therefore", "conclusion", "summary", "result",
        ]
        for word in important_words:
            if word in sentence.lower():
                score += 0.3

        # Capitalized words (potential named entities)
        caps_count = len(re.findall(r'\b[A-Z][a-z]+', sentence))
        score += min(caps_count * 0.1, 0.5)

        # Numbers (often contain important data)
        numbers_count = len(re.findall(r'\b\d+', sentence))
        score += min(numbers_count * 0.1, 0.3)

        return score


class AbstractiveSummarizer(BaseCompressor):
    """
    Abstractive summarization

    Generates new concise text (placeholder - would use LLM in production)
    """

    async def compress(self, text: str) -> CompressionResult:
        """
        Perform abstractive summarization

        In production, this would call an LLM to generate a summary
        For now, we use extractive + paraphrasing simulation
        """
        if not text:
            return CompressionResult(
                original_text=text,
                compressed_text=text,
                original_tokens=0,
                compressed_tokens=0,
                compression_ratio=1.0,
                strategy_used=CompressionStrategy.ABSTRACTIVE,
            )

        # Placeholder: Use extractive as base, then "paraphrase"
        # In production, use LLM: "Summarize this concisely: {text}"
        extractive = ExtractiveSummarizer(self.config)
        extractive_result = await extractive.compress(text)

        # Simulate abstractive compression (slightly better ratio)
        compressed_text = self._simulate_abstractive(extractive_result.compressed_text)

        original_tokens = TokenCounter.count_tokens(text)
        compressed_tokens = TokenCounter.count_tokens(compressed_text)

        logger.debug(
            f"Abstractive compression: {original_tokens} -> {compressed_tokens} tokens"
        )

        return CompressionResult(
            original_text=text,
            compressed_text=compressed_text,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=self._calculate_ratio(original_tokens, compressed_tokens),
            strategy_used=CompressionStrategy.ABSTRACTIVE,
            metadata={
                "method": "extractive_based",
                "note": "Production would use LLM",
            },
        )

    def _simulate_abstractive(self, text: str) -> str:
        """
        Simulate abstractive summarization

        In production, replace with actual LLM call
        """
        # Simple heuristic: remove filler words and simplify
        filler_words = [
            r'\b(very|really|quite|somewhat|rather)\b',
            r'\b(I think|I believe|perhaps|maybe)\b',
            r'\b(basically|actually|literally)\b',
        ]

        compressed = text
        for pattern in filler_words:
            compressed = re.sub(pattern, '', compressed, flags=re.IGNORECASE)

        # Clean up extra spaces
        compressed = re.sub(r'\s+', ' ', compressed).strip()

        return compressed


class TextChunker(BaseCompressor):
    """
    Text chunking strategy

    Splits long texts into manageable chunks
    """

    async def compress(self, text: str) -> CompressionResult:
        """
        Split text into chunks

        Note: This doesn't compress but organizes for processing
        """
        if not text:
            return CompressionResult(
                original_text=text,
                compressed_text=text,
                original_tokens=0,
                compressed_tokens=0,
                compression_ratio=1.0,
                strategy_used=CompressionStrategy.CHUNKING,
                chunks=[],
            )

        # Split into chunks
        chunks = TokenCounter.split_by_tokens(
            text,
            max_tokens=self.config.max_chunk_size,
            overlap_tokens=self.config.chunk_overlap,
        )

        # For compression, we select most important chunks
        if len(chunks) > 1:
            # Score chunks and select based on target ratio
            scored_chunks = []
            for chunk in chunks:
                score = self._score_chunk(chunk)
                scored_chunks.append((score, chunk))

            scored_chunks.sort(key=lambda x: x[0], reverse=True)

            # Select top chunks based on target ratio
            target_count = max(1, int(len(chunks) * self.config.target_ratio))
            selected_chunks = [c for _, c in scored_chunks[:target_count]]

            compressed_text = "\n\n".join(selected_chunks)
        else:
            compressed_text = text
            selected_chunks = chunks

        original_tokens = TokenCounter.count_tokens(text)
        compressed_tokens = TokenCounter.count_tokens(compressed_text)

        logger.debug(
            f"Chunking: {len(chunks)} chunks created, "
            f"{len(selected_chunks)} selected"
        )

        return CompressionResult(
            original_text=text,
            compressed_text=compressed_text,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=self._calculate_ratio(original_tokens, compressed_tokens),
            strategy_used=CompressionStrategy.CHUNKING,
            chunks=chunks,
            metadata={
                "total_chunks": len(chunks),
                "selected_chunks": len(selected_chunks),
                "chunk_size": self.config.max_chunk_size,
                "overlap": self.config.chunk_overlap,
            },
        )

    def _score_chunk(self, chunk: str) -> float:
        """Score chunk importance (similar to sentence scoring)"""
        score = 0.0

        # Information density
        unique_words = len(set(chunk.lower().split()))
        total_words = len(chunk.split())
        if total_words > 0:
            score += unique_words / total_words

        # Presence of numbers and data
        numbers = len(re.findall(r'\b\d+', chunk))
        score += min(numbers * 0.1, 0.5)

        # Capitalized words (named entities)
        caps = len(re.findall(r'\b[A-Z][a-z]+', chunk))
        score += min(caps * 0.05, 0.3)

        return score


class HybridCompressor(BaseCompressor):
    """
    Hybrid compression strategy

    Combines multiple compression techniques
    """

    async def compress(self, text: str) -> CompressionResult:
        """Apply hybrid compression"""
        if not text:
            return CompressionResult(
                original_text=text,
                compressed_text=text,
                original_tokens=0,
                compressed_tokens=0,
                compression_ratio=1.0,
                strategy_used=CompressionStrategy.HYBRID,
            )

        original_tokens = TokenCounter.count_tokens(text)

        # Step 1: If text is very long, chunk it first
        if original_tokens > self.config.max_chunk_size * 2:
            chunker = TextChunker(self.config)
            chunk_result = await chunker.compress(text)
            text = chunk_result.compressed_text

        # Step 2: Apply extractive summarization
        extractive = ExtractiveSummarizer(self.config)
        extractive_result = await extractive.compress(text)

        # Step 3: If still too long, apply abstractive
        if extractive_result.compressed_tokens > self.config.max_chunk_size:
            abstractive = AbstractiveSummarizer(self.config)
            final_result = await abstractive.compress(extractive_result.compressed_text)
        else:
            final_result = extractive_result

        # Update strategy used
        final_result.strategy_used = CompressionStrategy.HYBRID
        final_result.original_text = text
        final_result.original_tokens = original_tokens
        final_result.compression_ratio = self._calculate_ratio(
            original_tokens,
            final_result.compressed_tokens,
        )

        logger.debug(
            f"Hybrid compression: {original_tokens} -> "
            f"{final_result.compressed_tokens} tokens "
            f"(ratio: {final_result.compression_ratio:.2%})"
        )

        return final_result


class ContextCompressor:
    """
    Main context compressor that dispatches to specific strategies
    """

    def __init__(self, config: Optional[CompressionConfig] = None):
        self.config = config or CompressionConfig()
        self._compressors: Dict[CompressionStrategy, BaseCompressor] = {
            CompressionStrategy.EXTRACTIVE: ExtractiveSummarizer(self.config),
            CompressionStrategy.ABSTRACTIVE: AbstractiveSummarizer(self.config),
            CompressionStrategy.CHUNKING: TextChunker(self.config),
            CompressionStrategy.HYBRID: HybridCompressor(self.config),
        }

    async def compress(
        self,
        text: str,
        strategy: Optional[CompressionStrategy] = None,
    ) -> CompressionResult:
        """
        Compress text using specified strategy

        Args:
            text: Text to compress
            strategy: Compression strategy to use (overrides config)

        Returns:
            Compression result with metadata
        """
        if not text:
            return CompressionResult(
                original_text="",
                compressed_text="",
                original_tokens=0,
                compressed_tokens=0,
                compression_ratio=1.0,
                strategy_used=strategy or self.config.strategy,
            )

        strategy = strategy or self.config.strategy
        compressor = self._compressors[strategy]

        logger.info(f"Compressing text using {strategy.value} strategy")

        start_time = datetime.now()
        result = await compressor.compress(text)
        duration = (datetime.now() - start_time).total_seconds()

        result.metadata = result.metadata or {}
        result.metadata["duration_seconds"] = duration

        logger.info(
            f"Compression complete: {result.original_tokens} -> "
            f"{result.compressed_tokens} tokens "
            f"(ratio: {result.compression_ratio:.2%}, {duration:.3f}s)"
        )

        return result

    def update_config(self, config: CompressionConfig) -> None:
        """Update compression configuration"""
        self.config = config
        # Recreate compressors with new config
        self._compressors = {
            CompressionStrategy.EXTRACTIVE: ExtractiveSummarizer(self.config),
            CompressionStrategy.ABSTRACTIVE: AbstractiveSummarizer(self.config),
            CompressionStrategy.CHUNKING: TextChunker(self.config),
            CompressionStrategy.HYBRID: HybridCompressor(self.config),
        }


async def compress_context(
    text: str,
    strategy: CompressionStrategy = CompressionStrategy.HYBRID,
    target_ratio: float = 0.5,
) -> CompressionResult:
    """
    Convenience function for context compression

    Args:
        text: Text to compress
        strategy: Compression strategy to use
        target_ratio: Target compression ratio

    Returns:
        Compression result with metadata
    """
    config = CompressionConfig(
        strategy=strategy,
        target_ratio=target_ratio,
    )

    compressor = ContextCompressor(config)
    return await compressor.compress(text)


async def summarize_text(
    text: str,
    extractive: bool = True,
    target_ratio: float = 0.5,
) -> str:
    """
    Convenience function for text summarization

    Args:
        text: Text to summarize
        extractive: Use extractive (True) or abstractive (False) summarization
        target_ratio: Target compression ratio

    Returns:
        Summarized text
    """
    strategy = (
        CompressionStrategy.EXTRACTIVE
        if extractive
        else CompressionStrategy.ABSTRACTIVE
    )

    result = await compress_context(text, strategy, target_ratio)
    return result.compressed_text
