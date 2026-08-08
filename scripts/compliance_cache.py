"""File-backed JSON compliance result cache.
Key: ("check_type", "target_id")
TTL: 1 hour
Path: outputs/.cache/compliance_cache.json"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

DEFAULT_CACHE_PATH = Path(__file__).resolve().parents[1] / "outputs" / ".cache" / "compliance_cache.json"
TTL_SECONDS = 60 * 60  # 1 hour


def _read_cache( path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"entries": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "entries" not in data or not isinstance(data["entries"], dict):
            return {"entries": {}}
        return data
    except Exception:
        return {"entries": {}}


def _write_cache(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def _cache_key(check_type: str, target_id: str) -> str:
    return f"{check_type}\0{target_id}"


def get_cached(check_type: str, target_id: str, path: Path = DEFAULT_CACHE_PATH) -> dict[str, Any] | None:
    cache = _read_cache(path)
    key = _cache_key(check_type, target_id)
    entry = cache.get("entries", {}).get(key)
    if not entry:
        return None
    timestamp = entry.get("timestamp", 0)
    if time.time() - timestamp > TTL_SECONDS:
        return None
    return entry


def set_cached(check_type: str, target_id: str, value: dict[str, Any], path: Path = DEFAULT_CACHE_PATH) -> None:
    cache = _read_cache(path)
    cache["entries"][_cache_key(check_type, target_id)] = {
        "timestamp": time.time(),
        "value": value,
        "check_type": check_type,
        "target_id": target_id,
    }
    _write_cache(path, cache)


def entries_stored(path: Path = DEFAULT_CACHE_PATH) -> int:
    cache = _read_cache(path)
    return len(cache.get("entries", {}))


def cleanup(path: Path = DEFAULT_CACHE_PATH) -> int:
    cache = _read_cache(path)
    now = time.time()
    entries = cache.get("entries", {})
    expired = [k for k, v in entries.items() if now - v.get("timestamp", 0) > TTL_SECONDS]
    for k in expired:
        entries.pop(k, None)
    _write_cache(path, cache)
    return len(expired)


def _prune_entries(cache_path: Path = DEFAULT_CACHE_PATH) -> None:
    cleanup(cache_path)


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="compliance cache manager")
    parser.add_argument("--cleanup", action="store_true", help="remove expired entries")
    args = parser.parse_args(argv)
    if args.cleanup:
        removed = cleanup()
        print(f"Cache file: {DEFAULT_CACHE_PATH}")
        print(f"Entries stored: {entries_stored()}")
        print(f"Expired entries removed: {removed}")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
