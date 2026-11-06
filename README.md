# whitetape

Permit data for AI assistants. Nationwide government-issued building permits as clean rows in one schema. Search free. The first ten rows a month are free with nothing asked. After that 7 cents a row, paid per call by wallet (x402, USDC on Base). No account, no key, no signup. Rows carry the permit, the property, and the contractor, never the homeowner.

```
pip install whitetape
```

```python
from whitetape import search, count, permits

search("annapolis")                                   # free: the areas held, with row counts
count(state="MD", trade="roofing")                    # free: {"count": 412, "price": 12.36, "price_per_row": 0.07}
rows = permits(state="MD", trade="roofing", since=0)  # the first ten are free
rows["rows"][0]["contractor_name"]                    # the builder who pulled it
```

Daily, with no row twice:

```python
from whitetape import rows_since
cursor = 0                        # keep the last cursor between runs
for row, cursor in rows_since(state="MD", trade="roofing", cursor=cursor):
    ...
```

## Paying for more than ten

By card, once: buy a prepaid link at https://whitetape.io/credit/ ($20 is 400 rows) and put its token in the environment. No account.

```
export WHITETAPE_CREDIT=wt_…
```

By wallet, per call:

```
pip install "whitetape[pay]"
export WHITETAPE_WALLET_KEY=<the private key of a THROWAWAY Base wallet, funded with only what you mean to spend>
export WHITETAPE_MAX_USD=5          # the most one call may spend; default 5
export WHITETAPE_MAX_USD_TOTAL=20   # the most this process may spend in all; default 20
```

The payment happens inside the call. The key sits in your process's environment, where any package or tool in that process can read it: never a main wallet. The API address is pinned to api.whitetape.io; a 402 from anywhere else is never paid. The 402 door, for a program with no library: https://whitetape.io/402/

## As an MCP server for Claude

```
pip install "whitetape[mcp]"
```

```json
{"mcpServers": {"whitetape": {"command": "whitetape-mcp"}}}
```

Three tools: `search`, `count`, `permits`. The MCP server never spends a wallet: paid rows come only from a prepaid link in `WHITETAPE_CREDIT` (its balance is the worst case), at most `WHITETAPE_MCP_MAX_ROWS` a session, default 500.

## Command line

```
whitetape search annapolis
whitetape count --state MD --trade roofing
whitetape rows --state MD --trade roofing --since 0
```

## The schema

https://whitetape.io/schema.json. Trades: roofing, hvac, plumbing, electrical, solar, pool, fence, demolition, new_construction, remodel, windows_doors, garage_adu, fire.

Built and used by Monarc Build for its home-services clients. Questions: hello@whitetape.io

## Who is behind it

Monarc Build, LLC, Annapolis, Maryland, doing business as White Tape. Terms: https://whitetape.io/terms/. Privacy: https://whitetape.io/privacy/. Rows never carry the homeowner's or the applicant's name, and an owner-builder permit, where the homeowner is the contractor of record, is never sold. Calling the contractors on the rows is on you: follow the telemarketing and do-not-call rules where you call.

<!-- mcp-name: io.github.JonathanTECH1217/whitetape -->
