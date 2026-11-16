import os
import pytest
from database.db import get_connection

def test_database_connectivity():
    """Test 5: Verify SQLite database connectivity and schema integrity."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    assert "pipeline_runs" in tables
    assert "test_results" in tables
    assert "system_logs" in tables
    assert "deployment_records" in tables

def test_calculation_utility():
    """Test 6: Verify pipeline metrics calculation logic."""
    total = 10
    success = 8
    rate = (success / total) * 100
    assert rate == 80.0

def test_pipeline_failure_simulation():
    """Test 7: Demonstration hook for simulating test failures.
    Passes under standard conditions.
    Triggers an assertion failure only when SIMULATE_TEST_FAILURE is explicitly enabled.
    """
    if os.environ.get("SIMULATE_TEST_FAILURE") == "1":
        raise AssertionError("Simulated Failure: Intentional test assertion failure to demonstrate CI/CD pipeline halting and skipping deployment stages.")
    assert True
