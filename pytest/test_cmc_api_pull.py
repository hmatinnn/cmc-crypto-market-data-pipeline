
import io
import json
import urllib.error

import pytest

import cmc_api_pull as mod



class _FakeResponse:

    def __init__(self, payload: dict, code: int = 200):
        self._payload = payload
        self._code = code

    def getcode(self):
        return self._code

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


@pytest.fixture
def client():
    return mod.CoinMarketCapClient(api_key="test-key", base_url="https://example.com")


@pytest.fixture(autouse=True)
def isolate_dirs(tmp_path, monkeypatch):
    """Point INPUT_DIR/OUTPUT_DIR at a throwaway directory for every test."""
    monkeypatch.setattr(mod, "INPUT_DIR", str(tmp_path))
    monkeypatch.setattr(mod, "OUTPUT_DIR", str(tmp_path))
    return tmp_path




def test_get_returns_parsed_json_on_200(client, monkeypatch):
    payload = {"data": {"id": 1}}
    monkeypatch.setattr(
        mod.urllib.request, "urlopen", lambda req, context=None: _FakeResponse(payload)
    )
    result = client._get("/v1/cryptocurrency/map", {"limit": 10})
    assert result == payload


def test_get_builds_url_with_query_string(client, monkeypatch):
    captured = {}

    def fake_urlopen(req, context=None):
        captured["url"] = req.full_url
        return _FakeResponse({"ok": True})

    monkeypatch.setattr(mod.urllib.request, "urlopen", fake_urlopen)
    client._get("/v1/cryptocurrency/map", {"start": 1, "limit": 500})
    assert captured["url"] == "https://example.com/v1/cryptocurrency/map?start=1&limit=500"


def test_get_returns_none_when_status_not_200(client, monkeypatch):
    monkeypatch.setattr(
        mod.urllib.request, "urlopen", lambda req, context=None: _FakeResponse({}, code=204)
    )
    assert client._get("/v1/cryptocurrency/map") is None


def test_get_returns_none_on_http_error(client, monkeypatch, capsys):
    def raise_http_error(req, context=None):
        raise urllib.error.HTTPError(
            url="https://example.com", code=429, msg="Too Many Requests",
            hdrs=None, fp=io.BytesIO(b'{"error": "rate limited"}'),
        )

    monkeypatch.setattr(mod.urllib.request, "urlopen", raise_http_error)
    result = client._get("/v1/cryptocurrency/map")
    assert result is None
    assert "429" in capsys.readouterr().out


def test_get_returns_none_on_unexpected_exception(client, monkeypatch, capsys):
    def raise_generic(req, context=None):
        raise ValueError("boom")

    monkeypatch.setattr(mod.urllib.request, "urlopen", raise_generic)
    result = client._get("/v1/cryptocurrency/map")
    assert result is None
    assert "boom" in capsys.readouterr().out




def test_save_to_json_writes_file(client, tmp_path):
    client.save_to_json({"data": [1, 2, 3]}, "out.json")
    written = tmp_path / "out.json"
    assert written.exists()
    assert json.loads(written.read_text(encoding="utf-8")) == {"data": [1, 2, 3]}


def test_save_to_json_skips_when_data_falsy(client, tmp_path, capsys):
    client.save_to_json(None, "out.json")
    assert not (tmp_path / "out.json").exists()
    assert "Skipping save" in capsys.readouterr().out


def test_save_to_json_skips_when_data_empty_dict(client, tmp_path):
    client.save_to_json({}, "out.json")
    assert not (tmp_path / "out.json").exists()




def test_get_crypto_map_params(client, monkeypatch):
    captured = {}
    monkeypatch.setattr(client, "_get", lambda ep, params=None: captured.update(endpoint=ep, params=params) or {})
    client.get_crypto_map(limit=250)
    assert captured["endpoint"] == "/v1/cryptocurrency/map"
    assert captured["params"] == {
        "listing_status": "active", "start": 1, "limit": 250, "sort": "cmc_rank",
    }


def test_get_latest_listings_params(client, monkeypatch):
    captured = {}
    monkeypatch.setattr(client, "_get", lambda ep, params=None: captured.update(endpoint=ep, params=params) or {})
    client.get_latest_listings(limit=100)
    assert captured["endpoint"] == "/v1/cryptocurrency/listings/latest"
    assert captured["params"] == {"listing_status": "active", "start": 1, "limit": 100, "convert": "USD"}


def test_get_categories_params(client, monkeypatch):
    captured = {}
    monkeypatch.setattr(client, "_get", lambda ep, params=None: captured.update(endpoint=ep, params=params) or {})
    client.get_categories(limit=50)
    assert captured["endpoint"] == "/v1/cryptocurrency/categories"
    assert captured["params"] == {"start": 1, "limit": 50}


def test_get_category_params(client, monkeypatch):
    captured = {}
    monkeypatch.setattr(client, "_get", lambda ep, params=None: captured.update(endpoint=ep, params=params) or {})
    client.get_category("defi")
    assert captured["endpoint"] == "/v1/cryptocurrency/category"
    assert captured["params"] == {"id": "defi"}


def test_get_crypto_info_joins_ids(client, monkeypatch):
    captured = {}
    monkeypatch.setattr(client, "_get", lambda ep, params=None: captured.update(endpoint=ep, params=params) or {})
    client.get_crypto_info([1, 2, 3])
    assert captured["endpoint"] == "/v2/cryptocurrency/info"
    assert captured["params"] == {"id": "1,2,3"}


def test_client_raises_without_api_key(monkeypatch):
    monkeypatch.setattr(mod, "API_KEY", "")
    with pytest.raises(RuntimeError, match="X_CMC_PRO_API_KEY"):
        mod._client()


def test_client_builds_instance_with_api_key(monkeypatch):
    monkeypatch.setattr(mod, "API_KEY", "abc123")
    c = mod._client()
    assert isinstance(c, mod.CoinMarketCapClient)
    assert c.headers["X-CMC_PRO_API_KEY"] == "abc123"



def test_load_ids_from_reads_first_available_file(tmp_path):
    (tmp_path / "listings.json").write_text(
        json.dumps({"data": [{"id": 1}, {"id": 2}]}), encoding="utf-8"
    )
    ids = mod._load_ids_from("listings.json", "map.json")
    assert ids == [1, 2]


def test_load_ids_from_falls_back_to_second_file(tmp_path):
    (tmp_path / "map.json").write_text(
        json.dumps({"data": [{"id": 5}]}), encoding="utf-8"
    )
    ids = mod._load_ids_from("listings.json", "map.json")
    assert ids == [5]


def test_load_ids_from_raises_when_no_file_found(tmp_path):
    with pytest.raises(RuntimeError, match="Could not find crypto ids"):
        mod._load_ids_from("listings.json", "map.json")


def test_load_ids_from_raises_when_file_has_no_data(tmp_path):
    (tmp_path / "listings.json").write_text(json.dumps({"data": []}), encoding="utf-8")
    with pytest.raises(RuntimeError):
        mod._load_ids_from("listings.json")



class _StubClient:
    """Stand-in for CoinMarketCapClient used to drive fetch_* functions."""

    def __init__(self, responses=None, category_responses=None):
        self.responses = responses or {}
        self.category_responses = category_responses or {}
        self.saved = []

    def get_crypto_map(self, limit=500):
        return self.responses.get("map")

    def get_latest_listings(self, limit=500):
        return self.responses.get("listings")

    def get_categories(self, limit=500):
        return self.responses.get("categories")

    def get_category(self, category_id):
        return self.category_responses.get(category_id)

    def get_crypto_info(self, crypto_ids):
        return self.responses.get("info")

    def save_to_json(self, data, filename):
        self.saved.append((filename, data))


def test_fetch_map_saves_data(monkeypatch):
    stub = _StubClient(responses={"map": {"data": [{"id": 1}]}})
    monkeypatch.setattr(mod, "_client", lambda: stub)
    mod.fetch_map(limit=10)
    assert stub.saved == [("v1_cryptocurrency_map.json", {"data": [{"id": 1}]})]


def test_fetch_map_raises_when_empty(monkeypatch):
    stub = _StubClient(responses={"map": None})
    monkeypatch.setattr(mod, "_client", lambda: stub)
    with pytest.raises(RuntimeError, match="Failed to fetch /v1/cryptocurrency/map"):
        mod.fetch_map()


def test_fetch_listings_saves_data(monkeypatch):
    stub = _StubClient(responses={"listings": {"data": [{"id": 2}]}})
    monkeypatch.setattr(mod, "_client", lambda: stub)
    mod.fetch_listings(limit=5)
    assert stub.saved == [("v1_cryptocurrency_listings_latest.json", {"data": [{"id": 2}]})]


def test_fetch_listings_raises_when_empty(monkeypatch):
    stub = _StubClient(responses={"listings": None})
    monkeypatch.setattr(mod, "_client", lambda: stub)
    with pytest.raises(RuntimeError, match="Failed to fetch /v1/cryptocurrency/listings/latest"):
        mod.fetch_listings()


def test_fetch_categories_saves_data(monkeypatch):
    stub = _StubClient(responses={"categories": {"data": [{"id": "defi"}]}})
    monkeypatch.setattr(mod, "_client", lambda: stub)
    mod.fetch_categories(limit=5)
    assert stub.saved == [("v1_cryptocurrency_categories.json", {"data": [{"id": "defi"}]})]


def test_fetch_categories_raises_when_empty(monkeypatch):
    stub = _StubClient(responses={"categories": None})
    monkeypatch.setattr(mod, "_client", lambda: stub)
    with pytest.raises(RuntimeError, match="Failed to fetch /v1/cryptocurrency/categories"):
        mod.fetch_categories()


def test_fetch_category_details_raises_without_categories_file(monkeypatch):
    monkeypatch.setattr(mod, "_client", lambda: _StubClient())
    with pytest.raises(RuntimeError, match="categories.json not found"):
        mod.fetch_category_details()


def test_fetch_category_details_aggregates_and_saves(tmp_path, monkeypatch):
    (tmp_path / "v1_cryptocurrency_categories.json").write_text(
        json.dumps({"data": [{"id": "defi"}, {"id": "nft"}]}), encoding="utf-8"
    )
    stub = _StubClient(category_responses={
        "defi": {"data": {"id": "defi", "num_tokens": 10}},
        "nft": {"data": {"id": "nft", "num_tokens": 5}},
    })
    monkeypatch.setattr(mod, "_client", lambda: stub)
    monkeypatch.setattr(mod.time, "sleep", lambda *_: None)

    mod.fetch_category_details()

    assert len(stub.saved) == 1
    filename, payload = stub.saved[0]
    assert filename == "v1_cryptocurrency_category_details.json"
    assert payload == {"data": [
        {"id": "defi", "num_tokens": 10},
        {"id": "nft", "num_tokens": 5},
    ]}


def test_fetch_category_details_raises_when_nothing_fetched(tmp_path, monkeypatch):
    (tmp_path / "v1_cryptocurrency_categories.json").write_text(
        json.dumps({"data": [{"id": "defi"}]}), encoding="utf-8"
    )
    stub = _StubClient(category_responses={})  # get_category returns None for everything
    monkeypatch.setattr(mod, "_client", lambda: stub)
    monkeypatch.setattr(mod.time, "sleep", lambda *_: None)

    with pytest.raises(RuntimeError, match="No category details fetched"):
        mod.fetch_category_details()


def test_fetch_info_combines_chunks(tmp_path, monkeypatch):
    (tmp_path / "v1_cryptocurrency_listings_latest.json").write_text(
        json.dumps({"data": [{"id": i} for i in range(1, 6)]}), encoding="utf-8"
    )
    stub = _StubClient(responses={"info": {"data": {"1": {"name": "coin"}}}})
    monkeypatch.setattr(mod, "_client", lambda: stub)

    mod.fetch_info(chunk_size=2)

    assert len(stub.saved) == 1
    filename, payload = stub.saved[0]
    assert filename == "v2_cryptocurrency_info.json"
    # 3 chunks of size 2 => get_crypto_info called 3 times, each merging {"1": ...}
    assert payload["data"] == {"1": {"name": "coin"}}
    assert payload["status"]["error_code"] == 0


def test_fetch_info_raises_when_nothing_fetched(tmp_path, monkeypatch):
    (tmp_path / "v1_cryptocurrency_listings_latest.json").write_text(
        json.dumps({"data": [{"id": 1}]}), encoding="utf-8"
    )
    stub = _StubClient(responses={"info": None})
    monkeypatch.setattr(mod, "_client", lambda: stub)
    with pytest.raises(RuntimeError, match="Failed to fetch any /v2/cryptocurrency/info data"):
        mod.fetch_info()


def test_fetch_info_raises_when_no_source_file(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_client", lambda: _StubClient())
    with pytest.raises(RuntimeError, match="Could not find crypto ids"):
        mod.fetch_info()


def _coin_with_quote(coin_id, **usd_overrides):
    usd = {
        "price": 100.0,
        "volume_24h": 1.0,
        "volume_change_24h": 2.0,
        "cex_volume_24h": 3.0,
        "dex_volume_24h": 4.0,
        "percent_change_1h": 5.0,
        "percent_change_24h": 6.0,
        "percent_change_7d": 7.0,
        "percent_change_30d": 8.0,
        "percent_change_60d": 9.0,
        "percent_change_90d": 10.0,
        "market_cap": 11.0,
        "market_cap_dominance": 12.0,
        "fully_diluted_market_cap": 13.0,
        "tvl": None,
        "last_updated": "2026-07-22T00:00:00.000Z",
    }
    usd.update(usd_overrides)
    return {
        "id": coin_id,
        "name": f"Coin {coin_id}",
        "symbol": f"C{coin_id}",
        "slug": f"coin-{coin_id}",
        "minted_market_cap": 999.0,
        "quote": {"USD": usd},
    }


def test_fetch_quotes_derives_from_listings_without_client_call(tmp_path, monkeypatch):
    (tmp_path / "v1_cryptocurrency_listings_latest.json").write_text(
        json.dumps({"data": [_coin_with_quote(1)]}), encoding="utf-8"
    )
    stub = _StubClient()
    monkeypatch.setattr(mod, "_client", lambda: stub)

    mod.fetch_quotes()

    assert len(stub.saved) == 1
    filename, payload = stub.saved[0]
    assert filename == "v3_cryptocurrency_quotes_latest.json"
    coin = payload["data"][0]
    assert coin["id"] == 1
    assert coin["is_fiat"] == 0
    q = coin["quote"][0]
    assert q["id"] == mod.USD_QUOTE_CURRENCY_ID
    assert q["symbol"] == "USD"
    assert q["price"] == 100.0
    assert q["market_cap"] == 11.0
    # sourced from the coin's top-level minted_market_cap, since
    # listings/latest doesn't nest it under quote.USD
    assert q["minted_market_cap"] == 999.0


def test_fetch_quotes_truncates_to_limit(tmp_path, monkeypatch):
    (tmp_path / "v1_cryptocurrency_listings_latest.json").write_text(
        json.dumps({"data": [_coin_with_quote(i) for i in range(1, 11)]}), encoding="utf-8"
    )
    stub = _StubClient()
    monkeypatch.setattr(mod, "_client", lambda: stub)

    mod.fetch_quotes(limit=3)

    _, payload = stub.saved[0]
    assert [c["id"] for c in payload["data"]] == [1, 2, 3]


def test_fetch_quotes_skips_coins_without_usd_quote(tmp_path, monkeypatch):
    coin_without_quote = {"id": 99, "name": "NoQuote", "symbol": "NQ", "slug": "no-quote"}
    (tmp_path / "v1_cryptocurrency_listings_latest.json").write_text(
        json.dumps({"data": [_coin_with_quote(1), coin_without_quote]}), encoding="utf-8"
    )
    stub = _StubClient()
    monkeypatch.setattr(mod, "_client", lambda: stub)

    mod.fetch_quotes()

    _, payload = stub.saved[0]
    assert [c["id"] for c in payload["data"]] == [1]


def test_fetch_quotes_raises_when_no_listings_file(tmp_path, monkeypatch):
    stub = _StubClient()
    monkeypatch.setattr(mod, "_client", lambda: stub)
    with pytest.raises(RuntimeError, match="fetch_listings first"):
        mod.fetch_quotes()


def test_fetch_quotes_raises_when_nothing_derived(tmp_path, monkeypatch):
    (tmp_path / "v1_cryptocurrency_listings_latest.json").write_text(
        json.dumps({"data": [{"id": 1, "name": "NoQuote"}]}), encoding="utf-8"
    )
    stub = _StubClient()
    monkeypatch.setattr(mod, "_client", lambda: stub)
    with pytest.raises(RuntimeError, match="No quotes could be derived"):
        mod.fetch_quotes()




def test_tasks_dict_maps_all_expected_names():
    assert set(mod.TASKS.keys()) == {
        "map", "listings", "categories", "category_details", "info", "quotes",
    }


def test_main_dispatches_to_correct_task(monkeypatch):
    called = {}
    monkeypatch.setattr(mod, "TASKS", {"map": lambda: called.setdefault("ran", "map")})
    monkeypatch.setattr(mod.sys, "argv", ["cmc_api_pull.py", "map"])
    mod.main()
    assert called["ran"] == "map"


def test_main_rejects_unknown_task(monkeypatch, capsys):
    monkeypatch.setattr(mod.sys, "argv", ["cmc_api_pull.py", "bogus"])
    with pytest.raises(SystemExit):
        mod.main()
