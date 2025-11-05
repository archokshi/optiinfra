"""
Prompt templates for LLM-powered cost optimization insights.

Centralized prompt management for consistency and maintainability.
"""

from typing import Dict, Any
import json


# System prompts
COST_OPTIMIZATION_SYSTEM_PROMPT = """You are an expert cloud cost optimization consultant with 10+ years of experience in AWS, GCP, and Azure infrastructure optimization.

Your expertise includes:
- Cloud cost analysis and optimization strategies
- Infrastructure right-sizing and resource optimization
- Spot instance migration and reserved instance planning
- Risk assessment and mitigation strategies
- ROI calculation and business case development

Guidelines:
- Be specific with numbers, percentages, and resource IDs
- Provide actionable recommendations with clear next steps
- Assess risks honestly and suggest mitigation strategies
- Use business-friendly language while maintaining technical accuracy
- Focus on ROI and business impact
- Never speculate or make up data - only use provided information
"""


# Insight generation prompt
INSIGHT_GENERATION_PROMPT = """Analyze this cloud infrastructure cost data and generate actionable insights.

Analysis Data:
{analysis_data}

Generate comprehensive insights covering:

1. **Cost Waste Analysis**
   - Identify the biggest sources of waste
   - Quantify the financial impact
   - Explain root causes

2. **Quick Wins** (High impact, low effort, low risk)
   - List immediate optimization opportunities
   - Estimate savings for each
   - Explain why they're low-risk

3. **Strategic Opportunities** (Higher impact, requires planning)
   - Identify longer-term optimizations
   - Assess complexity and risk
   - Provide implementation roadmap

4. **Priority Recommendations**
   - Rank opportunities by ROI
   - Consider risk vs reward
   - Suggest execution order

Format your response in clear, executive-friendly language with specific numbers and resource IDs.
Be concise but comprehensive (3-5 paragraphs).
"""


# Recommendation enhancement prompt
RECOMMENDATION_ENHANCEMENT_PROMPT = """Enhance this technical cost optimization recommendation with business context and implementation guidance.

Technical Recommendation:
{recommendation}

Provide:

1. **Business Impact**
   - Monthly and annual cost savings
   - Performance implications
   - Risk level (LOW/MEDIUM/HIGH)

2. **Implementation Guidance**
   - Step-by-step implementation plan
   - Estimated effort and timeline
   - Required skills/tools
   - Rollback procedure

3. **Risk Assessment**
   - Potential risks and their likelihood
   - Impact if things go wrong
   - Mitigation strategies

4. **Success Criteria**
   - How to measure success
   - Expected outcomes
   - Monitoring requirements

Format as a clear, actionable recommendation that a DevOps engineer can execute.
"""


# Executive summary prompt
EXECUTIVE_SUMMARY_PROMPT = """Create an executive summary for C-suite leadership from this cloud cost optimization analysis.

Analysis Data:
{analysis_data}

Key Insights:
{insights}

Create a compelling executive summary that includes:

1. **Executive Overview** (2-3 sentences)
   - Total optimization opportunity (monthly and annual)
   - Key findings in business terms
   - Recommended action

2. **Financial Impact**
   - Total potential savings (monthly and annual)
   - Quick wins (this week/month)
   - Strategic initiatives (this quarter)
   - ROI and payback period

3. **Recommended Actions**
   - Immediate actions (this week)
   - Short-term initiatives (this month)
   - Long-term strategy (this quarter)

4. **Risk Assessment**
   - Overall risk level
   - Key risks and mitigation
   - Success probability

5. **Next Steps**
   - Specific actions to take
   - Timeline and milestones
   - Resources required

Format for C-suite audience: clear, concise, business-focused, emphasizing ROI and strategic value.
Length: 4-6 paragraphs.
"""


# Query handling prompt
QUERY_HANDLING_PROMPT = """Answer this question about cloud cost optimization based on the provided analysis data.

Question: {query}

Analysis Data:
{analysis_data}

Provide a clear, specific answer that:
- Directly addresses the question
- Uses specific numbers and resource IDs from the data
- Explains the reasoning
- Suggests actionable next steps if relevant

Be concise but comprehensive. If the data doesn't contain enough information to answer, say so clearly.
"""


# Anomaly explanation prompt
ANOMALY_EXPLANATION_PROMPT = """Explain this cost anomaly in business-friendly terms.

Anomaly Details:
{anomaly}

Context:
{context}

Provide:
1. **What Happened** - Clear explanation of the anomaly
2. **Why It Matters** - Business impact and urgency
3. **Root Cause** - Most likely explanation
4. **Recommended Action** - What to do about it
5. **Prevention** - How to avoid in future

Format: Clear, non-technical language suitable for management.
"""


# Risk assessment prompt
RISK_ASSESSMENT_PROMPT = """Assess the risk of this cloud infrastructure change.

Proposed Change:
{change_description}

Current State:
{current_state}

Provide a comprehensive risk assessment:

1. **Risk Level** - LOW / MEDIUM / HIGH / CRITICAL

2. **Potential Risks**
   - List specific risks
   - Assess likelihood (LOW/MEDIUM/HIGH)
   - Assess impact (LOW/MEDIUM/HIGH)

3. **Mitigation Strategies**
   - For each risk, provide mitigation
   - Suggest testing approach
   - Recommend rollback plan

4. **Go/No-Go Recommendation**
   - Clear recommendation
   - Conditions for proceeding
   - Red flags to watch for

Be honest and thorough in risk assessment. Better to be cautious than cause outages.
"""


class PromptTemplate:
    """Helper class for rendering prompt templates."""
    
    @staticmethod
    def render(template: str, **kwargs) -> str:
        """
        Render a prompt template with variables.
        
        Args:
            template: Prompt template string
            **kwargs: Variables to substitute
        
        Returns:
            Rendered prompt
        """
        # Convert complex objects to JSON strings
        for key, value in kwargs.items():
            if isinstance(value, (dict, list)):
                kwargs[key] = json.dumps(value, indent=2)
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")
    
    @staticmethod
    def render_insight_generation(analysis_data: Dict[str, Any]) -> str:
        """Render insight generation prompt."""
        return PromptTemplate.render(
            INSIGHT_GENERATION_PROMPT,
            analysis_data=analysis_data
        )
    
    @staticmethod
    def render_recommendation_enhancement(recommendation: Dict[str, Any]) -> str:
        """Render recommendation enhancement prompt."""
        return PromptTemplate.render(
            RECOMMENDATION_ENHANCEMENT_PROMPT,
            recommendation=recommendation
        )
    
    @staticmethod
    def render_executive_summary(
        analysis_data: Dict[str, Any],
        insights: str
    ) -> str:
        """Render executive summary prompt."""
        return PromptTemplate.render(
            EXECUTIVE_SUMMARY_PROMPT,
            analysis_data=analysis_data,
            insights=insights
        )
    
    @staticmethod
    def render_query_handling(
        query: str,
        analysis_data: Dict[str, Any]
    ) -> str:
        """Render query handling prompt."""
        return PromptTemplate.render(
            QUERY_HANDLING_PROMPT,
            query=query,
            analysis_data=analysis_data
        )
    
    @staticmethod
    def render_anomaly_explanation(
        anomaly: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Render anomaly explanation prompt."""
        return PromptTemplate.render(
            ANOMALY_EXPLANATION_PROMPT,
            anomaly=anomaly,
            context=context
        )
    
    @staticmethod
    def render_risk_assessment(
        change_description: str,
        current_state: Dict[str, Any]
    ) -> str:
        """Render risk assessment prompt."""
        return PromptTemplate.render(
            RISK_ASSESSMENT_PROMPT,
            change_description=change_description,
            current_state=current_state
        )
    
    @staticmethod
    def validate_template(template: str, required_vars: list) -> bool:
        """
        Validate that template contains required variables.
        
        Args:
            template: Template string
            required_vars: List of required variable names
        
        Returns:
            True if all required variables are present
        """
        for var in required_vars:
            if f"{{{var}}}" not in template:
                return False
        return True
