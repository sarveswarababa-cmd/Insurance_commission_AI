"""
audit_service.py - Audit Trail & Compliance Service
Insurance Commission Intelligence Assistant
"""

import pandas as pd
from datetime import datetime
from database import run_query, log_action, get_audit_logs


def get_full_audit_trail(days: int = 30) -> pd.DataFrame:
    sql = f"""
        SELECT audit_id, audit_date, user_action, remarks
        FROM AUDIT_LOGS
        WHERE audit_date >= datetime('now', '-{days} days')
        ORDER BY audit_date DESC
    """
    return run_query(sql)


def get_commission_audit_report() -> pd.DataFrame:
    sql = """
        SELECT
            c.commission_id,
            a.agent_name,
            a.agent_type,
            a.region,
            p.policy_number,
            p.policy_type,
            p.premium_amount,
            c.commission_rate,
            c.commission_amount,
            ROUND(p.premium_amount * c.commission_rate / 100, 2) AS expected_amount,
            ROUND(c.commission_amount - (p.premium_amount * c.commission_rate / 100), 2) AS variance,
            c.commission_month
        FROM COMMISSIONS c
        JOIN AGENTS a ON c.agent_id = a.agent_id
        JOIN POLICIES p ON c.policy_id = p.policy_id
        ORDER BY c.commission_month DESC
    """
    df = run_query(sql)
    if not df.empty:
        df["status"] = df["variance"].apply(
            lambda v: "✅ OK" if abs(v) < 1 else ("⚠️ Minor" if abs(v) < 500 else "🚨 Review")
        )
    log_action("AUDIT_REPORT", "Commission audit report generated")
    return df


def get_incentive_audit_report() -> pd.DataFrame:
    sql = """
        SELECT
            i.incentive_id,
            a.agent_name,
            a.agent_type,
            a.region,
            i.scheme_name,
            i.achievement_percentage,
            i.reward_amount,
            i.incentive_month,
            COALESCE(SUM(c.commission_amount), 0) AS base_commission,
            ROUND(i.reward_amount * 100.0 / NULLIF(SUM(c.commission_amount), 0), 2) AS incentive_pct_of_commission
        FROM INCENTIVES i
        JOIN AGENTS a ON i.agent_id = a.agent_id
        LEFT JOIN COMMISSIONS c ON i.agent_id = c.agent_id
        GROUP BY i.incentive_id, a.agent_name, a.agent_type, a.region,
                 i.scheme_name, i.achievement_percentage, i.reward_amount, i.incentive_month
        ORDER BY i.reward_amount DESC
    """
    return run_query(sql)


def export_audit_report_csv(report_df: pd.DataFrame, filename: str = "audit_report.csv") -> str:
    path = f"reports/{filename}"
    import os
    os.makedirs("reports", exist_ok=True)
    report_df.to_csv(path, index=False)
    log_action("EXPORT", f"Audit report exported to {path}")
    return path
