"""Flask app: routes + DB connection management."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import requests
from flask import (
    Flask, abort, g, jsonify, redirect, render_template, request, send_file, url_for,
)

from khmdhs.config import CONTRACT_PDF_URL, DEFAULT_DB, PAYMENT_PDF_URL, PDF_CACHE_DIR
from webui import filters, queries

# kind -> (ADAM infix, registry attachment URL template)
_PDF_KINDS = {
    "contract": ("SYMV", CONTRACT_PDF_URL),
    "payment": ("PAY", PAYMENT_PDF_URL),
}


def create_app(db_path: Path | None = None, pdf_cache_dir: Path | None = None) -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["DB_PATH"] = Path(db_path) if db_path else DEFAULT_DB
    app.config["PDF_CACHE_DIR"] = Path(pdf_cache_dir) if pdf_cache_dir else PDF_CACHE_DIR
    filters.register(app)

    @app.before_request
    def _open_db() -> None:
        g.conn = queries.open_ro(app.config["DB_PATH"])

    @app.teardown_request
    def _close_db(exc) -> None:
        conn = g.pop("conn", None)
        if conn is not None:
            conn.close()

    @app.route("/")
    def dashboard():
        return render_template(
            "dashboard.html",
            kpis=queries.kpis(g.conn),
            top_contractors=queries.top_contractors(g.conn, limit=10),
            top_authorities=queries.top_authorities(g.conn, limit=5),
            top_signers=queries.top_signers(g.conn, limit=5),
        )

    @app.route("/contractors")
    def contractors_list():
        q = (request.args.get("q") or "").strip()
        sort = request.args.get("sort", "total_eur")
        # If the query is exactly a 9-digit VAT, jump straight to the detail page.
        if q.isdigit() and len(q) == 9:
            return redirect(url_for("contractor_detail", vat=q))
        rows = queries.list_contractors(g.conn, q=q or None, sort=sort)
        return render_template("contractors.html", rows=rows, q=q, sort=sort)

    @app.route("/contracts")
    def contracts_list():
        q = (request.args.get("q") or "").strip()
        # An exact ADAM (e.g. 22SYMV010473684) jumps straight to the detail page.
        if len(q) >= 12 and q[:2].isdigit() and "SYMV" in q.upper():
            d = queries.contract_detail(g.conn, q)
            if d is not None:
                return redirect(url_for("contract_detail", adam=q))
        rows = queries.list_contracts(g.conn, q=q or None)
        total_eur = sum(r["total_cost_with_vat"] or 0 for r in rows)
        return render_template("contracts.html", rows=rows, q=q, total_eur=total_eur)

    @app.route("/contractor/<vat>")
    def contractor_detail(vat: str):
        summary = queries.contractor_summary(g.conn, vat)
        if summary is None:
            abort(404)
        return render_template(
            "contractor_detail.html",
            summary=summary,
            contracts=queries.contractor_contracts(g.conn, vat),
            partners=queries.consortium_partners(g.conn, vat),
            signers=queries.contractor_signers(g.conn, vat),
            location=queries.contractor_location(g.conn, vat),
        )

    @app.route("/contract/<adam>")
    def contract_detail(adam: str):
        d = queries.contract_detail(g.conn, adam)
        if d is None:
            abort(404)
        return render_template(
            "contract_detail.html",
            c=d,
            regions=queries.contract_project_regions(g.conn, adam),
        )

    @app.route("/authorities")
    def authorities():
        return render_template(
            "authorities.html",
            authorities=queries.list_authorities(g.conn),
            unit_operators=queries.list_unit_operators(g.conn),
            signers=queries.list_signers(g.conn),
        )

    @app.route("/api/contractors.json")
    def api_contractors():
        q = (request.args.get("q") or "").strip()
        sort = request.args.get("sort", "total_eur")
        return jsonify(queries.list_contractors(g.conn, q=q or None, sort=sort))

    @app.route("/map")
    def flow_map():
        target = (request.args.get("target") or "").strip() or None
        return render_template(
            "map.html",
            coverage=queries.flow_coverage(g.conn),
            target_filter=target,
            target_options=queries.project_region_origins(g.conn),
        )

    @app.route("/api/flows.json")
    def api_flows():
        target = (request.args.get("target") or "").strip() or None
        source = (request.args.get("source") or "").strip() or None
        return jsonify(queries.region_flows(g.conn, target_pe=target, source_pe=source))

    @app.route("/origins")
    def origins():
        return render_template(
            "origins.html",
            rows=queries.project_region_origins(g.conn),
            coverage=queries.flow_coverage(g.conn),
        )

    @app.route("/pdf/<kind>/<adam>")
    def pdf_attachment(kind: str, adam: str):
        """Serve a KHMDHS attachment from the local cache, fetching it from
        the registry on first request. The registry rate-limits bursts of
        attachment downloads (HTTP 429), so cache-and-serve keeps every
        repeat download instant and off the registry entirely; on a 429 the
        user gets an auto-retrying wait page instead of raw JSON.
        """
        spec = _PDF_KINDS.get(kind)
        if spec is None:
            abort(404)
        infix, url_template = spec
        if not re.fullmatch(rf"\d{{2}}{infix}\d{{6,12}}", adam):
            abort(404)

        cache_dir = Path(app.config["PDF_CACHE_DIR"])
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
        # as_attachment=False → Content-Disposition: inline, so the browser
        # renders the PDF in the tab; download_name still names the file if
        # the user chooses to save it.
        return send_file(
            path, mimetype="application/pdf",
            as_attachment=False, download_name=f"{adam}.pdf",
        )

    @app.errorhandler(404)
    def _not_found(_e):
        return render_template("404.html"), 404

    return app
