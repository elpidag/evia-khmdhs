"""Command-line entry point: argparse + the fetch/persist loop."""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import requests

from khmdhs.api import fetch_contract
from khmdhs.config import (
    DEFAULT_DB,
    DEFAULT_INPUT,
    DEFAULT_LOG,
    DEFAULT_OUTPUT,
    THROTTLE_SECONDS,
)
from khmdhs.db import already_done, init_db, record_failure, upsert_contract
from khmdhs.excel_io import read_adams, write_enriched_xlsx


def configure_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m khmdhs",
        description="Enrich KHMDHS contract data via the public open-data API.",
    )
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Source xlsx")
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Destination xlsx")
    p.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite path")
    p.add_argument("--log", type=Path, default=DEFAULT_LOG, help="Log file path")
    p.add_argument("--limit", type=int, default=None, help="Process only the first N pending ADAMs")
    p.add_argument("--sleep", type=float, default=THROTTLE_SECONDS, help="Seconds between requests")
    p.add_argument("--refetch", action="store_true", help="Re-fetch ADAMs already marked OK")
    p.add_argument("--skip-xlsx", action="store_true", help="Don't write the enriched xlsx")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    configure_logging(args.log)
    logging.info("Input : %s", args.input)
    logging.info("DB    : %s", args.db)
    logging.info("Output: %s", args.output)

    if not args.input.exists():
        logging.error("Input file does not exist: %s", args.input)
        return 2

    adams = read_adams(args.input)
    logging.info("Read %d ADAMs from input", len(adams))

    conn = init_db(args.db)
    done = set() if args.refetch else already_done(conn)
    todo = [a for a in adams if a not in done]
    if args.limit is not None:
        todo = todo[: args.limit]
    logging.info(
        "%d already in DB, %d to fetch%s",
        len(done), len(todo),
        f" (limit {args.limit})" if args.limit else "",
    )

    session = requests.Session()
    counts = {"ok": 0, "not_found": 0, "http_error": 0, "parse_error": 0}
    for i, adam in enumerate(todo, start=1):
        status, item, http_status, err = fetch_contract(session, adam)
        if status == "ok" and item is not None:
            try:
                upsert_contract(conn, item)
            except Exception as e:
                logging.exception("DB write failed for %s: %s", adam, e)
                record_failure(conn, adam, "parse_error", http_status, str(e))
                counts["parse_error"] += 1
            else:
                counts["ok"] += 1
        else:
            record_failure(conn, adam, status, http_status, err)
            counts[status] = counts.get(status, 0) + 1
            level = logging.WARNING if status == "not_found" else logging.ERROR
            logging.log(level, "[%d/%d] %s -> %s (%s)", i, len(todo), adam, status, err or "")
        if i % 25 == 0 or i == len(todo):
            logging.info(
                "Progress %d/%d  ok=%d not_found=%d errors=%d",
                i, len(todo), counts["ok"], counts["not_found"],
                counts["http_error"] + counts["parse_error"],
            )
        if args.sleep and i < len(todo):
            time.sleep(args.sleep)

    if args.skip_xlsx:
        logging.info("Skipping xlsx output (--skip-xlsx).")
    else:
        logging.info("Writing enriched xlsx: %s", args.output)
        write_enriched_xlsx(conn, args.input, args.output)
        logging.info("xlsx written.")

    n_contracts = conn.execute("SELECT COUNT(*) FROM contracts").fetchone()[0]
    n_ok = conn.execute("SELECT COUNT(*) FROM fetch_log WHERE status='ok'").fetchone()[0]
    n_nf = conn.execute("SELECT COUNT(*) FROM fetch_log WHERE status='not_found'").fetchone()[0]
    n_err = conn.execute(
        "SELECT COUNT(*) FROM fetch_log WHERE status NOT IN ('ok','not_found')"
    ).fetchone()[0]
    logging.info(
        "DB totals: contracts=%d  fetch_log ok=%d not_found=%d errors=%d",
        n_contracts, n_ok, n_nf, n_err,
    )
    conn.close()
    return 0
