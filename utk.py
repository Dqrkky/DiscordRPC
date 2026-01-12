import uptime_kuma_api
import dotenv

credentials = dotenv.dotenv_values(
    dotenv_path=".env"
)

with uptime_kuma_api.UptimeKumaApi(
        url="http://192.168.31.101:3001",
        timeout=60,
        ssl_verify=False
    ) as api:
        api.login(
            username=credentials.get("UPTIME_KUMA_USERNAME", None),
            password=credentials.get("UPTIME_KUMA_PASSWORD", None)
        )