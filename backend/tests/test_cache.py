import pytest
import time
from backend.app.metadata.cache import MetadataCache
from backend.app.core.paths import CACHE_DIR

def test_cache_set_and_get(tmp_path):
    cache = MetadataCache(ttl_days=1)
    cache.dirs["crossref"] = tmp_path / "crossref"
    cache.dirs["crossref"].mkdir(parents=True, exist_ok=True)

    query = "10.1145/test.doi"
    data = {"title": "Test Paper", "year": 2022}

    # Cache should be empty initially
    assert cache.get("crossref", query) is None

    # Set cache
    cache.set("crossref", query, data, http_status=200)

    # Retrieve cache
    cached = cache.get("crossref", query)
    assert cached is not None
    assert cached["title"] == "Test Paper"
    assert cached["year"] == 2022

def test_cache_expiration(tmp_path):
    # TTL of 0 seconds
    cache = MetadataCache(ttl_days=0)
    cache.ttl_seconds = 0.01
    cache.dirs["crossref"] = tmp_path / "crossref"
    cache.dirs["crossref"].mkdir(parents=True, exist_ok=True)

    query = "10.1145/expired.doi"
    cache.set("crossref", query, {"title": "Old"}, http_status=200)
    time.sleep(0.05)

    # Expired
    assert cache.get("crossref", query) is None
