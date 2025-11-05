"""
Groq LLM Client for Quality Analysis
Phase 6.5: Application Quality Monitoring
"""
import logging
from typing import Dict, Any, Optional
from groq import Groq

logger = logging.getLogger(__name__)


class GroqClient:
    """
    Client for Groq LLM API to analyze application quality
    
    Features:
    - Quality scoring (coherence, relevance, accuracy)
    - Hallucination detection
    - Toxicity/safety analysis
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Groq client
        
        Args:
            api_key: Groq API key
        """
        self.client = Groq(api_key=api_key)
        self.logger = logging.getLogger(f"{__name__}.GroqClient")
    
    def analyze_quality(
        self,
        prompt: str,
        response: str,
        model_name: str = "openai/gpt-oss-20b"
    ) -> Dict[str, Any]:
        """
        Analyze the quality of an LLM response
        
        Args:
            prompt: The original prompt
            response: The LLM response to analyze
            model_name: Model used for generation
        
        Returns:
            Dict with quality scores
        """
        try:
            analysis_prompt = f"""
Analyze the following LLM interaction for quality. Rate each aspect from 0.0 to 1.0:

PROMPT: {prompt}

RESPONSE: {response}

Provide scores for:
1. Coherence (logical flow and structure)
2. Relevance (addresses the prompt)
3. Accuracy (factual correctness)
4. Completeness (thorough answer)

Return ONLY a JSON object with these exact keys: coherence, relevance, accuracy, completeness, overall_quality
"""
            
            completion = self.client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            result_text = completion.choices[0].message.content
            
            # Parse JSON response
            import json
            scores = json.loads(result_text)
            
            self.logger.info(f"Quality analysis completed: overall={scores.get('overall_quality', 0)}")
            return scores
            
        except Exception as e:
            self.logger.error(f"Quality analysis failed: {e}")
            return {
                "coherence": 0.0,
                "relevance": 0.0,
                "accuracy": 0.0,
                "completeness": 0.0,
                "overall_quality": 0.0,
                "error": str(e)
            }
    
    def detect_hallucination(
        self,
        prompt: str,
        response: str
    ) -> Dict[str, Any]:
        """
        Detect potential hallucinations in LLM response
        
        Args:
            prompt: The original prompt
            response: The LLM response to check
        
        Returns:
            Dict with hallucination score and details
        """
        try:
            analysis_prompt = f"""
Analyze if the following LLM response contains hallucinations (false or fabricated information):

PROMPT: {prompt}

RESPONSE: {response}

Provide:
1. hallucination_score (0.0 = no hallucination, 1.0 = definite hallucination)
2. confidence (how confident you are in the assessment)
3. reasoning (brief explanation)

Return ONLY a JSON object with keys: hallucination_score, confidence, reasoning
"""
            
            completion = self.client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.1,
                max_tokens=300
            )
            
            result_text = completion.choices[0].message.content
            
            # Parse JSON response
            import json
            result = json.loads(result_text)
            
            self.logger.info(f"Hallucination detection: score={result.get('hallucination_score', 0)}")
            return result
            
        except Exception as e:
            self.logger.error(f"Hallucination detection failed: {e}")
            return {
                "hallucination_score": 0.0,
                "confidence": 0.0,
                "reasoning": f"Analysis failed: {str(e)}",
                "error": str(e)
            }
    
    def check_toxicity(
        self,
        text: str
    ) -> Dict[str, Any]:
        """
        Check text for toxicity, hate speech, or unsafe content
        
        Args:
            text: Text to analyze
        
        Returns:
            Dict with toxicity scores
        """
        try:
            analysis_prompt = f"""
Analyze the following text for toxicity and safety issues:

TEXT: {text}

Rate from 0.0 to 1.0:
1. toxicity (offensive or harmful language)
2. hate_speech (discriminatory content)
3. violence (violent content)
4. profanity (inappropriate language)

Return ONLY a JSON object with keys: toxicity, hate_speech, violence, profanity, overall_safety
"""
            
            completion = self.client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.1,
                max_tokens=300
            )
            
            result_text = completion.choices[0].message.content
            
            # Parse JSON response
            import json
            scores = json.loads(result_text)
            
            self.logger.info(f"Toxicity check: overall_safety={scores.get('overall_safety', 1.0)}")
            return scores
            
        except Exception as e:
            self.logger.error(f"Toxicity check failed: {e}")
            return {
                "toxicity": 0.0,
                "hate_speech": 0.0,
                "violence": 0.0,
                "profanity": 0.0,
                "overall_safety": 1.0,
                "error": str(e)
            }
