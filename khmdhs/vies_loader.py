"""Sweep unresolved contractors through VIES and update contractor_locations.json.

Reads khmdhs/data/contractor_locations.json, iterates entries where
`source == "unresolved"`, queries VIES (anonymous, EU-level VAT validation —
does NOT email the AFM holder), parses the address, resolves Π.Ε. via
city / postal-prefix lookups, and writes back atomically.

After this runs, push to the DB with `python -m khmdhs.contractor_loader`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import time
from collections import Counter
from pathlib import Path

import requests

from khmdhs.greek_regions import resolve_pe
from khmdhs.vies import lookup

DATA_FILE = Path(__file__).parent / "data" / "contractor_locations.json"
DEFAULT_RATE_SLEEP = 1.0  # seconds between VIES calls — polite default
CHECKPOINT_EVERY = 10     # save the JSON every N processed entries


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m khmdhs.vies_loader")
    p.add_argument("--data", type=Path, default=DATA_FILE,
                   help="contractor_locations.json path")
    p.add_argument("--dry-run", action="store_true",
                   help="Print actions without writing JSON")
    p.add_argument("--limit", type=int, default=None,
                   help="Process only the first N unresolved entries")
    p.add_argument("--retry-failed", action="store_true",
                   help="Also re-query entries previously marked vies_failed / vies_no_address")
    p.add_argument("--rate-sleep", type=float, default=DEFAULT_RATE_SLEEP,
                   help="Seconds between VIES requests (default: 1.0)")
    return p


_RETRY_SOURCES = {"unresolved"}
_RETRY_SOURCES_WITH_FAILED = _RETRY_SOURCES | {"vies_failed", "vies_no_address"}


def _save_atomic(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _candidates(curation: dict, retry_failed: bool) -> list[str]:
    sources = _RETRY_SOURCES_WITH_FAILED if retry_failed else _RETRY_SOURCES
    return [k for k, v in curation.items() if v.get("source") in sources]


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    with args.data.open(encoding="utf-8") as f:
        curation: dict = json.load(f)

    keys = _candidates(curation, args.retry_failed)
    if args.limit is not None:
        keys = keys[: args.limit]

    logging.info(
        "VIES sweep: %d candidate entries (retry_failed=%s, limit=%s)",
        len(keys), args.retry_failed, args.limit,
    )
    if not keys:
        logging.info("Nothing to do.")
        return 0

    today = dt.date.today().isoformat()
    counts: Counter[str] = Counter()
    method_counts: Counter[str] = Counter()
    session = requests.Session()

    processed = 0
    for i, key in enumerate(keys, start=1):
        vat_raw = key.strip()
        entry = curation[key]
        logging.info("[%d/%d] VAT %s — %s", i, len(keys), vat_raw, (entry.get("legal_name") or "?")[:50])

        result = lookup(vat_raw, session=session)

        if result.error == "invalid" or (result.error or "").startswith("vat_format"):
            counts["invalid"] += 1
            update = dict(entry)
            update.update(
                source="vies_invalid",
                source_url=result.source_url,
                notes=(
                    f"VAT format invalid: {result.error}"
                    if (result.error or "").startswith("vat_format")
                    else "VIES says VAT is not valid"
                ),
                curated_at=today,
            )
        elif result.error and result.error.startswith(("http_", "network", "bad_json")):
            counts["failed"] += 1
            update = dict(entry)
            update.update(
                source="vies_failed",
                source_url=result.source_url,
                notes=f"VIES error: {result.error}",
                curated_at=today,
            )
        elif result.error == "no_address":
            counts["no_address"] += 1
            update = dict(entry)
            update.update(
                legal_name=result.name or entry.get("legal_name"),
                source="vies_no_address",
                source_url=result.source_url,
                notes="VIES validates the VAT but returns no address",
                curated_at=today,
            )
        else:
            # Got an address — try to resolve region
            pe, method = resolve_pe(result.city, result.postal_code)
            method_counts[method] += 1
            if pe:
                counts["resolved"] += 1
            else:
                counts["partial"] += 1
            update = dict(entry)
            update.update(
                legal_name=result.name or entry.get("legal_name"),
                address=result.street,
                postal_code=result.postal_code,
                city=result.city,
                region_pe=pe,
                source="vies",
                source_url=result.source_url,
                notes=(entry.get("notes") if pe else "VIES address parsed; region not auto-resolved"),
                curated_at=today,
            )
            logging.info("  → %s | %s | %s | %s (%s)",
                         result.street or "—", result.postal_code or "—",
                         result.city or "—", pe or "—", method)

        if not args.dry_run:
            curation[key] = update

        processed += 1
        if not args.dry_run and processed % CHECKPOINT_EVERY == 0:
            _save_atomic(args.data, curation)
            logging.info("  ↳ checkpoint saved (%d/%d processed)", processed, len(keys))

        # Polite rate limiting
        if i < len(keys):
            time.sleep(args.rate_sleep)

    if not args.dry_run:
        _save_atomic(args.data, curation)

    print()
    print("=" * 60)
    print(f"VIES sweep summary ({processed} processed)")
    print("=" * 60)
    print(f"  resolved (with region):     {counts['resolved']:4d}")
    print(f"  partial (address, no Π.Ε.): {counts['partial']:4d}")
    print(f"  no_address (VIES validates, no address): {counts['no_address']:4d}")
    print(f"  invalid (VIES rejects):     {counts['invalid']:4d}")
    print(f"  failed (HTTP/network):      {counts['failed']:4d}")
    print()
    print("Region resolution method:")
    for m, n in method_counts.most_common():
        print(f"  {m:10s} {n:4d}")
    print()
    print("Next: .venv/bin/python -m khmdhs.contractor_loader")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
