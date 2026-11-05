"""The checks: the client against a fake door. `python -m pytest tests/` before a release; a change in an answer's shape fails here first."""
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import pytest

ROWS = [{"id": 1, "jurisdiction_id": "128028", "permit_number": "MECHR-2026-00436", "permit_type": "Mechanical (Residential)", "address": "110 HOLECLOW ST", "contractor_name": "ARS/Rescue Rooter",
         "contractor_phone": "(301) 364-5873", "value": 15200.0, "issue_date": "2026-10-27", "loaded_at": "2026-10-27T20:00:00"}]
SEEN = []


class Door(BaseHTTPRequestHandler):
    def log_message(self, *a):   # quiet
        pass

    def _json(self, code, body, headers=None):
        self.send_response(code); self.send_header("Content-Type", "application/json")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers(); self.wfile.write(json.dumps(body).encode())

    def do_GET(self):
        u = urlparse(self.path); q = {k: v[0] for k, v in parse_qs(u.query).items()}
        SEEN.append((u.path, q, dict(self.headers)))
        if u.path == "/permits/search":
            return self._json(200, {"results": [{"jurisdiction_id": "128028", "name": "City Of Annapolis", "state": "MD", "permits_last_30_days": 338}], "price_per_row": 0.07})
        if u.path == "/permits":
            if q.get("count_only") == "1":
                return self._json(200, {"count": 338, "price": 14.20, "price_per_row": 0.07})
            if q.get("state") == "ZZ":   # the free ten are used, no payment
                return self._json(402, {"x402Version": 1, "accepts": [{"scheme": "exact", "network": "base", "maxAmountRequired": "3000000"}], "error": "Your free 10 rows this month are used."})
            rows = [] if q.get("since") == "2026-10-27T20:00:00|1" else ROWS
            return self._json(200, {"rows": rows, "count": len(rows), "next": "2026-10-27T20:00:00|1", "billable_rows_this_call": 0, "price_per_row": 0.07, "paid_by": "free"})
        self._json(404, {"error": "no"})


@pytest.fixture(scope="module")
def door():
    srv = HTTPServer(("127.0.0.1", 0), Door)
    t = threading.Thread(target=srv.serve_forever, daemon=True); t.start()
    os.environ["WHITETAPE_API"] = f"http://127.0.0.1:{srv.server_port}"
    import importlib, whitetape
    importlib.reload(whitetape)
    yield whitetape
    srv.shutdown()


def test_search_is_free_and_never_a_row(door):
    r = door.search("annapolis", "MD")
    assert r[0]["name"] == "City Of Annapolis" and "permit_number" not in r[0]


def test_count_prices_the_filter(door):
    r = door.count(state="MD", trade="roofing")
    assert r["count"] == 338 and r["price"] == 14.20
    assert SEEN[-1][1]["count_only"] == "1" and SEEN[-1][1]["trade"] == "roofing"


def test_permits_returns_rows_and_a_cursor(door):
    r = door.permits(state="MD", trade="roofing", since=0)
    assert r["rows"][0]["contractor_name"] == "ARS/Rescue Rooter" and r["next"]
    assert SEEN[-1][1]["since"] == "0"


def test_bad_trade_is_refused_before_the_call(door):
    with pytest.raises(ValueError):
        door.permits(trade="roofs")


def test_402_without_a_wallet_is_a_plain_error(door):
    with pytest.raises(door.PaymentRequired) as e:
        door.permits(state="ZZ")
    assert "free 10" in str(e.value)


def test_rows_since_stops_when_nothing_new(door):
    out = list(door.rows_since(state="MD", cursor=0))
    assert len(out) == 1 and out[0][1] == "2026-10-27T20:00:00|1"


def test_user_agent_names_the_package(door):
    door.search("a")
    assert SEEN[-1][2].get("User-Agent", "").startswith("whitetape-python/")
