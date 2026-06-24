"""
app.py - Insurance Commission Intelligence Assistant
Main Streamlit Application
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json, os, time
from datetime import datetime

# ── Services ──────────────────────────────────────────────────────────
from database import (
    initialize_db, get_all_agents, get_monthly_summary,
    get_region_summary, get_top_agents, get_audit_logs,
    get_ai_analysis_logs, run_query, log_action, load_csv_to_db
)
from commission_service import (
    get_kpi_summary, generate_agent_summary, identify_anomalies,
    validate_commission, generate_region_summary, get_total_payout
)
from claude_service import (
    explain_commission, validate_incentive_ai, generate_audit_summary,
    analyze_anomalies_ai, generate_executive_summary, answer_nl_query,
    analyze_uploaded_data
)
from audit_service import (
    get_commission_audit_report, get_incentive_audit_report,
    get_full_audit_trail, export_audit_report_csv
)
from report_service import export_agent_statement, export_commission_report

# ── Page Config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Insurance Commission AI",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Fonts ── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* ── App background ── */
  .stApp { background: #0d1117; color: #e6edf3; }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
    border-right: 1px solid #21262d;
  }
  [data-testid="stSidebar"] * { color: #c9d1d9 !important; }

  /* ── KPI Cards ── */
  .kpi-card {
    background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px 24px;
    margin: 4px 0;
    position: relative;
    overflow: hidden;
    transition: border-color .2s, transform .1s;
  }
  .kpi-card:hover { border-color: #58a6ff; transform: translateY(-2px); }
  .kpi-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: var(--accent, #58a6ff);
  }
  .kpi-label { font-size: 12px; color: #8b949e; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 8px; }
  .kpi-value { font-size: 28px; font-weight: 700; color: #e6edf3; font-family: 'JetBrains Mono', monospace; }
  .kpi-delta { font-size: 12px; margin-top: 4px; color: #3fb950; }

  /* ── Section headers ── */
  .section-header {
    font-size: 20px; font-weight: 600; color: #e6edf3;
    border-left: 4px solid #58a6ff; padding-left: 12px;
    margin: 24px 0 16px 0;
  }

  /* ── Severity badges ── */
  .badge-critical { background:#da3633;color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600; }
  .badge-high     { background:#d29922;color:#000;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600; }
  .badge-medium   { background:#388bfd;color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600; }
  .badge-low      { background:#238636;color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600; }

  /* ── AI response box ── */
  .ai-response {
    background: #161b22;
    border: 1px solid #30363d;
    border-left: 4px solid #388bfd;
    border-radius: 8px;
    padding: 20px;
    margin-top: 12px;
    font-size: 14px;
    line-height: 1.7;
  }

  /* ── Anomaly card ── */
  .anomaly-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
    margin: 8px 0;
  }

  /* ── Data tables ── */
  .stDataFrame { border: 1px solid #30363d !important; border-radius: 8px !important; }
  [data-testid="stDataFrame"] th { background: #21262d !important; }

  /* ── Buttons ── */
  .stButton > button {
    background: linear-gradient(135deg, #238636, #2ea043) !important;
    color: #fff !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important;
    padding: 10px 20px !important; transition: all .2s !important;
  }
  .stButton > button:hover { opacity: .88 !important; transform: translateY(-1px) !important; }

  /* ── Selectbox / Input ── */
  .stSelectbox > div > div { background: #21262d !important; border-color: #30363d !important; color: #e6edf3 !important; }
  .stTextInput > div > div > input { background: #21262d !important; border-color: #30363d !important; color: #e6edf3 !important; }
  .stTextArea > div > div > textarea { background: #21262d !important; border-color: #30363d !important; color: #e6edf3 !important; }

  /* ── Tabs ── */
  [data-testid="stTabs"] button { color: #8b949e !important; }
  [data-testid="stTabs"] button[aria-selected="true"] { color: #58a6ff !important; border-bottom-color: #58a6ff !important; }

  /* ── Metric delta ── */
  [data-testid="stMetricDelta"] { color: #3fb950 !important; }

  /* ── Toast / info ── */
  .stAlert { border-radius: 8px !important; }

  /* ── Logo strip ── */
  .logo-strip {
    background: linear-gradient(90deg,#238636,#388bfd);
    padding: 3px; border-radius: 8px; margin-bottom: 20px; text-align:center;
  }
  .logo-text { background:#0d1117; padding:12px 20px; border-radius:6px; display:block; }
  .logo-title { font-size:20px; font-weight:700; color:#e6edf3; }
  .logo-sub   { font-size:11px; color:#8b949e; margin-top:2px; }

  /* ── Spinner override ── */
  [data-testid="stSpinner"] { color: #58a6ff !important; }
</style>
""", unsafe_allow_html=True)


# ── Init ──────────────────────────────────────────────────────────────
@st.cache_resource
def init():
    initialize_db()
    return True

init()

# ── Helper: format rupees ──────────────────────────────────────────────
def fmt_inr(amount: float) -> str:
    if amount >= 10_000_000:
        return f"₹{amount/10_000_000:.2f}Cr"
    elif amount >= 100_000:
        return f"₹{amount/100_000:.2f}L"
    elif amount >= 1000:
        return f"₹{amount/1000:.1f}K"
    return f"₹{amount:,.0f}"


def kpi_card(label: str, value: str, delta: str = "", accent: str = "#58a6ff") -> str:
    return f"""
<div class="kpi-card" style="--accent:{accent}">
  <div class="kpi-label">{label}</div>
  <div class="kpi-value">{value}</div>
  {"<div class='kpi-delta'>"+delta+"</div>" if delta else ""}
</div>"""


def severity_badge(sev: str) -> str:
    cls = {"CRITICAL": "badge-critical", "HIGH": "badge-high",
           "MEDIUM": "badge-medium", "LOW": "badge-low"}.get(sev, "badge-low")
    return f'<span class="{cls}">{sev}</span>'


# ── Sidebar Navigation ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="logo-strip">
      <span class="logo-text">
        <div class="logo-title">🏛️ Commission AI</div>
        <div class="logo-sub">Insurance Intelligence Assistant</div>
      </span>
    </div>""", unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "🔍 Agent Search", "📋 Commission Analyzer",
         "🔎 Audit Assistant", "🤖 AI Insights", "📁 Reports", "⚙️ Admin"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    agents_df = get_all_agents()
    st.markdown(f"""
    <div style='background:#21262d;border-radius:8px;padding:12px;font-size:12px;'>
      <b>System Status</b><br>
      🟢 DB Connected &nbsp;|&nbsp; {len(agents_df)} Agents<br>
      🔵 Claude API Ready<br>
      🕐 {datetime.now().strftime('%H:%M · %d %b %Y')}
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# PAGE 1: DASHBOARD
# ══════════════════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.markdown("## 📊 Commission Operations Dashboard")
    st.markdown("*Real-time overview of insurance commission payouts, agent performance, and regional trends*")
    st.markdown("---")

    kpi = get_kpi_summary()

    # KPI Row 1
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_card("Active Agents", str(kpi.get("active_agents", 0)), "↑ All regions", "#238636"), unsafe_allow_html=True)
    c2.markdown(kpi_card("Total Policies", str(kpi.get("total_policies", 0)), "YTD 2024", "#388bfd"), unsafe_allow_html=True)
    c3.markdown(kpi_card("Total Commission", fmt_inr(kpi.get("total_commission", 0)), "Commission earned", "#d29922"), unsafe_allow_html=True)
    c4.markdown(kpi_card("Total Payout", fmt_inr(kpi.get("total_payout", 0)), "Incl. incentives & rewards", "#da3633"), unsafe_allow_html=True)

    st.markdown("")

    # KPI Row 2
    c5, c6, c7, c8 = st.columns(4)
    c5.markdown(kpi_card("Incentives Paid", fmt_inr(kpi.get("total_incentives", 0)), "All schemes", "#58a6ff"), unsafe_allow_html=True)
    c6.markdown(kpi_card("Special Rewards", fmt_inr(kpi.get("special_rewards", 0)), "Chairman/MD awards", "#e6a723"), unsafe_allow_html=True)
    incentive_pct = round(kpi.get("total_incentives", 0) / max(kpi.get("total_commission", 1), 1) * 100, 1)
    c7.markdown(kpi_card("Incentive %", f"{incentive_pct}%", "of total commission", "#388bfd"), unsafe_allow_html=True)
    avg_per_agent = round(kpi.get("total_commission", 0) / max(kpi.get("active_agents", 1), 1))
    c8.markdown(kpi_card("Avg / Agent", fmt_inr(avg_per_agent), "Commission average", "#3fb950"), unsafe_allow_html=True)

    st.markdown("<div class='section-header'>📈 Monthly Commission Trend</div>", unsafe_allow_html=True)

    monthly_df = get_monthly_summary()
    if not monthly_df.empty:
        fig_trend = px.area(
            monthly_df, x="commission_month", y="total_commission",
            labels={"commission_month": "Month", "total_commission": "Commission (₹)"},
            color_discrete_sequence=["#388bfd"],
            template="plotly_dark",
        )
        fig_trend.update_layout(
            plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
            font_color="#c9d1d9", height=300,
            margin=dict(l=20, r=20, t=20, b=40),
            xaxis=dict(showgrid=False, linecolor="#30363d"),
            yaxis=dict(showgrid=True, gridcolor="#21262d", linecolor="#30363d"),
        )
        fig_trend.update_traces(fill="tozeroy", line_color="#58a6ff", fillcolor="rgba(56,139,253,0.15)")
        st.plotly_chart(fig_trend, use_container_width=True)

    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.markdown("<div class='section-header'>🏆 Top Agents</div>", unsafe_allow_html=True)
        top_agents_df = get_top_agents(8)
        if not top_agents_df.empty:
            fig_agents = px.bar(
                top_agents_df.head(8), x="agent_name", y="grand_total",
                color="region", template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.G10,
                labels={"agent_name": "", "grand_total": "Total Payout (₹)", "region": "Region"},
            )
            fig_agents.update_layout(
                plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
                font_color="#c9d1d9", height=320,
                margin=dict(l=10, r=10, t=20, b=60),
                xaxis=dict(showgrid=False, tickangle=-30),
                yaxis=dict(showgrid=True, gridcolor="#21262d"),
                legend=dict(orientation="h", yanchor="bottom", y=1),
            )
            st.plotly_chart(fig_agents, use_container_width=True)

    with col_r:
        st.markdown("<div class='section-header'>🌍 Region Performance</div>", unsafe_allow_html=True)
        region_df = get_region_summary()
        if not region_df.empty:
            # Aggregate by region
            agg = region_df.groupby("region").agg(
                total_commission=("total_commission", "sum"),
                agents=("agents", "sum")
            ).reset_index()
            fig_pie = px.pie(
                agg, names="region", values="total_commission",
                color_discrete_sequence=["#388bfd", "#3fb950", "#d29922", "#da3633"],
                template="plotly_dark", hole=0.5,
            )
            fig_pie.update_layout(
                paper_bgcolor="#0d1117", font_color="#c9d1d9",
                height=320, margin=dict(l=10, r=10, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            )
            fig_pie.update_traces(textposition="outside", textinfo="label+percent")
            st.plotly_chart(fig_pie, use_container_width=True)

    # Agent type breakdown
    st.markdown("<div class='section-header'>👥 Agent Type Distribution</div>", unsafe_allow_html=True)
    type_sql = """
        SELECT a.agent_type, COUNT(DISTINCT a.agent_id) agents,
               ROUND(SUM(c.commission_amount),2) total_commission
        FROM AGENTS a JOIN COMMISSIONS c ON a.agent_id=c.agent_id
        GROUP BY a.agent_type ORDER BY total_commission DESC
    """
    type_df = run_query(type_sql)
    if not type_df.empty:
        tc1, tc2, tc3, tc4 = st.columns(len(type_df))
        colors = ["#388bfd", "#3fb950", "#d29922", "#da3633"]
        for i, (_, row) in enumerate(type_df.iterrows()):
            col = [tc1, tc2, tc3, tc4][i % 4]
            col.markdown(kpi_card(
                f"{row['agent_type']} ({int(row['agents'])})",
                fmt_inr(row["total_commission"]),
                accent=colors[i % len(colors)]
            ), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# PAGE 2: AGENT SEARCH
# ══════════════════════════════════════════════════════════════════════
elif page == "🔍 Agent Search":
    st.markdown("## 🔍 Agent Search & Profile")
    st.markdown("*Search any agent to view their complete commission, incentive, and reward history*")
    st.markdown("---")

    agents_df = get_all_agents()
    agent_options = {
        f"{row['agent_id']} – {row['agent_name']} ({row['agent_type']}, {row['region']})": row["agent_id"]
        for _, row in agents_df.iterrows()
    }

    col_search, col_btn = st.columns([3, 1])
    with col_search:
        selected_label = st.selectbox("Select Agent", list(agent_options.keys()))
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        search_clicked = st.button("🔍 Load Profile", use_container_width=True)

    if selected_label:
        agent_id = agent_options[selected_label]
        summary = generate_agent_summary(agent_id)

        if "error" in summary:
            st.error(summary["error"])
        else:
            agent = summary["agent_info"]
            payout = summary["payout_summary"]

            # Agent header card
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,#161b22,#1c2128);
                        border:1px solid #30363d;border-radius:12px;padding:24px;margin:16px 0;'>
              <div style='display:flex;align-items:center;gap:16px;'>
                <div style='width:56px;height:56px;background:linear-gradient(135deg,#238636,#388bfd);
                            border-radius:50%;display:flex;align-items:center;justify-content:center;
                            font-size:24px;font-weight:700;color:#fff;'>
                  {agent.get('agent_name','?')[0]}
                </div>
                <div>
                  <div style='font-size:22px;font-weight:700;color:#e6edf3;'>{agent.get('agent_name')}</div>
                  <div style='font-size:13px;color:#8b949e;margin-top:2px;'>
                    {agent.get('agent_id')} &nbsp;·&nbsp; {agent.get('agent_type')} &nbsp;·&nbsp;
                    {agent.get('region')} Region &nbsp;·&nbsp; Joined: {agent.get('joining_date')}
                  </div>
                </div>
                <div style='margin-left:auto;'>
                  <span style='background:#238636;color:#fff;padding:6px 14px;border-radius:20px;font-size:13px;font-weight:600;'>
                    {agent.get('status','Active')}
                  </span>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

            # Payout KPIs
            pc1, pc2, pc3, pc4 = st.columns(4)
            pc1.markdown(kpi_card("Commission", fmt_inr(payout["commission"]), accent="#388bfd"), unsafe_allow_html=True)
            pc2.markdown(kpi_card("Incentives", fmt_inr(payout["incentives"]), accent="#3fb950"), unsafe_allow_html=True)
            pc3.markdown(kpi_card("Special Rewards", fmt_inr(payout["special_rewards"]), accent="#d29922"), unsafe_allow_html=True)
            pc4.markdown(kpi_card("Grand Total", fmt_inr(payout["grand_total"]), accent="#da3633"), unsafe_allow_html=True)

            # Tabs for detail
            tab1, tab2, tab3, tab4 = st.tabs(
                ["💼 Commissions", "🎯 Incentives", "🏆 Special Rewards", "📈 Monthly Trend"]
            )

            with tab1:
                comm_df = pd.DataFrame(summary["commissions"])
                if not comm_df.empty:
                    st.markdown(f"**{len(comm_df)} commission records**")
                    st.dataframe(
                        comm_df.rename(columns={
                            "commission_month": "Month", "policy_number": "Policy",
                            "policy_type": "Type", "premium_amount": "Premium (₹)",
                            "commission_rate": "Rate %", "commission_amount": "Commission (₹)"
                        }),
                        use_container_width=True, hide_index=True,
                        column_config={
                            "Premium (₹)": st.column_config.NumberColumn(format="₹%.0f"),
                            "Commission (₹)": st.column_config.NumberColumn(format="₹%.0f"),
                        }
                    )
                else:
                    st.info("No commission records found.")

            with tab2:
                inc_df = pd.DataFrame(summary["incentives"])
                if not inc_df.empty:
                    st.dataframe(
                        inc_df[["incentive_id", "scheme_name", "achievement_percentage", "reward_amount", "incentive_month"]].rename(
                            columns={"scheme_name": "Scheme", "achievement_percentage": "Achievement %",
                                     "reward_amount": "Reward (₹)", "incentive_month": "Month"}
                        ),
                        use_container_width=True, hide_index=True,
                        column_config={"Reward (₹)": st.column_config.NumberColumn(format="₹%.0f")}
                    )
                else:
                    st.info("No incentive records found.")

            with tab3:
                rwd_df = pd.DataFrame(summary["special_rewards"])
                if not rwd_df.empty:
                    st.dataframe(
                        rwd_df[["reward_id", "reward_type", "reward_amount", "reward_date"]].rename(
                            columns={"reward_type": "Award Type", "reward_amount": "Amount (₹)", "reward_date": "Date"}
                        ),
                        use_container_width=True, hide_index=True,
                        column_config={"Amount (₹)": st.column_config.NumberColumn(format="₹%.0f")}
                    )
                else:
                    st.info("No special rewards found.")

            with tab4:
                trend = summary.get("monthly_trend", {})
                if trend:
                    trend_df = pd.DataFrame(
                        [{"Month": k, "Commission": v} for k, v in sorted(trend.items())]
                    )
                    fig_t = px.bar(trend_df, x="Month", y="Commission",
                                   template="plotly_dark", color_discrete_sequence=["#388bfd"],
                                   text="Commission")
                    fig_t.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
                    fig_t.update_layout(
                        plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
                        font_color="#c9d1d9", height=300, margin=dict(l=10, r=10, t=20, b=40),
                    )
                    st.plotly_chart(fig_t, use_container_width=True)

            # Export button
            st.markdown("---")
            if st.button("📥 Export Agent Statement (Excel)"):
                path = export_agent_statement(summary)
                st.success(f"✅ Exported to `{path}`")


# ══════════════════════════════════════════════════════════════════════
# PAGE 3: COMMISSION ANALYZER
# ══════════════════════════════════════════════════════════════════════
elif page == "📋 Commission Analyzer":
    st.markdown("## 📋 Commission Analyzer")
    st.markdown("*Validate commission calculations, detect rate mismatches, and upload new commission data*")
    st.markdown("---")

    tab_validate, tab_upload, tab_register = st.tabs(
        ["✅ Validate Commission", "📤 Upload Data", "📄 Commission Register"]
    )

    with tab_validate:
        st.markdown("<div class='section-header'>Commission Validation Engine</div>", unsafe_allow_html=True)
        st.markdown("*Validates commission amounts against standard rate tables — equivalent to Oracle `PKG_COMMISSION.VALIDATE_COMMISSION`*")

        comm_ids_df = run_query("SELECT commission_id FROM COMMISSIONS ORDER BY commission_id")
        if not comm_ids_df.empty:
            selected_comm = st.selectbox("Select Commission ID to Validate", comm_ids_df["commission_id"].tolist())

            if st.button("🔎 Run Validation"):
                result = validate_commission(selected_comm)
                if result.get("valid"):
                    st.success("✅ Commission is VALID — amounts and rates are correct")
                else:
                    st.error("🚨 Validation FAILED — issues detected")

                vc1, vc2 = st.columns(2)
                with vc1:
                    st.markdown("**Expected Values**")
                    st.markdown(f"- Rate: **{result.get('expected_rate')}%**")
                    st.markdown(f"- Amount: **₹{result.get('expected_amount', 0):,.0f}**")
                with vc2:
                    st.markdown("**Actual Values**")
                    st.markdown(f"- Rate: **{result.get('actual_rate')}%**")
                    st.markdown(f"- Amount: **₹{result.get('actual_amount', 0):,.0f}**")

                if result.get("issues"):
                    st.markdown("**Issues Found:**")
                    for issue in result["issues"]:
                        st.warning(f"⚠️ {issue}")

        # Bulk validation
        st.markdown("---")
        st.markdown("**Bulk Validation — All Commissions**")
        if st.button("🔄 Run Full Validation Sweep"):
            all_ids = run_query("SELECT commission_id FROM COMMISSIONS")["commission_id"].tolist()
            results = []
            prog = st.progress(0, text="Validating...")
            for i, cid in enumerate(all_ids):
                r = validate_commission(cid)
                results.append({
                    "Commission ID": cid,
                    "Valid": "✅" if r["valid"] else "🚨",
                    "Expected Rate": r.get("expected_rate"),
                    "Actual Rate": r.get("actual_rate"),
                    "Expected Amt": r.get("expected_amount", 0),
                    "Actual Amt": r.get("actual_amount", 0),
                    "Issues": "; ".join(r.get("issues", [])) or "—"
                })
                prog.progress((i + 1) / len(all_ids), text=f"Validating {cid}...")

            prog.empty()
            results_df = pd.DataFrame(results)
            ok = len(results_df[results_df["Valid"] == "✅"])
            fail = len(results_df[results_df["Valid"] == "🚨"])
            st.markdown(f"**Results: {ok} ✅ Valid &nbsp;|&nbsp; {fail} 🚨 Issues**")
            st.dataframe(results_df, use_container_width=True, hide_index=True)

    with tab_upload:
        st.markdown("<div class='section-header'>Upload Commission Data</div>", unsafe_allow_html=True)
        st.markdown("""
        Upload a CSV file with commission data. The system will:
        1. Validate the file structure
        2. Store data in the database
        3. Run anomaly detection
        4. Generate AI analysis
        """)

        uploaded_file = st.file_uploader("Choose CSV File", type=["csv", "xlsx"])

        if uploaded_file:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                st.markdown(f"**File:** `{uploaded_file.name}` | **Rows:** {len(df)} | **Columns:** {len(df.columns)}")
                st.dataframe(df.head(10), use_container_width=True, hide_index=True)

                col_a, col_b = st.columns(2)
                with col_a:
                    table_target = st.selectbox("Load into table", ["COMMISSIONS", "POLICIES", "AGENTS", "INCENTIVES"])
                with col_b:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("📥 Load to Database"):
                        with st.spinner("Loading data..."):
                            load_csv_to_db(df, table_target)
                        st.success(f"✅ {len(df)} rows loaded into `{table_target}`")

                st.markdown("---")
                if st.button("🤖 AI Analysis of This File"):
                    df_summary = {
                        "rows": len(df),
                        "columns": list(df.columns),
                        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
                        "nulls": df.isnull().sum().to_dict(),
                        "sample": df.head(3).to_dict("records"),
                    }
                    with st.spinner("🤖 Claude is analyzing your data..."):
                        analysis = analyze_uploaded_data(df_summary)
                    st.markdown(f'<div class="ai-response">{analysis}</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

    with tab_register:
        st.markdown("<div class='section-header'>Commission Register</div>", unsafe_allow_html=True)
        reg_sql = """
            SELECT a.agent_id, a.agent_name, a.agent_type, a.region,
                   p.policy_number, p.policy_type,
                   ROUND(p.premium_amount,0) premium,
                   c.commission_rate rate_pct,
                   ROUND(c.commission_amount,0) commission,
                   c.commission_month month
            FROM COMMISSIONS c
            JOIN AGENTS a ON c.agent_id=a.agent_id
            JOIN POLICIES p ON c.policy_id=p.policy_id
            ORDER BY c.commission_month DESC
        """
        reg_df = run_query(reg_sql)

        # Filter controls
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            months = ["All"] + sorted(reg_df["month"].unique().tolist(), reverse=True)
            selected_month = st.selectbox("Filter by Month", months)
        with fc2:
            regions = ["All"] + sorted(reg_df["region"].unique().tolist())
            selected_region = st.selectbox("Filter by Region", regions)
        with fc3:
            types = ["All"] + sorted(reg_df["agent_type"].unique().tolist())
            selected_type = st.selectbox("Filter by Type", types)

        filtered = reg_df.copy()
        if selected_month != "All":
            filtered = filtered[filtered["month"] == selected_month]
        if selected_region != "All":
            filtered = filtered[filtered["region"] == selected_region]
        if selected_type != "All":
            filtered = filtered[filtered["agent_type"] == selected_type]

        st.markdown(f"**{len(filtered)} records** | Total: ₹{filtered['commission'].sum():,.0f}")
        st.dataframe(filtered, use_container_width=True, hide_index=True,
                     column_config={
                         "premium": st.column_config.NumberColumn("Premium (₹)", format="₹%.0f"),
                         "commission": st.column_config.NumberColumn("Commission (₹)", format="₹%.0f"),
                     })

        if st.button("📥 Export as CSV"):
            path = export_commission_report()
            st.success(f"✅ Exported to `{path}`")


# ══════════════════════════════════════════════════════════════════════
# PAGE 4: AUDIT ASSISTANT
# ══════════════════════════════════════════════════════════════════════
elif page == "🔎 Audit Assistant":
    st.markdown("## 🔎 Audit Assistant")
    st.markdown("*Automated anomaly detection, audit report generation, and compliance monitoring*")
    st.markdown("---")

    tab_anomaly, tab_report, tab_trail = st.tabs(
        ["🚨 Anomaly Detection", "📋 Audit Reports", "📜 Audit Trail"]
    )

    with tab_anomaly:
        st.markdown("<div class='section-header'>Automated Anomaly Detection</div>", unsafe_allow_html=True)
        st.markdown("*Scans commission data for rate mismatches, payout spikes, missing linkages, and incentive inconsistencies*")

        if st.button("🔍 Run Full Anomaly Scan"):
            with st.spinner("Scanning all commission records..."):
                anomalies = identify_anomalies()
                st.session_state["anomalies"] = anomalies

        if "anomalies" in st.session_state:
            anomalies = st.session_state["anomalies"]

            if not anomalies:
                st.success("✅ No anomalies detected. All records are within expected parameters.")
            else:
                # Summary badges
                sev_counts = {}
                for a in anomalies:
                    s = a.get("severity", "LOW")
                    sev_counts[s] = sev_counts.get(s, 0) + 1

                sc1, sc2, sc3, sc4 = st.columns(4)
                sc1.markdown(kpi_card("Total Anomalies", str(len(anomalies)), accent="#da3633"), unsafe_allow_html=True)
                sc2.markdown(kpi_card("Critical", str(sev_counts.get("CRITICAL", 0)), accent="#da3633"), unsafe_allow_html=True)
                sc3.markdown(kpi_card("High", str(sev_counts.get("HIGH", 0)), accent="#d29922"), unsafe_allow_html=True)
                sc4.markdown(kpi_card("Medium", str(sev_counts.get("MEDIUM", 0)), accent="#388bfd"), unsafe_allow_html=True)

                st.markdown("")
                for a in anomalies:
                    badge = severity_badge(a.get("severity", "LOW"))
                    st.markdown(f"""
                    <div class="anomaly-card">
                      <div style='display:flex;align-items:center;gap:10px;margin-bottom:8px;'>
                        {badge}
                        <span style='font-weight:600;color:#e6edf3;'>{a.get('type')}</span>
                        <span style='margin-left:auto;font-family:monospace;font-size:12px;color:#58a6ff;'>{a.get('entity')}</span>
                      </div>
                      <div style='color:#8b949e;font-size:13px;'>{a.get('detail')}</div>
                      <div style='color:#3fb950;font-size:12px;margin-top:6px;'>→ {a.get('action')}</div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("---")
                if st.button("🤖 AI Root Cause Analysis"):
                    with st.spinner("Claude is analyzing anomalies..."):
                        ai_analysis = analyze_anomalies_ai(anomalies)
                    st.markdown(f'<div class="ai-response">{ai_analysis}</div>', unsafe_allow_html=True)

    with tab_report:
        st.markdown("<div class='section-header'>Commission Audit Report</div>", unsafe_allow_html=True)
        audit_df = get_commission_audit_report()
        if not audit_df.empty:
            ok = len(audit_df[audit_df["status"] == "✅ OK"])
            warn = len(audit_df[audit_df["status"] == "⚠️ Minor"])
            crit = len(audit_df[audit_df["status"] == "🚨 Review"])
            a1, a2, a3 = st.columns(3)
            a1.markdown(kpi_card("✅ Passed", str(ok), accent="#3fb950"), unsafe_allow_html=True)
            a2.markdown(kpi_card("⚠️ Minor Issues", str(warn), accent="#d29922"), unsafe_allow_html=True)
            a3.markdown(kpi_card("🚨 Needs Review", str(crit), accent="#da3633"), unsafe_allow_html=True)
            st.markdown("")
            st.dataframe(
                audit_df[["commission_id", "agent_name", "region", "policy_type",
                           "commission_rate", "commission_amount", "expected_amount", "variance", "status"]],
                use_container_width=True, hide_index=True,
                column_config={
                    "commission_amount": st.column_config.NumberColumn("Actual (₹)", format="₹%.0f"),
                    "expected_amount": st.column_config.NumberColumn("Expected (₹)", format="₹%.0f"),
                    "variance": st.column_config.NumberColumn("Variance (₹)", format="₹%.2f"),
                }
            )

        st.markdown("<div class='section-header'>Incentive Audit Report</div>", unsafe_allow_html=True)
        inc_audit_df = get_incentive_audit_report()
        if not inc_audit_df.empty:
            st.dataframe(
                inc_audit_df[["incentive_id", "agent_name", "scheme_name",
                              "achievement_percentage", "reward_amount",
                              "base_commission", "incentive_pct_of_commission"]],
                use_container_width=True, hide_index=True,
                column_config={
                    "reward_amount": st.column_config.NumberColumn("Reward (₹)", format="₹%.0f"),
                    "base_commission": st.column_config.NumberColumn("Base Commission (₹)", format="₹%.0f"),
                    "incentive_pct_of_commission": st.column_config.NumberColumn("Incentive %", format="%.1f%%"),
                }
            )

        if st.button("📥 Export Audit Report as CSV"):
            path = export_audit_report_csv(audit_df)
            st.success(f"✅ Audit report exported to `{path}`")

        if st.button("🤖 Generate AI Audit Summary"):
            monthly_data = get_monthly_summary().to_dict("records")
            anomalies = identify_anomalies()
            with st.spinner("Claude is drafting the audit summary..."):
                ai_summary = generate_audit_summary(monthly_data, anomalies)
            st.markdown(f'<div class="ai-response">{ai_summary}</div>', unsafe_allow_html=True)

    with tab_trail:
        st.markdown("<div class='section-header'>System Audit Trail</div>", unsafe_allow_html=True)
        days = st.slider("Show last N days", 1, 90, 30)
        trail_df = get_full_audit_trail(days)
        if not trail_df.empty:
            st.markdown(f"**{len(trail_df)} entries** in the last {days} days")
            st.dataframe(trail_df, use_container_width=True, hide_index=True)
        else:
            st.info("No audit entries found for the selected period.")


# ══════════════════════════════════════════════════════════════════════
# PAGE 5: AI INSIGHTS
# ══════════════════════════════════════════════════════════════════════
elif page == "🤖 AI Insights":
    st.markdown("## 🤖 AI Insights — Powered by Claude")
    st.markdown("*Ask anything, get expert AI analysis of your commission data*")
    st.markdown("---")

    tab_explain, tab_incentive, tab_exec, tab_nlq = st.tabs(
        ["💬 Commission Explain", "🎯 Incentive Validate", "📊 Executive Summary", "💡 Ask AI Anything"]
    )

    with tab_explain:
        st.markdown("<div class='section-header'>Commission Explanation Generator</div>", unsafe_allow_html=True)
        st.markdown("*Get a plain-language explanation of any agent's commission — perfect for client disputes and management queries*")

        agents_df = get_all_agents()
        agent_opts = {
            f"{r['agent_id']} – {r['agent_name']}": r["agent_id"]
            for _, r in agents_df.iterrows()
        }
        sel = st.selectbox("Select Agent", list(agent_opts.keys()), key="explain_agent")

        if st.button("🤖 Explain This Commission"):
            agent_id = agent_opts[sel]
            summary = generate_agent_summary(agent_id)
            agent_data = summary["agent_info"]
            comm_data = summary["commissions"]

            if not comm_data:
                st.warning("No commission records found for this agent.")
            else:
                with st.spinner(f"Claude is analyzing {agent_data.get('agent_name')}'s commission..."):
                    explanation = explain_commission(agent_data, comm_data)
                st.markdown(f'<div class="ai-response">{explanation}</div>', unsafe_allow_html=True)

    with tab_incentive:
        st.markdown("<div class='section-header'>Incentive Validation</div>", unsafe_allow_html=True)
        st.markdown("*AI validation of incentive amounts — are the rewards proportionate and justified?*")

        agents_df = get_all_agents()
        agent_opts2 = {
            f"{r['agent_id']} – {r['agent_name']}": r["agent_id"]
            for _, r in agents_df.iterrows()
        }
        sel2 = st.selectbox("Select Agent", list(agent_opts2.keys()), key="incentive_agent")

        if st.button("🎯 Validate Incentives"):
            agent_id = agent_opts2[sel2]
            summary = generate_agent_summary(agent_id)

            if not summary["incentives"]:
                st.info("No incentive records found for this agent.")
            else:
                with st.spinner("Claude is validating incentives..."):
                    validation = validate_incentive_ai(
                        summary["agent_info"],
                        summary["incentives"],
                        summary["commissions"]
                    )
                st.markdown(f'<div class="ai-response">{validation}</div>', unsafe_allow_html=True)

    with tab_exec:
        st.markdown("<div class='section-header'>Executive Summary Generator</div>", unsafe_allow_html=True)
        st.markdown("*Generate a board-ready executive summary with insights, trends, and strategic recommendations*")

        if st.button("📊 Generate Executive Summary"):
            with st.spinner("Claude is preparing the executive summary..."):
                kpi = get_kpi_summary()
                top_agents = get_top_agents(10).to_dict("records")
                region_data = get_region_summary().to_dict("records")
                monthly_data = get_monthly_summary().to_dict("records")
                exec_summary = generate_executive_summary(kpi, top_agents, region_data, monthly_data)

            st.markdown(f'<div class="ai-response">{exec_summary}</div>', unsafe_allow_html=True)

            # Save to log
            from database import log_ai_analysis
            log_ai_analysis("EXEC_SUMMARY", "Executive Summary Request", exec_summary[:1000])

    with tab_nlq:
        st.markdown("<div class='section-header'>Ask AI Anything</div>", unsafe_allow_html=True)
        st.markdown("*Ask any question about your commission data in plain English*")

        st.markdown("**Example questions:**")
        examples = [
            "Which region has the highest commission payout this year?",
            "Why does agent A007 earn more than others?",
            "Are the incentive amounts for brokers justified?",
            "What is the average commission rate for motor policies?",
            "Which agent type generates the most business?",
        ]
        for ex in examples:
            if st.button(f"💬 {ex}", key=ex):
                st.session_state["nl_question"] = ex

        user_q = st.text_area(
            "Your Question",
            value=st.session_state.get("nl_question", ""),
            placeholder="Type your question here...",
            height=80
        )

        if st.button("🤖 Get Answer") and user_q:
            context = {
                "kpi": get_kpi_summary(),
                "top_agents": get_top_agents(5).to_dict("records"),
                "region_summary": get_region_summary().to_dict("records"),
                "monthly_summary": get_monthly_summary().to_dict("records"),
            }
            with st.spinner("Claude is thinking..."):
                answer = answer_nl_query(user_q, context)
            st.markdown(f'<div class="ai-response">{answer}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# PAGE 6: REPORTS
# ══════════════════════════════════════════════════════════════════════
elif page == "📁 Reports":
    st.markdown("## 📁 Reports & Analytics")
    st.markdown("*Generate, export, and analyze commission reports — including Power BI metric reference*")
    st.markdown("---")

    tab_dash, tab_pbi, tab_export = st.tabs(
        ["📊 Analytics", "🔷 Power BI Metrics", "📥 Export Reports"]
    )

    with tab_dash:
        st.markdown("<div class='section-header'>Commission Analytics</div>", unsafe_allow_html=True)

        # Agent type heatmap
        sql_heat = """
            SELECT a.agent_type, p.policy_type, ROUND(SUM(c.commission_amount),0) total
            FROM COMMISSIONS c
            JOIN AGENTS a ON c.agent_id=a.agent_id
            JOIN POLICIES p ON c.policy_id=p.policy_id
            GROUP BY a.agent_type, p.policy_type
        """
        heat_df = run_query(sql_heat)
        if not heat_df.empty:
            heat_pivot = heat_df.pivot_table(index="agent_type", columns="policy_type", values="total", fill_value=0)
            fig_heat = px.imshow(
                heat_pivot, template="plotly_dark",
                color_continuous_scale="Blues",
                labels={"color": "Commission (₹)"},
                title="Commission by Agent Type × Policy Type"
            )
            fig_heat.update_layout(
                paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
                font_color="#c9d1d9", height=350, margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_heat, use_container_width=True)

        # Monthly trend by region
        sql_region_trend = """
            SELECT c.commission_month, a.region, ROUND(SUM(c.commission_amount),0) total
            FROM COMMISSIONS c JOIN AGENTS a ON c.agent_id=a.agent_id
            GROUP BY c.commission_month, a.region ORDER BY c.commission_month
        """
        rt_df = run_query(sql_region_trend)
        if not rt_df.empty:
            fig_rt = px.line(
                rt_df, x="commission_month", y="total", color="region",
                template="plotly_dark", markers=True,
                title="Monthly Commission by Region",
                labels={"commission_month": "Month", "total": "Commission (₹)", "region": "Region"}
            )
            fig_rt.update_layout(
                paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
                font_color="#c9d1d9", height=320, margin=dict(l=20, r=20, t=40, b=40),
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#21262d")
            )
            st.plotly_chart(fig_rt, use_container_width=True)

        # Incentive breakdown
        inc_sql = """
            SELECT i.scheme_name, COUNT(*) agents, ROUND(SUM(i.reward_amount),0) total
            FROM INCENTIVES i GROUP BY i.scheme_name ORDER BY total DESC
        """
        inc_df = run_query(inc_sql)
        if not inc_df.empty:
            fig_inc = px.bar(
                inc_df, x="scheme_name", y="total", color="agents",
                template="plotly_dark", title="Incentive by Scheme",
                color_continuous_scale="Teal",
                labels={"scheme_name": "Scheme", "total": "Total Reward (₹)", "agents": "Agents"}
            )
            fig_inc.update_layout(
                paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
                font_color="#c9d1d9", height=320,
                margin=dict(l=20, r=20, t=40, b=80),
                xaxis=dict(tickangle=-15),
            )
            st.plotly_chart(fig_inc, use_container_width=True)

    with tab_pbi:
        st.markdown("<div class='section-header'>Power BI Dashboard Reference</div>", unsafe_allow_html=True)
        st.markdown("*Sample DAX measures and metrics for Power BI integration*")

        dax_measures = {
            "Total Commission": """
Total Commission = 
SUMX(
    COMMISSIONS,
    COMMISSIONS[commission_amount]
)""",
            "Total Incentives": """
Total Incentives = 
SUM(INCENTIVES[reward_amount])""",
            "Grand Total Payout": """
Grand Total Payout = 
[Total Commission] + [Total Incentives] + 
COALESCE(SUM(SPECIAL_REWARDS[reward_amount]), 0)""",
            "Commission YOY Growth %": """
Commission YOY % = 
VAR CurrentYear = CALCULATE([Total Commission], YEAR(TODAY()))
VAR PriorYear = CALCULATE([Total Commission], YEAR(TODAY())-1)
RETURN DIVIDE(CurrentYear - PriorYear, PriorYear, 0) * 100""",
            "Avg Commission per Agent": """
Avg Commission Per Agent = 
DIVIDE(
    [Total Commission],
    DISTINCTCOUNT(AGENTS[agent_id]),
    0
)""",
            "Incentive % of Commission": """
Incentive % of Commission = 
DIVIDE([Total Incentives], [Total Commission], 0) * 100""",
            "Top Agent Name": """
Top Agent = 
MAXX(
    TOPN(1, AGENTS, CALCULATE([Grand Total Payout])),
    AGENTS[agent_name]
)""",
        }

        for measure, dax in dax_measures.items():
            with st.expander(f"📐 {measure}"):
                st.code(dax.strip(), language="sql")

        st.markdown("---")
        st.markdown("**Recommended Power BI Visuals**")
        pbi_visuals = [
            ("Card", "Total Commission, Grand Total Payout, Active Agents"),
            ("Clustered Bar", "Top 10 Agents by Grand Total Payout"),
            ("Pie Chart", "Commission split by Region"),
            ("Line Chart", "Monthly Commission Trend (Sparkline)"),
            ("Matrix", "Agent Type × Policy Type × Total Commission"),
            ("Table", "Commission Register with conditional formatting on Variance"),
            ("Gauge", "Achievement % vs Target (Incentive schemes)"),
            ("Map", "Region-wise commission heat map"),
        ]
        for visual, description in pbi_visuals:
            st.markdown(f"- **{visual}**: {description}")

    with tab_export:
        st.markdown("<div class='section-header'>Export Reports</div>", unsafe_allow_html=True)
        e1, e2, e3 = st.columns(3)
        with e1:
            st.markdown("**Commission Register**")
            if st.button("📥 Export Commission CSV"):
                path = export_commission_report()
                st.success(f"✅ `{path}`")
        with e2:
            st.markdown("**Audit Report**")
            if st.button("📥 Export Audit CSV"):
                df = get_commission_audit_report()
                path = export_audit_report_csv(df)
                st.success(f"✅ `{path}`")
        with e3:
            st.markdown("**Agent Summary**")
            agents_df = get_all_agents()
            agent_opts = {f"{r['agent_id']} – {r['agent_name']}": r["agent_id"] for _, r in agents_df.iterrows()}
            sel = st.selectbox("Select Agent", list(agent_opts.keys()), key="export_agent")
            if st.button("📥 Export Agent Excel"):
                summary = generate_agent_summary(agent_opts[sel])
                path = export_agent_statement(summary)
                st.success(f"✅ `{path}`")


# ══════════════════════════════════════════════════════════════════════
# PAGE 7: ADMIN
# ══════════════════════════════════════════════════════════════════════
elif page == "⚙️ Admin":
    st.markdown("## ⚙️ System Administration")
    st.markdown("*Database management, AI analysis history, and system configuration*")
    st.markdown("---")

    tab_db, tab_ai_log, tab_sql, tab_plsql = st.tabs(
        ["🗄️ Database", "🤖 AI Log", "🔧 SQL Console", "📜 PL/SQL Reference"]
    )

    with tab_db:
        st.markdown("<div class='section-header'>Database Overview</div>", unsafe_allow_html=True)
        tables = ["AGENTS", "POLICIES", "COMMISSIONS", "INCENTIVES", "SPECIAL_REWARDS", "AUDIT_LOGS"]
        for tbl in tables:
            try:
                cnt = run_query(f"SELECT COUNT(*) AS cnt FROM {tbl}")["cnt"].iloc[0]
                st.markdown(f"- **{tbl}**: {cnt} rows")
            except Exception:
                st.markdown(f"- **{tbl}**: ⚠️ error")

        st.markdown("---")
        if st.button("🔄 Re-initialize with Sample Data"):
            with st.spinner("Reinitializing..."):
                initialize_db()
            st.success("✅ Database reinitialized with fresh sample data")

    with tab_ai_log:
        st.markdown("<div class='section-header'>AI Analysis History</div>", unsafe_allow_html=True)
        ai_logs = get_ai_analysis_logs(30)
        if not ai_logs.empty:
            st.dataframe(
                ai_logs[["analysis_id", "analysis_type", "created_date", "input_prompt"]].rename(
                    columns={"analysis_type": "Type", "created_date": "Date", "input_prompt": "Input (preview)"}
                ),
                use_container_width=True, hide_index=True
            )

            selected_id = st.number_input("View AI Response (enter analysis_id)", min_value=1, step=1)
            if st.button("View Response"):
                row = ai_logs[ai_logs["analysis_id"] == selected_id]
                if not row.empty:
                    st.markdown(f'<div class="ai-response">{row.iloc[0]["ai_response"]}</div>', unsafe_allow_html=True)
        else:
            st.info("No AI analysis logs yet. Use the AI Insights page to generate analyses.")

    with tab_sql:
        st.markdown("<div class='section-header'>SQL Console</div>", unsafe_allow_html=True)
        st.markdown("*Run raw SQL queries against the commission database (read-only recommended)*")

        default_query = "SELECT a.agent_name, a.region, SUM(c.commission_amount) total\nFROM COMMISSIONS c\nJOIN AGENTS a ON c.agent_id=a.agent_id\nGROUP BY a.agent_name, a.region\nORDER BY total DESC\nLIMIT 10"
        query = st.text_area("SQL Query", value=default_query, height=150, key="sql_console")

        if st.button("▶️ Run Query"):
            try:
                result_df = run_query(query)
                st.success(f"✅ {len(result_df)} rows returned")
                st.dataframe(result_df, use_container_width=True, hide_index=True)
                log_action("SQL_CONSOLE", f"Executed: {query[:100]}")
            except Exception as e:
                st.error(f"❌ SQL Error: {e}")

    with tab_plsql:
        st.markdown("<div class='section-header'>Oracle PL/SQL Reference</div>", unsafe_allow_html=True)
        st.markdown("*Portfolio demonstration — equivalent Oracle PL/SQL package for commission processing*")

        plsql_code = '''-- =====================================================
-- PKG_COMMISSION - Oracle PL/SQL Package Specification
-- Insurance Commission Processing System
-- Author: Senior Oracle PL/SQL Developer
-- =====================================================

CREATE OR REPLACE PACKAGE PKG_COMMISSION AS

    -- Custom exception for invalid commission
    e_invalid_commission EXCEPTION;
    PRAGMA EXCEPTION_INIT(e_invalid_commission, -20001);

    -- Types
    TYPE t_agent_rec IS RECORD (
        agent_id   AGENTS.AGENT_ID%TYPE,
        agent_name AGENTS.AGENT_NAME%TYPE,
        agent_type AGENTS.AGENT_TYPE%TYPE,
        region     AGENTS.REGION%TYPE
    );

    -- Procedures
    PROCEDURE calculate_commission(
        p_policy_id      IN  POLICIES.POLICY_ID%TYPE,
        p_commission_id  OUT COMMISSIONS.COMMISSION_ID%TYPE,
        p_status         OUT VARCHAR2
    );

    PROCEDURE generate_monthly_commission(
        p_month          IN  VARCHAR2,
        p_records_proc   OUT NUMBER
    );

    PROCEDURE validate_commission(
        p_commission_id  IN  COMMISSIONS.COMMISSION_ID%TYPE,
        p_is_valid       OUT BOOLEAN,
        p_issues         OUT VARCHAR2
    );

    PROCEDURE generate_agent_statement(
        p_agent_id       IN  AGENTS.AGENT_ID%TYPE,
        p_month          IN  VARCHAR2,
        p_cursor         OUT SYS_REFCURSOR
    );

    -- Functions
    FUNCTION get_agent_commission(
        p_agent_id  IN AGENTS.AGENT_ID%TYPE,
        p_month     IN VARCHAR2 DEFAULT NULL
    ) RETURN NUMBER;

    FUNCTION get_reward_amount(
        p_base_commission   IN NUMBER,
        p_achievement_pct   IN NUMBER
    ) RETURN NUMBER;

    FUNCTION get_total_payout(
        p_agent_id  IN AGENTS.AGENT_ID%TYPE
    ) RETURN NUMBER;

    FUNCTION get_commission_rate(
        p_policy_type  IN POLICIES.POLICY_TYPE%TYPE,
        p_agent_type   IN AGENTS.AGENT_TYPE%TYPE
    ) RETURN NUMBER;

END PKG_COMMISSION;
/

-- =====================================================
-- PKG_COMMISSION - Package Body
-- =====================================================

CREATE OR REPLACE PACKAGE BODY PKG_COMMISSION AS

    -- ─── FUNCTION: get_commission_rate ───────────────
    FUNCTION get_commission_rate(
        p_policy_type  IN POLICIES.POLICY_TYPE%TYPE,
        p_agent_type   IN AGENTS.AGENT_TYPE%TYPE
    ) RETURN NUMBER IS
        v_rate NUMBER := 10;
    BEGIN
        SELECT NVL(cr.commission_rate, 10)
        INTO   v_rate
        FROM   COMMISSION_RATE_MASTER cr
        WHERE  cr.policy_type = p_policy_type
          AND  cr.agent_type  = p_agent_type
          AND  cr.effective_date <= SYSDATE
          AND  ROWNUM = 1
        ORDER BY cr.effective_date DESC;

        RETURN v_rate;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN 10; -- Default rate
        WHEN OTHERS THEN
            pkg_error_log.log_error(SQLCODE, SQLERRM, 'GET_COMMISSION_RATE');
            RAISE;
    END get_commission_rate;

    -- ─── FUNCTION: get_reward_amount ─────────────────
    FUNCTION get_reward_amount(
        p_base_commission   IN NUMBER,
        p_achievement_pct   IN NUMBER
    ) RETURN NUMBER IS
        v_reward NUMBER := 0;
    BEGIN
        v_reward := CASE
            WHEN p_achievement_pct >= 150 THEN p_base_commission * 0.05
            WHEN p_achievement_pct >= 130 THEN p_base_commission * 0.04
            WHEN p_achievement_pct >= 110 THEN p_base_commission * 0.03
            WHEN p_achievement_pct >= 100 THEN p_base_commission * 0.02
            WHEN p_achievement_pct >= 90  THEN p_base_commission * 0.01
            ELSE 0
        END;
        RETURN ROUND(v_reward, 2);
    END get_reward_amount;

    -- ─── FUNCTION: get_agent_commission ──────────────
    FUNCTION get_agent_commission(
        p_agent_id  IN AGENTS.AGENT_ID%TYPE,
        p_month     IN VARCHAR2 DEFAULT NULL
    ) RETURN NUMBER IS
        v_total NUMBER := 0;
    BEGIN
        SELECT NVL(SUM(c.commission_amount), 0)
        INTO   v_total
        FROM   COMMISSIONS c
        WHERE  c.agent_id = p_agent_id
          AND  (p_month IS NULL OR c.commission_month = p_month);

        RETURN v_total;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN RETURN 0;
    END get_agent_commission;

    -- ─── FUNCTION: get_total_payout ──────────────────
    FUNCTION get_total_payout(
        p_agent_id  IN AGENTS.AGENT_ID%TYPE
    ) RETURN NUMBER IS
        v_commission NUMBER;
        v_incentives NUMBER;
        v_rewards    NUMBER;
    BEGIN
        v_commission := get_agent_commission(p_agent_id);

        SELECT NVL(SUM(reward_amount), 0)
        INTO   v_incentives
        FROM   INCENTIVES
        WHERE  agent_id = p_agent_id;

        SELECT NVL(SUM(reward_amount), 0)
        INTO   v_rewards
        FROM   SPECIAL_REWARDS
        WHERE  agent_id = p_agent_id;

        RETURN ROUND(v_commission + v_incentives + v_rewards, 2);
    END get_total_payout;

    -- ─── PROCEDURE: calculate_commission ─────────────
    PROCEDURE calculate_commission(
        p_policy_id      IN  POLICIES.POLICY_ID%TYPE,
        p_commission_id  OUT COMMISSIONS.COMMISSION_ID%TYPE,
        p_status         OUT VARCHAR2
    ) IS
        v_agent_id    AGENTS.AGENT_ID%TYPE;
        v_agent_type  AGENTS.AGENT_TYPE%TYPE;
        v_pol_type    POLICIES.POLICY_TYPE%TYPE;
        v_premium     POLICIES.PREMIUM_AMOUNT%TYPE;
        v_rate        NUMBER;
        v_comm_amt    NUMBER;
        v_new_id      VARCHAR2(20);
    BEGIN
        -- Fetch policy details
        SELECT p.agent_id, p.policy_type, p.premium_amount,
               a.agent_type
        INTO   v_agent_id, v_pol_type, v_premium, v_agent_type
        FROM   POLICIES p
        JOIN   AGENTS a ON p.agent_id = a.agent_id
        WHERE  p.policy_id = p_policy_id;

        -- Get applicable rate
        v_rate     := get_commission_rate(v_pol_type, v_agent_type);
        v_comm_amt := ROUND(v_premium * v_rate / 100, 2);

        -- Validate
        IF v_comm_amt <= 0 THEN
            RAISE_APPLICATION_ERROR(-20001, 'Invalid commission amount: ' || v_comm_amt);
        END IF;

        -- Generate ID
        SELECT 'C' || LPAD(COMMISSIONS_SEQ.NEXTVAL, 6, '0')
        INTO   v_new_id FROM DUAL;

        -- Insert
        INSERT INTO COMMISSIONS (
            commission_id, policy_id, agent_id,
            commission_amount, commission_rate,
            commission_month
        ) VALUES (
            v_new_id, p_policy_id, v_agent_id,
            v_comm_amt, v_rate,
            TO_CHAR(SYSDATE, 'YYYY-MM')
        );

        p_commission_id := v_new_id;
        p_status        := 'SUCCESS';
        COMMIT;

    EXCEPTION
        WHEN e_invalid_commission THEN
            p_status := 'ERROR: ' || SQLERRM;
            ROLLBACK;
        WHEN NO_DATA_FOUND THEN
            p_status := 'ERROR: Policy or Agent not found';
            ROLLBACK;
        WHEN DUP_VAL_ON_INDEX THEN
            p_status := 'ERROR: Commission already exists for this policy';
            ROLLBACK;
        WHEN OTHERS THEN
            p_status := 'ERROR: ' || SQLERRM;
            ROLLBACK;
            RAISE;
    END calculate_commission;

    -- ─── PROCEDURE: validate_commission ──────────────
    PROCEDURE validate_commission(
        p_commission_id  IN  COMMISSIONS.COMMISSION_ID%TYPE,
        p_is_valid       OUT BOOLEAN,
        p_issues         OUT VARCHAR2
    ) IS
        v_exp_rate   NUMBER;
        v_exp_amt    NUMBER;
        v_act_rate   NUMBER;
        v_act_amt    NUMBER;
        v_pol_type   VARCHAR2(50);
        v_agt_type   VARCHAR2(50);
        v_premium    NUMBER;
        v_issues     VARCHAR2(2000) := '';
    BEGIN
        SELECT c.commission_rate, c.commission_amount,
               p.policy_type, a.agent_type, p.premium_amount
        INTO   v_act_rate, v_act_amt, v_pol_type, v_agt_type, v_premium
        FROM   COMMISSIONS c
        JOIN   POLICIES p ON c.policy_id = p.policy_id
        JOIN   AGENTS a   ON c.agent_id  = a.agent_id
        WHERE  c.commission_id = p_commission_id;

        v_exp_rate := get_commission_rate(v_pol_type, v_agt_type);
        v_exp_amt  := ROUND(v_premium * v_exp_rate / 100, 2);

        IF v_act_rate <> v_exp_rate THEN
            v_issues := v_issues || 'Rate mismatch: expected ' ||
                        v_exp_rate || '%, found ' || v_act_rate || '%. ';
        END IF;

        IF ABS(v_act_amt - v_exp_amt) > 1 THEN
            v_issues := v_issues || 'Amount mismatch: expected ' ||
                        v_exp_amt || ', found ' || v_act_amt || '. ';
        END IF;

        p_is_valid := (LENGTH(TRIM(v_issues)) = 0);
        p_issues   := NVL(v_issues, 'No issues found');

    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            p_is_valid := FALSE;
            p_issues   := 'Commission ID not found';
    END validate_commission;

    -- ─── PROCEDURE: generate_agent_statement ─────────
    PROCEDURE generate_agent_statement(
        p_agent_id  IN  AGENTS.AGENT_ID%TYPE,
        p_month     IN  VARCHAR2,
        p_cursor    OUT SYS_REFCURSOR
    ) IS
    BEGIN
        OPEN p_cursor FOR
            SELECT a.agent_name, a.agent_type, a.region,
                   p.policy_number, p.policy_type,
                   p.premium_amount, c.commission_rate,
                   c.commission_amount, c.commission_month,
                   NVL(i.reward_amount, 0) incentive_amount,
                   NVL(i.scheme_name, 'N/A') scheme_name
            FROM   COMMISSIONS c
            JOIN   AGENTS a   ON c.agent_id   = a.agent_id
            JOIN   POLICIES p ON c.policy_id  = p.policy_id
            LEFT JOIN INCENTIVES i ON i.agent_id = c.agent_id
                                  AND i.incentive_month = p_month
            WHERE  c.agent_id = p_agent_id
              AND  (p_month IS NULL OR c.commission_month = p_month)
            ORDER BY c.commission_month DESC;

        INSERT INTO AUDIT_LOGS(user_action, remarks)
        VALUES ('AGENT_STATEMENT',
                'Statement generated for ' || p_agent_id || ' month ' || p_month);
        COMMIT;
    END generate_agent_statement;

    -- ─── PROCEDURE: generate_monthly_commission ──────
    PROCEDURE generate_monthly_commission(
        p_month         IN  VARCHAR2,
        p_records_proc  OUT NUMBER
    ) IS
        v_count        NUMBER := 0;
        v_comm_id      VARCHAR2(20);
        v_status       VARCHAR2(200);
        CURSOR c_policies IS
            SELECT p.policy_id
            FROM   POLICIES p
            WHERE  TO_CHAR(p.policy_date, 'YYYY-MM') = p_month
              AND  NOT EXISTS (
                SELECT 1 FROM COMMISSIONS c
                WHERE c.policy_id = p.policy_id
                  AND c.commission_month = p_month
              );
    BEGIN
        FOR rec IN c_policies LOOP
            calculate_commission(rec.policy_id, v_comm_id, v_status);
            IF v_status = 'SUCCESS' THEN
                v_count := v_count + 1;
            END IF;
        END LOOP;

        p_records_proc := v_count;
        INSERT INTO AUDIT_LOGS(user_action, remarks)
        VALUES ('MONTHLY_COMMISSION',
                'Generated ' || v_count || ' commissions for ' || p_month);
        COMMIT;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END generate_monthly_commission;

END PKG_COMMISSION;
/'''
        st.code(plsql_code, language="sql")
        st.markdown("""
        > **Portfolio Note**: This PL/SQL package demonstrates production-grade Oracle development including:
        > custom exception types, REF CURSORs, CASE expressions, autonomous transactions,
        > sequence-based ID generation, and structured error handling with ROLLBACK/COMMIT patterns.
        """)
