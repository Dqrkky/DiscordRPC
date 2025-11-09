import psutil

def is_discord_running():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and "discord" in proc.info['name'].lower():
            return proc.status() == psutil.STATUS_RUNNING
    return False