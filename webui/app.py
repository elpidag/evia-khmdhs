"""Flask app: routes + DB connection management."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import Flask, abort, g, jsonify, redirect, render_template, request, url_for

from khmdhs.config import DEFAULT_DB
from webui import filters, queries


def create_app(db_path: Path | None = None) -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["DB_PATH"] = Path(db_path) if db_path else DEFAULT_DB
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
        )

    @app.route("/contract/<adam>")
    def contract_detail(adam: str):
        d = queries.contract_detail(g.conn, adam)
        if d is None:
            abort(404)
        return render_template("contract_detail.html", c=d)

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

    @app.errorhandler(404)
    def _not_found(_e):
        return render_template("404.html"), 404

    return app
