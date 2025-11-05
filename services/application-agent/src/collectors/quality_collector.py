"""
Quality Metrics Collector

Collects and analyzes quality metrics for LLM responses.
"""

import re
import time
import uuid
from typing import Dict, List
from datetime import datetime
from ..models.quality_metrics import (
    QualityRequest,
    QualityMetrics,
    RelevanceScore,
    CoherenceScore,
    HallucinationResult
)
from ..core.logger import logger


class QualityCollector:
    """Collects quality metrics for LLM responses."""
    
    def __init__(self):
        """Initialize quality collector."""
        self.confidence_markers = [
            "i think", "maybe", "probably", "possibly", "might be",
            "could be", "seems like", "appears to", "i believe",
            "in my opinion", "not sure", "uncertain"
        ]
        
        self.question_words = ["what", "when", "where", "who", "why", "how"]
    
    async def collect_quality_metrics(
        self,
        request: QualityRequest
    ) -> QualityMetrics:
        """
        Collect quality metrics for a response.
        
        Args:
            request: Quality analysis request
            
        Returns:
            Complete quality metrics
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        logger.info(f"Collecting quality metrics for request {request_id}")
        
        # Analyze relevance
        relevance = self._analyze_relevance(request.prompt, request.response)
        
        # Analyze coherence
        coherence = self._analyze_coherence(request.response)
        
        # Detect hallucinations
        hallucination = self._detect_hallucination(request.response)
        
        # Calculate overall quality
        overall_quality = self._calculate_overall_quality(
            relevance, coherence, hallucination
        )
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        metrics = QualityMetrics(
            request_id=request_id,
            timestamp=datetime.utcnow(),
            prompt=request.prompt,
            response=request.response,
            model_name=request.model_name,
            relevance=relevance,
            coherence=coherence,
            hallucination=hallucination,
            overall_quality=overall_quality,
            quality_grade="",  # Will be set by get_grade()
            processing_time_ms=processing_time,
            metadata=request.metadata
        )
        
        metrics.quality_grade = metrics.get_grade()
        
        logger.info(
            f"Quality metrics collected: "
            f"Overall={overall_quality:.1f}, "
            f"Grade={metrics.quality_grade}, "
            f"Time={processing_time:.1f}ms"
        )
        
        return metrics
    
    def _analyze_relevance(self, prompt: str, response: str) -> RelevanceScore:
        """
        Analyze response relevance to prompt.
        
        Args:
            prompt: User prompt
            response: LLM response
            
        Returns:
            Relevance score
        """
        # Calculate keyword overlap
        prompt_words = set(self._tokenize(prompt.lower()))
        response_words = set(self._tokenize(response.lower()))
        
        # Remove common stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
        prompt_words -= stop_words
        response_words -= stop_words
        
        if len(prompt_words) == 0:
            keyword_overlap = 0.0
        else:
            overlap = len(prompt_words & response_words)
            keyword_overlap = overlap / len(prompt_words)
        
        # Check response length appropriateness
        response_length = len(response.split())
        length_appropriate = 10 <= response_length <= 500  # Reasonable range
        
        # Check question type matching
        question_type_match = self._check_question_type(prompt, response)
        
        # Calculate relevance score
        score = (
            keyword_overlap * 50 +  # 50 points for keyword overlap
            (30 if length_appropriate else 10) +  # 30 points for appropriate length
            (20 if question_type_match else 0)  # 20 points for type match
        )
        
        return RelevanceScore(
            score=min(score, 100),
            keyword_overlap=keyword_overlap,
            length_appropriate=length_appropriate,
            question_type_match=question_type_match,
            details={
                "prompt_words": len(prompt_words),
                "response_words": len(response_words),
                "overlap_words": len(prompt_words & response_words),
                "response_length": response_length
            }
        )
    
    def _analyze_coherence(self, response: str) -> CoherenceScore:
        """
        Analyze response coherence.
        
        Args:
            response: LLM response
            
        Returns:
            Coherence score
        """
        # Sentence quality (basic check)
        sentences = self._split_sentences(response)
        sentence_quality = self._assess_sentence_quality(sentences)
        
        # Logical flow (check for transition words)
        logical_flow = self._assess_logical_flow(response)
        
        # Contradiction detection (basic)
        contradictions = self._detect_contradictions(response)
        
        # Readability (based on sentence length and complexity)
        readability = self._assess_readability(sentences)
        
        # Calculate coherence score
        score = (
            sentence_quality * 0.3 +
            logical_flow * 0.3 +
            readability * 0.3 +
            (10 if contradictions == 0 else 0)  # Penalty for contradictions
        )
        
        return CoherenceScore(
            score=min(score, 100),
            sentence_quality=sentence_quality,
            logical_flow=logical_flow,
            contradictions=contradictions,
            readability=readability,
            details={
                "num_sentences": len(sentences),
                "avg_sentence_length": sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
            }
        )
    
    def _detect_hallucination(self, response: str) -> HallucinationResult:
        """
        Detect potential hallucinations in response.
        
        Args:
            response: LLM response
            
        Returns:
            Hallucination detection result
        """
        response_lower = response.lower()
        
        # Count confidence markers
        confidence_markers = sum(
            1 for marker in self.confidence_markers
            if marker in response_lower
        )
        
        # Detect unsupported claims (sentences with specific facts but no context)
        unsupported_claims = self._detect_unsupported_claims(response)
        
        # Detect overly specific numbers (potential fabrication)
        numeric_precision = self._detect_numeric_precision(response)
        
        # Calculate hallucination rate
        total_indicators = confidence_markers + unsupported_claims + numeric_precision
        hallucination_rate = min(total_indicators * 10, 100)  # Each indicator adds 10%
        
        # Determine risk level
        if hallucination_rate < 20:
            risk_level = "LOW"
        elif hallucination_rate < 50:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        return HallucinationResult(
            hallucination_rate=hallucination_rate,
            confidence_markers=confidence_markers,
            unsupported_claims=unsupported_claims,
            numeric_precision=numeric_precision,
            risk_level=risk_level,
            details={
                "total_indicators": total_indicators,
                "response_length": len(response.split())
            }
        )
    
    def _calculate_overall_quality(
        self,
        relevance: RelevanceScore,
        coherence: CoherenceScore,
        hallucination: HallucinationResult
    ) -> float:
        """
        Calculate overall quality score.
        
        Args:
            relevance: Relevance score
            coherence: Coherence score
            hallucination: Hallucination result
            
        Returns:
            Overall quality score (0-100)
        """
        quality = (
            relevance.score * 0.4 +
            coherence.score * 0.4 +
            (100 - hallucination.hallucination_rate) * 0.2
        )
        
        return round(quality, 2)
    
    # Helper methods
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        return re.findall(r'\b\w+\b', text)
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _check_question_type(self, prompt: str, response: str) -> bool:
        """Check if response matches question type."""
        prompt_lower = prompt.lower()
        
        # Check if it's a question
        is_question = any(word in prompt_lower for word in self.question_words)
        
        if not is_question:
            return True  # Not a question, so type matching doesn't apply
        
        # Basic check: response should not be empty and should be relevant
        return len(response.strip()) > 0
    
    def _assess_sentence_quality(self, sentences: List[str]) -> float:
        """Assess sentence quality."""
        if not sentences:
            return 0.0
        
        # Check for complete sentences (basic heuristic)
        complete_sentences = sum(
            1 for s in sentences
            if len(s.split()) >= 3  # At least 3 words
        )
        
        return (complete_sentences / len(sentences)) * 100
    
    def _assess_logical_flow(self, text: str) -> float:
        """Assess logical flow using transition words."""
        transition_words = [
            "however", "therefore", "furthermore", "moreover",
            "additionally", "consequently", "thus", "hence",
            "first", "second", "finally", "in conclusion"
        ]
        
        text_lower = text.lower()
        transitions_found = sum(1 for word in transition_words if word in text_lower)
        
        # Score based on presence of transitions (not too many, not too few)
        if transitions_found == 0:
            return 60.0  # Acceptable but could be better
        elif transitions_found <= 3:
            return 90.0  # Good
        else:
            return 75.0  # Too many transitions
    
    def _assess_readability(self, sentences: List[str]) -> float:
        """Assess readability based on sentence length."""
        if not sentences:
            return 0.0
        
        avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
        
        # Ideal sentence length is 15-20 words
        if 15 <= avg_length <= 20:
            return 100.0
        elif 10 <= avg_length <= 25:
            return 80.0
        else:
            return 60.0
    
    def _detect_contradictions(self, text: str) -> int:
        """Detect basic contradictions."""
        # Simple contradiction detection (can be enhanced)
        contradiction_patterns = [
            (r'\bnot\b.*\bbut\b', r'\bis\b'),
            (r'\byes\b.*\bno\b', r''),
            (r'\balways\b.*\bnever\b', r'')
        ]
        
        contradictions = 0
        text_lower = text.lower()
        
        for pattern, _ in contradiction_patterns:
            if re.search(pattern, text_lower):
                contradictions += 1
        
        return contradictions
    
    def _detect_unsupported_claims(self, text: str) -> int:
        """Detect unsupported factual claims."""
        # Look for specific claims without context
        claim_patterns = [
            r'\b\d{4}\b',  # Years
            r'\b\d+%\b',  # Percentages
            r'\$\d+',  # Dollar amounts
        ]
        
        claims = 0
        for pattern in claim_patterns:
            claims += len(re.findall(pattern, text))
        
        # Normalize by response length
        words = len(text.split())
        if words > 0:
            claims = int((claims / words) * 100)
        
        return min(claims, 10)  # Cap at 10
    
    def _detect_numeric_precision(self, text: str) -> int:
        """Detect overly specific numbers."""
        # Look for very specific numbers (potential fabrication)
        specific_numbers = re.findall(r'\b\d{3,}\b', text)
        
        # Count numbers with high precision
        precise_count = sum(1 for num in specific_numbers if len(num) > 4)
        
        return min(precise_count, 5)  # Cap at 5


# Global instance
quality_collector = QualityCollector()
