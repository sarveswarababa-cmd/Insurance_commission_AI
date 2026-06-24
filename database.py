"""
database.py - SQLite Database Layer (Oracle PL/SQL Simulation)
Insurance Commission Intelligence Assistant
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os

DB_PATH = "data/commission.db"

# ─────────────────────────────────────────────
# DDL & SEED DATA
# ─────────────────────────────────────────────

DDL_SCRIPTS = """
CREATE TABLE IF NOT EXISTS AGENTS (
    agent_id    TEXT PRIMARY KEY,
    agent_name  TEXT NOT NULL,
    agent_type  TEXT CHECK(agent_type IN ('Broker','Agent','DO','BC')),
    region      TEXT NOT NULL,
    joining_date TEXT,
    status      TEXT DEFAULT 'Active'
);

CREATE TABLE IF NOT EXISTS POLICIES (
    policy_id      TEXT PRIMARY KEY,
    policy_number  TEXT UNIQUE NOT NULL,
    agent_id       TEXT NOT NULL,
    premium_amount REAL NOT NULL,
    policy_date    TEXT NOT NULL,
    policy_type    TEXT NOT NULL,
    FOREIGN KEY(agent_id) REFERENCES AGENTS(agent_id)
);

CREATE TABLE IF NOT EXISTS COMMISSIONS (
    commission_id     TEXT PRIMARY KEY,
    policy_id         TEXT NOT NULL,
    agent_id          TEXT NOT NULL,
    commission_amount REAL NOT NULL,
    commission_rate   REAL NOT NULL,
    commission_month  TEXT NOT NULL,
    FOREIGN KEY(policy_id) REFERENCES POLICIES(policy_id),
    FOREIGN KEY(agent_id)  REFERENCES AGENTS(agent_id)
);

CREATE TABLE IF NOT EXISTS INCENTIVES (
    incentive_id           TEXT PRIMARY KEY,
    agent_id               TEXT NOT NULL,
    scheme_name            TEXT NOT NULL,
    achievement_percentage REAL NOT NULL,
    reward_amount          REAL NOT NULL,
    incentive_month        TEXT,
    FOREIGN KEY(agent_id) REFERENCES AGENTS(agent_id)
);

CREATE TABLE IF NOT EXISTS SPECIAL_REWARDS (
    reward_id     TEXT PRIMARY KEY,
    agent_id      TEXT NOT NULL,
    reward_type   TEXT NOT NULL,
    reward_amount REAL NOT NULL,
    reward_date   TEXT NOT NULL,
    FOREIGN KEY(agent_id) REFERENCES AGENTS(agent_id)
);

CREATE TABLE IF NOT EXISTS AUDIT_LOGS (
    audit_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_date  TEXT DEFAULT (datetime('now','localtime')),
    user_action TEXT NOT NULL,
    remarks     TEXT
);

CREATE TABLE IF NOT EXISTS AI_ANALYSIS_LOG (
    analysis_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_type TEXT NOT NULL,
    input_prompt  TEXT,
    ai_response   TEXT,
    created_date  TEXT DEFAULT (datetime('now','localtime'))
);
"""

SAMPLE_DATA = """
INSERT OR IGNORE INTO AGENTS VALUES
('A001','Ramesh Kumar','Broker','South','2019-04-01','Active'),
('A002','Priya Sharma','Agent','North','2020-07-15','Active'),
('A003','Suresh Nair','DO','West','2018-01-10','Active'),
('A004','Meena Patel','BC','East','2021-03-22','Active'),
('A005','Arjun Singh','Broker','South','2017-09-05','Active'),
('A006','Divya Menon','Agent','North','2022-01-01','Active'),
('A007','Karthik Rao','Broker','West','2016-06-20','Active'),
('A008','Anitha Das','DO','East','2020-11-12','Active'),
('A009','Vijay Verma','BC','South','2019-08-30','Active'),
('A010','Lakshmi Iyer','Broker','North','2015-03-14','Active');

INSERT OR IGNORE INTO POLICIES VALUES
('P001','POL/2024/001','A001',150000,'2024-01-15','Motor'),
('P002','POL/2024/002','A001',200000,'2024-01-20','Health'),
('P003','POL/2024/003','A002',120000,'2024-01-25','Life'),
('P004','POL/2024/004','A003',300000,'2024-02-01','Fire'),
('P005','POL/2024/005','A004',180000,'2024-02-10','Motor'),
('P006','POL/2024/006','A005',250000,'2024-02-15','Health'),
('P007','POL/2024/007','A006',90000,'2024-03-01','Life'),
('P008','POL/2024/008','A007',400000,'2024-03-10','Marine'),
('P009','POL/2024/009','A008',160000,'2024-03-20','Fire'),
('P010','POL/2024/010','A009',220000,'2024-04-01','Motor'),
('P011','POL/2024/011','A010',350000,'2024-04-05','Health'),
('P012','POL/2024/012','A001',130000,'2024-04-10','Life'),
('P013','POL/2024/013','A002',275000,'2024-05-01','Motor'),
('P014','POL/2024/014','A005',190000,'2024-05-15','Fire'),
('P015','POL/2024/015','A007',450000,'2024-06-01','Marine');

INSERT OR IGNORE INTO COMMISSIONS VALUES
('C001','P001','A001',22500,15.0,'2024-01'),
('C002','P002','A001',30000,15.0,'2024-01'),
('C003','P003','A002',14400,12.0,'2024-01'),
('C004','P004','A003',36000,12.0,'2024-02'),
('C005','P005','A004',21600,12.0,'2024-02'),
('C006','P006','A005',37500,15.0,'2024-02'),
('C007','P007','A006',9000,10.0,'2024-03'),
('C008','P008','A007',60000,15.0,'2024-03'),
('C009','P009','A008',19200,12.0,'2024-03'),
('C010','P010','A009',26400,12.0,'2024-04'),
('C011','P011','A010',52500,15.0,'2024-04'),
('C012','P012','A001',15600,12.0,'2024-04'),
('C013','P013','A002',41250,15.0,'2024-05'),
('C014','P014','A005',22800,12.0,'2024-05'),
('C015','P015','A007',67500,15.0,'2024-06');

INSERT OR IGNORE INTO INCENTIVES VALUES
('I001','A001','Star Performer Q1',110.5,15000,'2024-01'),
('I002','A002','Growth Achiever',95.0,8000,'2024-01'),
('I003','A003','DO Excellence',120.0,25000,'2024-02'),
('I004','A005','Top Broker Award',135.0,35000,'2024-02'),
('I005','A007','Marine Specialist',118.5,20000,'2024-03'),
('I006','A010','Premium Club',142.0,40000,'2024-04'),
('I007','A001','Retention Bonus',105.0,12000,'2024-04'),
('I008','A004','New Business Drive',88.5,5000,'2024-05');

INSERT OR IGNORE INTO SPECIAL_REWARDS VALUES
('R001','A001','Annual Convention Trip',50000,'2024-03-31'),
('R002','A003','Long Service Award',30000,'2024-01-15'),
('R003','A005','Chairman Award',75000,'2024-06-01'),
('R004','A007','Marine Excellence Trophy',45000,'2024-04-20'),
('R005','A010','MD Award',80000,'2024-05-10');
"""


# ─────────────────────────────────────────────
# DATABASE CONNECTION
# ─────────────────────────────────────────────

def get_connection():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_db():
    """Initialize database with DDL and sample data."""
    conn = get_connection()
    try:
        conn.executescript(DDL_SCRIPTS)
        conn.executescript(SAMPLE_DATA)
        conn.commit()
        log_action("DB_INIT", "Database initialized with sample data")
    finally:
        conn.close()


# ─────────────────────────────────────────────
# GENERIC QUERY HELPERS
# ─────────────────────────────────────────────

def run_query(sql: str, params=()) -> pd.DataFrame:
    conn = get_connection()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


def execute_dml(sql: str, params=()):
    conn = get_connection()
    try:
        conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def log_action(action: str, remarks: str = ""):
    try:
        execute_dml(
            "INSERT INTO AUDIT_LOGS(user_action, remarks) VALUES (?,?)",
            (action, remarks)
        )
    except Exception:
        pass  # Don't crash on logging failure


def log_ai_analysis(analysis_type: str, prompt: str, response: str):
    try:
        execute_dml(
            "INSERT INTO AI_ANALYSIS_LOG(analysis_type,input_prompt,ai_response) VALUES (?,?,?)",
            (analysis_type, prompt, response)
        )
    except Exception:
        pass


# ─────────────────────────────────────────────
# TABLE-SPECIFIC QUERIES
# ─────────────────────────────────────────────

def get_all_agents() -> pd.DataFrame:
    return run_query("SELECT * FROM AGENTS ORDER BY agent_name")


def get_agent(agent_id: str) -> pd.DataFrame:
    return run_query("SELECT * FROM AGENTS WHERE agent_id=?", (agent_id,))


def get_commissions_by_agent(agent_id: str) -> pd.DataFrame:
    sql = """
        SELECT c.commission_id, c.commission_month, p.policy_number,
               p.policy_type, p.premium_amount, c.commission_rate,
               c.commission_amount
        FROM COMMISSIONS c
        JOIN POLICIES p ON c.policy_id = p.policy_id
        WHERE c.agent_id = ?
        ORDER BY c.commission_month DESC
    """
    return run_query(sql, (agent_id,))


def get_incentives_by_agent(agent_id: str) -> pd.DataFrame:
    return run_query(
        "SELECT * FROM INCENTIVES WHERE agent_id=? ORDER BY incentive_month DESC",
        (agent_id,)
    )


def get_special_rewards_by_agent(agent_id: str) -> pd.DataFrame:
    return run_query(
        "SELECT * FROM SPECIAL_REWARDS WHERE agent_id=? ORDER BY reward_date DESC",
        (agent_id,)
    )


def get_monthly_summary() -> pd.DataFrame:
    sql = """
        SELECT commission_month,
               COUNT(DISTINCT agent_id)        AS agents_count,
               COUNT(commission_id)             AS policies_count,
               ROUND(SUM(commission_amount),2)  AS total_commission
        FROM COMMISSIONS
        GROUP BY commission_month
        ORDER BY commission_month
    """
    return run_query(sql)


def get_region_summary() -> pd.DataFrame:
    sql = """
        SELECT a.region,
               COUNT(DISTINCT a.agent_id)       AS agents_count,
               ROUND(SUM(c.commission_amount),2) AS total_commission,
               ROUND(AVG(c.commission_amount),2) AS avg_commission
        FROM AGENTS a
        JOIN COMMISSIONS c ON a.agent_id = c.agent_id
        GROUP BY a.region
        ORDER BY total_commission DESC
    """
    return run_query(sql)


def get_top_agents(limit: int = 10) -> pd.DataFrame:
    sql = """
        SELECT a.agent_id, a.agent_name, a.agent_type, a.region,
               ROUND(SUM(c.commission_amount),2)  AS total_commission,
               ROUND(SUM(COALESCE(i.reward_amount,0)),2) AS total_incentive,
               ROUND(SUM(c.commission_amount) +
                     SUM(COALESCE(i.reward_amount,0)),2) AS grand_total
        FROM AGENTS a
        JOIN COMMISSIONS c ON a.agent_id = c.agent_id
        LEFT JOIN INCENTIVES i ON a.agent_id = i.agent_id
        GROUP BY a.agent_id, a.agent_name, a.agent_type, a.region
        ORDER BY grand_total DESC
        LIMIT ?
    """
    return run_query(sql, (limit,))


def get_audit_logs(limit: int = 50) -> pd.DataFrame:
    return run_query(
        "SELECT * FROM AUDIT_LOGS ORDER BY audit_date DESC LIMIT ?",
        (limit,)
    )


def get_ai_analysis_logs(limit: int = 20) -> pd.DataFrame:
    return run_query(
        "SELECT * FROM AI_ANALYSIS_LOG ORDER BY created_date DESC LIMIT ?",
        (limit,)
    )


def load_csv_to_db(df: pd.DataFrame, table_name: str):
    """Load a CSV/DataFrame into the specified table."""
    conn = get_connection()
    try:
        df.to_sql(table_name, conn, if_exists="append", index=False)
        conn.commit()
        log_action("CSV_IMPORT", f"Loaded {len(df)} rows into {table_name}")
    finally:
        conn.close()
