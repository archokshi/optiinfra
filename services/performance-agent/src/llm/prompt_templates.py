"""Prompt templates for LLM integration."""

# System prompt
PERFORMANCE_EXPERT_SYSTEM_PROMPT = """You are an expert in LLM inference optimization and performance tuning. You specialize in:
- vLLM, TGI, and SGLang optimization
- GPU memory management and KV cache tuning
- Quantization strategies (INT8, INT4, AWQ, GPTQ)
- Batch size and throughput optimization
- Performance bottleneck analysis

Provide clear, actionable insights with specific numbers and recommendations.
Focus on business impact: cost savings, latency improvements, throughput gains.
Always assess risks and provide mitigation strategies.
Use executive-friendly language while maintaining technical accuracy."""


# Performance insight generation
PERFORMANCE_INSIGHT_PROMPT = """Analyze this LLM inference performance data and generate actionable insights.

Instance Details:
- Instance ID: {instance_id}
- Instance Type: {instance_type}

Performance Metrics:
{metrics}

Detected Bottlenecks:
{bottlenecks}

Generate insights focusing on:
1. Root cause analysis of performance issues
2. Business impact (cost per month, latency impact, throughput loss)
3. Quick wins (high impact, low effort, low risk)
4. Strategic optimizations (higher impact, requires planning)
5. Estimated cost savings and performance improvements with specific numbers

Format: 3-5 concise paragraphs, executive-friendly language.
Be specific with percentages, dollar amounts, and resource IDs."""


# Bottleneck explanation
BOTTLENECK_EXPLANATION_PROMPT = """Explain this performance bottleneck in business-friendly language.

Bottleneck Details:
- Type: {bottleneck_type}
- Severity: {severity}
- Metric: {metric_name}
- Current Value: {current_value}
- Threshold: {threshold_value}

Technical Description: {description}

Provide:
1. What this bottleneck means in simple terms
2. Business impact (monthly cost, user experience, reliability)
3. Why it's happening (root cause in plain language)
4. Urgency level and consequences of inaction
5. Estimated monthly cost impact in dollars

Format: Clear, non-technical language suitable for business stakeholders."""


# Optimization recommendation enhancement
OPTIMIZATION_ENHANCEMENT_PROMPT = """Enhance this technical optimization recommendation with business context.

Optimization Details:
- Type: {optimization_type}
- Priority: {priority}
- Technical Description: {description}

Current Configuration:
{current_config}

Proposed Changes:
{config_changes}

Provide:
1. Business impact explanation (monthly cost savings, performance gain %, risk level)
2. Implementation complexity and timeline (hours/days)
3. Risk assessment and mitigation strategies
4. ROI calculation (savings vs. implementation cost)
5. Prerequisites and dependencies
6. Rollback plan

Format: Executive summary style, focus on business value and risk management.
Include specific dollar amounts and percentages."""


# Executive summary
EXECUTIVE_SUMMARY_PROMPT = """Create an executive summary for stakeholders from this performance analysis.

Instance: {instance_id} ({instance_type})

Performance Metrics Summary:
{metrics_summary}

Bottlenecks Detected:
{bottlenecks_summary}

Optimization Recommendations:
{optimizations_summary}

Include:
1. Current state: Key performance indicators and critical issues
2. Business impact: Monthly cost implications and user experience impact
3. Recommended actions: Prioritized list with ROI and timeline
4. Quick wins: Actions for this week (high impact, low risk, low effort)
5. Strategic initiatives: Actions for this quarter (higher impact, requires planning)
6. Expected outcomes: Specific cost savings and performance improvements
7. Risk assessment: What could go wrong and how to mitigate

Format: 5-7 paragraphs, C-suite friendly, focus on business value and ROI.
Use specific numbers for cost savings ($/month) and performance improvements (%)."""


# ROI analysis
ROI_ANALYSIS_PROMPT = """Calculate ROI for this optimization recommendation.

Optimization: {optimization_type}

Current State:
- GPU Type: {gpu_type}
- Monthly Infrastructure Cost: ${monthly_cost}
- Throughput: {throughput} tokens/sec
- Latency (TTFT): {latency}ms

Proposed Changes:
{config_changes}

Expected Improvements:
{expected_improvements}

Calculate and provide:
1. Monthly cost savings (infrastructure + efficiency gains)
2. Performance improvements (throughput increase %, latency reduction %)
3. Implementation cost (engineering hours × $200/hour + testing + deployment)
4. Payback period (months)
5. Annual ROI percentage
6. Risk-adjusted ROI (accounting for 10-20% risk of issues)

Provide specific dollar amounts, percentages, and timelines.
Format: Clear financial analysis suitable for budget discussions."""
