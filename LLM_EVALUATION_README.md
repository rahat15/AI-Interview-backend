# LLM-Based CV Evaluation

This document describes the LLM integration for CV and JD evaluation in the AI Interview backend.

## Overview

The CV evaluation system now supports both LLM-based and heuristic-based scoring. The system automatically tries LLM scoring first and falls back to heuristic methods if the LLM is unavailable or fails.

## Features

### 🎯 Three-Score System
1. **CV Quality** (100 pts): General resume strength assessment
2. **JD Match** (100 pts): How well CV fits the job description  
3. **Fit Index**: Weighted combination (0.6 × JD Match + 0.4 × CV Quality)

### 🤖 LLM Providers Supported
- **OpenAI**: GPT-4o-mini (default), GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude-3-Haiku, Claude-3-Sonnet, Claude-3-Opus
- **Groq**: llama3-8b-8192 (default), llama3-70b-8192, mixtral-8x7b-32768

### 🔄 Automatic Fallback
- LLM scoring attempted first
- Graceful fallback to heuristic scoring on any failure
- No interruption to API functionality

## Configuration

### Environment Variables

```bash
# Required for LLM scoring
OPENAI_API_KEY=your_openai_api_key_here
# OR
ANTHROPIC_API_KEY=your_anthropic_api_key_here
# OR
GROQ_API_KEY=your_groq_api_key_here

# Optional: Specify model
LLM_MODEL=gpt-4o-mini  # Default for OpenAI
LLM_MODEL=claude-3-haiku-20240307  # Default for Anthropic
LLM_MODEL=llama3-8b-8192  # Default for Groq
```

### API Usage

The public API remains unchanged:

```python
from evaluation.engine import CVEvaluationEngine
from evaluation.schemas import CVEvaluationRequest

# Initialize engine (automatically uses LLM if available)
engine = CVEvaluationEngine(use_llm=True)

# Evaluate CV against JD
request = CVEvaluationRequest(
    cv_text="...",
    jd_text="...",
    include_constraints=True
)

result = engine.evaluate(request)
print(f"Fit Index: {result.fit_index}/100 ({result.band})")
```

## Scoring Rubric

### CV Quality Dimensions (100 pts)
- **ATS Structure** (10): Contact info, parseable bullets, consistent dates
- **Writing Clarity** (15): Concise, active voice, parallel bullets
- **Quantified Impact** (20): Metrics (%/ms/$/users/xN) tied to actions
- **Technical Depth** (15): Concrete tools/frameworks and complex work
- **Projects/Portfolio** (10): Projects/OSS with outcomes/links
- **Leadership Skills** (10): Led/mentored/owned; cross-functional collaboration
- **Career Progression** (10): Recent relevant work; increasing responsibility
- **Consistency** (10): Coherent formatting; no large unexplained gaps

### JD Match Dimensions (100 pts)
- **Hard Skills** (35): Must-have coverage with recency preference
- **Responsibilities** (15): Overlap of verbs/outcomes with JD
- **Domain Relevance** (10): Industry/domain cues
- **Seniority** (10): Years vs JD range; partial if close
- **Nice-to-Haves** (5): Bonus skills and qualifications
- **Education/Certs** (5): Academic and professional certifications
- **Recent Achievements** (10): Recent, role-relevant wins
- **Constraints** (10): Location/work auth/shift (excluded by default)

### Score Bands
- **≥90**: Excellent
- **75–89**: Strong  
- **60–74**: Partial
- **<60**: Weak

## API Endpoints

### POST `/v1/evaluation/cv`
Evaluate CV against JD with direct text input.

**Request:**
```json
{
  "cv_text": "CV content...",
  "jd_text": "Job description content...",
  "include_constraints": true
}
```

**Response:**
```json
{
  "cv_quality": {
    "overall_score": 85.0,
    "band": "Strong",
    "subscores": [
      {
        "dimension": "ats_structure",
        "score": 8.0,
        "max_score": 10.0,
        "evidence": ["email@example.com present", "phone number included"]
      }
    ]
  },
  "jd_match": {
    "overall_score": 82.0,
    "band": "Strong",
    "subscores": [...]
  },
  "fit_index": 83.2,
  "band": "Strong",
  "constraints_disclosure": {
    "constraints_score": 10.0,
    "constraints_evidence": ["Location requirements met"]
  }
}
```

### POST `/v1/evaluation/cv/{cv_artifact_id}/{jd_artifact_id}`
Evaluate using stored CV and JD artifacts.

### GET `/v1/evaluation/cv/quality/{cv_artifact_id}`
Evaluate CV quality only (without job description).

## Testing

### Run Basic Test
```bash
python test_evaluation.py
```

### Test LLM Integration
```bash
python test_llm_integration.py
```

### Run Unit Tests
```bash
python -m pytest tests/test_llm_evaluation.py -v
```

## Implementation Details

### LLM Prompting Strategy
- **System Prompt**: Strict JSON-only output requirement
- **User Prompt**: Detailed rubric with specific scoring criteria
- **JSON Schema**: Enforced structure with exact field requirements
- **Evidence Extraction**: Cites exact CV text spans for each score

### Error Handling
- **API Failures**: Network issues, rate limits, authentication errors
- **JSON Parsing**: Invalid responses, malformed structure
- **Validation Errors**: Missing required fields, type mismatches
- **Graceful Degradation**: Automatic fallback to heuristic scoring

### Performance Considerations
- **Temperature**: Set to 0 for consistent scoring
- **Max Tokens**: 4000 for comprehensive evaluation
- **Caching**: Consider implementing response caching for repeated evaluations
- **Rate Limiting**: Respect API provider rate limits

## Security

- **API Keys**: Never logged or exposed in responses
- **Input Validation**: Sanitize CV/JD text before LLM submission
- **Error Messages**: Generic error responses to avoid information leakage
- **Environment Variables**: Secure storage of API credentials

## Monitoring

### Logging
- LLM initialization success/failure
- Scoring method used (LLM vs heuristic)
- API call success/failure rates
- Response parsing errors

### Metrics
- LLM vs heuristic usage ratio
- Average response times
- Error rates by provider
- Score distribution analysis

## Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY environment variable not set"**
   - Set the environment variable or use heuristic mode
   - Check API key validity

2. **"LLM API call failed"**
   - Verify API key is correct
   - Check network connectivity
   - Review rate limits

3. **"Failed to parse LLM response"**
   - LLM returned invalid JSON
   - System automatically falls back to heuristic

4. **High latency**
   - Consider using faster models (GPT-4o-mini, Claude-3-Haiku)
   - Implement response caching
   - Use heuristic mode for bulk processing

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- **Multi-Model Ensemble**: Combine multiple LLM providers for consensus
- **Custom Rubrics**: User-defined scoring criteria
- **Batch Processing**: Evaluate multiple CVs against one JD
- **Score Calibration**: Adjust scoring based on industry/role
- **Feedback Loop**: Learn from user corrections to improve scoring
