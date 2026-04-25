# pack/ui/refresh.py

from pathlib import Path
import subprocess
import threading
import sys
import time

from pack.data_access import (
    duck_query_df,
    get_latest_ipl_value,
)


REFRESH_STATE = {
    "running": False,
    "last_started": None,
    "last_finished": None,
    "success": None,
    "last_stand": None,
}

REFRESH_LOCK = threading.Lock()


def set_refresh_state(**kwargs):
    with REFRESH_LOCK:
        REFRESH_STATE.update(kwargs)


def get_refresh_state():
    with REFRESH_LOCK:
        return {
            "running": REFRESH_STATE["running"],
            "last_started": REFRESH_STATE["last_started"],
            "last_finished": REFRESH_STATE["last_finished"],
            "success": REFRESH_STATE["success"],
            "last_stand": REFRESH_STATE["last_stand"],
        }


def wait_until_db_readable(max_wait_seconds: float = 8.0) -> bool:
    started = time.time()

    while time.time() - started < max_wait_seconds:
        try:
            duck_query_df("SELECT 1")
            return True
        except Exception:
            time.sleep(0.25)

    return False


def run_generate_mock_data():
    script_path = Path(__file__).resolve().parents[2] / "generate_mock_data.py"

    if not script_path.exists():
        set_refresh_state(
            running=False,
            last_finished=time.strftime("%Y-%m-%d %H:%M:%S"),
            success=False,
        )
        return

    set_refresh_state(
        running=True,
        last_started=time.strftime("%Y-%m-%d %H:%M:%S"),
        last_finished=None,
        success=None,
    )

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        if result.returncode != 0:
            set_refresh_state(
                running=False,
                last_finished=time.strftime("%Y-%m-%d %H:%M:%S"),
                success=False,
            )
            return

        if not wait_until_db_readable():
            set_refresh_state(
                running=False,
                last_finished=time.strftime("%Y-%m-%d %H:%M:%S"),
                success=False,
            )
            return

        latest_ipl = get_latest_ipl_value()

        set_refresh_state(
            running=False,
            last_finished=time.strftime("%Y-%m-%d %H:%M:%S"),
            success=True,
            last_stand=latest_ipl,
        )

    except Exception:
        set_refresh_state(
            running=False,
            last_finished=time.strftime("%Y-%m-%d %H:%M:%S"),
            success=False,
        )