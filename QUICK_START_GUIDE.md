# Context Optimization Module - Quick Start Guide

## Installation

No installation required - the module is ready to use at:
```
/home/user/yelo/src/iras/optimization/
```

## Basic Import

```python
from iras.optimization import (
    ContextOptimizer,
    OptimizationConfig,
    OptimizationMode,
)
```

## Quick Examples

### 1. Simple Text Optimization
```python
from iras.optimization import optimize_text

# Optimize a long text
result = await optimize_text(
    text=long_document,
    mode=OptimizationMode.BALANCED,
    max_tokens=2000,
)

print(f"Optimized: {len(result)}")
```

### 2. Context Items Optimization
```python
from iras.optimization import ContextOptimizer, OptimizationConfig
from iras.optimization.pruning import ContextItem

# Create optimizer
config = OptimizationConfig(
    mode=OptimizationMode.BALANCED,
    max_token_count=3000,
    min_quality_score=0.7,
)
optimizer = ContextOptimizer(config)

# Create items
items = [
    ContextItem(id="1", content="...", importance=0.8),
    ContextItem(id="2", content="...", importance=0.6),
]

# Optimize
result = await optimizer.optimize(items, query="What is AI?")

print(f"Tokens: {result.metrics.original_tokens} → {result.metrics.final_tokens}")
print(f"Ratio: {result.metrics.compression_ratio:.2%}")
print(f"Quality: {result.metrics.validation_score:.3f}")
```

### 3. Individual Operations

#### Just Pruning
```python
from iras.optimization import prune_context
from iras.optimization.pruning import PruningStrategy

pruned_items = await prune_context(
    items=items,
    strategy=PruningStrategy.HYBRID,
    query="my query",
    max_tokens=2000,
)
```

#### Just Compression
```python
from iras.optimization import compress_context
from iras.optimization.compression import CompressionStrategy

result = await compress_context(
    text=long_text,
    strategy=CompressionStrategy.EXTRACTIVE,
    target_ratio=0.5,
)

print(f"Compressed: {result.compressed_text}")
print(f"Ratio: {result.compression_ratio:.2%}")
```

#### Just Validation
```python
from iras.optimization import validate_context
from iras.optimization.validation import ValidationCheck

result = await validate_context(
    items=items,
    query="my query",
    checks=[ValidationCheck.FRESHNESS, ValidationCheck.RELEVANCE],
)

print(f"Valid: {result.is_valid}")
print(f"Score: {result.score:.3f}")
for issue in result.issues:
    print(f"  - {issue.severity}: {issue.message}")
```

## Configuration Modes

### Aggressive Mode (Speed over Quality)
```python
config = OptimizationConfig(mode=OptimizationMode.AGGRESSIVE)
# - 60% compression
# - Fast execution
# - Minimal validation
```

### Balanced Mode (Default)
```python
config = OptimizationConfig(mode=OptimizationMode.BALANCED)
# - 50% compression
# - Good quality
# - Full validation
```

### Conservative Mode (Quality over Speed)
```python
config = OptimizationConfig(mode=OptimizationMode.CONSERVATIVE)
# - 30% compression
# - Highest quality
# - Strict validation
```

### Custom Mode
```python
from iras.optimization.pruning import PruningConfig, PruningStrategy
from iras.optimization.compression import CompressionConfig, CompressionStrategy
from iras.optimization.validation import ValidationConfig

config = OptimizationConfig(
    mode=OptimizationMode.CUSTOM,
    max_token_count=5000,
    min_quality_score=0.8,
    pruning_config=PruningConfig(
        strategy=PruningStrategy.IMPORTANCE_WEIGHTED,
        max_tokens=5000,
        similarity_threshold=0.9,
    ),
    compression_config=CompressionConfig(
        strategy=CompressionStrategy.HYBRID,
        target_ratio=0.6,
    ),
    validation_config=ValidationConfig(
        max_age_seconds=3600,
        strict_mode=True,
    ),
)
```

## Common Patterns

### Pattern 1: Optimize Agent Memory
```python
async def optimize_agent_memory(agent):
    # Get memory items
    memory_items = agent.memory.get_all_items()
    
    # Convert to ContextItems
    context_items = [
        ContextItem(
            id=str(item.id),
            content=item.content,
            timestamp=item.timestamp,
            importance=item.importance,
        )
        for item in memory_items
    ]
    
    # Optimize
    result = await optimizer.optimize(context_items)
    
    # Update memory with optimized items
    agent.memory.replace_items(result.optimized_items)
    
    return result.metrics
```

### Pattern 2: Fit Context to LLM Token Limit
```python
async def fit_to_token_limit(text: str, max_tokens: int = 4000):
    optimizer = ContextOptimizer(
        OptimizationConfig(
            mode=OptimizationMode.AGGRESSIVE,
            max_token_count=max_tokens,
        )
    )
    
    result = await optimizer.optimize_text(text)
    
    if result.success:
        return result.optimized_text
    else:
        raise ValueError(f"Failed to optimize: {result.issues}")
```

### Pattern 3: Quality-Aware Summarization
```python
async def summarize_with_quality_check(text: str, min_quality: float = 0.7):
    config = OptimizationConfig(
        mode=OptimizationMode.BALANCED,
        min_quality_score=min_quality,
        target_token_count=500,
    )
    
    optimizer = ContextOptimizer(config)
    result = await optimizer.optimize_text(text)
    
    if result.metrics.validation_score < min_quality:
        # Fall back to conservative mode
        config.mode = OptimizationMode.CONSERVATIVE
        optimizer.update_config(config)
        result = await optimizer.optimize_text(text)
    
    return result.optimized_text
```

### Pattern 4: Batch Processing
```python
async def optimize_multiple_contexts(contexts: List[str]):
    optimizer = ContextOptimizer()
    
    # Process in parallel
    results = await asyncio.gather(*[
        optimizer.optimize_text(context)
        for context in contexts
    ])
    
    return results
```

## Monitoring & Metrics

### Get Detailed Metrics
```python
result = await optimizer.optimize(items, query)

# Token metrics
print(f"Original: {result.metrics.original_tokens} tokens")
print(f"Final: {result.metrics.final_tokens} tokens")
print(f"Reduction: {result.metrics.token_reduction} tokens")
print(f"Ratio: {result.metrics.compression_ratio:.2%}")

# Item metrics
print(f"Items: {result.metrics.original_items} → {result.metrics.final_items}")
print(f"Removed: {result.metrics.items_removed}")

# Quality metrics
print(f"Quality score: {result.metrics.validation_score:.3f}")
print(f"Quality preserved: {result.metrics.quality_preserved}")

# Performance
print(f"Duration: {result.metrics.duration_seconds:.3f}s")
print(f"Rounds: {result.metrics.rounds_executed}")
```

### Get Summary
```python
summary = result.get_summary()
# Returns:
# {
#     'success': True,
#     'items_count': 25,
#     'token_count': 1500,
#     'compression_ratio': 0.55,
#     'validation_score': 0.85,
#     'issues_count': 0,
#     'duration': 0.234
# }
```

## Error Handling

```python
try:
    result = await optimizer.optimize(items, query)
    
    if not result.success:
        print(f"Optimization had issues:")
        for issue in result.issues:
            print(f"  - {issue}")
    
    if result.validation_result.has_critical_issues():
        print("Critical validation issues found!")
        for issue in result.validation_result.issues:
            if issue.severity == ValidationSeverity.CRITICAL:
                print(f"  - {issue.message}")
    
except Exception as e:
    print(f"Optimization failed: {e}")
```

## Performance Tips

1. **Use appropriate mode for your use case**
   - Aggressive for speed-critical paths
   - Conservative for quality-critical paths

2. **Reuse optimizer instances**
   ```python
   # Good: Reuse
   optimizer = ContextOptimizer(config)
   for batch in batches:
       await optimizer.optimize(batch)
   
   # Avoid: Creating new instances
   for batch in batches:
       optimizer = ContextOptimizer(config)  # Wasteful
       await optimizer.optimize(batch)
   ```

3. **Pre-generate embeddings if possible**
   ```python
   # If you have embeddings already
   item = ContextItem(
       id="1",
       content="...",
       embedding=my_embedding.tolist(),  # Reuse existing
   )
   ```

4. **Use batch processing for multiple contexts**
   ```python
   results = await asyncio.gather(*[
       optimizer.optimize_text(text)
       for text in texts
   ])
   ```

5. **Monitor metrics to tune configuration**
   ```python
   if result.metrics.compression_ratio < 0.3:
       # Not compressing enough, increase aggressiveness
       config.compression_config.target_ratio = 0.4
       optimizer.update_config(config)
   ```

## File Locations

- **Main Module**: `/home/user/yelo/src/iras/optimization/`
- **Pruning**: `/home/user/yelo/src/iras/optimization/pruning.py`
- **Compression**: `/home/user/yelo/src/iras/optimization/compression.py`
- **Validation**: `/home/user/yelo/src/iras/optimization/validation.py`
- **Optimizer**: `/home/user/yelo/src/iras/optimization/context_optimizer.py`

## Next Steps

1. Install dependencies: `numpy`, `loguru`, `pydantic`
2. Import the module in your IRAS agent
3. Configure based on your needs
4. Start optimizing!

For more details, see:
- `OPTIMIZATION_MODULE_SUMMARY.md` - Complete feature list
- `OPTIMIZATION_ARCHITECTURE.md` - Architecture details
