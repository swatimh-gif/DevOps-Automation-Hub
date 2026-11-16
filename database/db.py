import sqlite3
import datetime
from pathlib import Path
from config.settings import DB_PATH

def get_connection():
    """Returns a connection to SQLite with row factory set to sqlite3.Row."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes database tables if they do not already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Pipeline Runs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pipeline_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT UNIQUE NOT NULL,
        trigger_type TEXT NOT NULL,
        commit_hash TEXT,
        commit_msg TEXT,
        branch TEXT,
        start_time TEXT NOT NULL,
        end_time TEXT,
        duration REAL DEFAULT 0.0,
        source_status TEXT DEFAULT 'PENDING',
        dependency_status TEXT DEFAULT 'PENDING',
        test_status TEXT DEFAULT 'PENDING',
        docker_status TEXT DEFAULT 'PENDING',
        deployment_status TEXT DEFAULT 'PENDING',
        health_status TEXT DEFAULT 'PENDING',
        overall_status TEXT DEFAULT 'IN_PROGRESS',
        tests_passed INTEGER DEFAULT 0,
        tests_failed INTEGER DEFAULT 0,
        tests_total INTEGER DEFAULT 0,
        log_output TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Test Results Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        test_name TEXT NOT NULL,
        status TEXT NOT NULL,
        duration REAL DEFAULT 0.0,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(run_id) REFERENCES pipeline_runs(run_id)
    );
    """)

    # 3. System Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT,
        level TEXT NOT NULL,
        module TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp TEXT NOT NULL
    );
    """)

    # 4. Deployment Records Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deployment_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        environment TEXT NOT NULL,
        status TEXT NOT NULL,
        target TEXT NOT NULL,
        details TEXT,
        deployed_at TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()

def log_event(level: str, module: str, message: str, run_id: str = None):
    """Logs an event both to database and console/file."""
    now = datetime.datetime.now().isoformat()
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO system_logs (run_id, level, module, message, timestamp) VALUES (?, ?, ?, ?, ?)",
            (run_id, level.upper(), module, message, now)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB LOG ERROR] {e}")

def create_pipeline_run(run_id: str, trigger_type: str, commit_hash: str = "HEAD", commit_msg: str = "", branch: str = "main"):
    """Inserts a new pipeline run in IN_PROGRESS state."""
    start_time = datetime.datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO pipeline_runs (
            run_id, trigger_type, commit_hash, commit_msg, branch,
            start_time, overall_status
        ) VALUES (?, ?, ?, ?, ?, ?, 'IN_PROGRESS')
    """, (run_id, trigger_type, commit_hash, commit_msg, branch, start_time))
    conn.commit()
    conn.close()

def update_pipeline_run(run_id: str, **kwargs):
    """Dynamically updates fields for a pipeline run."""
    conn = get_connection()
    cursor = conn.cursor()
    set_clauses = []
    values = []
    for k, v in kwargs.items():
        set_clauses.append(f"{k} = ?")
        values.append(v)
    values.append(run_id)

    query = f"UPDATE pipeline_runs SET {', '.join(set_clauses)} WHERE run_id = ?"
    cursor.execute(query, values)
    conn.commit()
    conn.close()

def get_recent_runs(limit: int = 10):
    """Fetches recent pipeline runs."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pipeline_runs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_run_by_id(run_id: str):
    """Fetches a specific run by run_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pipeline_runs WHERE run_id = ?", (run_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_metrics():
    """Calculates summary statistics for dashboard metrics."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM pipeline_runs")
    total_runs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pipeline_runs WHERE overall_status = 'SUCCESS'")
    success_runs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pipeline_runs WHERE overall_status = 'FAILED'")
    failed_runs = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM pipeline_runs ORDER BY id DESC LIMIT 1")
    latest_run = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM test_results WHERE status = 'PASSED'")
    total_tests_passed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM test_results WHERE status = 'FAILED'")
    total_tests_failed = cursor.fetchone()[0]

    conn.close()

    success_rate = round((success_runs / total_runs * 100), 1) if total_runs > 0 else 0.0

    return {
        "total_runs": total_runs,
        "success_runs": success_runs,
        "failed_runs": failed_runs,
        "success_rate": success_rate,
        "latest_run": dict(latest_run) if latest_run else None,
        "total_tests_passed": total_tests_passed,
        "total_tests_failed": total_tests_failed,
    }

def record_test_result(run_id: str, test_name: str, status: str, duration: float, error_message: str = None):
    """Records an individual test outcome."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO test_results (run_id, test_name, status, duration, error_message)
        VALUES (?, ?, ?, ?, ?)
    """, (run_id, test_name, status, duration, error_message))
    conn.commit()
    conn.close()

def get_test_results_by_run(run_id: str):
    """Fetches tests executed for a particular run."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test_results WHERE run_id = ? ORDER BY id ASC", (run_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_test_results(limit: int = 50):
    """Fetches all test results."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test_results ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def record_deployment(run_id: str, environment: str, status: str, target: str, details: str):
    """Records a deployment event."""
    now = datetime.datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO deployment_records (run_id, environment, status, target, details, deployed_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (run_id, environment, status, target, details, now))
    conn.commit()
    conn.close()

def get_recent_deployments(limit: int = 10):
    """Fetches recent deployments."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deployment_records ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_recent_logs(limit: int = 100, level: str = None):
    """Fetches recent system logs with optional level filter."""
    conn = get_connection()
    cursor = conn.cursor()
    if level and level != "ALL":
        cursor.execute("SELECT * FROM system_logs WHERE level = ? ORDER BY id DESC LIMIT ?", (level.upper(), limit))
    else:
        cursor.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
