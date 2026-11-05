"""whitetape on the command line: `whitetape search annapolis`, `whitetape count --state MD --trade roofing`, `whitetape rows --state MD --trade roofing --since 0`."""
import argparse
import json
import sys

from . import count, permits, search, PaymentRequired


def main(argv=None):
    ap = argparse.ArgumentParser(prog="whitetape", description="Nationwide government-issued building permits in one schema. Ten rows free, then 7 cents a row by wallet.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search", help="free: the areas held that match a place"); s.add_argument("q", nargs="?", default=""); s.add_argument("--state", default="")
    for name in ("count", "rows"):
        p = sub.add_parser(name, help="free: rows and price for a filter" if name == "count" else "the rows (ten free, then paid)")
        p.add_argument("--jurisdiction", default=""); p.add_argument("--state", default=""); p.add_argument("--trade", default=""); p.add_argument("--type", default="")
        p.add_argument("--from", dest="from_", default=""); p.add_argument("--to", default=""); p.add_argument("--value-min", type=float); p.add_argument("--since"); p.add_argument("--limit", type=int, default=100)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "search":
            out = search(a.q, a.state)
        else:
            f = dict(jurisdiction_id=a.jurisdiction, state=a.state, trade=a.trade, permit_type=a.type, issue_date_from=a.from_, issue_date_to=a.to, value_min=a.value_min, since=a.since, limit=a.limit)
            out = count(**{k: v for k, v in f.items() if k not in ("limit",)}) if a.cmd == "count" else permits(**f)
    except PaymentRequired as e:
        print(str(e), file=sys.stderr); return 2
    json.dump(out, sys.stdout, indent=2, default=str); print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
