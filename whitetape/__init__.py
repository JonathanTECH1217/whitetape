"""White Tape: permit data for AI assistants. Nationwide government-issued building permits as clean rows in one schema.

    from whitetape import permits, search, count
    rows = permits(state="MD", trade="roofing")            # ten rows free, nothing asked
    rows = permits(state="MD", trade="roofing", since=0)   # the cursor: rows["next"] goes in the next call, no row twice

Search is free and never returns a row. The first ten rows a month are free with nothing asked. After that each row is 7 cents,
paid either by card once (a prepaid link from whitetape.io/credit/, its token in WHITETAPE_CREDIT) or per call by wallet (x402,
USDC on Base: a funded wallet's private key in WHITETAPE_WALLET_KEY and `whitetape[pay]`, and the payment happens inside the call). No account, no key, no signup. Rows carry no homeowner.
The door: https://whitetape.io/402/   The schema: https://whitetape.io/schema.json
"""
from __future__ import annotations

import os
from typing import Any, Optional

import requests

__version__ = "0.1.1"
API = os.environ.get("WHITETAPE_API", "https://api.whitetape.io").rstrip("/")
TRADES = ("roofing", "hvac", "plumbing", "electrical", "solar", "pool", "fence", "demolition", "new_construction", "remodel", "windows_doors", "garage_adu", "fire")
NETWORK = "eip155:8453"   # Base mainnet, USDC


class PaymentRequired(Exception):
    """The free ten are used and no wallet is set. The message says how to pay."""


_session: Optional[requests.Session] = None


def session() -> requests.Session:
    """A requests session; with WHITETAPE_WALLET_KEY set and whitetape[pay] installed it pays a 402 by itself, capped by WHITETAPE_MAX_USD a call (default 5)."""
    global _session
    if _session is not None:
        return _session
    s = requests.Session()
    s.headers["User-Agent"] = f"whitetape-python/{__version__}"
    credit = os.environ.get("WHITETAPE_CREDIT", "").strip()
    if credit:   # the prepaid link's token: a card payment made it at whitetape.io/credit/; each call debits it
        s.headers["X-Credit"] = credit
    key = os.environ.get("WHITETAPE_WALLET_KEY", "").strip()
    if key:
        try:
            from eth_account import Account
            from x402.client import x402ClientSync, max_amount
            from x402.http.clients.requests import wrapRequestsWithPayment
            from x402.mechanisms.evm import EthAccountSigner
            from x402.mechanisms.evm.exact import ExactEvmScheme
        except ImportError as e:   # the pay extra is not installed
            raise ImportError("WHITETAPE_WALLET_KEY is set but the payment libraries are missing: pip install 'whitetape[pay]'") from e
        scheme = ExactEvmScheme(EthAccountSigner(Account.from_key(key)))
        client = x402ClientSync().register(NETWORK, scheme).register_v1(NETWORK, scheme)
        cap = float(os.environ.get("WHITETAPE_MAX_USD", "5"))
        client.register_policy(max_amount(int(cap * 1_000_000)))   # USDC has six decimals
        s = wrapRequestsWithPayment(s, client)
    _session = s
    return s


def _get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    params = {k: v for k, v in params.items() if v is not None and v != ""}
    r = session().get(f"{API}{path}", params=params, timeout=60)
    if r.status_code == 402:
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        raise PaymentRequired(body.get("error") or "Payment required. Buy a prepaid link by card at https://whitetape.io/credit/ and set WHITETAPE_CREDIT, or set WHITETAPE_WALLET_KEY (a funded Base wallet) with pip install 'whitetape[pay]'. How: https://whitetape.io/402/")
    if r.status_code == 404:
        raise LookupError(r.json().get("error") if r.headers.get("content-type", "").startswith("application/json") else r.text)
    r.raise_for_status()
    return r.json()


def search(q: str = "", state: str = "") -> list[dict[str, Any]]:
    """Free. The areas White Tape holds that match a place or a state, with their row counts; never a row."""
    d = _get("/permits/search", {"q": q, "state": state})
    return d.get("results") or d.get("jurisdictions") or d


def count(**filters: Any) -> dict[str, Any]:
    """Free. How many rows a filter holds and what they would cost, so a wallet pays for exactly that many. Same filters as permits()."""
    return _get("/permits", {**_filters(filters), "count_only": "1"})


def permits(jurisdiction_id: str = "", state: str = "", trade: str = "", permit_type: str = "", issue_date_from: str = "", issue_date_to: str = "",
            value_min: Optional[float] = None, since: Any = None, limit: int = 100, **more: Any) -> dict[str, Any]:
    """Rows in the one schema. Returns {"rows": [...], "count", "next", "billable_rows_this_call", "price_per_row", "paid_by"}.

    trade: one word over every city's own types (whitetape.TRADES). since: the cursor; pass 0 the first time, then the answer's "next",
    and only rows loaded after it come back, none twice. limit: up to 1,000 a call.
    """
    if trade and trade not in TRADES:
        raise ValueError(f"trade must be one of {', '.join(TRADES)}")
    return _get("/permits", _filters({"jurisdiction_id": jurisdiction_id, "state": state, "trade": trade, "permit_type": permit_type, "issue_date_from": issue_date_from,
                                      "issue_date_to": issue_date_to, "value_min": value_min, "since": since, "limit": limit, **more}))


def _filters(f: dict[str, Any]) -> dict[str, Any]:
    f = dict(f)
    if f.get("since") is not None:
        f["since"] = str(f["since"])
    return f


def rows_since(state: str = "", trade: str = "", cursor: Any = 0, **filters: Any):
    """Every row loaded after the cursor, page by page, as a generator of (row, next_cursor). Keep the last cursor for tomorrow."""
    nxt = cursor
    while True:
        d = permits(state=state, trade=trade, since=nxt, limit=1000, **filters)
        for r in d.get("rows") or []:
            yield r, d.get("next")
        if not d.get("rows") or d.get("next") in (None, nxt):
            return
        nxt = d["next"]
