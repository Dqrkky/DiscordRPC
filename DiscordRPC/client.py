import requests
from . import discovery, utils

class DiscordRPCClient:
    def __init__(self, host=None, port=None, auto_discover=True):
        if auto_discover and not host:
            info = discovery.discover_server()
            host, port = info["host"], info["port"]
        self.base_url = f"http://{host}:{port}"
        utils.log({
            "status": "connected",
            "service": "RPC Client",
            "url": self.base_url,
            "message": "Connected to RPC server successfully"
        })
    def getJson(self, config :dict=None):
        if config == None or isinstance(config, dict) == False:  # noqa: E711, E712
            return
        res = requests.request(**config)
        res.raise_for_status()
        return res.json()
    def update(self, data :dict=None):
        if data == None or isinstance(data, dict) == False:  # noqa: E711, E712
            return
        config = {
            "method": "post",
            "url": f"{self.base_url}/update",
            "json": data
        }
        return self.getJson(config=config)
    def status(self):
        config = {
            "method": "get",
            "url": f"{self.base_url}/status",
        }
        return self.getJson(config=config)
        