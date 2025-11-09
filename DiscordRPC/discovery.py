import os
import json
import socket
from pathlib import Path
from . import config, utils

BROADCAST_PORT = 51423
DISCOVERY_SIGNATURE = b"discord_rpc_discover_v1"

def find_from_env():
    host = os.getenv("DISCORD_RPC_HOST")
    port = os.getenv("DISCORD_RPC_PORT")
    if host and port:
        utils.log({
            "service": "Discovery",
            "source": "environment",
            "status": "found",
            "host": host,
            "port": int(port),
            "message": "Found RPC configuration in environment variables"
        })
        return {"host": host, "port": int(port)}
    return None

def find_from_file():
    paths = [
        Path(".env"),
        Path("discord_rpc_config.json"),
        Path.home() / ".discord_rpc.json"
    ]
    for p in paths:
        if p.exists():
            try:
                if p.suffix == ".json":
                    data = json.loads(p.read_text())
                    host = data.get("host", None)
                    port = data.get("port", None)
                    if host and port:
                        utils.log({
                            "service": "Discovery",
                            "source": str(p),
                            "status": "found",
                            "host": host,
                            "port": port,
                            "message": f"Loaded RPC configuration from {p.name}"
                        })
                        return {"host": host, "port": port}
                else:
                    lines = p.read_text().splitlines()
                    env = dict(
                        line.split("=", 1)
                        for line in lines
                        if "=" in line
                    )
                    if "DISCORD_RPC_HOST" in env and \
                    "DISCORD_RPC_PORT" in env:
                        utils.log({
                            "service": "Discovery",
                            "source": str(p),
                            "status": "found",
                            "host": host,
                            "port": port,
                            "message": f"Loaded RPC configuration from {p.name}"
                        })
                        return {
                            "host": env["DISCORD_RPC_HOST"],
                            "port": int(env["DISCORD_RPC_PORT"])
                        }
            except Exception as e:
                utils.log({
                    "service": "Discovery",
                    "source": str(p),
                    "status": "error",
                    "error": str(e),
                    "message": f"Failed to read {p.name}"
                })
                continue
    return None

def broadcast_discover(timeout=2):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(timeout)
    utils.log({
        "service": "Discovery",
        "status": "broadcasting",
        "protocol": "UDP",
        "port": BROADCAST_PORT,
        "message": "Sending discovery broadcast"
    })
    try:
        sock.sendto(DISCOVERY_SIGNATURE, ("255.255.255.255", BROADCAST_PORT))
        data, addr = sock.recvfrom(1024)
        if data.startswith(DISCOVERY_SIGNATURE):
            payload = json.loads(data[len(DISCOVERY_SIGNATURE):].decode())
            utils.log({
                "service": "Discovery",
                "status": "found",
                "host": addr[0],
                "port": payload["port"],
                "message": f"Discovered RPC server at {addr[0]}:{payload['port']}"
            })
            return {
                "host": addr[0],
                "port": payload["port"]
            }
    except socket.timeout:
        utils.log({
            "service": "Discovery",
            "status": "timeout",
            "message": "No RPC server found via broadcast"
        })
        return None
    except Exception as e:
        utils.log({
            "service": "Discovery",
            "status": "error",
            "error": str(e),
            "message": "Error during broadcast discovery"
        })
        return None
    finally:
        sock.close()

def discover_server():
    for finder in (find_from_env, find_from_file, broadcast_discover):
        result = finder()
        if result:
            return result
    cfg = config.get_config()
    utils.log({
        "service": "Discovery",
        "status": "default",
        "host": cfg["host"],
        "port": cfg["port"],
        "message": "Using default configuration (no discovery found)"
    })
    return {
        "host": cfg["host"],
        "port": cfg["port"]
    }
