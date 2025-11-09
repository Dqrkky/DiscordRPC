import requests
import time
import uptime_kuma_api
import asyncio
import status_queue
import dotenv

wait_time = 60
last_seismic_time = 0  # Timestamp of last test

rpc = status_queue.Rpc()
credentials = dotenv.dotenv_values(
    dotenv_path=".env"
)


async def change_status(details=None, state=None):
    """Push status updates into the Rpc queue instead of sending directly."""
    payload = {
        "details": details,
        "state": state,
    }
    await rpc.write(item=payload)


async def check_seismic_events(rss: requests.Session):
    global last_seismic_time
    now = time.time()
    elapsed = now - last_seismic_time

    if elapsed < 3600:
        remaining_minutes = (3600 - elapsed) / 60
        await change_status(
            details="[SeismicPortal.eu]: Error",
            state=f'Ran ({elapsed / 60:.2f} minutes ago), will re-run in {remaining_minutes:.2f} minutes'
        )
        await asyncio.sleep(wait_time)
        return

    last_seismic_time = now
    try:
        req = rss.get(
            "https://www.seismicportal.eu/fdsnws/event/1/query",
            params={
                "format": "json",
                "limit": 1,
                "minlatitude": 34.8,
                "maxlatitude": 41.8,
                "minlongitude": 19.3,
                "maxlongitude": 28.3,
            },
            timeout=30,
        )
        req.raise_for_status()

        data = req.json().get("features", [])[0].get("properties", {})
        quake_msg = (
            f"[🌍 Quake {data.get('source_catalog', '')}]: "
            f"M{data.get('mag', '?')} D{data.get('depth', '?')} {data.get('flynn_region', 'Unknown')} "
            f"(at {data.get('time', '').split('T')[1].split('.')[0]}) "
            f"(lastupdate {data.get('lastupdate', '').split('T')[1].split('.')[0]}) UTC"
        )
        await change_status(details="[SeismicPortal.eu]", state=quake_msg)
    except Exception as e:
        await change_status(
            details="[SeismicPortal.eu]",
            state=f"Ops ... ErrorType: {type(e).__name__}, retrying in {wait_time}s :/"
        )

    await asyncio.sleep(wait_time)


def getstatus(api: uptime_kuma_api.UptimeKumaApi, monitor: dict[str, str]):
    try:
        status = api.get_monitor_status(monitor["id"])
        return status.name
    except Exception:
        return None

async def new_check_for_updates():
    try:
        with uptime_kuma_api.UptimeKumaApi(
            url="http://localhost:3001",
            timeout=60,
            ssl_verify=False
        ) as api:
            api.login(
                username=credentials.get("UPTIME_KUMA_USERNAME", None),
                password=credentials.get("UPTIME_KUMA_PASSWORD", None)
            )
            status_pages = [
                api.get_status_page(status_page["slug"])
                for status_page in api.get_status_pages()
            ]
    except Exception as e:
        await change_status(
            details="[UpTimeKuma.org 🤍]",
            state=f"Ops ... ErrorType: {type(e).__name__}('{', '.join(e.args)}'), retrying in {wait_time}s :/"
        )
        await asyncio.sleep(wait_time)
        return

    for page in status_pages:
        for monitorFolder in page["publicGroupList"]:
            for monitor in monitorFolder["monitorList"]:
                status = getstatus(api=api, monitor=monitor)
                message = {
                    "details": f"[UpTimeKuma.org 🤍]: {page['title']}/{monitorFolder['name']}",
                    "state": f"{monitor['name']} is {status}" if status else f"Ops ... Error in monitor: {monitor['name']}"
                }
                await change_status(**message)
                await asyncio.sleep(15)

    await asyncio.sleep(wait_time - 15)

async def worker():
    """Continuously read from Rpc queue and send to localhost update endpoint."""
    async with requests.Session() as session:
        while True:
            if not rpc.is_empty():
                item = await rpc.read()
                try:
                    resp = session.post(
                        "http://localhost:8000/update",
                        headers={"Content-Type": "application/json"},
                        json=item,
                        timeout=10
                    )
                    print(resp.json())
                except Exception as e:
                    print(f"Failed to send update: {e}")
            await asyncio.sleep(1)


async def main():
    print("📡 Listening for updates...")
    with requests.Session() as rss:
        rss.headers.update({
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        while True:
            await check_seismic_events(rss)
            await new_check_for_updates()
            await change_status(details="(Not always) Afk", state=f"Waiting {wait_time}s :/")
            await asyncio.sleep(wait_time)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(worker())
    loop.run_until_complete(main())