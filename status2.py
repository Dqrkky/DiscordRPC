import requests
import time
import uptime_kuma_api
import speedtest
import feedparser

def change_status(details=None, state=None):
    config = {
        "method": "POST",
        "url": "http://localhost:8100/update",
        "headers": {
            "Content-Type": "application/json"
        },
        "json": {
            **({"details": details} if details else {}),
            "state": state
        }
    }
    try:
        print(requests.request(**config).json())
    except Exception:
        pass

def nasa_feed():
    data = feedparser.parse(
        url_file_stream_or_string=requests.request(
            **{
                "method": "get",
                "url": "https://earthobservatory.nasa.gov/feeds/natural-hazards.rss"
            }
        ).text
    )
    data = data.get("entries", [])[0]
    title :str = data.get("title", None)
    summary :str = data.get("summary", None)
    published_parsed :time.struct_time = data.get("published_parsed", None)
    change_status(
        details=f'[NASA.gov]: {title} | Published : {published_parsed.tm_wday+1}/{published_parsed.tm_mon}/{published_parsed.tm_year} {published_parsed.tm_hour}:{published_parsed.tm_min}:{published_parsed.tm_sec}',
        state=summary
    )
    time.sleep(wait_time)

last_speedtest_time = 0  # Timestamp of last test
def runspeedtest():
    global last_speedtest_time
    now = time.time()
    elapsed = now - last_speedtest_time
    if elapsed < 3600:
        remaining_minutes = (3600 - elapsed) / 60
        change_status(
            details='[SpeedTest.net]: Error',
            state=f'Ran ({elapsed / 60:.2f} minutes ago) will re-run (in {remaining_minutes:.2f} minutes)'
        )
        time.sleep(wait_time)
        return
    last_speedtest_time = now  # Update the last run time
    test = speedtest.Speedtest(
        secure=True
    )
    test.get_best_server()
    test.download()
    test.upload()
    data = test.results.dict()
    server = data.get("server", {})
    for messages in [
        f'[Ping]: {round(data.get("ping", None))} ms',
        f'[Download]: {round(data.get("download", None) / 1_000_000)} Mbps',
        f'[Upload]: {round(data.get("upload", None) / 1_000_000)} Mbps',
    ]:
        change_status(
            details=f'[SpeedTest.net]: {server.get("sponsor", None)} | {server.get("name", None)}, {server.get("country", None)}',
            state=messages
        )
        time.sleep(10)

wait_time = 60
while True:
    # runspeedtest()
    # time.sleep(wait_time)
    #new_check_for_updates()
    change_status(
        details="(Not always) Afk",
        state=f"Waiting for next check (in {wait_time} seconds) :/",
    )
    # time.sleep(wait_time)