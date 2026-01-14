# Context Optimization Module Architecture

## Component Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                     ContextOptimizer                            │
│                  (Main Orchestrator)                            │
│  - Optimization modes (Aggressive/Balanced/Conservative)        │
│  - Adaptive multi-round optimization                            │
│  - Performance metrics & monitoring                             │
└──────────┬──────────────┬──────────────┬────────────────────────┘
           │              │              │
           ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────────┐
    │ Pruner   │   │Compressor│   │  Validator   │
    └──────────┘   └──────────┘   └──────────────┘
```

## Detailed Component Architecture

### 1. Pruning Layer (pruning.py)
```
ContextPruner
    │
    ├─► RecencyPruner
    │   └─ Time-based filtering
    │
    ├─► SemanticSimilarityPruner
    │   └─ Deduplication via embeddings
    │
    ├─► QueryRelevancePruner
    │   └─ Relevance scoring
    │
    ├─► ImportanceWeightedPruner
    │   └─ Multi-factor scoring
    │
    └─► HybridPruner
        └─ Sequential strategy application
```

### 2. Compression Layer (compression.py)
```
ContextCompressor
    │
    ├─► ExtractiveSummarizer
    │   └─ Key sentence selection
    │
    ├─► AbstractiveSummarizer
    │   └─ LLM-based summarization
    │
    ├─► TextChunker
    │   └─ Token-aware splitting
    │
    ├─► HybridCompressor
    │   └─ Multi-stage compression
    │
    └─► TokenCounter (Utility)
        └─ Token estimation & splitting
```

### 3. Validation Layer (validation.py)
```
ContextValidator
    │
    ├─► FreshnessValidator
    │   └─ Age-based validation
    │
    ├─► ContradictionDetector
    │   └─ Conflict identification
    │
    ├─► RelevanceScorer
    │   └─ Query relevance measurement
    │
    └─► ConsistencyChecker
        └─ Factual consistency
```

## Data Flow

```
Input Context Items
    │
    ▼
┌─────────────────┐
│ Pre-Validation  │  ◄── ValidationConfig
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Pruning      │  ◄── PruningConfig
│  - Remove stale │
│  - Deduplicate  │
│  - Filter by    │
│    relevance    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Compression    │  ◄── CompressionConfig
│  - Chunk text   │
│  - Summarize    │
│  - Reduce size  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Post-Validation  │
│  - Check quality│
│  - Score result │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Metrics Collect │
│  - Token counts │
│  - Quality score│
│  - Duration     │
└────────┬────────┘
         │
         ▼
Optimized Context
```

## Strategy Pattern Implementation

Each layer implements the Strategy pattern:

```python
# Abstract base class
class BasePruner(ABC):
    @abstractmethod
    async def prune(items, query) -> List[ContextItem]:
        pass

# Concrete strategies
class RecencyPruner(BasePruner):
    async def prune(...): # Recency logic

class SemanticSimilarityPruner(BasePruner):
    async def prune(...): # Similarity logic

# Orchestrator
class ContextPruner:
    def __init__(self):
        self._pruners = {
            Strategy.RECENCY: RecencyPruner(),
            Strategy.SEMANTIC: SemanticSimilarityPruner(),
            ...
        }
    
    async def prune(self, strategy):
        return await self._pruners[strategy].prune(...)
```

## Configuration Cascade

```
OptimizationConfig (Top Level)
    │
    ├─► mode: OptimizationMode
    │   ├─ AGGRESSIVE
    │   ├─ BALANCED
    │   ├─ CONSERVATIVE
    │   └─ CUSTOM
    │
    ├─► PruningConfig
    │   ├─ strategy: PruningStrategy
    │   ├─ max_items: int
    │   ├─ max_tokens: int
    │   ├─ similarity_threshold: float
    │   └─ relevance_threshold: float
    │
    ├─► CompressionConfig
    │   ├─ strategy: CompressionStrategy
    │   ├─ target_ratio: float
    │   ├─ max_chunk_size: int
    │   └─ chunk_overlap: int
    │
    └─► ValidationConfig
        ├─ max_age_seconds: float
        ├─ relevance_threshold: float
        ├─ check_contradictions: bool
        └─ strict_mode: bool
```

## Optimization Modes Comparison

| Feature | Aggressive | Balanced | Conservative |
|---------|-----------|----------|--------------|
| Compression Ratio | 0.4 (60% reduction) | 0.5 (50% reduction) | 0.7 (30% reduction) |
| Similarity Threshold | 0.75 (more dedup) | 0.85 (moderate) | 0.95 (less dedup) |
| Relevance Threshold | 0.4 (strict) | 0.3 (moderate) | 0.2 (lenient) |
| Max Age | 2 hours | 1 hour | 30 minutes |
| Contradiction Check | Disabled | Enabled | Enabled |
| Consistency Check | Disabled | Enabled | Enabled |
| Strict Mode | No | No | Yes |
| Speed | Fast | Medium | Slower |
| Quality | Lower | Good | Highest |

## Async Execution Flow

```
Main Thread
    │
    ├─► Validation Tasks (Parallel)
    │   ├─ FreshnessValidator.validate()
    │   ├─ ContradictionDetector.validate()
    │   ├─ RelevanceScorer.validate()
    │   └─ ConsistencyChecker.validate()
    │   └─► asyncio.gather() ──► Combined Result
    │
    ├─► Pruning (Sequential)
    │   └─ Strategy-specific pruning
    │
    ├─► Compression (Sequential)
    │   └─ Strategy-specific compression
    │
    └─► Final Validation (Parallel)
        └─► Results aggregation
```

## Error Handling Strategy

```
try:
    ┌─────────────────┐
    │ Pre-validation  │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │    Pruning      │ ──► Errors logged, continue
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │  Compression    │ ──► Errors logged, use original
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │Post-validation  │ ──► Errors in result
    └─────────────────┘
except Exception as e:
    └─► Return OptimizationResult(
            success=False,
            issues=[str(e)],
            optimized_items=original_items
        )
```

## Performance Optimization Techniques

1. **Lazy Evaluation**
   - Embeddings generated only when needed
   - Cached for reuse within operation

2. **Parallel Processing**
   - Multiple validators run concurrently
   - Async/await throughout

3. **Early Termination**
   - Stop pruning when target met
   - Exit loops on quality threshold

4. **Smart Chunking**
   - Token-based splitting
   - Overlap for context preservation

5. **Adaptive Algorithms**
   - Adjust aggressiveness per round
   - Monitor quality degradation

## Extension Points

To add new strategies:

### 1. New Pruning Strategy
```python
class MyCustomPruner(BasePruner):
    async def prune(self, items, query):
        # Custom logic
        return pruned_items

# Register in ContextPruner
self._pruners[PruningStrategy.CUSTOM] = MyCustomPruner(config)
```

### 2. New Compression Strategy
```python
class MyCustomCompressor(BaseCompressor):
    async def compress(self, text):
        # Custom logic
        return CompressionResult(...)

# Register in ContextCompressor
self._compressors[CompressionStrategy.CUSTOM] = MyCustomCompressor(config)
```

### 3. New Validation Check
```python
class MyCustomValidator(BaseValidator):
    async def validate(self, items, query):
        # Custom logic
        return ValidationResult(...)

# Register in ContextValidator
self._validators[ValidationCheck.CUSTOM] = MyCustomValidator(config)
```

## Integration with IRAS System

```
IRAS Agent
    │
    ├─► Memory System
    │   └─► Context Optimizer (prune old memories)
    │
    ├─► Planning Module
    │   └─► Context Optimizer (compress plans)
    │
    ├─► Reasoning Engine
    │   └─► Context Optimizer (validate reasoning)
    │
    └─► LLM Interface
        └─► Context Optimizer (fit token limits)
```

## File Dependencies

```
context_optimizer.py
    ├─ imports → pruning.py
    ├─ imports → compression.py
    └─ imports → validation.py

pruning.py
    ├─ numpy (embeddings)
    ├─ pydantic (config)
    └─ loguru (logging)

compression.py
    ├─ numpy (optional)
    ├─ pydantic (config)
    └─ loguru (logging)

validation.py
    ├─ numpy (embeddings)
    ├─ pydantic (config)
    └─ loguru (logging)
```

---

*Architecture designed for scalability, maintainability, and extensibility*
