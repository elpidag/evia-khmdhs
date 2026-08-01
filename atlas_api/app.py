"""Atlas JSON API: Flask app factory + route registration.

Mirrors the webui factory pattern (eager khmdhs connection, lazy ΔΑΣΕ
connection so khmdhs-only endpoints never open dase.sqlite) but serves JSON
only — the HTML lives in the SvelteKit app under atlas/.
"""
from __future__ import annotations

import gzip
from pathlib import Path

from flask import Flask, Response, abort, g, jsonify, request

from khmdhs.config import DASE_DB, DEFAULT_DB, PDF_CACHE_DIR
from webui import dase_queries, queries

from atlas_api import pdf_proxy, queries_extra


def create_app(db_path: Path | None = None, dase_db_path: Path | None = None,
               pdf_cache_dir: Path | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder=None)
    app.config["DB_PATH"] = Path(db_path) if db_path else DEFAULT_DB
    app.config["DASE_DB_PATH"] = Path(dase_db_path) if dase_db_path else DASE_DB
    app.config["PDF_CACHE_DIR"] = (
        Path(pdf_cache_dir) if pdf_cache_dir else PDF_CACHE_DIR
    )
    app.json.ensure_ascii = False
    app.register_blueprint(pdf_proxy.bp)

    # ------------------------------------------------------------ caching
    # The DBs are committed files that change only on an explicit refresh,
    # so every /api response is a pure function of (path, query, DB mtimes).
    # First hit computes; repeats are served from memory, pre-gzipped.
    _resp_cache: dict[str, tuple[tuple, bytes, bytes | None]] = {}

    def _db_stamp() -> tuple:
        out = []
        for key in ("DB_PATH", "DASE_DB_PATH"):
            p = app.config[key]
            try:
                out.append(p.stat().st_mtime_ns)
            except OSError:
                out.append(None)
        return tuple(out)

    def _accepts_gzip() -> bool:
        return "gzip" in (request.headers.get("Accept-Encoding") or "")

    @app.before_request
    def _serve_cached():
        if request.method != "GET" or not request.path.startswith("/api"):
            return None
        key = request.full_path
        hit = _resp_cache.get(key)
        if hit is None or hit[0] != _db_stamp():
            return None
        _, raw, gz = hit
        if gz is not None and _accepts_gzip():
            return Response(gz, mimetype="application/json",
                            headers={"Content-Encoding": "gzip",
                                     "Vary": "Accept-Encoding"})
        return Response(raw, mimetype="application/json")

    @app.before_request
    def _open_db() -> None:
        g.conn = queries.open_ro(app.config["DB_PATH"])

    def _dase_conn():
        """Lazy second connection (ΔΑΣΕ dataset) — khmdhs-only endpoints
        never touch dase.sqlite."""
        if "dase_conn" not in g:
            g.dase_conn = queries.open_ro(app.config["DASE_DB_PATH"])
        return g.dase_conn

    @app.teardown_request
    def _close_db(exc) -> None:
        conn = g.pop("conn", None)
        if conn is not None:
            conn.close()
        dconn = g.pop("dase_conn", None)
        if dconn is not None:
            dconn.close()

    @app.after_request
    def _cache_headers(resp):
        # The DBs are committed files that change only on refresh — JSON is
        # safely cacheable for a few minutes.
        if resp.mimetype != "application/json":
            return resp
        resp.cache_control.public = True
        resp.cache_control.max_age = 300
        if request.method == "GET" and request.path.startswith("/api") \
                and resp.status_code == 200 \
                and "Content-Encoding" not in resp.headers:
            raw = resp.get_data()
            gz = gzip.compress(raw, 6) if len(raw) > 1024 else None
            if len(_resp_cache) > 200:      # bound growth from search queries
                _resp_cache.pop(next(iter(_resp_cache)))
            _resp_cache[request.full_path] = (_db_stamp(), raw, gz)
            if gz is not None and _accepts_gzip():
                resp.set_data(gz)
                resp.headers["Content-Encoding"] = "gzip"
                resp.headers["Vary"] = "Accept-Encoding"
        return resp

    # ------------------------------------------------------------- meta

    @app.route("/api/meta")
    def api_meta():
        try:
            dase = _dase_conn()
        except Exception:
            dase = None
        return jsonify(queries_extra.meta(g.conn, dase))

    # -------------------------------------------------------- Anti-nero

    @app.route("/api/antinero/overview")
    def api_antinero_overview():
        return jsonify(queries_extra.antinero_overview(g.conn))

    @app.route("/api/antinero/payments")
    def api_antinero_payments():
        return jsonify(queries_extra.payment_events(g.conn))

    @app.route("/api/antinero/sankey")
    def api_antinero_sankey():
        return jsonify(queries_extra.sankey_flows(g.conn))

    @app.route("/api/antinero/swarm")
    def api_antinero_swarm():
        return jsonify(queries_extra.contract_swarm(g.conn))

    @app.route("/api/antinero/pe-yearly")
    def api_antinero_pe_yearly():
        return jsonify(queries_extra.money_by_pe_yearly(g.conn))

    @app.route("/api/antinero/map")
    def api_antinero_map():
        conn = g.conn
        return jsonify({
            "work_regions": queries.money_by_project_region(conn),
            "home_regions": queries.money_by_contractor_region(conn),
            "coverage": queries.flow_coverage(conn),
            "contract_points": queries.contract_authority_points(conn),
            "contractor_points": queries.contractor_points(conn),
            "contracts": queries.overview_contracts(conn),
        })

    def _trim_titles(rows: list[dict], n: int = 140) -> list[dict]:
        # list views never need multi-hundred-char titles — trimming them
        # roughly halves the big list payloads
        for r in rows:
            t = r.get("title")
            if t and len(t) > n:
                r["title"] = t[: n - 1] + "…"
        return rows

    @app.route("/api/antinero/contracts")
    def api_antinero_contracts():
        qterm = (request.args.get("q") or "").strip() or None
        rows = _trim_titles(queries.list_contracts(g.conn, q=qterm))
        return jsonify({"rows": rows,
                        "total_eur": round(sum(r["total_cost_with_vat"] or 0
                                               for r in rows), 2)})

    @app.route("/api/antinero/contract/<adam>")
    def api_antinero_contract(adam: str):
        d = queries.contract_detail(g.conn, adam)
        if d is None:
            abort(404)
        d.pop("raw_json", None)
        d.pop("raw_pretty", None)
        d["regions"] = queries.contract_project_regions(g.conn, adam)
        d["sites"] = queries.contract_sites(g.conn, adam)
        return jsonify(d)

    @app.route("/api/antinero/contractors")
    def api_antinero_contractors():
        qterm = (request.args.get("q") or "").strip() or None
        sort = (request.args.get("sort") or "total_eur").strip()
        return jsonify(queries.list_contractors(g.conn, q=qterm, sort=sort))

    @app.route("/api/antinero/contractor/<vat>")
    def api_antinero_contractor(vat: str):
        summary = queries.contractor_summary(g.conn, vat)
        if summary is None:
            abort(404)
        return jsonify({
            "summary": summary,
            "contracts": queries.contractor_contracts(g.conn, vat),
            "partners": queries.consortium_partners(g.conn, vat),
            "signers": queries.contractor_signers(g.conn, vat),
            "location": queries.contractor_location(g.conn, vat),
            "map_data": queries.contractor_map_data(g.conn, vat),
            "yearly": queries.contractor_yearly(g.conn, vat),
        })

    # ------------------------------------------------------------- ΔΑΣΕ

    @app.route("/api/dase/overview")
    def api_dase_overview():
        return jsonify(queries_extra.dase_overview(_dase_conn()))

    @app.route("/api/dase/swarm")
    def api_dase_swarm():
        return jsonify(queries_extra.dase_swarm(_dase_conn()))

    @app.route("/api/dase/contracts")
    def api_dase_contracts():
        qterm = (request.args.get("q") or "").strip() or None
        rows = _trim_titles(dase_queries.list_contracts(_dase_conn(), q=qterm))
        return jsonify({"rows": rows,
                        "total_eur": round(sum(r["total_cost_with_vat"] or 0
                                               for r in rows), 2)})

    @app.route("/api/dase/contract/<adam>")
    def api_dase_contract(adam: str):
        d = queries.contract_detail(_dase_conn(), adam)
        if d is None:
            abort(404)
        d.pop("raw_json", None)
        d.pop("raw_pretty", None)
        return jsonify(d)

    @app.route("/api/dase/coops")
    def api_dase_coops():
        qterm = (request.args.get("q") or "").strip() or None
        return jsonify(dase_queries.list_coops(_dase_conn(), q=qterm))

    @app.route("/api/dase/coop/<vat>")
    def api_dase_coop(vat: str):
        conn = _dase_conn()
        summary = dase_queries.coop_summary(conn, vat)
        if summary is None:
            abort(404)
        return jsonify({
            "summary": summary,
            "contracts": dase_queries.coop_contracts(conn, vat),
            "yearly": dase_queries.coop_yearly(conn, vat),
            "units": dase_queries.coop_units(conn, vat),
        })

    # ------------------------------------------------------ cross-dataset

    @app.route("/api/connections")
    def api_connections():
        return jsonify(queries_extra.network_payload(g.conn))

    @app.route("/api/authorities")
    def api_authorities():
        try:
            dase = _dase_conn()
        except Exception:
            dase = None
        return jsonify(queries_extra.authorities_index(g.conn, dase))

    @app.route("/api/authority/<slug>")
    def api_authority(slug: str):
        try:
            dase = _dase_conn()
        except Exception:
            dase = None
        d = queries_extra.authority_profile(g.conn, dase, slug)
        if d is None:
            abort(404)
        return jsonify(d)

    @app.route("/api/compare")
    def api_compare():
        dase = _dase_conn()
        payload = dase_queries.compare_payload(g.conn, dase)
        payload["pipelines"] = queries_extra.pipelines(g.conn, dase)
        return jsonify(payload)

    return app
