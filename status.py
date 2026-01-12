import requests
import time
import asyncio
import uptime_kuma_api
import dotenv
import json
import DiscordRPC
import status_queue

rpc = status_queue.Rpc()
credentials = dotenv.dotenv_values(
    dotenv_path=".env"
)
rp = DiscordRPC.client.DiscordRPCClient(auto_discover=True)

async def change_status(details=None, state=None):
    """Push status updates into the Rpc queue instead of sending directly."""
    payload = {
        "details": details,
        "state": state,
    }
    rpc.write(item=json.dumps(obj=payload))

last_seismic_time = 0  # Timestamp of last test
async def check_seismic_events(rss :requests.Session):
    global last_seismic_time
    now = time.time()
    time_until = 60 * 30
    elapsed = now - last_seismic_time
    if elapsed < time_until:
        remaining_minutes = (time_until - elapsed) / 60
        await change_status(
            details="[SeismicPortal.eu]: Error",
            state=f'Ran ({elapsed / 60:.2f} minutes ago) will re-run (in {remaining_minutes:.2f} minutes)'
        )
        await asyncio.sleep(wait_time)
        return
    last_seismic_time = now  # Update the last run time
    try:
        req = rss.request(
            **{
                "method": "get",
                "url": "https://www.seismicportal.eu/fdsnws/event/1/query",
                "params": {
                    "format": "json",  # Request the data in JSON format
                    "limit": 1,  # Limit number of events returned
                    "minlatitude": 34.8,  # Southern Greece
                    "maxlatitude": 41.8,  # Northern Greece
                    "minlongitude": 19.3,  # Western Greece
                    "maxlongitude": 28.3,  # Eastern Greece
                },
                "timeout": 30,
            }
        ) 
        req.raise_for_status()
        data = req.json().get("features", [])[0]
        data = data.get("properties", {})
        source_catalog = data.get("source_catalog", "")
        place = data.get("flynn_region", "Unknown location")
        mag = data.get("mag", "?")
        depth = data.get("depth", "?")
        lat = data.get("lat", None)  # noqa: F841
        lon = data.get("lon", None)  # noqa: F841
        time_str = data.get("time", "").split("T")[1].split(".")[0]
        lastupdate_str = data.get("lastupdate", "").split("T")[1].split(".")[0]
        quake_msg = f"[🌍 Quake {source_catalog}]: M{mag} D{depth} {place} (at {time_str}) (lastupdate {lastupdate_str}) UTC"
        await change_status(
            details="[SeismicPortal.eu]",
            state=quake_msg
        )
    except Exception as e:
        await change_status(
            details="[SeismicPortal.eu]",
            state=f"Ops ... Something happened (ErrorType: {type(e).__name__}) re-trying (in {wait_time} seconds) :/"
        )
    await asyncio.sleep(wait_time)

def getstatus(api :uptime_kuma_api.UptimeKumaApi, monitor :dict[str, str]):
    try:
        status = api.get_monitor_status(monitor_id=monitor["id"])
        return status.name
    except Exception:
        return None

def printJs0n(js0n :dict=None):
    print(json.dumps(
        obj=js0n,
        indent=4
    ))

async def new_check_for_updates():
    try:
        with uptime_kuma_api.UptimeKumaApi(
            url="http://undentified.ddns.net:84",
            timeout=60,
            ssl_verify=False
        ) as api:
            api.login(
                username=credentials.get("UPTIME_KUMA_USERNAME", None),
                password=credentials.get("UPTIME_KUMA_PASSWORD", None)
            )
            status_pages = [api.get_status_page(slug=status_page["slug"]) for status_page in api.get_status_pages()]
    except Exception as e:
        await change_status(
            details="[UpTimeKuma.org 🤍]",
            state=f"""Ops ... Something happened (ErrorType: {type(e).__name__}) re-trying (in {wait_time} seconds) :/""",
        )
        await asyncio.sleep(wait_time)
        return
    messages = [
        {
            "details": f'[UpTimeKuma.org 🤍]: {page["title"]}/{monitorFolder["name"]}',
            "state": f'{monitor["name"]} is {status}' if status != None else f'Couldnt retrieve status (in monitor: {monitor["name"]})'  # noqa: E711
        }
        for page in status_pages
        for monitorFolder in page["publicGroupList"]
        for monitor in monitorFolder["monitorList"]
        for status in [getstatus(api=api, monitor=monitor)]
    ]
    for message in messages:
        await change_status(
            details=message["details"],
            state=message["state"]
        )
        await asyncio.sleep(15)
    await asyncio.sleep(wait_time - 15)

async def worker():
    """Continuously read from Rpc queue and send to localhost update endpoint."""
    while True:
        if not rpc.is_empty():
            item = rpc.read()
            try:
                print(rp.update(data=json.loads(s=item)))
            except Exception as e:
                print(f"Failed to send update: {e}")
        await asyncio.sleep(1)


async def main():
    print("📡 Listening for updates...")
    with requests.Session() as rss:
        rss.headers.update(
            {
                "priority": "u=0, i",
                "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            }
        )
        if debug == True:  # noqa: E712
            await change_status(
                details="(Not always) Afk",
                state="Updating Rpc :/",
            )
        while debug == False:  # noqa: E712
            # check seismic first
            await check_seismic_events(rss)
            await new_check_for_updates()
            await change_status(
                details="(Not always) Afk",
                state=f"Waiting for next check (in {wait_time} seconds) :/",
            )
            await asyncio.sleep(wait_time)


wait_time = 60
debug = False  # Set to False to disable debug mode

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(worker())
    loop.run_until_complete(main())