# IRAS - Intelligent Research & Analysis Swarm

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> A production-ready multi-agent AI system demonstrating comprehensive multi-agent architectures, communication protocols, mathematical foundations, and autonomous operation.

## 🎯 Overview

IRAS (Intelligent Research & Analysis Swarm) is a **complete, production-ready multi-agent system** that showcases the full spectrum of multi-agent AI concepts through an exciting, practical use case: autonomous research and analysis.

The system demonstrates:
- ✅ **Multi-layer agent architecture** (Infrastructure → Tools → Memory → Communication → Agents → Orchestration)
- ✅ **Advanced agent anatomy** (LLM core, reasoning engine, planning module, memory systems, state management)
- ✅ **Communication protocols** (Contract Net, Blackboard, Pub/Sub)
- ✅ **Multi-database integration** (Vector, Graph, Time-Series, Document stores)
- ✅ **Mathematical foundations** (Task allocation, consensus, load balancing, graph analysis)
- ✅ **Context optimization** (Pruning, compression, validation)
- ✅ **Autonomous operation** (Self-monitoring, error recovery, adaptive learning)

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
cd yelo

# Install dependencies
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

### Simple Example

```python
import asyncio
from iras.orchestration import Coordinator

async def main():
    coordinator = Coordinator(num_researchers=1, num_analysts=1, num_synthesizers=1)
    await coordinator.initialize()

    result = await coordinator.research(topic="quantum computing", depth=2)
    print(f"Found {result['total_sources']} sources")
    print(f"Report quality: {result['report']['quality_score']:.2f}")

    await coordinator.shutdown()

asyncio.run(main())
```

### Run Examples

```bash
python examples/simple_example.py              # Single topic research
python examples/semi_complex_example.py        # Multi-topic comparative analysis
python examples/complex_example.py             # Full autonomous swarm
```

## 📚 Key Features

### Specialized Agents
- **ResearcherAgent**: Web search, source evaluation, query refinement
- **AnalystAgent**: Statistical analysis, pattern recognition, insights
- **FactCheckerAgent**: Fact verification, contradiction detection
- **SynthesizerAgent**: Multi-source synthesis, report generation

### Communication Protocols
- **Contract Net**: Task bidding and allocation
- **Blackboard**: Shared memory with pattern matching
- **Pub/Sub**: Topic-based messaging

### Databases
- **Vector Store**: Semantic search with embeddings
- **Graph Store**: Relationship mapping
- **Time-Series Store**: Metrics and forecasting
- **Document Store**: Flexible JSON storage

## 📊 Testing

```bash
pytest                                    # Run all tests
pytest --cov=src/iras --cov-report=html  # With coverage
pytest tests/test_core/test_agent.py -v  # Specific module
```

## 📖 Documentation

- [Quick Start Guide](QUICK_START_GUIDE.md)
- [Architecture Guide](OPTIMIZATION_ARCHITECTURE.md)
- [Module Summary](OPTIMIZATION_MODULE_SUMMARY.md)
- [Test Suite Summary](TEST_SUITE_SUMMARY.md)

## 🏆 What Makes IRAS Special

1. **Production-Ready**: Comprehensive error handling, monitoring, resilience
2. **Complete Implementation**: Full multi-agent system, not a toy example
3. **All Concepts Integrated**: Parts 1-5 working together seamlessly
4. **Reusable Architecture**: Easily adaptable to other domains
5. **Educational Value**: Learn multi-agent systems through working code
6. **Scalable Design**: From 1 to 100+ agent swarms

## 📝 Requirements

- Python 3.10+
- Key dependencies: anthropic/openai, numpy, scipy, networkx, pydantic, loguru

See `pyproject.toml` for complete list.

---

**Ready to build? Start with:** `python examples/simple_example.py`
