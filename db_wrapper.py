class CloudFlareD1:
    def __init__(
            self,
            getaway :str="https://api.cloudflare.com/client/v4"
        ):
        self.getaway = getaway if getaway != None and isinstance(getaway, str) else None  # noqa: E711
    def delete(
        self,
        databaseId :str=None
    ):
        config = {
            "method": "delete",
            "url": f"{self.getaway}/accounts/$ACCOUNT_ID/d1/database/$DATABASE_ID",
            "headers": {
                "X-Auth-Email: $CLOUDFLARE_EMAIL",
                "X-Auth-Key: $CLOUDFLARE_API_KEY"
            }
        }