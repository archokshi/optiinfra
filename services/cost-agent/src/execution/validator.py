"""
Execution Validator.

Validates recommendations before execution with safety checks.
"""

import logging
from typing import Dict, Any, List

from src.models.execution_engine import ValidationResult, RiskLevel

logger = logging.getLogger(__name__)


class ExecutionValidator:
    """Validates recommendations before execution."""
    
    def __init__(self):
        """Initialize validator."""
        pass
    
    async def validate_execution(
        self,
        recommendation: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate recommendation for execution.
        
        Args:
            recommendation: Recommendation to validate
        
        Returns:
            ValidationResult with validation details
        """
        errors = []
        warnings = []
        blocking_issues = []
        
        try:
            # Check 1: Verify required fields
            required_fields = ["recommendation_id", "recommendation_type", "resource_id"]
            for field in required_fields:
                if field not in recommendation:
                    errors.append(f"Missing required field: {field}")
                    blocking_issues.append(f"Missing {field}")
            
            if errors:
                return ValidationResult(
                    valid=False,
                    errors=errors,
                    warnings=warnings,
                    risk_level=RiskLevel.HIGH,
                    estimated_duration_minutes=0,
                    requires_approval=True,
                    blocking_issues=blocking_issues
                )
            
            # Check 2: Verify permissions
            has_permission = await self.check_permissions(recommendation)
            if not has_permission:
                errors.append("Insufficient permissions for this operation")
                blocking_issues.append("Permission denied")
            
            # Check 3: Check dependencies
            dependencies = await self.check_dependencies(recommendation)
            if dependencies:
                warnings.append(f"Found {len(dependencies)} dependencies")
                for dep in dependencies:
                    warnings.append(f"  - {dep}")
            
            # Check 4: Verify resource state
            state_valid = await self.check_resource_state(recommendation)
            if not state_valid:
                errors.append("Resource is not in a valid state for this operation")
                blocking_issues.append("Invalid resource state")
            
            # Check 5: Assess risk
            risk_assessment = await self.assess_risk(recommendation)
            risk_level = risk_assessment["risk_level"]
            
            if risk_assessment["warnings"]:
                warnings.extend(risk_assessment["warnings"])
            
            # Determine if approval is required
            requires_approval = (
                risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] or
                recommendation.get("requires_approval", True)
            )
            
            # Estimate duration
            estimated_duration = self._estimate_duration(recommendation)
            
            # Determine if valid
            valid = len(errors) == 0
            
            return ValidationResult(
                valid=valid,
                errors=errors,
                warnings=warnings,
                risk_level=risk_level,
                estimated_duration_minutes=estimated_duration,
                requires_approval=requires_approval,
                blocking_issues=blocking_issues
            )
            
        except Exception as e:
            logger.error(f"Error validating execution: {e}", exc_info=True)
            return ValidationResult(
                valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=[],
                risk_level=RiskLevel.HIGH,
                estimated_duration_minutes=0,
                requires_approval=True,
                blocking_issues=["Validation failed"]
            )
    
    async def check_permissions(
        self,
        recommendation: Dict[str, Any]
    ) -> bool:
        """
        Check if we have permissions to execute.
        
        Args:
            recommendation: Recommendation to check
        
        Returns:
            True if we have permissions
        """
        # In production, would check IAM permissions
        # For now, return True
        rec_type = recommendation.get("recommendation_type", "")
        resource_type = recommendation.get("resource_type", "")
        
        logger.info(f"Checking permissions for {rec_type} on {resource_type}")
        
        # Mock permission check
        return True
    
    async def check_dependencies(
        self,
        recommendation: Dict[str, Any]
    ) -> List[str]:
        """
        Check for blocking dependencies.
        
        Args:
            recommendation: Recommendation to check
        
        Returns:
            List of dependency descriptions
        """
        dependencies = []
        
        resource_id = recommendation.get("resource_id", "")
        rec_type = recommendation.get("recommendation_type", "")
        
        # Mock dependency check
        # In production, would check:
        # - Load balancer attachments
        # - Auto-scaling group membership
        # - Database replicas
        # - Network dependencies
        
        logger.info(f"Checking dependencies for {resource_id}")
        
        return dependencies
    
    async def check_resource_state(
        self,
        recommendation: Dict[str, Any]
    ) -> bool:
        """
        Check if resource is in valid state.
        
        Args:
            recommendation: Recommendation to check
        
        Returns:
            True if resource state is valid
        """
        resource_id = recommendation.get("resource_id", "")
        resource_type = recommendation.get("resource_type", "")
        
        logger.info(f"Checking state for {resource_type} {resource_id}")
        
        # In production, would check actual resource state
        # For now, return True
        return True
    
    async def assess_risk(
        self,
        recommendation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess execution risk.
        
        Args:
            recommendation: Recommendation to assess
        
        Returns:
            Risk assessment dict
        """
        rec_type = recommendation.get("recommendation_type", "")
        resource_type = recommendation.get("resource_type", "")
        
        # Risk levels by recommendation type
        risk_map = {
            "terminate": RiskLevel.HIGH,
            "right_size": RiskLevel.MEDIUM,
            "hibernate": RiskLevel.LOW,
            "spot": RiskLevel.MEDIUM,
            "ri": RiskLevel.LOW,
            "auto_scale": RiskLevel.MEDIUM,
            "storage_optimize": RiskLevel.LOW,
            "config_fix": RiskLevel.LOW
        }
        
        risk_level = risk_map.get(rec_type, RiskLevel.MEDIUM)
        
        warnings = []
        
        # Add warnings based on risk
        if risk_level == RiskLevel.HIGH:
            warnings.append("This operation is irreversible")
            warnings.append("Ensure backups are current")
        elif risk_level == RiskLevel.MEDIUM:
            warnings.append("Brief downtime may occur")
            warnings.append("Monitor application after execution")
        
        # Check for production resources
        if "production" in resource_type.lower() or "prod" in resource_type.lower():
            warnings.append("This is a production resource")
            risk_level = RiskLevel.HIGH
        
        return {
            "risk_level": risk_level,
            "warnings": warnings,
            "factors": [
                f"Recommendation type: {rec_type}",
                f"Resource type: {resource_type}"
            ]
        }
    
    def _estimate_duration(
        self,
        recommendation: Dict[str, Any]
    ) -> int:
        """
        Estimate execution duration in minutes.
        
        Args:
            recommendation: Recommendation to estimate
        
        Returns:
            Estimated duration in minutes
        """
        rec_type = recommendation.get("recommendation_type", "")
        
        # Duration estimates by type
        duration_map = {
            "terminate": 5,
            "right_size": 15,
            "hibernate": 10,
            "spot": 30,
            "ri": 5,
            "auto_scale": 20,
            "storage_optimize": 30,
            "config_fix": 5
        }
        
        return duration_map.get(rec_type, 10)
