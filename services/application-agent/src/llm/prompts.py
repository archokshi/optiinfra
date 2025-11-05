"""
LLM Prompt Templates

Prompt templates for quality scoring and analysis.
"""

RELEVANCE_PROMPT = """Evaluate how well this response answers the given prompt.

Prompt: {prompt}
Response: {response}

Rate the relevance on a scale of 0-100 where:
- 0-20: Completely irrelevant or off-topic
- 21-40: Somewhat related but misses key points
- 41-60: Partially relevant, addresses some aspects
- 61-80: Mostly relevant, covers main points
- 81-100: Highly relevant, directly and completely answers

Provide ONLY a number between 0-100."""

COHERENCE_PROMPT = """Evaluate the logical coherence and consistency of this response.

Response: {response}

Rate the coherence on a scale of 0-100 where:
- 0-20: Incoherent, contradictory, or nonsensical
- 21-40: Poor structure, some contradictions
- 41-60: Acceptable structure, minor inconsistencies
- 61-80: Good structure, logical flow
- 81-100: Excellent structure, perfectly coherent

Provide ONLY a number between 0-100."""

HALLUCINATION_PROMPT = """Analyze this response for potential hallucinations or factual errors.

Prompt: {prompt}
Response: {response}

Rate the factual accuracy on a scale of 0-100 where:
- 0-20: Contains major hallucinations or false information
- 21-40: Several questionable or unverified claims
- 41-60: Some minor inaccuracies
- 61-80: Mostly accurate with minor issues
- 81-100: Completely accurate, no hallucinations

Provide ONLY a number between 0-100."""

OVERALL_QUALITY_PROMPT = """Provide a comprehensive quality assessment of this response.

Prompt: {prompt}
Response: {response}

Consider:
1. Relevance to the prompt
2. Logical coherence
3. Factual accuracy
4. Completeness
5. Clarity

Rate the overall quality on a scale of 0-100.
Provide ONLY a number between 0-100."""

IMPROVEMENT_PROMPT = """Analyze this response and suggest specific improvements.

Prompt: {prompt}
Response: {response}

Provide 2-3 specific, actionable suggestions to improve this response.
Focus on relevance, accuracy, clarity, and completeness.
Keep suggestions concise (1-2 sentences each)."""
