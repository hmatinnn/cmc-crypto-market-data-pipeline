from operator import index
import os
import sys
import json
import certifi
from dotenv import load_dotenv
import pandas as pd
import time
from datetime import datetime, timezone


pd.set_option("display.max_columns", None)
    
JOB_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(JOB_DIR)

INPUT_DIR = os.path.join(PROJECT_DIR, "api_responses")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "api_responses_csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)


class CryptoDataParser:

    CONFIG = {
        "categories": {
            "path": os.path.join(INPUT_DIR, "v1_cryptocurrency_categories.json"),
            "use_values": False,
            "explode": [],
            "renormalize": False,
        },
        "listing_latest": {
            "path": os.path.join(INPUT_DIR, "v1_cryptocurrency_listings_latest.json"),
            "use_values": False,
            "explode": [],
            "renormalize": False,
            "exclude_cols": [
                "tags",
                "name",
                "symbol",
                "slug",
                "platform",
                "platform_id",
                "platform_name",
                "platform_symbol",
                "platform_slug",
                "platform_token_address",
                "quote_USD_price",
                "quote_USD_volume_24h",
                "quote_USD_cex_volume_24h",
                "quote_USD_dex_volume_24h",
                "quote_USD_volume_change_24h",
                "quote_USD_percent_change_1h",
                "quote_USD_percent_change_24h",
                "quote_USD_percent_change_7d",
                "quote_USD_percent_change_30d",
                "quote_USD_percent_change_60d",
                "quote_USD_percent_change_90d",
                "quote_USD_market_cap",
                "quote_USD_market_cap_dominance",
                "quote_USD_fully_diluted_market_cap",
                "quote_USD_tvl",
                "quote_USD_last_updated",
            ],
        },
        "map": {
            "path": os.path.join(INPUT_DIR, "v1_cryptocurrency_map.json"),
            "use_values": False,
            "explode": [],
            "renormalize": False,
            "exclude_cols": [
                "platform",
                "platform_id",
                "platform_name",
                "platform_symbol",
                "platform_slug",
                "platform_token_address",
                "rank",
            ],
        },
        "info": {
            "path": os.path.join(INPUT_DIR, "v2_cryptocurrency_info.json"),
            "use_values": True,
            "explode": [],
            "renormalize": False,
            "exclude_cols": [
                "name",
                "symbol",
                "slug",
                "subreddit",
                "notice",
                "tags",
                "tag-names",
                "platform",
                "tag-groups",
                "twitter_username",
                "contract_address",
                "is_hidden",
                "urls_website",
                "urls_twitter",
                "urls_message_board",
                "urls_chat",
                "urls_facebook",
                "urls_explorer",
                "urls_reddit",
                "urls_technical_doc",
                "urls_source_code",
                "urls_announcement",
                "self_reported_tags",
                "platform_id",
                "platform_name",
                "platform_symbol",
                "platform_slug",
                "platform_token_address",
                "infinite_supply",
                "date_added",
                "self_reported_circulating_supply",
                "self_reported_market_cap",
            ],
        },
        "quotes": {
            "path": os.path.join(INPUT_DIR, "v3_cryptocurrency_quotes_latest.json"),
            "use_values": False,
            "explode": ["quote"],
            "renormalize": True,
            "exclude_cols": [
                "tags",
                "circulating_supply",
                "total_supply",
                "max_supply",
                "date_added",
                "num_market_pairs",
                "cmc_rank",
                "last_updated",
                "tvl_ratio",
                "self_reported_circulating_supply",
                "self_reported_market_cap",
                "minted_market_cap",
                "infinite_supply",
                "platform",
                "platform_id",
                "platform_slug",
                "platform_name",
                "platform_symbol",
                "platform_token_address",
                "is_active",
            ],
        },
        "category_details": {
            "path": os.path.join(INPUT_DIR, "v1_cryptocurrency_category_details.json"),
            "use_values": False,
            "explode": ["coins"],
            "renormalize": True,
            "exclude_cols": [
                "coins_quote_USD_price",
                "coins_quote_USD_tvl",
                "coins_quote_USD_volume_24h",
                "coins_quote_USD_volume_change_24h",
                "coins_quote_USD_percent_change_1h",
                "coins_quote_USD_percent_change_24h",
                "coins_quote_USD_percent_change_7d",
                "coins_quote_USD_percent_change_30d",
                "coins_quote_USD_percent_change_60d",
                "coins_quote_USD_percent_change_90d",
                "coins_quote_USD_market_cap",
                "coins_quote_USD_market_cap_dominance",
                "coins_quote_USD_fully_diluted_market_cap",
                "coins_quote_USD_last_updated",
                "coins_name",
                "coins_symbol",
                "coins_slug",
                "coins_tags",
                "coins_num_market_pairs",
                "coins_date_added",
                "coins_max_supply",
                "coins_circulating_supply",
                "coins_total_supply",
                "coins_self_reported_circulating_supply",
                "coins_self_reported_market_cap",
                "coins_is_active",
                "coins_infinite_supply",
                "coins_is_fiat",
                "coins_minted_market_cap",
                "coins_cmc_rank",
                "coins_platform",
                "coins_tvl_ratio",
                "coins_last_updated",
                "coins_platform_id",
                "coins_platform_name",
                "coins_platform_symbol",
                "coins_platform_slug",
                "coins_platform_token_address",
            ],
        },
    }


    GROUPS = {
        "daily": ["listing_latest", "quotes"],
        "weekly": ["categories", "category_details"],
        "monthly": ["map", "info"],
    }

    def __init__(self, config: dict = None):
        self.config = config or self.CONFIG
        self.dfs: dict[str, pd.DataFrame] = {}

    def _load_raw(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        if "data" not in payload:
            raise ValueError(f"No 'data' key found in {path}")
        return payload["data"]

    def _parse_one(self, name: str, cfg: dict) -> pd.DataFrame:
        raw_data = self._load_raw(cfg["path"])

        df = pd.json_normalize(
            raw_data.values() if cfg["use_values"] else raw_data, sep="_"
        )

        for col in cfg.get("explode", []):
            if col in df.columns:
                df = df.explode(col)

        if cfg.get("renormalize"):
            df = pd.json_normalize(df.to_dict(orient="records"), sep="_")

        df = df.drop(columns=cfg.get("exclude_cols", []), errors="ignore")
        return df

    def parse_all(self, only: list = None) -> dict[str, pd.DataFrame]:
        """only: optional list of dataset names (CONFIG keys) to restrict
        parsing to -- e.g. GROUPS["daily"]. Defaults to every dataset."""
        items = self.config.items()
        if only is not None:
            items = [(name, self.config[name]) for name in only if name in self.config]

        for name, cfg in items:
            try:
                self.dfs[name] = self._parse_one(name, cfg)
                print(
                    f"Parsed '{name}': {len(self.dfs[name])} rows, "
                    f"{len(self.dfs[name].columns)} cols"
                )
            except FileNotFoundError:
                print(f"Skipping '{name}': file not found at {cfg['path']}")
            except Exception as e:
                print(f"Failed to parse '{name}': {e}")
        return self.dfs

    def get(self, name: str) -> pd.DataFrame:
        if name not in self.dfs:
            raise KeyError(f"'{name}' not parsed yet - call parse_all() first.")
        return self.dfs[name]


    KEY_COLUMNS = {
        "categories": ["id"],
        "category_details": ["id", "coins_id"],
        "listing_latest": ["id"],
        "quotes": ["id"],
    }

    @staticmethod
    def _same_as_last_snapshot(new_df: pd.DataFrame, existing_df: pd.DataFrame, key_cols: list) -> bool:
        """True if new_df (freshly parsed, no inserted_at yet) is identical,
        row for row, to the most recent inserted_at snapshot in existing_df."""
        if existing_df.empty or "inserted_at" not in existing_df.columns:
            return False
        if not all(k in existing_df.columns for k in key_cols):
            return False

        last_ts = existing_df["inserted_at"].max()
        last_snapshot = existing_df[existing_df["inserted_at"] == last_ts].drop(columns=["inserted_at"])

        if set(last_snapshot.columns) != set(new_df.columns) or len(last_snapshot) != len(new_df):
            return False

        cols = list(new_df.columns)
        last_sorted = last_snapshot[cols].sort_values(key_cols).reset_index(drop=True)
        new_sorted = new_df[cols].sort_values(key_cols).reset_index(drop=True)
        return last_sorted.astype(str).equals(new_sorted.astype(str))

    def save_to_csv(self, OUTPUT_DIR: str = "silver_csv", index: bool = False):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        HISTORICAL_TABLES = {"categories", "category_details", "listing_latest", "quotes"}

        run_ts = datetime.now()
        run_ts_str = run_ts.strftime("%Y-%m-%d %H:%M:%S")
        today_str = run_ts.strftime("%Y-%m-%d")

        for name, df in self.dfs.items():
            filepath = os.path.join(OUTPUT_DIR, f"{name}.csv")

            if name in HISTORICAL_TABLES:
                if os.path.exists(filepath):
                    existing_df = pd.read_csv(filepath)

                    if "inserted_at" in existing_df.columns:
                        key_cols = self.KEY_COLUMNS.get(name, [])
                        if key_cols and self._same_as_last_snapshot(df, existing_df, key_cols):
                            print(
                                f"'{name}' unchanged since last snapshot -- skipping "
                                f"append, no new '{today_str}' row written."
                            )
                            continue

                        existing_dates = pd.to_datetime(existing_df["inserted_at"]).dt.strftime("%Y-%m-%d")
                        existing_df = existing_df[existing_dates != today_str]
                        df["inserted_at"] = run_ts_str
                        df = pd.concat([existing_df, df], ignore_index=True)
                    else:
                        # Old file predates the inserted_at/accumulation logic for this table.
                        # Treat it as a one-time migration: stamp it with today's run and keep it,
                        # so we don't silently discard historical rows.
                        print(
                            f"'{filepath}' has no 'inserted_at' column (pre-accumulation file). "
                            f"Backfilling with run timestamp and merging."
                        )
                        df["inserted_at"] = run_ts_str
                        existing_df["inserted_at"] = run_ts_str
                        df = pd.concat([existing_df, df], ignore_index=True)
                else:
                    df["inserted_at"] = run_ts_str

                df.to_csv(filepath, index=index, encoding="utf-8")
                print(f"Saved '{name}' -> {filepath} ({len(df)} rows total, historical)")

            else:
                df.to_csv(filepath, index=index, encoding="utf-8")
                print(f"Saved '{name}' -> {filepath} ({len(df)} rows, overwritten)")

def main(group: str = None):
    """group: "daily" | "weekly" | "monthly" | None. Restricts parsing to
    that cadence's datasets (CryptoDataParser.GROUPS). None parses everything."""
    parser = CryptoDataParser()
    only = CryptoDataParser.GROUPS.get(group) if group else None
    if group and only is None:
        raise ValueError(f"Unknown group {group!r}; expected one of {list(CryptoDataParser.GROUPS)}")

    dfs = parser.parse_all(only=only)

    if not dfs:
        raise RuntimeError("No datasets were parsed - check Bronze JSON files exist.")

    parser.save_to_csv(OUTPUT_DIR=OUTPUT_DIR)
    return {name: len(df) for name, df in dfs.items()}


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)