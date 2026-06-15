"""Spend tracker — summarize this billing cycle's Modal spend for `make status`.

Reads `modal billing report --json` (usage line items) and sums their cost, then
frames it against the configured spend limit and credit budget so the $280 (expiry
Jun 30) draws down visibly instead of by guesswork.

The Modal billing report exposes *spend*, not the credit balance, so the credit
total and spend limit are passed in via env (set in .env / Makefile):
  CREDIT_BUDGET  total credits in the workspace      (default 280)
  SPEND_LIMIT    the hard cap you set in the dashboard (default 50)
"""
from __future__ import annotations
import os
import json
import subprocess


def _spend_this_month() -> float | None:
    try:
        out = subprocess.run(
            ["modal", "billing", "report", "--for", "this month", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        if out.returncode != 0:
            return None
        items = json.loads(out.stdout or "[]")
    except Exception:
        return None
    total = 0.0
    for it in items if isinstance(items, list) else []:
        if not isinstance(it, dict):
            continue
        # The billing report returns Cost as a STRING (e.g. "1.128"); be tolerant
        # of casing and of numeric-vs-string across schema variants.
        for k in ("Cost", "cost", "amount", "total", "cost_usd"):
            v = it.get(k)
            if v is None:
                continue
            try:
                total += float(v)
                break
            except (TypeError, ValueError):
                continue
    return total


def main() -> None:
    budget = float(os.environ.get("CREDIT_BUDGET", "280"))
    limit = float(os.environ.get("SPEND_LIMIT", "50"))
    spent = _spend_this_month()
    if spent is None:
        print("credits: (could not read billing report)")
        return
    bar_n = 20
    frac = min(1.0, spent / limit) if limit > 0 else 0.0
    bar = "█" * int(frac * bar_n) + "░" * (bar_n - int(frac * bar_n))
    warn = "  ⚠️ NEAR LIMIT" if frac >= 0.8 else ""
    print(f"spent this cycle: ${spent:,.2f} / ${limit:,.0f} limit  [{bar}]{warn}")
    print(f"credits: ${budget:,.0f} total (expire Jun 30) · ${max(0, budget - spent):,.2f} left")


if __name__ == "__main__":
    main()
