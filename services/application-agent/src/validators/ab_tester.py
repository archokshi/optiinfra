"""
A/B Tester

Implements A/B testing with statistical significance testing.
"""

import uuid
import statistics
import math
from typing import Dict, List, Optional
from scipy import stats
from ..models.validation import (
    ABTestConfig,
    ABTestObservation,
    ABTestResult,
    ABTestGroup
)
from ..core.logger import logger


class ABTester:
    """A/B testing framework with statistical analysis."""
    
    def __init__(self):
        """Initialize A/B tester."""
        self.tests: Dict[str, ABTestConfig] = {}
        self.observations: Dict[str, List[ABTestObservation]] = {}
    
    def setup_test(
        self,
        name: str,
        control_group: str,
        treatment_group: str,
        metric: str = "overall_quality",
        sample_size: int = 100,
        significance_level: float = 0.05
    ) -> ABTestConfig:
        """Setup a new A/B test."""
        test_id = str(uuid.uuid4())
        
        config = ABTestConfig(
            test_id=test_id,
            name=name,
            control_group=control_group,
            treatment_group=treatment_group,
            metric=metric,
            sample_size=sample_size,
            significance_level=significance_level
        )
        
        self.tests[test_id] = config
        self.observations[test_id] = []
        
        logger.info(f"A/B test setup: {test_id} - {name}")
        
        return config
    
    def add_observation(self, observation: ABTestObservation):
        """Add an observation to the test."""
        if observation.test_id not in self.tests:
            raise ValueError(f"Test {observation.test_id} not found")
        
        self.observations[observation.test_id].append(observation)
    
    def calculate_significance(self, test_id: str) -> ABTestResult:
        """Calculate statistical significance of A/B test."""
        if test_id not in self.tests:
            raise ValueError(f"Test {test_id} not found")
        
        config = self.tests[test_id]
        observations = self.observations[test_id]
        
        # Separate control and treatment observations
        control_values = [
            obs.value for obs in observations
            if obs.group == ABTestGroup.CONTROL
        ]
        treatment_values = [
            obs.value for obs in observations
            if obs.group == ABTestGroup.TREATMENT
        ]
        
        if len(control_values) < 2 or len(treatment_values) < 2:
            raise ValueError("Need at least 2 observations per group")
        
        # Calculate basic statistics
        control_mean = statistics.mean(control_values)
        treatment_mean = statistics.mean(treatment_values)
        control_std = statistics.stdev(control_values)
        treatment_std = statistics.stdev(treatment_values)
        
        # Perform t-test
        t_stat, p_value = stats.ttest_ind(treatment_values, control_values)
        
        # Calculate degrees of freedom
        df = len(control_values) + len(treatment_values) - 2
        
        # Determine statistical significance
        statistically_significant = p_value < config.significance_level
        
        # Calculate effect size (Cohen's d)
        n1 = len(control_values)
        n2 = len(treatment_values)
        pooled_std = math.sqrt(
            ((n1 - 1) * control_std ** 2 + (n2 - 1) * treatment_std ** 2) /
            (n1 + n2 - 2)
        )
        effect_size = (treatment_mean - control_mean) / pooled_std if pooled_std > 0 else 0.0
        
        # Calculate confidence intervals
        mean_diff = treatment_mean - control_mean
        control_var = statistics.variance(control_values)
        treatment_var = statistics.variance(treatment_values)
        se = math.sqrt(control_var / n1 + treatment_var / n2)
        
        # 95% CI
        t_95 = stats.t.ppf(0.975, df)
        margin_95 = t_95 * se
        ci_95_lower = mean_diff - margin_95
        ci_95_upper = mean_diff + margin_95
        
        # 99% CI
        t_99 = stats.t.ppf(0.995, df)
        margin_99 = t_99 * se
        ci_99_lower = mean_diff - margin_99
        ci_99_upper = mean_diff + margin_99
        
        # Determine winner
        winner = None
        if statistically_significant:
            if treatment_mean > control_mean:
                winner = ABTestGroup.TREATMENT
            elif control_mean > treatment_mean:
                winner = ABTestGroup.CONTROL
        
        # Calculate improvement percentage
        improvement = ((treatment_mean - control_mean) / control_mean) * 100
        
        result = ABTestResult(
            test_id=test_id,
            control_mean=control_mean,
            treatment_mean=treatment_mean,
            control_std=control_std,
            treatment_std=treatment_std,
            control_size=len(control_values),
            treatment_size=len(treatment_values),
            t_statistic=float(t_stat),
            p_value=float(p_value),
            degrees_of_freedom=df,
            statistically_significant=statistically_significant,
            effect_size=effect_size,
            ci_95_lower=ci_95_lower,
            ci_95_upper=ci_95_upper,
            ci_99_lower=ci_99_lower,
            ci_99_upper=ci_99_upper,
            winner=winner,
            improvement_percentage=improvement
        )
        
        logger.info(
            f"A/B test result: {test_id} - "
            f"winner={winner}, p={p_value:.4f}, "
            f"improvement={improvement:.2f}%"
        )
        
        return result


# Global instance
ab_tester = ABTester()
