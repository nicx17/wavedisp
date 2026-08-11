import threading
import time
from datetime import datetime


def scheduler_loop(shared_state, shared_lock, dirty_flag=None):
    from backend.config import apply_preset, save_debounced

    last_fired_minute = -1

    while True:
        try:
            now = datetime.now()
            current_minute = now.minute

            # Prevent firing multiple times in the same minute
            if current_minute != last_fired_minute:
                current_time_str = now.strftime("%H:%M")
                current_weekday = now.weekday()

                with shared_lock:
                    schedules = list(shared_state.get("schedules", []))
                preset_to_load = None

                for sched in schedules:
                    if not sched.get("enabled", True):
                        continue

                    if sched.get(
                        "time"
                    ) == current_time_str and current_weekday in sched.get("days", []):
                        preset_to_load = sched.get("preset_slot")
                        break

                if preset_to_load:
                    should_save = False
                    with shared_lock:
                        presets = shared_state.get("presets", {})
                        target_preset = presets.get(preset_to_load)
                        if target_preset:
                            print(
                                f"[Scheduler] Loading preset {preset_to_load} "
                                "from schedule"
                            )
                            success = apply_preset(shared_state, target_preset)
                            if success:
                                if dirty_flag is not None:
                                    dirty_flag.value = shared_state.get(
                                        "_last_updated", time.time()
                                    )
                                should_save = True
                    if should_save:
                        save_debounced(shared_state, 0.5)

                # We update the last fired minute whether or not a schedule fired
                last_fired_minute = current_minute

        except Exception as e:
            print(f"Error in scheduler loop: {e}")

        # Check every 5 seconds
        time.sleep(5)


def start_scheduler(shared_state, shared_lock, dirty_flag=None):
    t = threading.Thread(
        target=scheduler_loop,
        args=(shared_state, shared_lock, dirty_flag),
        daemon=True,
        name="SchedulerThread",
    )
    t.start()
    return t
