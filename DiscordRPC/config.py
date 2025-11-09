import os
import time

DEFAULT_CONFIG = {
    "client_id": "1114910688872247350",
    "host": "0.0.0.0",
    "port": 8000,
    "update_interval": 30,
}

DEFAULT_PRESENCE = {
    "activity_type": 3, # Watching
    "details": "(Not always) Afk",
    "state": "welp ...",
    "buttons": [
        {
            "label": "Website",
            "url": "https://dqrkky.pages.dev"
        },
        {
            "label": "GitHub",
            "url": "https://github.com/Dqrkky"
        }
    ],
    "start": time.time(),
    "large_text": "Inspired by Nyx, Greek goddess of night.",
    "large_image": "https://cdn.discordapp.com/app-icons/1114910688872247350/368679aef46cf4bd182114fceb2708ad.png"
}

def get_config(overrides: dict = None) -> dict:
    cfg = DEFAULT_CONFIG.copy()
    cfg["client_id"] = os.getenv("DISCORD_RPC_CLIENT_ID", cfg["client_id"])
    cfg["host"] = os.getenv("DISCORD_RPC_HOST", cfg["host"])
    cfg["port"] = int(os.getenv("DISCORD_RPC_PORT", cfg["port"]))
    cfg["update_interval"] = int(os.getenv("DISCORD_RPC_UPDATE_INTERVAL", cfg["update_interval"]))
    if overrides:
        cfg.update(overrides)
    return cfg
