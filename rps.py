import struct
import json
import threading
import win32pipe
import win32file
import time

FAKE_PIPE = r'\\.\pipe\discord-ipc-0'  # fake pipe for Discord to connect
BUFSIZE = 65536

# Thread-safe list of client pipes
clients = []
clients_lock = threading.Lock()

# Activity-related events we want to log
ACTIVITY_EVENTS = ["SET_ACTIVITY", "ACTIVITY_JOIN", "ACTIVITY_SPECTATE"]

def find_real_pipe():
    """Find the first available real Discord pipe (ipc-0 → ipc-9)."""
    for i in range(10):
        name = fr'\\.\pipe\discord-ipc-{i}'
        try:
            handle = win32file.CreateFile(
                name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0, None,
                win32file.OPEN_EXISTING,
                0, None
            )
            return handle, name
        except Exception:
            continue
    raise RuntimeError("No real Discord pipe found!")

def log_activity(prefix, payload):
    """Pretty-print activity events."""
    evt = payload.get("evt") or payload.get("cmd") or "UNKNOWN"
    if evt in ACTIVITY_EVENTS:
        print(f"[{prefix}] {evt}:\n{json.dumps(payload, indent=2)}\n")

def forward(src_pipe, dst_pipe, prefix):
    """Bidirectional forwarding between pipes with optional logging."""
    while True:
        try:
            hr, header = win32file.ReadFile(src_pipe, 8)
            if hr != 0 or not header:
                break
            op, length = struct.unpack('<II', header)
            hr, payload_bytes = win32file.ReadFile(src_pipe, length)
            if hr != 0:
                break

            # Log only activity events
            try:
                payload = json.loads(payload_bytes.decode('utf-8'))
                log_activity(prefix, payload)
            except Exception:
                pass

            # Forward unchanged
            packet = struct.pack('<II', op, len(payload_bytes)) + payload_bytes
            win32file.WriteFile(dst_pipe, packet)
        except Exception:
            break

def handle_client(fake_pipe_handle):
    """Handle one Discord client, forwarding to real Discord pipe."""
    try:
        real_pipe, real_name = find_real_pipe()
        print(f"[proxy] Forwarding to real pipe: {real_name}")
    except RuntimeError as e:
        print(f"[proxy] {e}")
        win32file.CloseHandle(fake_pipe_handle)
        return

    # Start bidirectional forwarding
    threading.Thread(target=forward, args=(fake_pipe_handle, real_pipe, "C->S"), daemon=True).start()
    threading.Thread(target=forward, args=(real_pipe, fake_pipe_handle, "S->C"), daemon=True).start()

def main():
    print(f"Sniffer listening on {FAKE_PIPE}...")
    while True:
        fake_pipe = win32pipe.CreateNamedPipe(
            FAKE_PIPE,
            win32pipe.PIPE_ACCESS_DUPLEX,
            win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
            4, BUFSIZE, BUFSIZE, 0, None
        )
        print("[proxy] Waiting for client...")
        try:
            win32pipe.ConnectNamedPipe(fake_pipe, None)
        except Exception:
            win32file.CloseHandle(fake_pipe)
            continue

        print("[proxy] Client connected, starting handler thread")
        threading.Thread(target=handle_client, args=(fake_pipe,), daemon=True).start()

if __name__ == "__main__":
    main()
