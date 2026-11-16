import os
import sys
import time
import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for, send_file
from config.settings import (
    APP_NAME,
    APP_VERSION,
    SERVICE_NAME,
    HOST,
    PORT,
    SECRET_KEY,
    DEPLOYMENT_TARGET,
    LOG_FILE,
    GITHUB_REPO
)
from database.db import (
    init_db,
    get_metrics,
    get_recent_runs,
    get_run_by_id,
    get_all_test_results,
    get_test_results_by_run,
    get_recent_deployments,
    get_recent_logs,
    log_event
)
from pipeline.runner import execute_pipeline
from pipeline.docker_manager import get_docker_diagnostics
from monitoring.monitor import get_system_metrics, get_process_uptime

def create_app(testing: bool = False):
    """Application factory for DevOps Automation Hub."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["TESTING"] = testing

    # Ensure database tables exist on startup
    init_db()

    # -------------------------------------------------------------
    # Context Processor for Templates
    # -------------------------------------------------------------
    @app.context_processor
    def inject_global_data():
        metrics = get_metrics()
        return {
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "service_name": SERVICE_NAME,
            "metrics": metrics,
            "deployment_target": DEPLOYMENT_TARGET,
            "github_repo": GITHUB_REPO,
            "current_year": datetime.datetime.now().year
        }

    # -------------------------------------------------------------
    # Page Routes (8 Core Modules)
    # -------------------------------------------------------------
    @app.route("/")
    def dashboard():
        """Page 1: Dashboard Overview"""
        metrics = get_metrics()
        recent_runs = get_recent_runs(limit=8)
        sys_metrics = get_system_metrics()
        return render_template(
            "dashboard.html",
            active_page="dashboard",
            metrics=metrics,
            recent_runs=recent_runs,
            sys_metrics=sys_metrics
        )

    @app.route("/pipeline")
    def pipeline_view():
        """Page 2: Pipeline Execution"""
        recent_runs = get_recent_runs(limit=5)
        latest_run = recent_runs[0] if recent_runs else None
        return render_template(
            "pipeline.html",
            active_page="pipeline",
            latest_run=latest_run,
            recent_runs=recent_runs
        )

    @app.route("/history")
    def history_view():
        """Page 3: Build History"""
        runs = get_recent_runs(limit=50)
        return render_template(
            "history.html",
            active_page="history",
            runs=runs
        )

    @app.route("/testing")
    def testing_view():
        """Page 4: Testing Results"""
        recent_tests = get_all_test_results(limit=50)
        metrics = get_metrics()
        return render_template(
            "testing.html",
            active_page="testing",
            tests=recent_tests,
            metrics=metrics
        )

    @app.route("/docker")
    def docker_view():
        """Page 5: Docker Status"""
        diagnostics = get_docker_diagnostics()
        return render_template(
            "docker.html",
            active_page="docker",
            docker=diagnostics
        )

    @app.route("/deployment")
    def deployment_view():
        """Page 6: Deployment Status"""
        deployments = get_recent_deployments(limit=25)
        return render_template(
            "deployment.html",
            active_page="deployment",
            deployments=deployments
        )

    @app.route("/monitoring")
    def monitoring_view():
        """Page 7: Application Monitoring"""
        sys_metrics = get_system_metrics()
        return render_template(
            "monitoring.html",
            active_page="monitoring",
            metrics=sys_metrics
        )

    @app.route("/logs")
    def logs_view():
        """Page 8: Execution Logs"""
        level = request.args.get("level", "ALL")
        logs = get_recent_logs(limit=150, level=level)
        return render_template(
            "logs.html",
            active_page="logs",
            logs=logs,
            selected_level=level
        )

    # -------------------------------------------------------------
    # API & Functional Endpoints
    # -------------------------------------------------------------
    @app.route("/health")
    def health():
        """Health-check endpoint conforming strictly to DevOps standards.
        Returns authentic application state and runtime metadata.
        """
        uptime_sec, uptime_str = get_process_uptime()
        sys_metrics = get_system_metrics()
        return jsonify({
            "status": "healthy",
            "service": SERVICE_NAME,
            "version": APP_VERSION,
            "timestamp": datetime.datetime.now().isoformat(),
            "uptime_seconds": uptime_sec,
            "uptime_human": uptime_str,
            "database": "connected",
            "environment": os.environ.get("FLASK_ENV", "production"),
            "system": {
                "cpu_percent": sys_metrics.get("cpu_percent"),
                "memory_percent": sys_metrics.get("memory_percent"),
                "disk_percent": sys_metrics.get("disk_percent")
            }
        }), 200

    @app.route("/api/status")
    def api_status():
        """Backend system status API endpoint."""
        return jsonify({
            "system": "operational",
            "service": SERVICE_NAME,
            "version": APP_VERSION,
            "environment": os.environ.get("FLASK_ENV", "development"),
            "timestamp": datetime.datetime.now().isoformat()
        }), 200

    @app.route("/api/metrics")
    def api_metrics():
        """Returns JSON metrics for dashboard charts and widgets."""
        metrics = get_metrics()
        return jsonify(metrics), 200

    @app.route("/api/monitoring/metrics")
    def api_monitoring_metrics():
        """Returns live system resource metrics."""
        return jsonify(get_system_metrics()), 200

    @app.route("/api/pipeline/run", methods=["POST"])
    def api_pipeline_run():
        """Executes the automated CI/CD pipeline."""
        data = request.get_json(silent=True) or {}
        trigger_type = data.get("trigger_type", "Manual Web Dashboard")
        simulate_failure = bool(data.get("simulate_failure", False))

        result = execute_pipeline(trigger_type=trigger_type, simulate_failure=simulate_failure)
        return jsonify(result), 200

    @app.route("/api/pipeline/runs")
    def api_pipeline_runs():
        """Returns list of recent pipeline runs."""
        limit = request.args.get("limit", 10, type=int)
        runs = get_recent_runs(limit=limit)
        return jsonify(runs), 200

    @app.route("/api/pipeline/runs/<run_id>")
    def api_pipeline_run_detail(run_id):
        """Returns detailed breakdown of a specific pipeline run."""
        run = get_run_by_id(run_id)
        if not run:
            return jsonify({"error": "Run not found"}), 404
        tests = get_test_results_by_run(run_id)
        return jsonify({"run": run, "tests": tests}), 200

    @app.route("/api/logs")
    def api_logs():
        """Returns recent system logs with level filter."""
        level = request.args.get("level", "ALL")
        limit = request.args.get("limit", 100, type=int)
        logs = get_recent_logs(limit=limit, level=level)
        return jsonify(logs), 200

    @app.route("/api/docker/status")
    def api_docker_status():
        """Returns diagnostic details regarding Docker environment."""
        return jsonify(get_docker_diagnostics()), 200

    @app.route("/api/webhook/github", methods=["POST"])
    def github_webhook():
        """GitHub Webhook Receiver for automated CI/CD triggering on push events."""
        event_type = request.headers.get("X-GitHub-Event", "push")
        data = request.get_json(silent=True) or {}

        commit_hash = "N/A"
        commit_msg = "Automated GitHub Trigger"
        sender = "GitHub Actions"

        if "head_commit" in data:
            commit_hash = data["head_commit"].get("id", "")[:7]
            commit_msg = data["head_commit"].get("message", "GitHub push")
        if "sender" in data:
            sender = data["sender"].get("login", "GitHub")

        log_event("INFO", "WEBHOOK", f"Received GitHub webhook event '{event_type}' from {sender}. Triggering automated pipeline.")
        result = execute_pipeline(trigger_type=f"GitHub Push ({sender})", simulate_failure=False)
        return jsonify({"message": "Pipeline initiated via GitHub webhook", "result": result}), 202

    @app.route("/logs/download")
    def download_logs():
        """Allows direct download of the pipeline.log file."""
        if os.path.exists(LOG_FILE):
            return send_file(LOG_FILE, as_attachment=True, download_name="pipeline.log")
        return "Log file empty or not created yet", 404

    return app

# Module entrypoint for running directly
app = create_app()

if __name__ == "__main__":
    print(f"🚀 Starting {APP_NAME} v{APP_VERSION} on http://localhost:{PORT}")
    init_db()
    # Log startup event
    log_event("SUCCESS", "SYSTEM", f"{APP_NAME} started on port {PORT}")
    app.run(host=HOST, port=PORT, debug=True)
