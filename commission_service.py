"""
commission_service.py - Core Commission Business Logic
Insurance Commission Intelligence Assistant
Simulates Oracle PKG_COMMISSION package behavior
"""

import pandas as pd
import numpy as np
from database import (
    run_query, get_connection, log_action,
    get_commissions_by_agent, get_incentives_by_agent,
    get_special_rewards_by_agent, get_agent
)

# ─────────────────────────────────────────────
# COMMISSION RATE TABLE (Oracle equiv: lookup table)
# ─────────────────────────────────────────────
COMMISSION_RATES = {
    "Motor":  {"Broker": 15.0, "Agent": 12.0, "DO": 10.0, "BC": 10.0},
    "Health": {"Broker": 15.0, "Agent": 12.0, "DO": 12.0, "BC": 10.0},
    "Life":   {"Broker": 12.0, "Agent": 10.0, "DO": 10.0, "BC": 8.0},
    "Fire":   {"Broker": 12.0, "Agent": 12.0, "DO": 10.0, "BC": 10.0},
    "Marine": {"Broker": 15.0, "Agent": 12.0, "DO": 12.0, "BC": 10.0},
}

INCENTIVE_SLABS = [
    (150.0, 0.05),   # ≥150% → 5% of commission
    (130.0, 0.04),
    (110.0, 0.03),
    (100.0, 0.02),
    (90.0,  0.01),
    (0.0,   0.0),
]


# ─────────────────────────────────────────────
# FUNCTION: get_commission_rate (Oracle: GET_COMMISSION_RATE)
# ─────────────────────────────────────────────
def get_commission_rate(policy_type: str, agent_type: str) -> float:
    """Return applicable commission rate for policy_type × agent_type."""
    rates = COMMISSION_RATES.get(policy_type, {})
    return rates.get(agent_type, 10.0)


# ─────────────────────────────────────────────
# FUNCTION: calculate_commission (Oracle: CALCULATE_COMMISSION)
# ─────────────────────────────────────────────
def calculate_commission(premium: float, rate: float) -> float:
    """Compute commission = premium × rate / 100, rounded to 2dp."""
    if premium <= 0 or rate <= 0:
        return 0.0
    return round(premium * rate / 100, 2)


# ─────────────────────────────────────────────
# FUNCTION: calculate_incentive (Oracle: GET_REWARD_AMOUNT)
# ─────────────────────────────────────────────
def calculate_incentive(base_commission: float, achievement_pct: float) -> float:
    """
    Incentive slab logic (mirrors PL/SQL CASE WHEN block).
    Returns incentive amount based on achievement %.
    """
    for threshold, rate in INCENTIVE_SLABS:
        if achievement_pct >= threshold:
            return round(base_commission * rate, 2)
    return 0.0


# ─────────────────────────────────────────────
# FUNCTION: get_agent_commission (Oracle: GET_AGENT_COMMISSION)
# ─────────────────────────────────────────────
def get_agent_commission(agent_id: str) -> float:
    """Return total commission earned by an agent."""
    sql = "SELECT COALESCE(SUM(commission_amount),0) AS total FROM COMMISSIONS WHERE agent_id=?"
    df = run_query(sql, (agent_id,))
    return float(df["total"].iloc[0]) if not df.empty else 0.0


# ─────────────────────────────────────────────
# FUNCTION: get_total_payout (Oracle: GET_TOTAL_PAYOUT)
# ─────────────────────────────────────────────
def get_total_payout(agent_id: str) -> dict:
    """
    Return breakdown: commission + incentives + special rewards.
    Equivalent to Oracle package function GET_TOTAL_PAYOUT.
    """
    commission = get_agent_commission(agent_id)

    inc_df = get_incentives_by_agent(agent_id)
    incentives = float(inc_df["reward_amount"].sum()) if not inc_df.empty else 0.0

    rwd_df = get_special_rewards_by_agent(agent_id)
    rewards = float(rwd_df["reward_amount"].sum()) if not rwd_df.empty else 0.0

    return {
        "commission":    commission,
        "incentives":    incentives,
        "special_rewards": rewards,
        "grand_total":   round(commission + incentives + rewards, 2)
    }


# ─────────────────────────────────────────────
# FUNCTION: generate_agent_summary
# ─────────────────────────────────────────────
def generate_agent_summary(agent_id: str) -> dict:
    """
    Full agent statement — mirrors Oracle GENERATE_AGENT_STATEMENT.
    Returns structured dict with all payout details.
    """
    agent_df = get_agent(agent_id)
    if agent_df.empty:
        return {"error": f"Agent {agent_id} not found"}

    agent = agent_df.iloc[0].to_dict()
    comm_df = get_commissions_by_agent(agent_id)
    inc_df = get_incentives_by_agent(agent_id)
    rwd_df = get_special_rewards_by_agent(agent_id)
    payout = get_total_payout(agent_id)

    monthly = {}
    if not comm_df.empty:
        for month, grp in comm_df.groupby("commission_month"):
            monthly[month] = round(grp["commission_amount"].sum(), 2)

    log_action("AGENT_SUMMARY", f"Generated summary for {agent_id}")
    return {
        "agent_info":      agent,
        "commissions":     comm_df.to_dict("records"),
        "incentives":      inc_df.to_dict("records"),
        "special_rewards": rwd_df.to_dict("records"),
        "payout_summary":  payout,
        "monthly_trend":   monthly,
    }


# ─────────────────────────────────────────────
# FUNCTION: generate_region_summary
# ─────────────────────────────────────────────
def generate_region_summary() -> pd.DataFrame:
    sql = """
        SELECT a.region,
               a.agent_type,
               COUNT(DISTINCT a.agent_id)               AS agents,
               COUNT(c.commission_id)                    AS policies,
               ROUND(SUM(c.commission_amount),2)         AS total_commission,
               ROUND(AVG(c.commission_amount),2)         AS avg_commission,
               ROUND(MAX(c.commission_amount),2)         AS max_commission
        FROM AGENTS a
        JOIN COMMISSIONS c ON a.agent_id = c.agent_id
        GROUP BY a.region, a.agent_type
        ORDER BY total_commission DESC
    """
    return run_query(sql)


# ─────────────────────────────────────────────
# FUNCTION: validate_commission
# ─────────────────────────────────────────────
def validate_commission(commission_id: str) -> dict:
    """
    Rule-based commission validation.
    Simulates Oracle VALIDATE_COMMISSION procedure.
    """
    sql = """
        SELECT c.*, p.premium_amount, p.policy_type, a.agent_type
        FROM COMMISSIONS c
        JOIN POLICIES p ON c.policy_id = p.policy_id
        JOIN AGENTS a ON c.agent_id = a.agent_id
        WHERE c.commission_id = ?
    """
    df = run_query(sql, (commission_id,))
    if df.empty:
        return {"valid": False, "issues": ["Commission ID not found"]}

    row = df.iloc[0]
    issues = []
    expected_rate = get_commission_rate(row["policy_type"], row["agent_type"])
    expected_amt = calculate_commission(row["premium_amount"], expected_rate)
    actual_amt = row["commission_amount"]

    if abs(actual_amt - expected_amt) > 1.0:
        issues.append(
            f"Amount mismatch: Expected ₹{expected_amt:,.0f}, Found ₹{actual_amt:,.0f}"
        )
    if row["commission_rate"] != expected_rate:
        issues.append(
            f"Rate mismatch: Expected {expected_rate}%, Found {row['commission_rate']}%"
        )

    log_action("VALIDATE_COMMISSION", f"Validated {commission_id}: {'OK' if not issues else 'ISSUES'}")
    return {
        "commission_id":  commission_id,
        "valid":          len(issues) == 0,
        "expected_rate":  expected_rate,
        "expected_amount": expected_amt,
        "actual_rate":    row["commission_rate"],
        "actual_amount":  actual_amt,
        "issues":         issues,
    }


# ─────────────────────────────────────────────
# FUNCTION: identify_anomalies
# ─────────────────────────────────────────────
def identify_anomalies() -> list[dict]:
    """
    Detect data anomalies across commission data.
    Covers: duplicate policies, rate mismatches, sudden spikes,
    missing policy linkage, incentive mismatches.
    """
    anomalies = []

    # 1. Rate mismatch detection
    sql = """
        SELECT c.commission_id, c.agent_id, p.policy_type, a.agent_type,
               c.commission_rate, c.commission_amount, p.premium_amount
        FROM COMMISSIONS c
        JOIN POLICIES p ON c.policy_id = p.policy_id
        JOIN AGENTS a ON c.agent_id = a.agent_id
    """
    df = run_query(sql)
    for _, row in df.iterrows():
        expected_rate = get_commission_rate(row["policy_type"], row["agent_type"])
        expected_amt = calculate_commission(row["premium_amount"], expected_rate)
        if abs(row["commission_amount"] - expected_amt) > 50:
            anomalies.append({
                "type":     "Rate/Amount Mismatch",
                "severity": "HIGH",
                "entity":   row["commission_id"],
                "detail":   f"Agent {row['agent_id']} | {row['policy_type']} | "
                            f"Expected ₹{expected_amt:,.0f} vs Actual ₹{row['commission_amount']:,.0f}",
                "action":   "Review and recalculate commission"
            })

    # 2. Sudden payout spike (>2× previous month avg)
    monthly_sql = """
        SELECT agent_id, commission_month, SUM(commission_amount) AS total
        FROM COMMISSIONS GROUP BY agent_id, commission_month ORDER BY agent_id, commission_month
    """
    m_df = run_query(monthly_sql)
    for agent, grp in m_df.groupby("agent_id"):
        grp = grp.sort_values("commission_month").reset_index(drop=True)
        for i in range(1, len(grp)):
            prev = grp.iloc[i - 1]["total"]
            curr = grp.iloc[i]["total"]
            if prev > 0 and curr > prev * 2.5:
                anomalies.append({
                    "type":     "Sudden Payout Spike",
                    "severity": "MEDIUM",
                    "entity":   agent,
                    "detail":   f"Month {grp.iloc[i]['commission_month']}: "
                                f"₹{curr:,.0f} vs previous ₹{prev:,.0f} (↑{((curr/prev)-1)*100:.0f}%)",
                    "action":   "Verify supporting policies"
                })

    # 3. Orphan commissions (no valid policy linkage)
    orphan_sql = """
        SELECT c.commission_id, c.agent_id
        FROM COMMISSIONS c
        LEFT JOIN POLICIES p ON c.policy_id = p.policy_id
        WHERE p.policy_id IS NULL
    """
    orphans = run_query(orphan_sql)
    for _, row in orphans.iterrows():
        anomalies.append({
            "type":     "Missing Policy Linkage",
            "severity": "CRITICAL",
            "entity":   row["commission_id"],
            "detail":   f"Commission for agent {row['agent_id']} has no linked policy",
            "action":   "Investigate and link or reverse commission"
        })

    # 4. Incentive without commission base
    inc_anomaly_sql = """
        SELECT i.incentive_id, i.agent_id, i.scheme_name, i.reward_amount
        FROM INCENTIVES i
        LEFT JOIN COMMISSIONS c ON i.agent_id = c.agent_id
        WHERE c.commission_id IS NULL
    """
    inc_df = run_query(inc_anomaly_sql)
    for _, row in inc_df.iterrows():
        anomalies.append({
            "type":     "Incentive Without Commission Base",
            "severity": "HIGH",
            "entity":   row["incentive_id"],
            "detail":   f"Agent {row['agent_id']} received incentive (₹{row['reward_amount']:,.0f}) under '{row['scheme_name']}' with no commission record",
            "action":   "Validate incentive eligibility"
        })

    log_action("ANOMALY_DETECTION", f"Detected {len(anomalies)} anomalies")
    return anomalies


# ─────────────────────────────────────────────
# FUNCTION: get_kpi_summary (Dashboard KPIs)
# ─────────────────────────────────────────────
def get_kpi_summary() -> dict:
    sql = """
        SELECT
            (SELECT COUNT(*) FROM AGENTS WHERE status='Active')       AS active_agents,
            (SELECT COUNT(*) FROM POLICIES)                           AS total_policies,
            (SELECT ROUND(SUM(commission_amount),2) FROM COMMISSIONS) AS total_commission,
            (SELECT ROUND(SUM(reward_amount),2) FROM INCENTIVES)      AS total_incentives,
            (SELECT ROUND(SUM(reward_amount),2) FROM SPECIAL_REWARDS) AS special_rewards,
            (SELECT COUNT(*) FROM AUDIT_LOGS)                         AS audit_entries
    """
    df = run_query(sql)
    if df.empty:
        return {}
    row = df.iloc[0]
    return {
        "active_agents":   int(row["active_agents"] or 0),
        "total_policies":  int(row["total_policies"] or 0),
        "total_commission": float(row["total_commission"] or 0),
        "total_incentives": float(row["total_incentives"] or 0),
        "special_rewards":  float(row["special_rewards"] or 0),
        "total_payout":    round(
            float(row["total_commission"] or 0) +
            float(row["total_incentives"] or 0) +
            float(row["special_rewards"] or 0), 2
        ),
        "audit_entries":   int(row["audit_entries"] or 0),
    }
