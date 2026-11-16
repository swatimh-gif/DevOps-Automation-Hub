import time
import datetime
import random
from config.settings import LOG_FILE
from database.db import (
    create_pipeline_run,
    update_pipeline_run,
    log_event
)
from pipeline.source_checker import check_source
from pipeline.dependency_manager import check_dependencies
from pipeline.test_runner import run_tests
from pipeline.docker_manager import build_docker_image
from pipeline.deployment_manager import handle_deployment
from pipeline.health_checker import check_application_health

def generate_run_id():
    """Generates a sequential or randomized run identifier like RUN-1042."""
    timestamp_suffix = int(time.time()) % 10000
    random_num = random.randint(10, 99)
    return f"RUN-{timestamp_suffix}{random_num}"

def append_file_log(line: str):
    """Appends a line to the physical logs/pipeline.log file."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {line}\n")
    except Exception as e:
        print(f"Log file write error: {e}")

def execute_pipeline(trigger_type: str = "Manual", simulate_failure: bool = False):
    """Orchestrates the complete 8-step CI/CD pipeline execution with genuine checks,
    database persistence, logging, and accurate status detection.
    """
    run_id = generate_run_id()
    start_time = time.time()
    iso_start = datetime.datetime.now().isoformat()
    log_lines = []

    def log(msg, level="INFO"):
        formatted = f"[{level}] {msg}"
        log_lines.append(formatted)
        append_file_log(f"[{run_id}] {formatted}")
        log_event(level, "PIPELINE_RUNNER", msg, run_id)

    log(f"Starting CI/CD Pipeline Execution (Trigger: {trigger_type})", "INFO")

    # Step 1: Initialize Database Record
    create_pipeline_run(
        run_id=run_id,
        trigger_type=trigger_type,
        commit_hash="Pending",
        commit_msg="Inspecting source...",
        branch="main"
    )

    # Step 2: Check Project Source
    log("Step 1/6: Validating project source and git repository state...", "INFO")
    src_res = check_source()
    log(f"Source Check: {src_res['summary']}", "SUCCESS" if src_res['status'] == "PASSED" else "ERROR")

    commit_hash = src_res["commit_hash"]
    commit_msg = src_res["commit_msg"]
    branch = src_res["branch"]

    update_pipeline_run(
        run_id,
        source_status=src_res["status"],
        commit_hash=commit_hash,
        commit_msg=commit_msg,
        branch=branch
    )

    if src_res["status"] == "FAILED":
        log("Pipeline aborted: Source repository check failed.", "ERROR")
        duration = round(time.time() - start_time, 2)
        update_pipeline_run(
            run_id,
            overall_status="FAILED",
            end_time=datetime.datetime.now().isoformat(),
            duration=duration,
            log_output="\n".join(log_lines)
        )
        return {"run_id": run_id, "status": "FAILED", "duration": duration}

    # Step 3: Dependency Verification
    log("Step 2/6: Verifying Python environment and requirements manifest...", "INFO")
    dep_res = check_dependencies()
    log(f"Dependency Check: {dep_res['summary']}", "SUCCESS" if dep_res['status'] == "PASSED" else "ERROR")

    update_pipeline_run(run_id, dependency_status=dep_res["status"])

    if dep_res["status"] == "FAILED":
        log("Pipeline aborted: Missing dependencies in environment.", "ERROR")
        duration = round(time.time() - start_time, 2)
        update_pipeline_run(
            run_id,
            overall_status="FAILED",
            end_time=datetime.datetime.now().isoformat(),
            duration=duration,
            log_output="\n".join(log_lines)
        )
        return {"run_id": run_id, "status": "FAILED", "duration": duration}

    # Step 4: Execute Automated Tests
    log("Step 3/6: Executing automated test suite with pytest...", "INFO")
    test_res = run_tests(run_id, simulate_failure=simulate_failure)
    log(f"Test Execution: {test_res['summary']}", "SUCCESS" if test_res['status'] == "PASSED" else "ERROR")

    update_pipeline_run(
        run_id,
        test_status=test_res["status"],
        tests_passed=test_res["passed_count"],
        tests_failed=test_res["failed_count"],
        tests_total=test_res["total_count"]
    )

    # CRITICAL DEVOPS CHECK: If tests fail, abort subsequent deployment and docker steps!
    if test_res["status"] != "PASSED":
        log("⚠️ Automated tests FAILED! Aborting Docker build and Deployment stages as per CI/CD failure-containment policy.", "ERROR")
        duration = round(time.time() - start_time, 2)
        update_pipeline_run(
            run_id,
            docker_status="SKIPPED",
            deployment_status="SKIPPED",
            health_status="SKIPPED",
            overall_status="FAILED",
            end_time=datetime.datetime.now().isoformat(),
            duration=duration,
            log_output="\n".join(log_lines)
        )
        return {
            "run_id": run_id,
            "status": "FAILED",
            "reason": "Test suite failure",
            "duration": duration,
            "tests_passed": test_res["passed_count"],
            "tests_failed": test_res["failed_count"]
        }

    # Step 5: Docker Containerization
    log("Step 4/6: Inspecting Docker environment and container build readiness...", "INFO")
    docker_res = build_docker_image(run_id)
    log(f"Docker Stage: {docker_res['summary']}", "SUCCESS" if docker_res['status'] == "PASSED" else ("WARNING" if docker_res['status'] == "SKIPPED" else "ERROR"))

    update_pipeline_run(run_id, docker_status=docker_res["status"])

    # Step 6: Application Deployment
    log("Step 5/6: Processing application deployment...", "INFO")
    deploy_res = handle_deployment(run_id, commit_hash)
    log(f"Deployment Stage: {deploy_res['summary']}", "SUCCESS" if deploy_res['status'] == "PASSED" else ("WARNING" if deploy_res['status'] == "PENDING" else "ERROR"))

    update_pipeline_run(run_id, deployment_status=deploy_res["status"])

    # Step 7: Application Health Verification
    log("Step 6/6: Verifying application health endpoint (/health)...", "INFO")
    health_res = check_application_health()
    log(f"Health Verification: {health_res['summary']}", "SUCCESS" if health_res['status'] == "HEALTHY" else "ERROR")

    update_pipeline_run(run_id, health_status=health_res["status"])

    # Step 8: Final Pipeline Evaluation
    duration = round(time.time() - start_time, 2)
    overall_status = "SUCCESS"

    # If critical stages failed (excluding SKIPPED/PENDING non-fatal stages)
    if docker_res["status"] == "FAILED" or deploy_res["status"] == "FAILED" or health_res["status"] == "UNHEALTHY":
        overall_status = "FAILED"

    log(f"Pipeline Run {run_id} completed with status: {overall_status} (Total duration: {duration}s)", "SUCCESS" if overall_status == "SUCCESS" else "ERROR")

    update_pipeline_run(
        run_id,
        overall_status=overall_status,
        end_time=datetime.datetime.now().isoformat(),
        duration=duration,
        log_output="\n".join(log_lines)
    )

    return {
        "run_id": run_id,
        "status": overall_status,
        "duration": duration,
        "source": src_res["status"],
        "dependencies": dep_res["status"],
        "tests": test_res["status"],
        "docker": docker_res["status"],
        "deployment": deploy_res["status"],
        "health": health_res["status"],
        "tests_passed": test_res["passed_count"],
        "tests_failed": test_res["failed_count"]
    }
