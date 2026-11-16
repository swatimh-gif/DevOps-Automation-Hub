import shutil
import subprocess
import time
from config.settings import BASE_DIR
from database.db import log_event

def is_docker_available():
    """Checks whether Docker CLI is installed and the daemon is reachable."""
    docker_bin = shutil.which("docker")
    if not docker_bin:
        return False, "Docker executable not found in system PATH."

    try:
        # Check if docker daemon is responding
        proc = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if proc.returncode == 0:
            return True, "Docker daemon is running and responsive."
        else:
            return False, f"Docker CLI found, but daemon is not responding (exit code {proc.returncode})."
    except subprocess.TimeoutExpired:
        return False, "Docker command timed out while attempting to reach daemon."
    except Exception as e:
        return False, f"Failed to query Docker: {str(e)}"

def build_docker_image(run_id: str):
    """Attempts to build the Docker image if Docker is available.
    Accurately reports SKIPPED when Docker is unavailable, adhering strictly
    to honest status reporting without fabricated results.
    """
    available, reason = is_docker_available()

    if not available:
        msg = f"[{run_id}] Docker stage SKIPPED: {reason}"
        log_event("WARNING", "DOCKER_MANAGER", msg, run_id)
        return {
            "status": "SKIPPED",
            "available": False,
            "summary": "Docker build skipped (Daemon/CLI not detected)",
            "details": f"{reason} In accordance with DevOps standards, this stage was marked SKIPPED rather than reporting false success.",
            "output": f"Notice: Docker CLI/Engine is not active on this environment.\nReason: {reason}\nSuggested action: Install Docker Desktop and start the daemon to enable container builds."
        }

    # If Docker is available, proceed with genuine image build
    log_event("INFO", "DOCKER_MANAGER", f"[{run_id}] Initiating Docker build: 'docker build -t devops-automation-hub:latest .'", run_id)
    start_time = time.time()
    try:
        proc = subprocess.run(
            ["docker", "build", "-t", "devops-automation-hub:latest", "."],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=120
        )
        duration = round(time.time() - start_time, 2)
        combined_output = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")

        if proc.returncode == 0:
            log_event("SUCCESS", "DOCKER_MANAGER", f"[{run_id}] Docker image 'devops-automation-hub:latest' built successfully ({duration}s)", run_id)
            return {
                "status": "PASSED",
                "available": True,
                "duration": duration,
                "summary": f"Image 'devops-automation-hub:latest' built successfully ({duration}s)",
                "details": f"Container image constructed from Dockerfile. Tags: devops-automation-hub:latest. Build duration: {duration}s.",
                "output": combined_output
            }
        else:
            log_event("ERROR", "DOCKER_MANAGER", f"[{run_id}] Docker build failed with exit code {proc.returncode}", run_id)
            return {
                "status": "FAILED",
                "available": True,
                "duration": duration,
                "summary": f"Docker image build failed (exit code {proc.returncode})",
                "details": f"Docker build returned error code {proc.returncode}.",
                "output": combined_output
            }
    except subprocess.TimeoutExpired:
        duration = round(time.time() - start_time, 2)
        msg = f"Docker build timed out after {duration}s"
        log_event("ERROR", "DOCKER_MANAGER", f"[{run_id}] {msg}", run_id)
        return {
            "status": "FAILED",
            "available": True,
            "duration": duration,
            "summary": msg,
            "details": msg,
            "output": msg
        }
    except Exception as e:
        msg = f"Exception during Docker build: {str(e)}"
        log_event("ERROR", "DOCKER_MANAGER", f"[{run_id}] {msg}", run_id)
        return {
            "status": "FAILED",
            "available": True,
            "duration": 0,
            "summary": msg,
            "details": msg,
            "output": msg
        }

def get_docker_diagnostics():
    """Returns comprehensive Docker diagnostic data for the Docker Status page."""
    available, reason = is_docker_available()
    docker_bin = shutil.which("docker")

    version_str = "Not installed"
    images_list = []
    containers_list = []

    if available:
        try:
            ver_proc = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
            version_str = ver_proc.stdout.strip()

            img_proc = subprocess.run(["docker", "images", "--format", "{{.Repository}}:{{.Tag}} ({{.Size}})"], capture_output=True, text=True, timeout=5)
            images_list = [line.strip() for line in img_proc.stdout.splitlines() if line.strip()]

            cnt_proc = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}} - {{.Status}} ({{.Image}})"], capture_output=True, text=True, timeout=5)
            containers_list = [line.strip() for line in cnt_proc.stdout.splitlines() if line.strip()]
        except Exception:
            pass

    return {
        "installed": docker_bin is not None,
        "available": available,
        "binary_path": docker_bin or "N/A",
        "reason": reason,
        "version": version_str,
        "images": images_list,
        "containers": containers_list
    }
