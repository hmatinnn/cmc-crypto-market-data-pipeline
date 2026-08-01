import os
import json
import ssl
import sys
import argparse
import urllib.parse
import urllib.request
import certifi
from dotenv import load_dotenv
import pandas as pd
import time

pd.set_option('display.max_columns', None)

load_dotenv()
API_KEY = os.getenv("X_CMC_PRO_API_KEY")
BASE_URL = "https://pro-api.coinmarketcap.com"
JOB_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(JOB_DIR)

INPUT_DIR = os.path.join(PROJECT_DIR, "api_responses")  
OUTPUT_DIR = os.path.join(PROJECT_DIR, "api_responses")

os.makedirs(OUTPUT_DIR, exist_ok=True)


class CoinMarketCapClient:

    def __init__(self, api_key: str, base_url: str):
        self.base_url = base_url
        self.headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': api_key,
        }
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())


    
    RATE_LIMIT_RESET_SECONDS = 65
    MAX_RATE_LIMIT_RETRIES = 5

    def _get(self, endpoint: str, params: dict = None) -> dict:
        query_string = urllib.parse.urlencode(params) if params else ""
        url = f"{self.base_url}{endpoint}?{query_string}"

        for attempt in range(1, self.MAX_RATE_LIMIT_RETRIES + 1):
            req = urllib.request.Request(url, headers=self.headers, method='GET')
            try:
                with urllib.request.urlopen(req, context=self.ssl_context) as response:
                    if response.getcode() == 200:
                        return json.loads(response.read().decode('utf-8'))
            except urllib.error.HTTPError as e:
                error_msg = e.read().decode('utf-8', errors='ignore')
                if e.code == 429:

                   
                    retry_after = e.headers.get("Retry-After") if e.headers else None
                    try:
                        wait_seconds = float(retry_after) if retry_after else self.RATE_LIMIT_RESET_SECONDS
                    except ValueError:
                        wait_seconds = self.RATE_LIMIT_RESET_SECONDS

                    if attempt < self.MAX_RATE_LIMIT_RETRIES:
                        print(
                            f"HTTP Error (429) on {endpoint}: {error_msg} -- "
                            f"retrying in {wait_seconds:.0f}s (attempt {attempt}/{self.MAX_RATE_LIMIT_RETRIES})"
                        )
                        time.sleep(wait_seconds)
                        continue
                    print(
                        f"HTTP Error (429) on {endpoint}: {error_msg} -- "
                        f"giving up after {self.MAX_RATE_LIMIT_RETRIES} attempts"
                    )
                else:
                    print(f"HTTP Error ({e.code}) on {endpoint}: {error_msg}")
            except Exception as e:
                print(f"Unexpected error on {endpoint}: {str(e)}")
            return None
        return None

    def save_to_json(self, data: dict, filename: str):
        if not data:
            print(f"Skipping save: No data available for {filename}")
            return
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved data to: {filepath}")

    def get_crypto_map(self, limit: int = 500) -> dict:
        print(f"Fetching cryptocurrency map (limit: {limit})...")

   
        params = {"listing_status": "active", "start": 1, "limit": limit, "sort": "cmc_rank"}
        return self._get("/v1/cryptocurrency/map", params)

    def get_latest_listings(self, limit: int = 500) -> dict:
        print(f"Fetching top {limit} listings...")
        params = {"listing_status": "active", "start": 1, "limit": limit, "convert": "USD"}
        return self._get("/v1/cryptocurrency/listings/latest", params)

    def get_categories(self, limit: int = 500) -> dict:
        print(f"Fetching coin categories (limit: {limit})...")
        params = {"start": 1, "limit": limit}
        return self._get("/v1/cryptocurrency/categories", params)

    def get_category(self, category_id: str) -> dict:
        print(f"Fetching category details: {category_id}")
        return self._get("/v1/cryptocurrency/category", {"id": category_id})

    def get_crypto_info(self, crypto_ids: list) -> dict:
        id_string = ",".join([str(cid) for cid in crypto_ids])
        return self._get("/v2/cryptocurrency/info", {"id": id_string})


def _client() -> CoinMarketCapClient:
    if not API_KEY:
        raise RuntimeError("X_CMC_PRO_API_KEY not found in environment variables.")
    return CoinMarketCapClient(API_KEY, BASE_URL)


def _load_ids_from(*filenames) -> list:
    """Read crypto ids from whichever previously-saved response file is available.
    Used by tasks (info/quotes) that depend on map or listings having already run. 
    """
    for fname in filenames:
        path = os.path.join(INPUT_DIR, fname)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            data = payload.get("data")
            if data:
                return [coin["id"] for coin in data]
    raise RuntimeError(
        f"Could not find crypto ids in any of: {filenames}. "
        "Make sure the map or listings task ran first."
    )



def fetch_map(limit: int = 500):
    cmc = _client()
    data = cmc.get_crypto_map(limit=limit)
    if not data:
        raise RuntimeError("Failed to fetch /v1/cryptocurrency/map")
    cmc.save_to_json(data, "v1_cryptocurrency_map.json")


def fetch_listings(limit: int = 500):
    cmc = _client()
    data = cmc.get_latest_listings(limit=limit)
    if not data:
        raise RuntimeError("Failed to fetch /v1/cryptocurrency/listings/latest")
    cmc.save_to_json(data, "v1_cryptocurrency_listings_latest.json")


def fetch_categories(limit: int = 500):
    cmc = _client()
    data = cmc.get_categories(limit=limit)
    if not data:
        raise RuntimeError("Failed to fetch /v1/cryptocurrency/categories")
    cmc.save_to_json(data, "v1_cryptocurrency_categories.json")


def fetch_category_details():
    """Depends on fetch_categories having run first (reads its saved output)."""
    cmc = _client()
    cat_path = os.path.join(INPUT_DIR, "v1_cryptocurrency_categories.json")
    if not os.path.exists(cat_path):
        raise RuntimeError("v1_cryptocurrency_categories.json not found. Run fetch_categories first.")

    with open(cat_path, "r", encoding="utf-8") as f:
        categories_data = json.load(f)

    all_categories = []
    for category in categories_data.get("data", []):
        category_data = cmc.get_category(category["id"])
        if category_data and "data" in category_data:
            all_categories.append(category_data["data"])
        time.sleep(1)

    if all_categories:
        cmc.save_to_json({"data": all_categories}, "v1_cryptocurrency_category_details.json")
    else:
        raise RuntimeError("No category details fetched.")


def fetch_info(chunk_size: int = 500):
    """Depends on fetch_listings or fetch_map having run first."""
    cmc = _client()
    crypto_ids = _load_ids_from(
        "v1_cryptocurrency_listings_latest.json",
        "v1_cryptocurrency_map.json",
    )

    all_info_combined = {}
    for i in range(0, len(crypto_ids), chunk_size):
        chunk = crypto_ids[i:i + chunk_size]
        print(f"Fetching Info batch {i // chunk_size + 1} ({len(chunk)} IDs)...")
        batch_data = cmc.get_crypto_info(chunk)
        if batch_data and "data" in batch_data:
            all_info_combined.update(batch_data["data"])

    if not all_info_combined:
        raise RuntimeError("Failed to fetch any /v2/cryptocurrency/info data")

    payload = {"data": all_info_combined, "status": {"error_code": 0, "notice": "Combined via script"}}
    cmc.save_to_json(payload, "v2_cryptocurrency_info.json")




USD_QUOTE_CURRENCY_ID = 2781


def fetch_quotes(limit: int = 500):



    listings_path = os.path.join(INPUT_DIR, "v1_cryptocurrency_listings_latest.json")
    if not os.path.exists(listings_path):
        raise RuntimeError(
            f"{listings_path} not found. fetch_quotes derives its data from "
            "fetch_listings's output -- run fetch_listings first."
        )

    with open(listings_path, "r", encoding="utf-8") as f:
        listings_data = json.load(f)

    coins = listings_data.get("data", [])[:limit]

    quotes_data = []
    for coin in coins:
        usd = (coin.get("quote") or {}).get("USD")
        if not usd:
            continue
        quotes_data.append({
            "id": coin.get("id"),
            "name": coin.get("name"),
            "symbol": coin.get("symbol"),
            "slug": coin.get("slug"),
            "is_fiat": 0,
            "quote": [
                {
                    "id": USD_QUOTE_CURRENCY_ID,
                    "symbol": "USD",
                    "price": usd.get("price"),
                    "volume_24h": usd.get("volume_24h"),
                    "volume_change_24h": usd.get("volume_change_24h"),
                    "cex_volume_24h": usd.get("cex_volume_24h"),
                    "dex_volume_24h": usd.get("dex_volume_24h"),
                    "percent_change_1h": usd.get("percent_change_1h"),
                    "percent_change_24h": usd.get("percent_change_24h"),
                    "percent_change_7d": usd.get("percent_change_7d"),
                    "percent_change_30d": usd.get("percent_change_30d"),
                    "percent_change_60d": usd.get("percent_change_60d"),
                    "percent_change_90d": usd.get("percent_change_90d"),
                    "market_cap": usd.get("market_cap"),
                    "market_cap_dominance": usd.get("market_cap_dominance"),
                    "fully_diluted_market_cap": usd.get("fully_diluted_market_cap"),
                   
                    "minted_market_cap": coin.get("minted_market_cap"),
                    "tvl": usd.get("tvl"),
                    "last_updated": usd.get("last_updated"),
                }
            ],
        })

    if not quotes_data:
        raise RuntimeError("No quotes could be derived from listings_latest data.")

    cmc = _client()
    payload = {
        "data": quotes_data,
        "status": {"error_code": 0, "notice": "Derived from listings/latest -- no separate API call"},
    }
    cmc.save_to_json(payload, "v3_cryptocurrency_quotes_latest.json")


TASKS = {
    "map": fetch_map,
    "listings": fetch_listings,
    "categories": fetch_categories,
    "category_details": fetch_category_details,
    "info": fetch_info,
    "quotes": fetch_quotes,
}


def main():
    parser = argparse.ArgumentParser(description="Fetch a single CMC endpoint.")
    parser.add_argument("task", choices=TASKS.keys(), help="Which endpoint to pull")
    args = parser.parse_args()
    TASKS[args.task]()


if __name__ == "__main__":
    main()