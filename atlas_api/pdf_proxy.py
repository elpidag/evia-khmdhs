"""Caching PDF proxy — a Blueprint copy of the webui closure
(webui/app.py `pdf_attachment`), unchanged in behaviour so both sites share
one cache directory. The registry rate-limits attachment bursts (HTTP 429);
cache-and-serve keeps repeat downloads instant and off the registry.

Also serves Diavgeia decision PDFs (`/pdf/diavgeia/<ΑΔΑ>`) for the Ανάδοχοι
dataset — same mechanics, its own cache dir (the harvest already filled it).
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import requests
from flask import Blueprint, abort, current_app, render_template, send_file

from khmdhs.config import (AUCTION_PDF_URL, CONTRACT_PDF_URL, NOTICE_PDF_URL,
                           PAYMENT_PDF_URL, REQUEST_PDF_URL)

# kind -> (ADAM infix, registry attachment URL template)
_PDF_KINDS = {
    "contract": ("SYMV", CONTRACT_PDF_URL),
    "payment": ("PAY", PAYMENT_PDF_URL),
    "request": ("REQ", REQUEST_PDF_URL),
    "notice": ("PROC", NOTICE_PDF_URL),
    "auction": ("AWRD", AUCTION_PDF_URL),
}

bp = Blueprint("pdf", __name__, template_folder="templates")


@bp.route("/pdf/<kind>/<adam>")
def pdf_attachment(kind: str, adam: str):
    spec = _PDF_KINDS.get(kind)
    if spec is None:
        abort(404)
    infix, url_template = spec
    if not re.fullmatch(rf"\d{{2}}{infix}\d{{6,12}}", adam):
        abort(404)

    cache_dir = Path(current_app.config["PDF_CACHE_DIR"])
    path = cache_dir / f"{adam}.pdf"
    if not path.exists():
        try:
            resp = requests.get(url_template.format(adam=adam), timeout=60)
        except requests.RequestException as e:
            return render_template(
                "pdf_wait.html", adam=adam, retry=30,
                reason=f"network error reaching the registry ({type(e).__name__})",
            ), 503
        if resp.status_code == 429:
            retry = max(5, int(resp.headers.get("Retry-After", "30") or 30))
            return (
                render_template(
                    "pdf_wait.html", adam=adam, retry=retry,
                    reason="the KHMDHS registry is rate-limiting downloads right now",
                ),
                503,
                {"Retry-After": str(retry)},
            )
        if resp.status_code != 200 or not resp.content.startswith(b"%PDF"):
            return render_template(
                "pdf_wait.html", adam=adam, retry=None,
                reason=f"the registry returned HTTP {resp.status_code} instead of a PDF "
                       "(the document may have no attachment)",
            ), 502
        cache_dir.mkdir(parents=True, exist_ok=True)
        tmp = cache_dir / f"{adam}.pdf.tmp"
        tmp.write_bytes(resp.content)
        tmp.replace(path)
    return send_file(
        path, mimetype="application/pdf",
        as_attachment=False, download_name=f"{adam}.pdf",
    )


# Diavgeia ΑΔΑ: 10 chars + '-' + 3, digits and Greek capitals only.
_ADA_RE = re.compile(r"[0-9Α-Ω]{10}-[0-9Α-Ω]{3}")


@bp.route("/pdf/diavgeia/<ada>")
def diavgeia_pdf(ada: str):
    ada = unicodedata.normalize("NFC", ada)
    if not _ADA_RE.fullmatch(ada):
        abort(404)
    cache_dir = Path(current_app.config["ANADOHOI_PDF_CACHE"])
    path = cache_dir / f"{ada}.pdf"
    if not path.exists():
        # the arogi harvest pre-fetches its acts into its own cache
        arogi = Path(current_app.config.get("AROGI_CACHE", "")) / f"{ada}.pdf"
        if arogi.exists():
            path = arogi
    if not path.exists():
        try:
            resp = requests.get(f"https://diavgeia.gov.gr/doc/{ada}",
                                timeout=60)
        except requests.RequestException as e:
            return render_template(
                "pdf_wait.html", adam=ada, retry=30,
                reason=f"network error reaching Diavgeia ({type(e).__name__})",
            ), 503
        if resp.status_code == 429:
            retry = max(5, int(resp.headers.get("Retry-After", "30") or 30))
            return (
                render_template(
                    "pdf_wait.html", adam=ada, retry=retry,
                    reason="Diavgeia is rate-limiting downloads right now",
                ),
                503,
                {"Retry-After": str(retry)},
            )
        if resp.status_code != 200 or not resp.content.startswith(b"%PDF"):
            return render_template(
                "pdf_wait.html", adam=ada, retry=None,
                reason=f"Diavgeia returned HTTP {resp.status_code} instead of "
                       "a PDF (the decision may have no signed document)",
            ), 502
        cache_dir.mkdir(parents=True, exist_ok=True)
        tmp = cache_dir / f"{ada}.pdf.tmp"
        tmp.write_bytes(resp.content)
        tmp.replace(path)
    return send_file(
        path, mimetype="application/pdf",
        as_attachment=False, download_name=f"{ada}.pdf",
    )
