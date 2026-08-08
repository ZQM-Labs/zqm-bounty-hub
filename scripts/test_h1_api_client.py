import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

import h1_api_client as h1  # noqa: E402


class AuthHeaderSelection(unittest.TestCase):
    def test_basic_for_h1_prefix(self):
        got = h1._auth_headers_for("h1_abc")
        self.assertTrue(got["Authorization"].startswith("Basic "))
        decoded = base64.b64decode(got["Authorization"].split(" ", 1)[1]).decode()
        self.assertEqual(decoded, "zqm-computing:h1_abc")

    def test_basic_for_colon_token(self):
        got = h1._auth_headers_for("id:token")
        self.assertTrue(got["Authorization"].startswith("Basic "))
        decoded = base64.b64decode(got["Authorization"].split(" ", 1)[1]).decode()
        self.assertEqual(decoded, "zqm-computing:id:token")

    def test_bearer_for_generic_token(self):
        got = h1._auth_headers_for("abc123")
        self.assertTrue(got["Authorization"].startswith("Bearer abc123"))

    def test_auth_headers_requires_token(self):
        with patch.object(h1, "_token", return_value=""):
            with self.assertRaises(RuntimeError) as cm:
                h1.auth_headers()
            self.assertIn("Missing required secret", str(cm.exception))


class ResponseCheck(unittest.TestCase):
    def test_401_payload_raises(self):
        body = json.dumps({"errors": [{"status": "401", "detail": "Unauthorized"}]}).encode()
        with self.assertRaises(RuntimeError) as cm:
            h1._check_response(body)
        self.assertIn("401", str(cm.exception))

    def test_ok_payload_silent(self):
        body = json.dumps({"data": []}).encode()
        h1._check_response(body)


class TokenSource(unittest.TestCase):
    def test_token_source_env(self):
        with patch.object(h1.os, "environ", {"HACKERONE_API_TOKEN": "tok"}):
            self.assertEqual(h1.token_source(), "env")

    def test_effective_token_source_and_token_env(self):
        with patch.object(h1.os, "environ", {"HACKERONE_API_TOKEN": "mytok"}):
            src, tok = h1.effective_token_source_and_token()
        self.assertEqual(src, "env")
        self.assertEqual(tok, "mytok")


class TokenCacheRoundTrip(unittest.TestCase):
    def test_persist_and_load(self):
        orig = h1.TOKEN_CACHE_PATH
        try:
            tmp = Path(tempfile.gettempdir()) / "h1_token_cache_test"
            tmp.write_text("cached-token", encoding="utf-8")
            h1.TOKEN_CACHE_PATH = tmp
            self.assertEqual(h1._load_persisted_token(), "cached-token")
            h1._persist_token("new-token")
            self.assertEqual(tmp.read_text(encoding="utf-8"), "new-token")
        finally:
            h1.TOKEN_CACHE_PATH = orig
            try:
                tmp.unlink()
            except Exception:
                pass


class GetJsonOk(unittest.TestCase):
    def test_success(self):
        class DummyResp:
            code = 200
            def read(self):
                return json.dumps({"data": [{"id": "ok"}]}).encode()
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False

        with patch.object(h1, "_primary_token", return_value="tok"), \
             patch.object(h1, "_cached_token", return_value="cached"), \
             patch.object(h1, "_url", return_value="https://api.hackerone.com/v1/hackers/me"):
            with patch("h1_api_client.urllib.request.urlopen", return_value=DummyResp()):
                payload = h1._get_json("/v1/hackers/me")
        self.assertEqual(payload["data"][0]["id"], "ok")

    def test_source_meta_stamped(self):
        class DummyResp:
            code = 200
            def read(self):
                return json.dumps({"data": [{"id": "ok"}]}).encode()
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False

        with patch.object(h1, "_primary_token", return_value="tok"), \
             patch.object(h1, "_cached_token", return_value="cached"), \
             patch.object(h1, "_url", return_value="https://api.hackerone.com/v1/hackers/me"):
            with patch("h1_api_client.urllib.request.urlopen", return_value=DummyResp()):
                payload = h1._get_json("/v1/hackers/me", source_meta=True)
        self.assertEqual(payload["__auth_source"], "env")
        self.assertEqual(payload["__auth_token_prefix"], "tok")


class GetJson401Fallback(unittest.TestCase):
    def test_auth_failure_message_and_cache_fallback(self):
        class DummyResp1:
            code = 401
            def read(self):
                return json.dumps({"errors": [{"status": "401", "detail": "Unauthorized"}]}).encode()
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False

        class DummyResp2:
            code = 200
            def read(self):
                return json.dumps({"data": [{"id": "ok"}]}).encode()
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False

        seq = [DummyResp1(), DummyResp2()]
        def fake_urlopen(req, timeout=0):
            return seq.pop(0)

        with patch.object(h1, "_primary_token", return_value="bad-token"), \
             patch.object(h1, "_cached_token", return_value="good-token"), \
             patch.object(h1, "_url", return_value="https://api.hackerone.com/v1/hackers/me"):
            with patch("h1_api_client.urllib.request.urlopen", side_effect=fake_urlopen):
                payload = h1._get_json("/v1/hackers/me")
        self.assertEqual(payload["data"][0]["id"], "ok")


if __name__ == "__main__":
    unittest.main()
