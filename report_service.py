"""
report_service.py - Report Generation Service
Insurance Commission Intelligence Assistant
"""

import pandas as pd
import os
from database import run_query, log_action
from commission_service import get_kpi_summary, generate_region_summary


def ensure_reports_dir():
    os.makedirs("reports", exist_ok=True)


def export_agent_statement(agent_summary: dict) -> str:
    """Export full agent statement as Excel."""
    ensure_reports_dir()
    agent_id = agent_summary.get("agent_info", {}).get("agent_id", "unknown")
    path = f"reports/agent_statement_{agent_id}.xlsx"

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame([agent_summary["agent_info"]]).to_excel(writer, sheet_name="Agent Info", index=False)
        if agent_summary["commissions"]:
            pd.DataFrame(agent_summary["commissions"]).to_excel(writer, sheet_name="Commissions", index=False)
        if agent_summary["incentives"]:
            pd.DataFrame(agent_summary["incentives"]).to_excel(writer, sheet_name="Incentives", index=False)
        if agent_summary["special_rewards"]:
            pd.DataFrame(agent_summary["special_rewards"]).to_excel(writer, sheet_name="Special Rewards", index=False)
        pd.DataFrame([agent_summary["payout_summary"]]).to_excel(writer, sheet_name="Payout Summary", index=False)

    log_action("EXPORT_STATEMENT", f"Agent statement exported: {path}")
    return path


def export_commission_report() -> str:
    """Export full commission register as CSV."""
    ensure_reports_dir()
    sql = """
        SELECT a.agent_id, a.agent_name, a.agent_type, a.region,
               p.policy_number, p.policy_type, p.premium_amount,
               c.commission_rate, c.commission_amount, c.commission_month
        FROM COMMISSIONS c
        JOIN AGENTS a ON c.agent_id = a.agent_id
        JOIN POLICIES p ON c.policy_id = p.policy_id
        ORDER BY c.commission_month, a.agent_name
    """
    df = run_query(sql)
    path = "reports/commission_register.csv"
    df.to_csv(path, index=False)
    log_action("EXPORT_COMMISSION", f"Commission register exported: {path}")
    return path


def get_power_bi_metrics() -> dict:
    """Return metrics dict suitable for Power BI / reporting display."""
    kpi = get_kpi_summary()
    region_df = generate_region_summary()
    monthly_df = run_query("""
        SELECT commission_month, ROUND(SUM(commission_amount),2) AS total
        FROM COMMISSIONS GROUP BY commission_month ORDER BY commission_month
    """)

    return {
        "kpi": kpi,
        "by_region": region_df.to_dict("records") if not region_df.empty else [],
        "monthly_trend": monthly_df.to_dict("records") if not monthly_df.empty else [],
    }
