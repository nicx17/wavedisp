"""
Preset scheduler: loads a preset when a schedule's time and weekday match.
"""

import threading
import time
from datetime import datetime


def due_preset(schedules, now):
    """Return the preset slot of the first enabled schedule matching `now`."""
    current_time = now.strftime("%H:%M")
    weekday = now.weekday()  # Monday = 0, matching the dashboard
    for sched in schedules:
        if not sched.get("enabled", True):
            continue
        if sched.get("time") == current_time and weekday in sched.get("days", []):
            return sched.get("preset_slot")
    return None


def scheduler_loop(store, interval=5):
    last_fired_minute = None

    while True:
        try:
            now = datetime.now()
            minute = now.strftime("%Y-%m-%d %H:%M")
            # Prevent firing multiple times in the same minute
            if minute != last_fired_minute:
                last_fired_minute = minute
                slot = due_preset(store.get("schedules", []), now)
                if slot:
                    print(f"[Scheduler] Loading preset {slot} from schedule")
                    if not store.load_preset(slot):
                        print(f"[Scheduler] Preset {slot} is empty, skipping")
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Error in scheduler loop: {e}")

        time.sleep(interval)


def start_scheduler(store):
    t = threading.Thread(
        target=scheduler_loop,
        args=(store,),
        daemon=True,
        name="SchedulerThread",
    )
    t.start()
    return t
