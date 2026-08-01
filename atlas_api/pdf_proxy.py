"""Caching PDF proxy — a Blueprint copy of the webui closure
(webui/app.py `pdf_attachment`), unchanged in behaviour so both sites share
one cache directory. The registry rate-limits attachment bursts (HTTP 429);
cache-and-serve keeps repeat downloads instant and off the registry.
"""
from __future__ import annotations

import re
from pathlib import Path

import requests
from flask import Blueprint, abort, current_app, render_template, send_file

from khmdhs.config import CONTRACT_PDF_URL, PAYMENT_PDF_URL

# kind -> (ADAM infix, registry attachment URL template)
_PDF_KINDS = {
    "contract": ("SYMV", CONTRACT_PDF_URL),
    "payment": ("PAY", PAYMENT_PDF_URL),
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
