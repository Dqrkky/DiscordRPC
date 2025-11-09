import requests
import time
import uptime_kuma_api
import dotenv
import json
import DiscordRPC

credentials = dotenv.dotenv_values(
    dotenv_path=".env"
)
rp = DiscordRPC.client.DiscordRPCClient(auto_discover=True)

def change_status(details=None, state=None):
    print(json.dumps(
        obj=rp.update(
            data={
                **({"details": details} if details else {}),
                "state": state,
            }
        ),
        indent=4
    ))

last_seismic_time = 0  # Timestamp of last test
def check_seismic_events(rss :requests.Session):
    global last_seismic_time
    now = time.time()
    elapsed = now - last_seismic_time
    if elapsed < 3600:
        remaining_minutes = (3600 - elapsed) / 60
        change_status(
            details="[SeismicPortal.eu]: Error",
            state=f'Ran ({elapsed / 60:.2f} minutes ago) will re-run (in {remaining_minutes:.2f} minutes)'
        )
        time.sleep(wait_time)
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
        change_status(
            details="[SeismicPortal.eu]",
            state=quake_msg
        )
        time.sleep(wait_time)
        return
    except Exception as e:
        change_status(
            details="[SeismicPortal.eu]",
            state=f"Ops ... Something happened (ErrorType: {type(e).__name__}) re-trying (in {wait_time} seconds) :/"
        )
        time.sleep(wait_time)
        return

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

def new_check_for_updates():
    try:
        with uptime_kuma_api.UptimeKumaApi(
            url="http://192.168.31.101:3001",
            timeout=60,
            ssl_verify=False
        ) as api:
            api.login(
                username=credentials.get("UPTIME_KUMA_USERNAME", None),
                password=credentials.get("UPTIME_KUMA_PASSWORD", None)
            )
            status_pages = [api.get_status_page(slug=status_page["slug"]) for status_page in api.get_status_pages()]
    except Exception as e:
        change_status(
            details="[UpTimeKuma.org 🤍]",
            state=f"""Ops ... Something happened (ErrorType: {type(e).__name__}) re-trying (in {wait_time} seconds) :/""",
        )
        time.sleep(wait_time)
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
        change_status(
            details=message["details"],
            state=message["state"]
        )
        time.sleep(15)
    time.sleep(wait_time-15)

wait_time = 60
debug = False  # Set to False to disable debug mode
# Run the RSS listener every 60 seconds
if __name__ == "__main__":  # noqa: E712
    print("📡 Listening for UptimeRobot RSS feed updates...")
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
            change_status(
                details="(Not always) Afk",
                state="Updating Rpc :/",
            )
        while debug == False:  # noqa: E712
            # check seismic first
            check_seismic_events(rss)
            new_check_for_updates()
            change_status(
                details="(Not always) Afk",
                state=f"Waiting for next check (in {wait_time} seconds) :/",
            )
            time.sleep(wait_time)