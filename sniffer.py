import struct
import json
import threading
import win32pipe
import win32file
import time

FAKE_PIPE = r'\\.\pipe\discord-ipc-0'
REAL_PIPE = r'\\.\pipe\discord-ipc-1'  # change if discord-ipc-1 is in use
BUFSIZE = 65536

def log_packet(prefix, data_bytes):
    try:
        payload = json.loads(data_bytes.decode('utf-8'))
        print(f"[{prefix}] {json.dumps(payload, indent=2)}")
    except Exception:
        print(f"[{prefix}] {data_bytes}")

def forward(src_pipe, dst_pipe, prefix):
    while True:
        try:
            hr, header = win32file.ReadFile(src_pipe, 2024)
            
            # Log the message
            log_packet(prefix, header)

            win32file.WriteFile(dst_pipe, header)
        except Exception:
            break

def handle_client(fake_pipe_handle):
    # Connect to the real Discord pipe
    try:
        real_pipe = win32file.CreateFile(
            REAL_PIPE,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None,
            win32file.OPEN_EXISTING,
            0, None
        )
    except Exception as e:
        print(f"[proxy] Failed to open real pipe: {e}")
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
        print("[proxy] Client connected, starting handler")
        threading.Thread(target=handle_client, args=(fake_pipe,), daemon=True).start()

if __name__ == "__main__":
    main()
