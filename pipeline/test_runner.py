import os
import sys
import time
import subprocess
import re
from pathlib import Path
from config.settings import BASE_DIR
from database.db import record_test_result, log_event

def run_tests(run_id: str, simulate_failure: bool = False):
    """Executes automated tests using pytest, records results into database,
    and returns comprehensive test execution metrics.
    """
    start_time = time.time()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR)

    if simulate_failure:
        env["SIMULATE_TEST_FAILURE"] = "1"
        log_event("WARNING", "TEST_RUNNER", f"[{run_id}] Executing tests with SIMULATE_TEST_FAILURE=1 (Demonstration mode)", run_id)
    else:
        env.pop("SIMULATE_TEST_FAILURE", None)

    log_event("INFO", "TEST_RUNNER", f"[{run_id}] Launching automated test suite via pytest...", run_id)

    cmd = [sys.executable, "-m", "pytest", "tests/test_app.py", "tests/test_functionality.py", "-v", "--no-header", "-rA"]

    try:
        process = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        duration = round(time.time() - start_time, 2)
        stdout = process.stdout
        stderr = process.stderr
        combined_output = stdout + ("\n" + stderr if stderr else "")

        # Parse test outcomes line by line
        # Format usually: tests/test_app.py::test_homepage_availability PASSED
        # or tests/test_functionality.py::test_pipeline_failure_simulation FAILED
        test_pattern = re.compile(r"^(tests/[\w\.\-\_]+::[\w\.\-\_]+)\s+([A-Z]+)", re.MULTILINE)
        matches = test_pattern.findall(stdout)

        passed_count = 0
        failed_count = 0
        total_count = len(matches)

        for test_name, status in matches:
            norm_status = "PASSED" if "PASS" in status else "FAILED"
            if norm_status == "PASSED":
                passed_count += 1
                record_test_result(run_id, test_name, "PASSED", 0.05, None)
            else:
                failed_count += 1
                record_test_result(run_id, test_name, "FAILED", 0.05, "Assertion failure in automated test suite")

        # Fallback parsing from short test summary info if matches is empty
        if total_count == 0:
            if "passed" in stdout or "failed" in stdout:
                passed_match = re.search(r"(\d+) passed", stdout)
                failed_match = re.search(r"(\d+) failed", stdout)
                passed_count = int(passed_match.group(1)) if passed_match else 0
                failed_count = int(failed_match.group(1)) if failed_match else 0
                total_count = passed_count + failed_count
                if total_count > 0:
                    record_test_result(run_id, "TestSuite::AllTests", "PASSED" if failed_count == 0 else "FAILED", duration, None if failed_count == 0 else "Test suite failure")

        is_success = (process.returncode == 0) and (failed_count == 0)
        overall_test_status = "PASSED" if is_success else "FAILED"

        summary = f"{passed_count} passed, {failed_count} failed out of {total_count} tests ({duration}s)"
        log_event(
            "SUCCESS" if is_success else "ERROR",
            "TEST_RUNNER",
            f"[{run_id}] Test execution completed: {summary}",
            run_id
        )

        return {
            "status": overall_test_status,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "total_count": total_count,
            "duration": duration,
            "summary": summary,
            "output": combined_output,
            "details": f"Pytest exited with code {process.returncode}. {summary}"
        }

    except subprocess.TimeoutExpired:
        duration = round(time.time() - start_time, 2)
        msg = "Pytest execution timed out after 30 seconds"
        log_event("ERROR", "TEST_RUNNER", f"[{run_id}] {msg}", run_id)
        record_test_result(run_id, "TestSuite::Timeout", "FAILED", duration, msg)
        return {
            "status": "FAILED",
            "passed_count": 0,
            "failed_count": 1,
            "total_count": 1,
            "duration": duration,
            "summary": msg,
            "output": msg,
            "details": msg
        }
    except Exception as e:
        duration = round(time.time() - start_time, 2)
        msg = f"Unexpected error while executing test suite: {str(e)}"
        log_event("ERROR", "TEST_RUNNER", f"[{run_id}] {msg}", run_id)
        record_test_result(run_id, "TestSuite::Error", "FAILED", duration, msg)
        return {
            "status": "FAILED",
            "passed_count": 0,
            "failed_count": 1,
            "total_count": 1,
            "duration": duration,
            "summary": msg,
            "output": msg,
            "details": msg
        }
