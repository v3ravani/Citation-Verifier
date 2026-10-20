import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Any
from backend.app.core.paths import CROSSREF_CACHE_DIR, SEMANTIC_SCHOLAR_CACHE_DIR
from backend.app.core.config import settings
from backend.app.core.logging_config import logger

class MetadataCache:
    def __init__(self, ttl_days: int = settings.CACHE_TTL_DAYS):
        self.ttl_seconds = ttl_days * 86400
        self.dirs = {
            "crossref": CROSSREF_CACHE_DIR,
            "semantic_scholar": SEMANTIC_SCHOLAR_CACHE_DIR,
        }
        for d in self.dirs.values():
            d.mkdir(parents=True, exist_ok=True)

    def _get_dir(self, source: str) -> Path:
        if source not in self.dirs:
            d = CACHE_DIR / source
            d.mkdir(parents=True, exist_ok=True)
            self.dirs[source] = d
        return self.dirs[source]

    def _hash_key(self, key: str) -> str:
        clean = " ".join(key.lower().strip().split())
        return hashlib.sha256(clean.encode("utf-8")).hexdigest()

    def get(self, source: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached response if valid and not expired.
        """
        cache_dir = self._get_dir(source)

        h = self._hash_key(key)
        cache_file = cache_dir / f"{h}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                entry = json.load(f)

            cached_time = entry.get("timestamp", 0)
            if time.time() - cached_time > self.ttl_seconds:
                logger.info(f"Cache expired for {source} query: {key[:30]}...")
                return None

            return entry.get("data")
        except Exception as e:
            logger.warning(f"Corrupted cache file {cache_file.name}: {e}. Removing.")
            try:
                cache_file.unlink()
            except OSError:
                pass
            return None

    def set(self, source: str, key: str, data: Any, http_status: int = 200) -> None:
        """
        Stores an API response in the local cache.
        """
        cache_dir = self._get_dir(source)

        h = self._hash_key(key)
        cache_file = cache_dir / f"{h}.json"

        entry = {
            "source": source,
            "query": key,
            "timestamp": time.time(),
            "http_status": http_status,
            "data": data,
        }

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to write cache for {source}: {e}")

metadata_cache = MetadataCache()
