# LLM Configuration Guide

Bloom uses large language models (LLMs) for AI-powered evaluation content generation and agent intent understanding. This guide explains how to configure and use different LLM providers.

---

## Supported Providers

Bloom supports three LLM providers:

1. **Anthropic Claude** (Recommended)
2. **OpenAI GPT**
3. **Google Gemini**

---

## Quick Start

### 1. Choose Your Provider

Pick one LLM provider and obtain an API key:

**Anthropic Claude:**
```bash
# Get API key from: https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**OpenAI GPT:**
```bash
# Get API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Google Gemini:**
```bash
# Get API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2. Configure Environment

Add to your `.env` file:

```bash
# LLM Provider Configuration
LLM_PROVIDER=anthropic  # Options: anthropic, openai, gemini
LLM_MODEL=claude-3-5-sonnet-20241022  # See model options below
LLM_TEMPERATURE=0.7  # Creativity (0.0-1.0)
LLM_MAX_TOKENS=4096  # Maximum response length

# API Key (at least one required)
ANTHROPIC_API_KEY=your-key-here
# OPENAI_API_KEY=your-key-here
# GEMINI_API_KEY=your-key-here
```

### 3. Verify Configuration

```bash
# Start Bloom
./start.sh

# Check logs for LLM initialization
docker-compose logs api | grep "LLM Client initialized"
```

You should see:
```
LLM Client initialized: provider=anthropic, model=claude-3-5-sonnet-20241022
```

---

## Provider Details

### Anthropic Claude (Recommended)

**Why Choose Claude:**
- Best for evaluation writing (professional, nuanced)
- Excellent at following complex instructions
- Strong at evidence synthesis
- Long context window (200K tokens)

**Available Models:**
```bash
# Production (Recommended)
LLM_MODEL=claude-3-5-sonnet-20241022  # Best balance of quality and speed

# High Quality
LLM_MODEL=claude-3-opus-20240229  # Maximum quality, slower

# Fast & Economical
LLM_MODEL=claude-3-haiku-20240307  # Quick responses, lower cost
```

**Configuration Example:**
```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
```

**Cost:**
- Input: $3/million tokens
- Output: $15/million tokens
- Typical evaluation: ~$0.05-0.15

---

### OpenAI GPT

**Why Choose GPT:**
- Widely adopted and well-documented
- Fast response times
- Strong general capabilities

**Available Models:**
```bash
# Production
LLM_MODEL=gpt-4-turbo  # Latest GPT-4 Turbo

# High Quality
LLM_MODEL=gpt-4  # Original GPT-4

# Fast & Economical
LLM_MODEL=gpt-3.5-turbo  # Fastest, most economical
```

**Configuration Example:**
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
```

**Cost:**
- GPT-4 Turbo: ~$10-30/million tokens
- Typical evaluation: ~$0.03-0.10

---

### Google Gemini

**Why Choose Gemini:**
- Multimodal capabilities (text, images)
- Long context window (1M tokens)
- Free tier available

**Available Models:**
```bash
# Production
LLM_MODEL=gemini-pro  # Standard Gemini

# Vision (future use)
LLM_MODEL=gemini-pro-vision  # Multimodal
```

**Configuration Example:**
```bash
LLM_PROVIDER=gemini
LLM_MODEL=gemini-pro
GEMINI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
```

**Cost:**
- Free tier: 60 requests/minute
- Paid: $0.50/million tokens
- Typical evaluation: ~$0.01-0.03

---

## Advanced Configuration

### Temperature Settings

Controls creativity vs. determinism (0.0-1.0):

```bash
# Factual, consistent (good for theme extraction)
LLM_TEMPERATURE=0.3

# Balanced (recommended for evaluations)
LLM_TEMPERATURE=0.7

# Creative, varied (good for narrative)
LLM_TEMPERATURE=0.9
```

**By Agent:**
- **Watchkeeper**: 0.5 (deterministic planning)
- **ContextMiner**: 0.3 (factual analysis)
- **Scribe**: 0.7 (creative writing)
- **Analyst**: 0.3 (statistical accuracy)

### Token Limits

Maximum response length:

```bash
# Short responses (faster, cheaper)
LLM_MAX_TOKENS=1024

# Standard (recommended)
LLM_MAX_TOKENS=4096

# Long-form content
LLM_MAX_TOKENS=8192
```

### Multiple Providers (Fallback)

Configure multiple providers for redundancy:

```bash
# Primary provider
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Fallback providers (if primary fails)
OPENAI_API_KEY=sk-xxxxx
GEMINI_API_KEY=xxxxx
```

Bloom will automatically fallback to rule-based generation if all LLM calls fail.

---

## How Bloom Uses LLMs

### Scribe Agent (RAG Pipeline)

**1. Theme Extraction**
```python
# Input: Raw peer feedback
# Output: ["technical_excellence", "leadership", "communication"]
themes = await scribe._extract_themes(feedback_text)
```

**2. Professional Narrative Generation**
```python
# Input: Informal feedback + themes
# Output: Professional 2-3 sentence summary
narrative = await scribe._generate_professional_narrative(
    text="John really helped me debug that gnarly issue",
    themes=["technical_excellence", "collaboration"],
    context_type="peer_feedback"
)
# Result: "Demonstrated strong technical troubleshooting capabilities..."
```

**3. Evaluation Section Generation**
```python
# Input: Themes + evidence citations
# Output: 2-3 paragraph professional assessment
section = await scribe._generate_section(
    title="Technical Excellence",
    themes=["problem_solving", "code_quality"],
    evidence_map=evidence_map
)
```

**4. Executive Summary**
```python
# Input: All evaluation data
# Output: 1-paragraph overview
summary = await scribe._generate_summary(
    peer_feedbacks=peer_feedbacks,
    self_eval=self_eval,
    theme_clusters=clusters,
    evidence_map=evidence_map
)
```

**5. Clarifying Questions**
```python
# Input: Evaluation coverage gaps
# Output: JSON array of questions
questions = await scribe._generate_gap_questions(
    sections=sections,
    peer_count=5,
    has_self_eval=True
)
# Result: [
#   {"question": "What specific metrics improved?", "category": "impact"},
#   {"question": "Which projects did they lead?", "category": "leadership"}
# ]
```

### Base Agent (Intent Understanding)

All agents use LLM to understand task intent:

```python
# Agent receives task: "Process peer selection for Jane Doe"
execution_plan = await agent.llm.generate(
    prompt="How should I accomplish this task?",
    system=f"You are {agent.name}, capable of {agent.capabilities}"
)
# Agent uses plan to execute task intelligently
```

---

## Troubleshooting

### Issue: "LLM Client failed to initialize"

**Solution:**
```bash
# Check API key is set
docker-compose exec api env | grep -E "(ANTHROPIC|OPENAI|GEMINI)_API_KEY"

# Verify provider setting
docker-compose exec api env | grep LLM_PROVIDER

# Check logs
docker-compose logs api | grep -i error
```

### Issue: "LLM call failed, using fallback"

**Solution:**
1. Check API key validity
2. Verify internet connectivity
3. Check provider status page
4. Review rate limits

**Fallback behavior:**
Bloom gracefully falls back to rule-based generation if LLM unavailable.

### Issue: Responses are too creative/random

**Solution:**
```bash
# Lower temperature in .env
LLM_TEMPERATURE=0.3  # More deterministic

# Restart services
docker-compose restart api
```

### Issue: Responses are too generic

**Solution:**
```bash
# Increase temperature in .env
LLM_TEMPERATURE=0.8  # More creative

# Use higher-quality model
LLM_MODEL=claude-3-opus-20240229  # or gpt-4

# Restart services
docker-compose restart api
```

---

## Cost Optimization

### 1. Choose Economical Models

```bash
# Anthropic
LLM_MODEL=claude-3-haiku-20240307  # ~10x cheaper than Opus

# OpenAI
LLM_MODEL=gpt-3.5-turbo  # ~30x cheaper than GPT-4

# Gemini
LLM_MODEL=gemini-pro  # Free tier available
```

### 2. Reduce Token Usage

```bash
# Lower max tokens
LLM_MAX_TOKENS=2048  # Instead of 4096

# Use caching (if provider supports)
# Anthropic Claude supports prompt caching
```

### 3. Batch Evaluations

Run evaluations in batches during off-peak hours to maximize throughput.

### 4. Monitor Usage

```bash
# Check logs for token usage
docker-compose logs api | grep "usage"

# Example output:
# "usage": {"input_tokens": 1250, "output_tokens": 450}
```

---

## Security Best Practices

### 1. Protect API Keys

```bash
# Never commit .env file
echo ".env" >> .gitignore

# Use secrets management in production
# AWS Secrets Manager, Google Secret Manager, etc.
```

### 2. Rate Limiting

Configure rate limits in `.env`:

```bash
# Anthropic: 50 requests/minute (tier 1)
# OpenAI: 500 requests/minute (tier 1)
# Gemini: 60 requests/minute (free tier)
```

### 3. Content Filtering

Bloom automatically sanitizes:
- PII (personally identifiable information)
- Sensitive company data
- Inappropriate content

---

## Testing Different Providers

### Quick Switch Test

```bash
# Test Anthropic
LLM_PROVIDER=anthropic ./start.sh

# Test OpenAI
LLM_PROVIDER=openai ./start.sh

# Test Gemini
LLM_PROVIDER=gemini ./start.sh
```

### Compare Output Quality

Run the same evaluation with different providers:

```bash
# Generate evaluation with Claude
LLM_PROVIDER=anthropic python examples/simple_evaluation.py > claude_output.txt

# Generate evaluation with GPT
LLM_PROVIDER=openai python examples/simple_evaluation.py > gpt_output.txt

# Compare results
diff claude_output.txt gpt_output.txt
```

---

## Production Recommendations

### For Startups (<100 evaluations/month)

```bash
LLM_PROVIDER=gemini  # Free tier
LLM_MODEL=gemini-pro
LLM_TEMPERATURE=0.7
```

**Cost:** Free
**Quality:** Good
**Speed:** Fast

### For Mid-Size Companies (100-1000 evaluations/month)

```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_TEMPERATURE=0.7
```

**Cost:** ~$50-500/month
**Quality:** Excellent
**Speed:** Very Fast

### For Enterprises (1000+ evaluations/month)

```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022  # Or Opus for highest quality
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
```

**Cost:** ~$500-5000/month
**Quality:** Exceptional
**Speed:** Very Fast

Consider:
- Negotiated enterprise pricing
- Dedicated capacity
- Custom fine-tuning

---

## Support

For LLM-related issues:
- Check provider status pages
- Review Bloom logs
- Contact support at bloom-support@company.com

**Provider Status Pages:**
- Anthropic: https://status.anthropic.com/
- OpenAI: https://status.openai.com/
- Google: https://status.cloud.google.com/
