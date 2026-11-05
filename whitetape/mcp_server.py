"""White Tape as an MCP server: three tools a Claude can call. `pip install 'whitetape[mcp]'` then `whitetape-mcp` (stdio).

Claude Desktop / Claude Code config:
  {"mcpServers": {"whitetape": {"command": "whitetape-mcp", "env": {"WHITETAPE_CREDIT": "<optional, a prepaid link token from whitetape.io/credit/>"}}}}
"""
from __future__ import annotations

from typing import Any, Optional

from . import count as _count, permits as _permits, search as _search, PaymentRequired, TRADES


def build():
    from mcp.server.mcpserver import MCPServer
    server = MCPServer("whitetape", title="White Tape permits", version="0.1.0", website_url="https://whitetape.io",
                       instructions="Nationwide government-issued building permits in one schema. search is free and lists the areas held. count is free and prices a filter. "
                                    "permits returns rows: the first ten a month are free with nothing asked, after that 7 cents a row from the prepaid link in WHITETAPE_CREDIT (bought by card at whitetape.io/credit/) or the wallet in WHITETAPE_WALLET_KEY. "
                                    "Rows carry the permit, the property, and the contractor; never the homeowner. A fresh permit near a contractor is a lead; the contractor_name on a row is the builder.")

    @server.tool(description="Free. The areas White Tape holds that match a place name, city, zip, or state, with row counts. Never returns a row.")
    def search(q: str = "", state: str = "") -> Any:
        return _search(q, state)

    @server.tool(description=f"Free. How many permit rows a filter holds and the price to pull them all. trade is one of: {', '.join(TRADES)}.")
    def count(state: str = "", trade: str = "", jurisdiction_id: str = "", permit_type: str = "", issue_date_from: str = "", issue_date_to: str = "", value_min: Optional[float] = None) -> Any:
        return _count(state=state, trade=trade, jurisdiction_id=jurisdiction_id, permit_type=permit_type, issue_date_from=issue_date_from, issue_date_to=issue_date_to, value_min=value_min)

    @server.tool(description=f"Permit rows in the one schema (permit_number, permit_type, description, address, city, state, zip, parcel_id, contractor_name, contractor_license, contractor_phone, value, issue_date, ...). "
                             f"Ten rows a month free, then 7 cents a row by wallet. trade is one of: {', '.join(TRADES)}. since: pass 0 the first time, then the answer's next, and no row comes twice.")
    def permits(state: str = "", trade: str = "", jurisdiction_id: str = "", permit_type: str = "", issue_date_from: str = "", issue_date_to: str = "", value_min: Optional[float] = None,
                since: Optional[str] = None, limit: int = 100) -> Any:
        try:
            return _permits(state=state, trade=trade, jurisdiction_id=jurisdiction_id, permit_type=permit_type, issue_date_from=issue_date_from, issue_date_to=issue_date_to,
                            value_min=value_min, since=since, limit=limit)
        except PaymentRequired as e:
            return {"error": str(e), "how_to_pay": "https://whitetape.io/402/"}

    return server


def main():
    build().run("stdio")


if __name__ == "__main__":
    main()
