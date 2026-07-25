"""Sweep contractor VATs through the anonymous GEMI publicity API.

Two modes:
  default        — resolve entries VIES could not (consortium VATs etc.):
                   sources unresolved / vies_invalid / vies_no_address /
                   vies_failed / consortium_unresolved. Fills address +
                   region and stores the GEMI number.
  --backfill-numbers — for entries already located by other means, fetch
                   just the GEMI number (search call only) so contractor
                   pages can link the public profile.

A miss is recorded as "gemi": "-1" so it is never re-queried. Writes back
to khmdhs/data/contractor_locations.json atomically; push to the DB with
`python -m khmdhs.contractor_loader` afterwards.
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

from khmdhs.gemi import COMPANY_URL, lookup, search_by_afm
from khmdhs.greek_regions import pe_from_genitive, resolve_pe

DATA_FILE = Path(__file__).parent / "data" / "contractor_locations.json"
DEFAULT_RATE_SLEEP = 2.0
CHECKPOINT_EVERY = 10

_RESOLVE_SOURCES = {
    "unresolved", "vies_invalid", "vies_no_address", "vies_failed",
    "consortium_unresolved",
}


def _save_atomic(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m khmdhs.gemi_loader")
    p.add_argument("--data", type=Path, default=DATA_FILE)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--rate-sleep", type=float, default=DEFAULT_RATE_SLEEP)
    p.add_argument("--retry-missing", action="store_true",
                   help='re-query entries previously marked "gemi": "-1"')
    p.add_argument("--backfill-numbers", action="store_true",
                   help="only fetch GEMI numbers for already-located entries")
    p.add_argument("--verify", action="store_true",
                   help="re-resolve every stored GEMI number (seat, not branch) "
                        "and report entries whose region disagrees with the "
                        "GEMI seat address — regions are NOT auto-changed")
    return p


def _candidates(curation: dict, backfill: bool, retry_missing: bool) -> list[str]:
    keys = []
    for vat, e in curation.items():
        gemi = e.get("gemi")
        if gemi == "-1" and not retry_missing:
            continue
        if backfill:
            if not gemi:
                keys.append(vat)
        else:
            if e.get("source") in _RESOLVE_SOURCES and not e.get("region_pe"):
                keys.append(vat)
    return keys


def _verify(curation: dict, args) -> int:
    """Re-resolve stored GEMI numbers to the seat record and cross-check
    each entry's curated region against the GEMI seat address."""
    import requests as _rq

    from khmdhs.gemi import company_details, parse_address, search_by_afm

    keys = [k for k, e in curation.items()
            if e.get("gemi") and e.get("gemi") != "-1"]
    if args.limit is not None:
        keys = keys[: args.limit]
    logging.info("GEMI verify: %d entries", len(keys))
    session = _rq.Session()
    n_renumbered = 0
    mismatches: list[str] = []
    failures: list[str] = []
    for i, vat in enumerate(keys, start=1):
        entry = curation[vat]
        gemi, err = search_by_afm(vat, session=session)
        if gemi is None:
            failures.append(f"{vat.strip()}: search failed ({err})")
            time.sleep(args.rate_sleep)
            continue
        if gemi != entry.get("gemi"):
            logging.info("[%d/%d] %s: gemi %s → %s (seat, was branch/stale)",
                         i, len(keys), vat.strip(), entry.get("gemi"), gemi)
            if not args.dry_run:
                entry["gemi"] = gemi
            n_renumbered += 1
        time.sleep(args.rate_sleep)
        company, err = company_details(gemi, session=session)
        if company is None:
            failures.append(f"{vat.strip()}: details failed ({err})")
            time.sleep(args.rate_sleep)
            continue
        _, city, prefecture, _ = parse_address(company.get("company_address"))
        pe_seat = pe_from_genitive(prefecture)

        def _fold(s: str) -> str:
            import unicodedata
            dec = unicodedata.normalize("NFD", s.upper())
            return "".join(ch for ch in dec if not unicodedata.combining(ch))

        # Accent-fold before comparing: «Π.Ε. Ευβοίας» and «Π.Ε. Εύβοιας»
        # are the same regional unit under alternative spellings.
        if (pe_seat and entry.get("region_pe")
                and _fold(pe_seat) != _fold(entry["region_pe"])):
            mismatches.append(
                f"{vat.strip()} ({(entry.get('legal_name') or '?')[:40]}): "
                f"curated {entry['region_pe']} [{entry.get('source')}] vs "
                f"GEMI seat {pe_seat} ({company.get('company_address')})")
        if i % CHECKPOINT_EVERY == 0 and not args.dry_run:
            _save_atomic(args.data, curation)
        time.sleep(args.rate_sleep)
    if not args.dry_run:
        _save_atomic(args.data, curation)
    print()
    print("=" * 60)
    print(f"GEMI verify — {len(keys)} entries, {n_renumbered} number(s) "
          f"re-pointed to the seat record, {len(mismatches)} region mismatch(es), "
          f"{len(failures)} failure(s)")
    for m in mismatches:
        print(f"  MISMATCH {m}")
    for f_ in failures:
        print(f"  FAILED   {f_}")
    if mismatches:
        print("  → review each against GEMI/VIES/the contract PDFs before "
              "changing contractor_locations.json; regions are never auto-edited.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    with args.data.open(encoding="utf-8") as f:
        curation: dict = json.load(f)

    if args.verify:
        return _verify(curation, args)

    keys = _candidates(curation, args.backfill_numbers, args.retry_missing)
    if args.limit is not None:
        keys = keys[: args.limit]
    mode = "backfill-numbers" if args.backfill_numbers else "resolve-unlocated"
    logging.info("GEMI sweep (%s): %d candidates", mode, len(keys))
    if not keys:
        logging.info("Nothing to do.")
        return 0

    today = dt.date.today().isoformat()
    counts: Counter[str] = Counter()
    session = requests.Session()
    processed = 0
    for i, vat in enumerate(keys, start=1):
        entry = curation[vat]
        logging.info("[%d/%d] VAT %s — %s", i, len(keys), vat.strip(),
                     (entry.get("legal_name") or "?")[:50])

        if args.backfill_numbers:
            gemi, err = search_by_afm(vat, session=session)
            if gemi:
                counts["number_found"] += 1
                update = {**entry, "gemi": gemi}
            elif err == "not_found":
                counts["not_in_gemi"] += 1
                update = {**entry, "gemi": "-1"}
            else:
                counts["failed"] += 1
                logging.warning("  → %s", err)
                update = entry
        else:
            r = lookup(vat, session=session)
            if r.error == "not_found":
                counts["not_in_gemi"] += 1
                update = {**entry, "gemi": "-1", "curated_at": today,
                          "notes": ((entry.get("notes") or "") +
                                    " | Not in GEMI publicity search.").strip(" |")}
            elif r.error:
                counts["failed"] += 1
                logging.warning("  → %s", r.error)
                update = entry
            else:
                pe, method = resolve_pe(r.city, r.postal_code)
                # The GEMI prefecture is authoritative — let it override the
                # weak 2-digit-postal fallback (38xxx spans Λάρισας/Μαγνησίας).
                pe_pref = pe_from_genitive(r.prefecture)
                if pe_pref and (pe is None or method in ("postal2", "none")):
                    pe, method = pe_pref, "gemi_prefecture"
                counts["resolved" if pe else "partial"] += 1
                update = {**entry,
                          "legal_name": r.name or entry.get("legal_name"),
                          "address": r.street, "postal_code": r.postal_code,
                          "city": r.city, "region_pe": pe,
                          "gemi": r.gemi_number,
                          "source": "gemi",
                          "source_url": r.source_url,
                          "notes": (f"GEMI publicity profile ({r.status or '?'}). "
                                    + ("" if pe else "Region not auto-resolved. ")
                                    + (entry.get("notes") or "")).strip(),
                          "curated_at": today}
                logging.info("  → %s | %s | %s | %s (%s)", r.street or "—",
                             r.postal_code or "—", r.city or "—", pe or "—", method)

        if not args.dry_run:
            curation[vat] = update
        processed += 1
        if not args.dry_run and processed % CHECKPOINT_EVERY == 0:
            _save_atomic(args.data, curation)
            logging.info("  ↳ checkpoint saved (%d/%d)", processed, len(keys))
        if i < len(keys):
            time.sleep(args.rate_sleep)

    if not args.dry_run:
        _save_atomic(args.data, curation)

    print()
    print("=" * 60)
    print(f"GEMI sweep summary ({mode}, {processed} processed)")
    for k, v in counts.most_common():
        print(f"  {k:16s} {v:4d}")
    print()
    print("Next: .venv/bin/python -m khmdhs.contractor_loader")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
