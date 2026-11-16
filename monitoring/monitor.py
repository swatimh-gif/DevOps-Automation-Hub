import os
import time
import platform
import datetime
import psutil
from config.settings import SERVICE_NAME, APP_VERSION

_START_TIME = time.time()

def get_process_uptime():
    """Returns uptime of the current application in seconds and formatted string."""
    uptime_seconds = int(time.time() - _START_TIME)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    formatted = f"{hours}h {minutes}m {seconds}s"
    return uptime_seconds, formatted

def get_system_metrics():
    """Retrieves real-time system resource metrics."""
    try:
        cpu_pct = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage(os.path.abspath(os.sep))
        process = psutil.Process()
        proc_mem = process.memory_info().rss / (1024 * 1024) # MB

        uptime_sec, uptime_str = get_process_uptime()

        return {
            "cpu_percent": round(cpu_pct, 1),
            "cpu_count": psutil.cpu_count(logical=True),
            "memory_percent": round(mem.percent, 1),
            "memory_used_gb": round(mem.used / (1024**3), 2),
            "memory_total_gb": round(mem.total / (1024**3), 2),
            "disk_percent": round(disk.percent, 1),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "process_pid": os.getpid(),
            "process_memory_mb": round(proc_mem, 1),
            "uptime_seconds": uptime_sec,
            "uptime_formatted": uptime_str,
            "os_name": platform.system(),
            "os_release": platform.release(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "service": SERVICE_NAME,
            "version": APP_VERSION,
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        uptime_sec, uptime_str = get_process_uptime()
        return {
            "cpu_percent": 0.0,
            "cpu_count": 1,
            "memory_percent": 0.0,
            "memory_used_gb": 0.0,
            "memory_total_gb": 0.0,
            "disk_percent": 0.0,
            "disk_used_gb": 0.0,
            "disk_total_gb": 0.0,
            "process_pid": os.getpid(),
            "process_memory_mb": 0.0,
            "uptime_seconds": uptime_sec,
            "uptime_formatted": uptime_str,
            "os_name": platform.system(),
            "os_release": platform.release(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "service": SERVICE_NAME,
            "version": APP_VERSION,
            "timestamp": datetime.datetime.now().isoformat(),
            "error": str(e)
        }
