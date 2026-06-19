import os
import gc
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

STATUS_FILE_PATH = Path("/tmp/ram_status")

def get_system_ram_percent():
    """
    Reads the system RAM percentage.
    First tries to read from /tmp/ram_status (written by external bash).
    Falls back to parsing /proc/meminfo (Linux-only, zero dependencies).
    Falls back to psutil if available.
    """
    # 1. Try status file
    if STATUS_FILE_PATH.exists():
        try:
            with open(STATUS_FILE_PATH, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content.isdigit():
                    return int(content)
        except Exception:
            pass

    # 2. Try pure Linux /proc/meminfo
    if os.path.exists("/proc/meminfo"):
        try:
            mem_total = 0
            mem_avail = 0
            with open("/proc/meminfo", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        mem_total = int(line.split()[1]) # in kB
                    elif line.startswith("MemAvailable:"):
                        mem_avail = int(line.split()[1]) # in kB
            if mem_total > 0 and mem_avail > 0:
                used = mem_total - mem_avail
                return int((used / mem_total) * 100)
        except Exception as e:
            logger.debug(f"[abelion_core.ram] Failed to parse /proc/meminfo: {e}")

    # 3. Try psutil fallback
    try:
        import psutil
        return int(psutil.virtual_memory().percent)
    except ImportError:
        pass

    return 0

def get_hermes_rss_bytes():
    """
    Returns the resident set size (RSS) memory of the current Hermes Python process in bytes.
    Uses /proc/self/status or falls back to psutil.
    """
    if os.path.exists("/proc/self/status"):
        try:
            with open("/proc/self/status", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        rss_kb = int(line.split()[1]) # in kB
                        return rss_kb * 1024
        except Exception as e:
            logger.debug(f"[abelion_core.ram] Failed to parse /proc/self/status: {e}")

    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss
    except (ImportError, Exception):
        pass

    return 0

def enforce_ram_guard():
    """
    Checks memory levels and applies RAM protection.
    If RAM > 80% and Hermes is using >500MB, trigger gc.collect().
    If RAM > 80% and spike is external, log warning and returns block flag.
    """
    sys_percent = get_system_ram_percent()
    if sys_percent < 80:
        return False

    hermes_rss = get_hermes_rss_bytes()
    hermes_rss_mb = hermes_rss / (1024 * 1024)

    logger.warning(
        f"[abelion_core.ram] System RAM usage is high: {sys_percent}% (Hermes RSS: {hermes_rss_mb:.1f} MB)"
    )

    # If Hermes is using more than 500MB, collect garbage
    if hermes_rss_mb > 500:
        logger.info("[abelion_core.ram] Triggering aggressive gc.collect() to reclaim memory.")
        before = gc.mem_free() if hasattr(gc, "mem_free") else 0
        gc.collect()
        after = gc.mem_free() if hasattr(gc, "mem_free") else 0
        if after > before:
            logger.info(f"[abelion_core.ram] Reclaimed {after - before} bytes via gc.")

    # Return True to indicate that system RAM is critical (>80%)
    return True
