import time
import threading
from datetime import datetime

def scheduler_loop(shared_state, shared_lock):
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
                    schedules = shared_state.get("schedules", [])
                    preset_to_load = None
                    
                    for sched in schedules:
                        if not sched.get("enabled", True):
                            continue
                            
                        # Check time match
                        if sched.get("time") == current_time_str:
                            # Check day match
                            days = sched.get("days", [])
                            if current_weekday in days:
                                preset_to_load = sched.get("preset_slot")
                                break
                    
                    if preset_to_load:
                        presets = shared_state.get("presets", {})
                        target_preset = presets.get(preset_to_load)
                        if target_preset:
                            print(f"[Scheduler] Loading preset {preset_to_load} from schedule")
                            success = apply_preset(shared_state, target_preset)
                            if success:
                                save_debounced(shared_state, 0.5)
                
                # We update the last fired minute whether or not a schedule fired
                last_fired_minute = current_minute
                
        except Exception as e:
            print(f"Error in scheduler loop: {e}")
            
        # Check every 5 seconds
        time.sleep(5)

def start_scheduler(shared_state, shared_lock):
    t = threading.Thread(
        target=scheduler_loop,
        args=(shared_state, shared_lock),
        daemon=True,
        name="SchedulerThread",
    )
    t.start()
    return t
