import subprocess
import signal
import time
import os

extra = ["start", "/min", "cmd", "/k"] if os.name == "nt" else ["gnome-terminal", "--"]
__dir = "cd /d G:/File/Projects/Coding/DiscordRPC &&"
# Open new terminal windows (replace gnome-terminal if needed)
p1 = subprocess.Popen(args=' '.join([*extra, '"', __dir, "python3", "test.py", '"']), shell=True)
p2 = subprocess.Popen(args=' '.join([*extra, '"', __dir, "python3", "status.py", '"']), shell=True)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping...")
    p1.send_signal(signal.SIGTERM)
    p2.send_signal(signal.SIGTERM)