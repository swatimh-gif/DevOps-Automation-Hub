import importlib
import sys
from pathlib import Path
from config.settings import BASE_DIR

REQUIRED_MODULES = ["flask", "pytest", "requests", "psutil"]

def check_dependencies():
    """Verifies that project dependencies defined in requirements.txt are installed and functional."""
    req_file = BASE_DIR / "requirements.txt"
    if not req_file.exists():
        return {
            "status": "FAILED",
            "summary": "requirements.txt not found in project root",
            "details": "Missing requirements.txt manifest file."
        }

    missing = []
    verified = []
    for mod in REQUIRED_MODULES:
        try:
            importlib.import_module(mod)
            verified.append(mod)
        except ImportError:
            missing.append(mod)

    if missing:
        return {
            "status": "FAILED",
            "missing": missing,
            "verified": verified,
            "summary": f"Missing dependencies: {', '.join(missing)}",
            "details": f"The following required modules are missing from Python environment ({sys.executable}): {', '.join(missing)}."
        }

    return {
        "status": "PASSED",
        "verified": verified,
        "summary": f"All {len(verified)} core dependencies verified ({', '.join(verified)})",
        "details": f"Python runtime environment verified with packages: {', '.join(verified)}."
    }
