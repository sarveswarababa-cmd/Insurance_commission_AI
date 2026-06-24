"""
claude_service.py - Claude AI Integration Layer
Insurance Commission Intelligence Assistant
All AI-powered analysis, explanations, and insights
"""

import anthropic
import json
from database import log_ai_analysis

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1500

# ─────────────────────────────────────────────
# HELPER: call Claude
# ─────────────────────────────────────────────
def _call_claude(system_prompt: str, user_prompt: str, analysis_type: str) -> str:
    """
    Central Claude API call with logging.
    Returns the text response or an error message.
    """
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        result = response.content[0].text
        log_ai_analysis(analysis_type, user_prompt[:500], result[:2000])
        return result
    except anthropic.APIConnectionError:
        return "⚠️ Cannot connect to Claude API. Check your ANTHROPIC_API_KEY."
    except anthropic.RateLimitError:
        return "⚠️ Rate limit hit. Please wait a moment and retry."
    except Exception as e:
        return f"⚠️ AI Error: {str(e)}"


SYSTEM_INSURANCE = """You are a Senior Insurance Commission Analyst with 15+ years of experience 
in General Insurance operations, commission structures, and audit practices in India. 
You understand NIC (National Insurance Company) commission norms, IRDAI guidelines, 
and broker/agent incentive structures. 
Provide responses that are clear, professional, and suitable for business operations teams.
Use ₹ for currency. Format numbers in Indian numbering system (lakhs, crores).
Always structure your response with clear sections using markdown."""


# ─────────────────────────────────────────────
# 1. COMMISSION EXPLANATION
# ─────────────────────────────────────────────
def explain_commission(agent_data: dict, commission_data: list) -> str:
    """
    Generate a plain-language explanation of an agent's commission.
    Input: agent profile + list of commission records.
    """
    comm_text = "\n".join([
        f"  • {c.get('commission_month','N/A')} | {c.get('policy_type','N/A')} "
        f"| Premium: ₹{c.get('premium_amount',0):,.0f} "
        f"| Rate: {c.get('commission_rate',0)}% "
        f"| Commission: ₹{c.get('commission_amount',0):,.0f}"
        for c in commission_data
    ])

    prompt = f"""
An insurance operations executive needs a clear explanation of the following agent's commission:

**AGENT PROFILE**
- Agent ID   : {agent_data.get('agent_id')}
- Agent Name : {agent_data.get('agent_name')}
- Agent Type : {agent_data.get('agent_type')}
- Region     : {agent_data.get('region')}

**COMMISSION RECORDS**
{comm_text}

**TOTAL COMMISSION**: ₹{sum(c.get('commission_amount',0) for c in commission_data):,.0f}

Please provide:
1. A simple explanation of how each commission was calculated
2. Whether the rates applied are appropriate for this agent type
3. Key observations about the commission pattern
4. Any recommendations for the operations team
"""
    return _call_claude(SYSTEM_INSURANCE, prompt, "COMMISSION_EXPLANATION")


# ─────────────────────────────────────────────
# 2. INCENTIVE VALIDATION
# ─────────────────────────────────────────────
def validate_incentive_ai(agent_data: dict, incentives: list, commissions: list) -> str:
    """
    AI-based validation of incentive amounts against performance data.
    """
    base_commission = sum(c.get("commission_amount", 0) for c in commissions)
    inc_text = "\n".join([
        f"  • Scheme: {i.get('scheme_name')} | Achievement: {i.get('achievement_percentage')}% "
        f"| Reward: ₹{i.get('reward_amount',0):,.0f}"
        for i in incentives
    ])

    prompt = f"""
Validate the following incentive payouts for an insurance agent:

**AGENT**: {agent_data.get('agent_name')} ({agent_data.get('agent_id')}) | Type: {agent_data.get('agent_type')}

**BASE COMMISSION EARNED**: ₹{base_commission:,.0f}

**INCENTIVE RECORDS**
{inc_text}

**TOTAL INCENTIVES**: ₹{sum(i.get('reward_amount',0) for i in incentives):,.0f}

Please assess:
1. Are the incentive amounts proportionate to the base commission?
2. Are the achievement percentages realistic for this agent type?
3. Do the scheme names align with standard insurance incentive programs?
4. Flag any incentive that appears over-rewarded or under-rewarded
5. Overall audit verdict: APPROVED / REVIEW NEEDED / ESCALATE
"""
    return _call_claude(SYSTEM_INSURANCE, prompt, "INCENTIVE_VALIDATION")


# ─────────────────────────────────────────────
# 3. AUDIT SUMMARY
# ─────────────────────────────────────────────
def generate_audit_summary(monthly_data: list, anomalies: list) -> str:
    """
    Generate a formal audit summary from monthly payout data and detected anomalies.
    """
    monthly_text = "\n".join([
        f"  • {m.get('commission_month','N/A')}: "
        f"Agents={m.get('agents_count',0)}, "
        f"Policies={m.get('policies_count',0)}, "
        f"Total=₹{m.get('total_commission',0):,.0f}"
        for m in monthly_data
    ])

    anom_text = "\n".join([
        f"  [{a.get('severity','?')}] {a.get('type')} | {a.get('entity')} | {a.get('detail')}"
        for a in anomalies[:10]
    ]) if anomalies else "No anomalies detected"

    prompt = f"""
Generate a formal Audit Summary Report for the Insurance Commission Processing System:

**MONTHLY PAYOUT DATA**
{monthly_text}

**DETECTED ANOMALIES**
{anom_text}

Total Anomalies Found: {len(anomalies)}

Please produce a structured Audit Report with:
1. **Executive Summary** - 3-4 line overview
2. **Key Findings** - Critical observations
3. **Risk Assessment** - HIGH / MEDIUM / LOW issues
4. **Audit Observations** - Numbered list (as per audit standards)
5. **Recommendations** - Actionable next steps
6. **Compliance Status** - IRDAI / internal norms compliance note

Format as a professional audit document suitable for the Finance & Compliance team.
"""
    return _call_claude(SYSTEM_INSURANCE, prompt, "AUDIT_SUMMARY")


# ─────────────────────────────────────────────
# 4. ANOMALY ANALYSIS
# ─────────────────────────────────────────────
def analyze_anomalies_ai(anomalies: list) -> str:
    """
    Deep AI analysis of detected anomalies with root cause and remediation.
    """
    if not anomalies:
        return "✅ **No anomalies detected.** All commission records appear to be within expected parameters."

    anom_json = json.dumps(anomalies, indent=2)

    prompt = f"""
The following anomalies were detected in the Insurance Commission Processing System:

{anom_json}

As a Senior Audit Analyst, please provide:
1. **Root Cause Analysis** for each category of anomaly
2. **Business Impact Assessment** - financial and reputational risk
3. **Priority Matrix** - which to fix first and why
4. **Investigation Checklist** - steps for the audit team
5. **Preventive Controls** - system changes to avoid recurrence
6. **Escalation Recommendation** - which issues need management attention

Be specific and practical. This report will be presented to the Regional Manager and Finance Head.
"""
    return _call_claude(SYSTEM_INSURANCE, prompt, "ANOMALY_ANALYSIS")


# ─────────────────────────────────────────────
# 5. EXECUTIVE SUMMARY
# ─────────────────────────────────────────────
def generate_executive_summary(kpi: dict, top_agents: list, region_data: list, monthly_data: list) -> str:
    """
    Generate an executive-level business intelligence summary.
    """
    agents_text = "\n".join([
        f"  {i+1}. {a.get('agent_name')} ({a.get('agent_id')}) | {a.get('region')} "
        f"| ₹{a.get('grand_total',0):,.0f}"
        for i, a in enumerate(top_agents[:5])
    ])

    region_text = "\n".join([
        f"  • {r.get('region')}: ₹{r.get('total_commission',0):,.0f} across {r.get('agents_count',0)} agents"
        for r in region_data[:4]
    ])

    prompt = f"""
Generate an Executive Summary for the Insurance Commission Management System:

**KEY PERFORMANCE INDICATORS**
- Active Agents        : {kpi.get('active_agents', 0)}
- Total Policies       : {kpi.get('total_policies', 0)}
- Total Commission     : ₹{kpi.get('total_commission', 0):,.0f}
- Total Incentives     : ₹{kpi.get('total_incentives', 0):,.0f}
- Special Rewards      : ₹{kpi.get('special_rewards', 0):,.0f}
- **Grand Total Payout**: ₹{kpi.get('total_payout', 0):,.0f}

**TOP 5 AGENTS BY EARNINGS**
{agents_text}

**REGION-WISE PERFORMANCE**
{region_text}

Please write a compelling Executive Summary with:
1. **Business Performance Overview** - current state of commission operations
2. **Top Performer Highlights** - what's driving their success
3. **Regional Insights** - which regions need attention
4. **Trend Analysis** - based on monthly data patterns
5. **Strategic Recommendations** - for management to act on
6. **Outlook** - forward-looking observations

This will be presented to the MD/CEO. Keep it sharp, data-driven, and actionable.
"""
    return _call_claude(SYSTEM_INSURANCE, prompt, "EXECUTIVE_SUMMARY")


# ─────────────────────────────────────────────
# 6. NATURAL LANGUAGE QUERY
# ─────────────────────────────────────────────
def answer_nl_query(question: str, context_data: dict) -> str:
    """
    Answer any free-form question about commission data.
    """
    prompt = f"""
A business user from the Insurance Commission team has asked the following question:

**QUESTION**: {question}

**AVAILABLE DATA CONTEXT**:
{json.dumps(context_data, indent=2, default=str)[:3000]}

Please answer this question in clear, professional language.
- Refer to specific numbers from the data provided
- If the data is insufficient, say what additional information would be needed
- Keep the response concise but complete (max 300 words)
"""
    return _call_claude(SYSTEM_INSURANCE, prompt, "NL_QUERY")


# ─────────────────────────────────────────────
# 7. CSV UPLOAD ANALYSIS
# ─────────────────────────────────────────────
def analyze_uploaded_data(df_summary: dict) -> str:
    """
    Analyze a freshly uploaded commission CSV file.
    """
    prompt = f"""
A user has uploaded a new commission data file. Here is a summary of the data:

**FILE SUMMARY**
- Rows       : {df_summary.get('rows', 0)}
- Columns    : {', '.join(df_summary.get('columns', []))}
- Data Types : {json.dumps(df_summary.get('dtypes', {}), default=str)}
- Sample     : {json.dumps(df_summary.get('sample', []), default=str)[:1000]}
- Null Count : {json.dumps(df_summary.get('nulls', {}), default=str)}

Please provide:
1. **Data Quality Assessment** - completeness, accuracy, consistency
2. **Quick Observations** - what does this data tell us?
3. **Potential Issues** - missing fields, format problems, obvious outliers
4. **Recommended Actions** - what to validate or investigate further
5. **Data Readiness Score** - 1-10 rating for processing
"""
    return _call_claude(SYSTEM_INSURANCE, prompt, "CSV_ANALYSIS")
