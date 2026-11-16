import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)
DB_PATH = os.environ.get("DEVOPS_DB_PATH", str(INSTANCE_DIR / "devops_hub.db"))

# Logging configuration
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "pipeline.log"

# Application metadata
APP_NAME = "DevOps Automation Hub"
APP_VERSION = "1.0.0"
SERVICE_NAME = "DevOps-Automation-Hub"
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 5000))

# Environment & deployment settings
ENV = os.environ.get("FLASK_ENV", "development")
SECRET_KEY = os.environ.get("SECRET_KEY", "devops-secret-key-college-demo-2026")

# Deployment Target Configuration
# Supported targets: "Local Staging (Port 5001)", "Docker Container", "Cloud Webhook", "Pending"
DEPLOYMENT_TARGET = os.environ.get("DEPLOYMENT_TARGET", "Local Staging (Simulated Port 5001)")
DEPLOY_WEBHOOK_URL = os.environ.get("DEPLOY_WEBHOOK_URL", "")

# GitHub Integration
GITHUB_REPO = os.environ.get("GITHUB_REPO", "swati/DevOps-Automation-Hub")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
