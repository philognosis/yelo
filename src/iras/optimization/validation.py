"""
Context Validation Module

Implements validation checks for context quality:
- Freshness validation (check if data is stale)
- Contradiction detection (find conflicting information)
- Relevance scoring (measure relevance to query)
- Factual consistency checking
"""

from __future__ import annotations

import asyncio
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from loguru import logger
from pydantic import BaseModel, Field


class ValidationCheck(str, Enum):
    """Types of validation checks"""

    FRESHNESS = "freshness"
    CONTRADICTION = "contradiction"
    RELEVANCE = "relevance"
    CONSISTENCY = "consistency"
    ALL = "all"


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a validation issue"""

    check_type: ValidationCheck
    severity: ValidationSeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ValidationResult:
    """Result of validation checks"""

    is_valid: bool
    score: float  # 0.0 (invalid) to 1.0 (perfect)
    issues: List[ValidationIssue] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add a validation issue"""
        self.issues.append(issue)

        # Adjust validity based on severity
        if issue.severity == ValidationSeverity.CRITICAL:
            self.is_valid = False
            self.score = min(self.score, 0.3)
        elif issue.severity == ValidationSeverity.ERROR:
            self.score = min(self.score, 0.6)
        elif issue.severity == ValidationSeverity.WARNING:
            self.score = min(self.score, 0.8)

    def get_issues_by_severity(
        self,
        severity: ValidationSeverity,
    ) -> List[ValidationIssue]:
        """Get issues of specific severity"""
        return [issue for issue in self.issues if issue.severity == severity]

    def has_critical_issues(self) -> bool:
        """Check if there are critical issues"""
        return any(
            issue.severity == ValidationSeverity.CRITICAL
            for issue in self.issues
        )


class ValidationConfig(BaseModel):
    """Configuration for validation operations"""

    # Freshness settings
    max_age_seconds: Optional[float] = 3600.0  # 1 hour default
    warn_age_seconds: Optional[float] = 1800.0  # 30 minutes warning

    # Relevance settings
    relevance_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    min_relevance_score: float = Field(default=0.5, ge=0.0, le=1.0)

    # Contradiction settings
    contradiction_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    check_contradictions: bool = True

    # Consistency settings
    consistency_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    check_factual_consistency: bool = True

    # General settings
    strict_mode: bool = False  # Fail on warnings in strict mode


class ContextItem(BaseModel):
    """Context item for validation"""

    id: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    source: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None

    class Config:
        arbitrary_types_allowed = True


class BaseValidator(ABC):
    """Base class for all validators"""

    def __init__(self, config: ValidationConfig):
        self.config = config

    @abstractmethod
    async def validate(
        self,
        items: List[ContextItem],
        query: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validate context items

        Args:
            items: List of context items to validate
            query: Optional query for relevance checking

        Returns:
            Validation result with issues
        """
        pass

    def _get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for text (placeholder implementation)

        In production, use actual embedding model
        """
        np.random.seed(hash(text) % (2**32))
        return np.random.randn(384)

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))


class FreshnessValidator(BaseValidator):
    """
    Freshness validation

    Checks if context items are recent enough to be useful
    """

    async def validate(
        self,
        items: List[ContextItem],
        query: Optional[str] = None,
    ) -> ValidationResult:
        """Validate freshness of context items"""
        result = ValidationResult(is_valid=True, score=1.0)

        if not items:
            return result

        now = datetime.now()
        stale_items = []
        warned_items = []

        for item in items:
            age_seconds = (now - item.timestamp).total_seconds()

            # Check if critically stale
            if self.config.max_age_seconds and age_seconds > self.config.max_age_seconds:
                stale_items.append((item, age_seconds))
                result.add_issue(
                    ValidationIssue(
                        check_type=ValidationCheck.FRESHNESS,
                        severity=ValidationSeverity.ERROR,
                        message=f"Item '{item.id}' is stale",
                        details={
                            "item_id": item.id,
                            "age_seconds": age_seconds,
                            "max_age_seconds": self.config.max_age_seconds,
                            "age_minutes": age_seconds / 60,
                        },
                    )
                )
            # Check if approaching staleness
            elif self.config.warn_age_seconds and age_seconds > self.config.warn_age_seconds:
                warned_items.append((item, age_seconds))
                result.add_issue(
                    ValidationIssue(
                        check_type=ValidationCheck.FRESHNESS,
                        severity=ValidationSeverity.WARNING,
                        message=f"Item '{item.id}' is aging",
                        details={
                            "item_id": item.id,
                            "age_seconds": age_seconds,
                            "warn_age_seconds": self.config.warn_age_seconds,
                            "age_minutes": age_seconds / 60,
                        },
                    )
                )

        # Update metadata
        result.metadata.update({
            "total_items": len(items),
            "stale_items": len(stale_items),
            "warned_items": len(warned_items),
            "fresh_items": len(items) - len(stale_items) - len(warned_items),
        })

        logger.debug(
            f"Freshness validation: {result.metadata['fresh_items']}/{len(items)} fresh, "
            f"{len(warned_items)} aging, {len(stale_items)} stale"
        )

        return result


class ContradictionDetector(BaseValidator):
    """
    Contradiction detection

    Identifies conflicting information in context
    """

    async def validate(
        self,
        items: List[ContextItem],
        query: Optional[str] = None,
    ) -> ValidationResult:
        """Detect contradictions in context items"""
        result = ValidationResult(is_valid=True, score=1.0)

        if not items or not self.config.check_contradictions:
            return result

        # Generate embeddings for all items
        item_embeddings = []
        for item in items:
            if item.embedding is None:
                embedding = self._get_embedding(item.content)
                item.embedding = embedding.tolist()
            item_embeddings.append((item, np.array(item.embedding)))

        # Check for contradictions using semantic similarity and negation patterns
        contradictions = []

        for i, (item1, emb1) in enumerate(item_embeddings):
            for j, (item2, emb2) in enumerate(item_embeddings[i + 1:], start=i + 1):
                # Check semantic similarity
                similarity = self._cosine_similarity(emb1, emb2)

                # Check for negation patterns
                has_negation = self._check_negation_pattern(
                    item1.content,
                    item2.content,
                )

                # High similarity + negation = potential contradiction
                if similarity > self.config.contradiction_threshold and has_negation:
                    contradictions.append((item1, item2, similarity))

                    severity = (
                        ValidationSeverity.ERROR
                        if similarity > 0.85
                        else ValidationSeverity.WARNING
                    )

                    result.add_issue(
                        ValidationIssue(
                            check_type=ValidationCheck.CONTRADICTION,
                            severity=severity,
                            message=f"Potential contradiction between items",
                            details={
                                "item1_id": item1.id,
                                "item2_id": item2.id,
                                "similarity": similarity,
                                "item1_preview": item1.content[:100],
                                "item2_preview": item2.content[:100],
                            },
                        )
                    )

        result.metadata.update({
            "total_items": len(items),
            "contradictions_found": len(contradictions),
        })

        logger.debug(
            f"Contradiction detection: {len(contradictions)} potential contradictions"
        )

        return result

    def _check_negation_pattern(self, text1: str, text2: str) -> bool:
        """
        Check for negation patterns between two texts

        Simple heuristic - in production, use NLI model
        """
        negation_words = ["not", "no", "never", "neither", "nor", "n't"]

        # Count negations in each text
        text1_lower = text1.lower()
        text2_lower = text2.lower()

        negations1 = sum(1 for word in negation_words if word in text1_lower)
        negations2 = sum(1 for word in negation_words if word in text2_lower)

        # If one has negations and the other doesn't, might be contradiction
        return (negations1 > 0) != (negations2 > 0)


class RelevanceScorer(BaseValidator):
    """
    Relevance scoring

    Measures how relevant context is to the query
    """

    async def validate(
        self,
        items: List[ContextItem],
        query: Optional[str] = None,
    ) -> ValidationResult:
        """Score relevance of context items to query"""
        result = ValidationResult(is_valid=True, score=1.0)

        if not items:
            return result

        if not query:
            result.add_issue(
                ValidationIssue(
                    check_type=ValidationCheck.RELEVANCE,
                    severity=ValidationSeverity.INFO,
                    message="No query provided for relevance scoring",
                    details={},
                )
            )
            return result

        # Get query embedding
        query_embedding = self._get_embedding(query)

        # Score each item
        relevance_scores = []
        low_relevance_items = []

        for item in items:
            if item.embedding is None:
                item.embedding = self._get_embedding(item.content).tolist()

            item_embedding = np.array(item.embedding)
            relevance = self._cosine_similarity(query_embedding, item_embedding)
            relevance_scores.append((item, relevance))

            # Check if below threshold
            if relevance < self.config.relevance_threshold:
                low_relevance_items.append((item, relevance))

                severity = (
                    ValidationSeverity.WARNING
                    if relevance < self.config.min_relevance_score
                    else ValidationSeverity.INFO
                )

                result.add_issue(
                    ValidationIssue(
                        check_type=ValidationCheck.RELEVANCE,
                        severity=severity,
                        message=f"Low relevance item detected",
                        details={
                            "item_id": item.id,
                            "relevance_score": relevance,
                            "threshold": self.config.relevance_threshold,
                            "content_preview": item.content[:100],
                        },
                    )
                )

        # Calculate overall relevance score
        if relevance_scores:
            avg_relevance = sum(score for _, score in relevance_scores) / len(
                relevance_scores
            )
            result.score = min(result.score, avg_relevance)

        result.metadata.update({
            "total_items": len(items),
            "low_relevance_items": len(low_relevance_items),
            "average_relevance": avg_relevance if relevance_scores else 0.0,
            "query_provided": True,
        })

        logger.debug(
            f"Relevance scoring: avg={result.metadata['average_relevance']:.3f}, "
            f"{len(low_relevance_items)} low-relevance items"
        )

        return result


class ConsistencyChecker(BaseValidator):
    """
    Factual consistency checking

    Validates internal consistency of context
    """

    async def validate(
        self,
        items: List[ContextItem],
        query: Optional[str] = None,
    ) -> ValidationResult:
        """Check factual consistency of context"""
        result = ValidationResult(is_valid=True, score=1.0)

        if not items or not self.config.check_factual_consistency:
            return result

        # Extract factual claims (simplified)
        all_claims = []
        for item in items:
            claims = self._extract_claims(item.content)
            all_claims.extend([(item, claim) for claim in claims])

        # Check for inconsistent claims
        inconsistencies = []

        for i, (item1, claim1) in enumerate(all_claims):
            for j, (item2, claim2) in enumerate(all_claims[i + 1:], start=i + 1):
                if self._are_inconsistent(claim1, claim2):
                    inconsistencies.append((item1, item2, claim1, claim2))

                    result.add_issue(
                        ValidationIssue(
                            check_type=ValidationCheck.CONSISTENCY,
                            severity=ValidationSeverity.WARNING,
                            message=f"Potential inconsistency detected",
                            details={
                                "item1_id": item1.id,
                                "item2_id": item2.id,
                                "claim1": claim1,
                                "claim2": claim2,
                            },
                        )
                    )

        result.metadata.update({
            "total_items": len(items),
            "total_claims": len(all_claims),
            "inconsistencies": len(inconsistencies),
        })

        logger.debug(
            f"Consistency check: {len(all_claims)} claims, "
            f"{len(inconsistencies)} inconsistencies"
        )

        return result

    def _extract_claims(self, text: str) -> List[str]:
        """
        Extract factual claims from text

        Simplified implementation - in production, use NLP/NER
        """
        # Simple heuristic: look for sentences with numbers, dates, or entities
        sentences = re.split(r'[.!?]+', text)
        claims = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Look for numeric claims
            if re.search(r'\b\d+', sentence):
                claims.append(sentence)
            # Look for date claims
            elif re.search(r'\b(20\d{2}|19\d{2})\b', sentence):
                claims.append(sentence)
            # Look for definitive statements
            elif re.search(r'\b(is|are|was|were|has|have|will|must)\b', sentence):
                claims.append(sentence)

        return claims

    def _are_inconsistent(self, claim1: str, claim2: str) -> bool:
        """
        Check if two claims are inconsistent

        Simplified heuristic - in production, use NLI model
        """
        # Extract numbers from both claims
        nums1 = set(re.findall(r'\b\d+(?:\.\d+)?\b', claim1))
        nums2 = set(re.findall(r'\b\d+(?:\.\d+)?\b', claim2))

        # If same subject but different numbers, might be inconsistent
        words1 = set(claim1.lower().split())
        words2 = set(claim2.lower().split())

        common_words = words1 & words2
        different_numbers = nums1 != nums2

        # Simple heuristic: if >50% word overlap but different numbers
        if len(common_words) > max(len(words1), len(words2)) * 0.5:
            if different_numbers and nums1 and nums2:
                return True

        return False


class ContextValidator:
    """
    Main context validator that runs all validation checks
    """

    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()
        self._validators: Dict[ValidationCheck, BaseValidator] = {
            ValidationCheck.FRESHNESS: FreshnessValidator(self.config),
            ValidationCheck.CONTRADICTION: ContradictionDetector(self.config),
            ValidationCheck.RELEVANCE: RelevanceScorer(self.config),
            ValidationCheck.CONSISTENCY: ConsistencyChecker(self.config),
        }

    async def validate(
        self,
        items: List[ContextItem],
        query: Optional[str] = None,
        checks: Optional[List[ValidationCheck]] = None,
    ) -> ValidationResult:
        """
        Validate context items

        Args:
            items: List of context items to validate
            query: Optional query for relevance checking
            checks: List of checks to run (None = all)

        Returns:
            Combined validation result
        """
        if not items:
            return ValidationResult(
                is_valid=True,
                score=1.0,
                metadata={"total_items": 0},
            )

        # Determine which checks to run
        if checks is None or ValidationCheck.ALL in checks:
            checks_to_run = [
                ValidationCheck.FRESHNESS,
                ValidationCheck.CONTRADICTION,
                ValidationCheck.RELEVANCE,
                ValidationCheck.CONSISTENCY,
            ]
        else:
            checks_to_run = checks

        logger.info(
            f"Validating {len(items)} items with {len(checks_to_run)} checks"
        )

        start_time = datetime.now()

        # Run all checks
        results = await asyncio.gather(
            *[
                self._validators[check].validate(items, query)
                for check in checks_to_run
            ]
        )

        # Combine results
        combined_result = ValidationResult(is_valid=True, score=1.0)

        for check_result in results:
            # Add all issues
            combined_result.issues.extend(check_result.issues)

            # Update overall score (take minimum)
            combined_result.score = min(combined_result.score, check_result.score)

            # Update validity
            if not check_result.is_valid:
                combined_result.is_valid = False

            # Merge metadata
            combined_result.metadata.update(check_result.metadata)

        # Apply strict mode
        if self.config.strict_mode:
            if any(
                issue.severity
                in [ValidationSeverity.WARNING, ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
                for issue in combined_result.issues
            ):
                combined_result.is_valid = False

        duration = (datetime.now() - start_time).total_seconds()
        combined_result.metadata["validation_duration_seconds"] = duration
        combined_result.metadata["checks_run"] = [c.value for c in checks_to_run]

        logger.info(
            f"Validation complete: valid={combined_result.is_valid}, "
            f"score={combined_result.score:.3f}, "
            f"issues={len(combined_result.issues)} ({duration:.3f}s)"
        )

        return combined_result

    def update_config(self, config: ValidationConfig) -> None:
        """Update validation configuration"""
        self.config = config
        # Recreate validators with new config
        self._validators = {
            ValidationCheck.FRESHNESS: FreshnessValidator(self.config),
            ValidationCheck.CONTRADICTION: ContradictionDetector(self.config),
            ValidationCheck.RELEVANCE: RelevanceScorer(self.config),
            ValidationCheck.CONSISTENCY: ConsistencyChecker(self.config),
        }


async def validate_context(
    items: List[ContextItem],
    query: Optional[str] = None,
    checks: Optional[List[ValidationCheck]] = None,
    strict: bool = False,
) -> ValidationResult:
    """
    Convenience function for context validation

    Args:
        items: List of context items to validate
        query: Optional query for relevance checking
        checks: List of checks to run (None = all)
        strict: Enable strict mode (fail on warnings)

    Returns:
        Validation result with all issues
    """
    config = ValidationConfig(strict_mode=strict)
    validator = ContextValidator(config)
    return await validator.validate(items, query, checks)
