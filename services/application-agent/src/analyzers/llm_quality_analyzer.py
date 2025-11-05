"""
LLM Quality Analyzer

Uses LLM for advanced quality analysis and scoring.
"""

from typing import Dict, Optional, List
from ..llm.llm_client import llm_client
from ..llm.prompts import (
    RELEVANCE_PROMPT,
    COHERENCE_PROMPT,
    HALLUCINATION_PROMPT,
    OVERALL_QUALITY_PROMPT,
    IMPROVEMENT_PROMPT
)
from ..core.logger import logger


class LLMQualityAnalyzer:
    """LLM-based quality analyzer."""
    
    def __init__(self):
        """Initialize LLM quality analyzer."""
        self.cache = {}  # Simple cache for responses
    
    async def analyze_relevance(
        self,
        prompt: str,
        response: str
    ) -> Optional[float]:
        """
        Analyze relevance using LLM.
        
        Args:
            prompt: Input prompt
            response: Model response
            
        Returns:
            Relevance score (0-100) or None
        """
        try:
            llm_prompt = RELEVANCE_PROMPT.format(
                prompt=prompt,
                response=response
            )
            
            llm_response = await llm_client.generate(llm_prompt)
            score = llm_client.parse_score(llm_response)
            
            if score is not None:
                logger.debug(f"LLM relevance score: {score}")
            
            return score
            
        except Exception as e:
            logger.error(f"LLM relevance analysis failed: {e}")
            return None
    
    async def analyze_coherence(
        self,
        response: str
    ) -> Optional[float]:
        """
        Analyze coherence using LLM.
        
        Args:
            response: Model response
            
        Returns:
            Coherence score (0-100) or None
        """
        try:
            llm_prompt = COHERENCE_PROMPT.format(response=response)
            
            llm_response = await llm_client.generate(llm_prompt)
            score = llm_client.parse_score(llm_response)
            
            if score is not None:
                logger.debug(f"LLM coherence score: {score}")
            
            return score
            
        except Exception as e:
            logger.error(f"LLM coherence analysis failed: {e}")
            return None
    
    async def detect_hallucination(
        self,
        prompt: str,
        response: str
    ) -> Optional[float]:
        """
        Detect hallucinations using LLM.
        
        Args:
            prompt: Input prompt
            response: Model response
            
        Returns:
            Accuracy score (0-100) or None
        """
        try:
            llm_prompt = HALLUCINATION_PROMPT.format(
                prompt=prompt,
                response=response
            )
            
            llm_response = await llm_client.generate(llm_prompt)
            score = llm_client.parse_score(llm_response)
            
            if score is not None:
                logger.debug(f"LLM hallucination score: {score}")
            
            return score
            
        except Exception as e:
            logger.error(f"LLM hallucination detection failed: {e}")
            return None
    
    async def analyze_overall_quality(
        self,
        prompt: str,
        response: str
    ) -> Optional[float]:
        """
        Analyze overall quality using LLM.
        
        Args:
            prompt: Input prompt
            response: Model response
            
        Returns:
            Overall quality score (0-100) or None
        """
        try:
            llm_prompt = OVERALL_QUALITY_PROMPT.format(
                prompt=prompt,
                response=response
            )
            
            llm_response = await llm_client.generate(llm_prompt)
            score = llm_client.parse_score(llm_response)
            
            if score is not None:
                logger.debug(f"LLM overall quality score: {score}")
            
            return score
            
        except Exception as e:
            logger.error(f"LLM overall quality analysis failed: {e}")
            return None
    
    async def suggest_improvements(
        self,
        prompt: str,
        response: str
    ) -> Optional[str]:
        """
        Generate improvement suggestions using LLM.
        
        Args:
            prompt: Input prompt
            response: Model response
            
        Returns:
            Improvement suggestions or None
        """
        try:
            llm_prompt = IMPROVEMENT_PROMPT.format(
                prompt=prompt,
                response=response
            )
            
            suggestions = await llm_client.generate(
                llm_prompt,
                max_tokens=300
            )
            
            if suggestions:
                logger.debug(f"LLM suggestions generated: {len(suggestions)} chars")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"LLM improvement suggestions failed: {e}")
            return None
    
    async def analyze_all(
        self,
        prompt: str,
        response: str
    ) -> Dict[str, Optional[float]]:
        """
        Perform complete LLM-based analysis.
        
        Args:
            prompt: Input prompt
            response: Model response
            
        Returns:
            Dictionary of scores
        """
        logger.info("Performing LLM-based quality analysis")
        
        # Run all analyses
        relevance = await self.analyze_relevance(prompt, response)
        coherence = await self.analyze_coherence(response)
        hallucination = await self.detect_hallucination(prompt, response)
        overall = await self.analyze_overall_quality(prompt, response)
        
        return {
            "relevance": relevance,
            "coherence": coherence,
            "hallucination": hallucination,
            "overall": overall
        }


# Global instance
llm_quality_analyzer = LLMQualityAnalyzer()
