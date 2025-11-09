import asyncio
import json
import socket
from aiohttp import web
import pypresence
from . import config, discovery, utils

class DiscordRPCServer:
    def __init__(self, overrides=None):
        self.config = config.get_config(overrides)
        self.presence_data = config.DEFAULT_PRESENCE.copy()
        self.RPC = pypresence.AioPresence(self.config["client_id"])
        self.app = web.Application()
        self._setup_routes()
    def _setup_routes(self):
        self.app.add_routes([
            web.post("/update", self.update_rpc),
            web.get("/status", self.status)
        ])
    async def _update_presence(self):
        await self.RPC.update(**self.presence_data)
    async def update_rpc(self, request):
        try:
            new_data = await request.json()
            self.presence_data.update(new_data)
            await self._update_presence()
            return web.json_response({"status": "updated", "new_data": self.presence_data})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    async def status(self, _):
        return web.json_response({
            "status": "running",
            "config": self.config,
            "presence": self.presence_data
        })
    async def _broadcast_responder(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", discovery.BROADCAST_PORT))
        sock.setblocking(False)
        utils.log({
            "status": "listening",
            "service": "Discovery Responder",
            "protocol": "UDP",
            "port": discovery.BROADCAST_PORT,
            "message": "Discovery responder active"
        })
        loop = asyncio.get_event_loop()
        while True:
            try:
                data, addr = await loop.sock_recvfrom(sock, 1024)
                if data.startswith(discovery.DISCOVERY_SIGNATURE):
                    payload = json.dumps({"port": self.config["port"]}).encode()
                    response = discovery.DISCOVERY_SIGNATURE + payload
                    await loop.sock_sendto(sock, response, addr)
            except Exception:
                await asyncio.sleep(0.1)
    async def _start_server(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.config["host"], self.config["port"])
        await site.start()
        utils.log({
            "status": "running",
            "service": "RPC Server",
            "url": f"http://{self.config['host']}:{self.config['port']}",
            "message": "RPC server started successfully"
        })
        asyncio.create_task(self._broadcast_responder())
    async def run(self):
        await self.RPC.connect()
        await self._update_presence()
        asyncio.create_task(self._start_server())
        try:
            while True:
                await asyncio.sleep(self.config["update_interval"])
        except asyncio.CancelledError:
            pass
        finally:
            utils.log({
                "status": "stopping",
                "service": "RPC Server",
                "message": "Shutting down RPC"
            })
            await self.RPC.close()

def run_server(**overrides):
    server = DiscordRPCServer(overrides)
    asyncio.run(server.run())
