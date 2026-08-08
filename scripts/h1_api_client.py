"""Verified HackerOne API client using urllib instead of requests."""
import base64
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import winreg
from collections.abc import Generator
from pathlib import Path
from typing import Any

BASE_URL = "https://api.hackerone.com"
IDENTIFIER = "zqm-computing"
REQUIRED_SECRET = "HACKERONE_API_TOKEN"
TOKEN_CACHE_PATH = Path.home() / ".local" / "share" / "hermes" / "h1_token"


def _cache_path() -> Path:
    return TOKEN_CACHE_PATH


def _persist_token(tok: str) -> None:
    try:
        TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_CACHE_PATH.write_text(tok, encoding="utf-8")
    except Exception:
        pass


def _load_persisted_token() -> str:
    try:
        if TOKEN_CACHE_PATH.exists():
            return TOKEN_CACHE_PATH.read_text(encoding="utf-8").strip()
    except Exception:
        pass
    return ""


def _token_from_env() -> str:
    return os.environ.get(REQUIRED_SECRET) or ""


def _primary_token() -> str:
    tok = _token_from_env()
    if tok:
        _persist_token(tok)
        return tok
    return _token_from_registry()


def _cached_token() -> str:
    return _load_persisted_token()


def _token() -> str:
    tok = _token_from_env()
    if tok:
        return tok
    return _token_from_registry()


def _token_from_registry() -> str:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
            tok, _ = winreg.QueryValueEx(k, REQUIRED_SECRET)
        if tok and isinstance(tok, str):
            _persist_token(tok)
            return tok
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return ""


def token_source() -> str:
    if os.environ.get(REQUIRED_SECRET):
        return "env"
    if _load_persisted_token():
        return "cache"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
            try:
                tok, _ = winreg.QueryValueEx(k, REQUIRED_SECRET)
            except FileNotFoundError:
                tok = ""
        if tok and isinstance(tok, str) and tok.strip():
            return "registry"
    except Exception:
        pass
    return "none"


def effective_token_source_and_token() -> tuple[str, str]:
    tok = os.environ.get(REQUIRED_SECRET)
    if tok:
        return "env", tok
    tok = _load_persisted_token()
    if tok:
        return "cache", tok
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
            try:
                tok, _ = winreg.QueryValueEx(k, REQUIRED_SECRET)
            except FileNotFoundError:
                tok = ""
        if tok and isinstance(tok, str) and tok.strip():
            return "registry", tok.strip()
    except Exception:
        pass
    return "none", ""


def _auth_headers_for(token: str) -> dict[str, str]:
    if not token:
        raise RuntimeError(f"Missing required secret: {REQUIRED_SECRET}")
    if token.startswith(("h1_", "H1_")) or ":" in token:
        basic = base64.b64encode(f"{IDENTIFIER}:{token}".encode("ascii")).decode("ascii")
        return {
            "Authorization": f"Basic {basic}",
            "Accept": "application/json",
        }
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }


def auth_headers() -> dict[str, str]:
    tok = _token()
    if not tok:
        raise RuntimeError(f"Missing required secret: {REQUIRED_SECRET}")
    return _auth_headers_for(tok)


def _check_response(body: bytes) -> None:
    try:
        payload = json.loads(body.decode("utf-8", errors="ignore"))
    except Exception:  
        return
    errs = payload.get("errors") or []
    if not errs:
        return
    status = str(errs[0].get("status", ""))
    if status in {"401", "403"}:
        raise RuntimeError(
            f"HackerOne auth failed ({status}): {errs[0].get('detail', '')}"
        )


def _url(path: str, params: dict[str, Any] | None = None) -> str:
    url = f"{BASE_URL}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    return url


def _get_json(path: str, params: dict[str, Any] | None = None, *, source_meta: bool = False) -> dict[str, Any]:
    auth_failed = False
    last_err = None
    last_source = None
    for provider, label in ((_primary_token, "env"), (_cached_token, "cache")):
        tok = provider()
        if not tok:
            continue
        req = urllib.request.Request(
            _url(path, params), headers=_auth_headers_for(tok), method="GET"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read()
                _check_response(body)
                result = json.loads(body.decode("utf-8"))
                if source_meta:
                    result["__auth_source"] = label
                    result["__auth_token_prefix"] = tok[:8]
                return result
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="ignore")
            last_err = RuntimeError(f"HTTP {e.code} for {path}: {detail}")
            payload = {}
            try:
                payload = json.loads(detail)
            except Exception:
                pass
            errs = payload.get("errors") or []
            status = str((errs[0].get("status") or "") if errs else "")
            if status in {"401", "403"}:
                auth_failed = True
                last_source = label
                continue
            raise last_err from e
        except Exception as exc:
            last_err = exc

    if auth_failed:
        raise RuntimeError(
            f"HackerOne auth failed for all sources after trying primary/last={last_source}: {path}"
        ) from last_err
    if last_err:
        raise last_err
    raise RuntimeError("No HackerOne token available from env/cache")


def _extract_retry_after(error: urllib.error.HTTPError) -> int:
    try:
        payload = json.loads(error.read().decode("utf-8", errors="ignore"))
        detail = ((payload.get("errors") or [{}])[0]).get("detail", "")
        m = re.search(r"(\d+)\s*(?:seconds|second|s)", detail, re.IGNORECASE)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return 1


def iter_all(
    path: str,
    params: dict[str, Any] | None = None,
    delay: float = 0.35,
) -> Generator[dict[str, Any], None, None]:
    page = 1
    while True:
        payload = _get_json(
            path, {**(params or {}), "page[number]": page, "page[size]": 100}
        )
        data = (((payload or {}).get("data")) or [])
        if not data:
            break
        yield from data
        nxt = (((payload or {}).get("links")) or {}).get("next")
        if not nxt:
            break
        page += 1
        time.sleep(delay)


def programs() -> list[dict[str, Any]]:
    return list(iter_all("/v1/hackers/programs"))


def hacktivity() -> list[dict[str, Any]]:
    return list(iter_all("/v1/hackers/hacktivity"))


def my_reports() -> list[dict[str, Any]]:
    return list(iter_all("/v1/hackers/me/reports"))


def me() -> dict[str, Any]:
    return _get_json("/v1/hackers/me")


def balance() -> dict[str, Any]:
    return _get_json("/v1/hackers/payments/balance")


def earnings() -> list[dict[str, Any]]:
    return list(iter_all("/v1/hackers/payments/earnings"))


def payouts() -> list[dict[str, Any]]:
    return list(iter_all("/v1/hackers/payments/payouts"))


def program_by_handle(handle: str) -> dict[str, Any]:
    return _get_json(f"/v1/hackers/programs/{handle}")


def structured_scopes(handle: str) -> list[dict[str, Any]]:
    return list(iter_all(f"/v1/hackers/programs/{handle}/structured_scopes"))


def scope_exclusions(handle: str) -> list[dict[str, Any]]:
    return list(iter_all(f"/v1/hackers/programs/{handle}/scope_exclusions"))


def program_weaknesses(handle: str) -> list[dict[str, Any]]:
    return list(iter_all(f"/v1/hackers/programs/{handle}/weaknesses"))


def report_intents() -> list[dict[str, Any]]:
    return list(iter_all("/v1/hackers/report_intents"))


def hacktivity_program(program_handle: str | None = None) -> list[dict[str, Any]]:
    if program_handle:
        path = f"/v1/hackers/hacktivity?queryString=team:{program_handle}"
    else:
        path = "/v1/hackers/hacktivity"
    return list(iter_all(path))
