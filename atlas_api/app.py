"""Atlas JSON API: Flask app factory + route registration.

Mirrors the webui factory pattern (eager khmdhs connection, lazy ΔΑΣΕ
connection so khmdhs-only endpoints never open dase.sqlite) but serves JSON
only — the HTML lives in the SvelteKit app under atlas/.
"""
from __future__ import annotations

import gzip
import os
from pathlib import Path

from flask import Flask, Response, abort, g, jsonify, request

from khmdhs.config import (ANADOHOI_DB, ANADOHOI_PDF_CACHE, DASE_DB,
                           DEFAULT_DB, PDF_CACHE_DIR)
from webui import dase_queries, queries

from atlas_api import pdf_proxy, queries_extra


def create_app(db_path: Path | None = None, dase_db_path: Path | None = None,
               pdf_cache_dir: Path | None = None,
               anadohoi_db_path: Path | None = None,
               anadohoi_pdf_cache: Path | None = None,
               pdf_cache_budget_mb: int | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder=None)
    # How much the on-demand PDF caches may grow before the proxy stops
    # keeping downloads (0 = unlimited, the local default). The container sets
    # ATLAS_PDF_CACHE_BUDGET_MB because its writable disk is memory.
    app.config["PDF_CACHE_BUDGET_MB"] = int(
        pdf_cache_budget_mb if pdf_cache_budget_mb is not None
        else (os.environ.get("ATLAS_PDF_CACHE_BUDGET_MB") or 0)
    )
    app.config["DB_PATH"] = Path(db_path) if db_path else DEFAULT_DB
    app.config["DASE_DB_PATH"] = Path(dase_db_path) if dase_db_path else DASE_DB
    app.config["ANADOHOI_DB_PATH"] = (
        Path(anadohoi_db_path) if anadohoi_db_path else ANADOHOI_DB
    )
    app.config["PDF_CACHE_DIR"] = (
        Path(pdf_cache_dir) if pdf_cache_dir else PDF_CACHE_DIR
    )
    app.config["ANADOHOI_PDF_CACHE"] = (
        Path(anadohoi_pdf_cache) if anadohoi_pdf_cache else ANADOHOI_PDF_CACHE
    )
    # The Αρωγή dataset (data/processed/arogi.sqlite) is NOT served: its
    # pages and endpoints left the site on 2026-08-23 (user); the data, the
    # harvest and `queries_extra.arogi_*` stay in the repository.
    app.json.ensure_ascii = False
    app.register_blueprint(pdf_proxy.bp)

    # ------------------------------------------------------------ caching
    # The DBs are committed files that change only on an explicit refresh,
    # so every /api response is a pure function of (path, query, DB mtimes).
    # First hit computes; repeats are served from memory, pre-gzipped.
    _resp_cache: dict[str, tuple[tuple, bytes, bytes | None]] = {}

    def _db_stamp() -> tuple:
        out = []
        for key in ("DB_PATH", "DASE_DB_PATH", "ANADOHOI_DB_PATH"):
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

    # Atlas presents every € net of ΦΠΑ, and contract-value analytics use
    # STATED values (DATA_DECISIONS 2026-08-03): g.conn passes through
    # apply_stated_basis (net views + an empty contract_payments view, so
    # every frozen effective_cost() collapses to the stated column). The
    # payments layer (strip timeline, disbursement, paid KPIs, per-contract
    # payment lists) reads through the lazy _pay_conn(), which sees the
    # real payment rows (net). The anadohoi DB has no VAT columns — its
    # net preference is explicit.
    @app.before_request
    def _open_db() -> None:
        g.conn = queries_extra.apply_stated_basis(
            queries.open_ro(app.config["DB_PATH"]))

    def _pay_conn():
        """Lazy khmdhs connection WITH payments (net basis) — the
        payments layer only; analytics stay on the stated-basis g.conn."""
        if "pay_conn" not in g:
            g.pay_conn = queries_extra.apply_net_basis(
                queries.open_ro(app.config["DB_PATH"]))
        return g.pay_conn

    def _dase_conn():
        """Lazy second connection (ΔΑΣΕ dataset) — khmdhs-only endpoints
        never touch dase.sqlite."""
        if "dase_conn" not in g:
            g.dase_conn = queries_extra.apply_net_basis(
                queries.open_ro(app.config["DASE_DB_PATH"]))
        return g.dase_conn

    def _anadohoi_conn():
        """Lazy third connection (Ανάδοχοι sponsor-acts dataset)."""
        if "anadohoi_conn" not in g:
            g.anadohoi_conn = queries.open_ro(app.config["ANADOHOI_DB_PATH"])
        return g.anadohoi_conn

    @app.teardown_request
    def _close_db(exc) -> None:
        conn = g.pop("conn", None)
        if conn is not None:
            conn.close()
        for key in ("pay_conn", "dase_conn", "anadohoi_conn"):
            extra = g.pop(key, None)
            if extra is not None:
                extra.close()

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
        try:
            ana = _anadohoi_conn()
        except Exception:
            ana = None
        return jsonify(queries_extra.meta(g.conn, dase, ana, _pay_conn()))

    # -------------------------------------------------------- Anti-nero

    @app.route("/api/antinero/overview")
    def api_antinero_overview():
        return jsonify(queries_extra.antinero_overview(g.conn, _pay_conn()))

    @app.route("/api/antinero/payments")
    def api_antinero_payments():
        return jsonify(queries_extra.payment_events(_pay_conn()))

    @app.route("/api/antinero/sankey")
    def api_antinero_sankey():
        return jsonify(queries_extra.sankey_flows(g.conn))

    @app.route("/api/antinero/unit-flow")
    def api_antinero_unit_flow():
        return jsonify(queries_extra.unit_flows(g.conn))

    @app.route("/api/antinero/network")
    def api_antinero_network():
        return jsonify(queries_extra.antinero_network(g.conn))

    @app.route("/api/antinero/swarm")
    def api_antinero_swarm():
        return jsonify(queries_extra.contract_swarm(g.conn))

    @app.route("/api/antinero/pe-yearly")
    def api_antinero_pe_yearly():
        return jsonify(queries_extra.money_by_pe_yearly(g.conn))

    @app.route("/api/antinero/map")
    def api_antinero_map():
        conn = g.conn
        payload = {
            "work_regions": queries.money_by_project_region(conn),
            "home_regions": queries.money_by_contractor_region(conn),
            "coverage": queries.flow_coverage(conn),
            "contract_points": queries.contract_authority_points(conn),
            "contractor_points": queries.contractor_points(conn),
            "contracts": queries.overview_contracts(conn),
        }
        # curated display names on the HQ dots and the drill tables
        # (DATA_DECISIONS 2026-08-20); the registry spelling rides along
        names = queries_extra.antinero_display_names(conn)

        def _dn(row, vat_key="vat"):
            d = names.get((row.get(vat_key) or "").strip())
            if d and row.get("name") != d["el"]:
                row["registry_name"] = row.get("name")
                row["name"] = d["el"]

        for pt in payload["contractor_points"]["points"]:
            _dn(pt)
        for c in payload["contracts"]:
            for ct in c.get("contractors") or []:
                _dn(ct)
        return jsonify(payload)

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
        # the detail page shows the payments layer → needs the pay conn
        pay = _pay_conn()
        d = queries.contract_detail(pay, adam)
        if d is None:
            abort(404)
        d.pop("raw_json", None)
        d.pop("raw_pretty", None)
        d["regions"] = queries.contract_project_regions(g.conn, adam)
        d["sites"] = queries.contract_sites(g.conn, adam)
        # own records only: the other lots of a multi-lot award are not
        # documents of this contract — the diagram carries that relation
        d["timeline"] = queries_extra.contract_timeline(
            g.conn, adam, own_records_only=True)
        # the procurement family the contract's own text names
        d["family"] = queries_extra.contract_family(g.conn, adam)
        d["gross"] = queries_extra.contract_gross(pay, adam)
        d["category"] = queries_extra.contract_category(g.conn, adam)
        # who signed it, where the registry named someone else
        d["party_correction"] = queries_extra.contract_party_correction(adam)
        # a joint venture wound up after the job still signed the contract:
        # name it, and say what the register says about it now
        # each party under its curated display name, registry spelling beside it
        queries_extra.overlay_contractor_names(g.conn, d.get("contractors") or [])
        d["contractor_status"] = queries_extra.contractor_registry_status(
            g.conn, [c.get("vat_number") for c in d.get("contractors", [])])
        # what the works ARE (multi-label, from the contract's own title)
        # and the deadline the contract itself states (DATA_DECISIONS
        # 2026-08-19) — the registry duration rides along as the crosscheck
        d["work_themes"] = queries_extra.contract_work_themes(g.conn, adam)
        # study / works / study and works — the 1-2-3 model (2026-08-22)
        d["deliverables"] = queries_extra.contract_deliverables(g.conn, adam)
        d["stated_duration"] = queries_extra.contract_stated_duration(g.conn, adam)
        # the δήμοι its documents place the works in — one level finer than
        # the Π.Ε. layer (DATA_DECISIONS 2026-08-19)
        d["municipalities"] = queries_extra.contract_municipalities(g.conn, adam)
        d["authorities"] = queries_extra.contract_authorities(g.conn, adam)
        d["document_kind"] = queries_extra.contract_document_kind(g.conn, adam)
        # the contract's own version chain (τροποποιήσεις, παρατάσεις,
        # εγκρίσεις συμπληρωματικών) — the registry chain does not carry it
        d["chain"] = queries_extra.contract_chain(g.conn, adam)
        # what the contract PROMISED — the deadline it announced and every
        # act that moved it; the timeline bar draws that, not the paperwork
        d["deadlines"] = queries_extra.contract_deadlines(g.conn, adam)
        # ΚΗΜΔΗΣ files a later act under the CONTRACT's signature date; the
        # header must show the date of THIS document (DATA_DECISIONS 2026-08-19)
        own_d, own_basis = queries_extra.record_date(
            adam, (d.get("document_kind") or {}).get("kind"),
            d.get("contract_signed_date"))
        d["own_date"], d["own_date_basis"] = own_d, own_basis
        # a date for every payment tick on the timeline: 182 of the 886 live
        # orders carry only the submission stamp, which contract_detail omits
        pdates = queries_extra.payment_dates(pay, adam)
        for p in d.get("payments") or []:
            p["d"] = pdates.get(p["payment_ref"])
        return jsonify(d)

    @app.route("/api/antinero/contractors")
    def api_antinero_contractors():
        qterm = (request.args.get("q") or "").strip() or None
        sort = (request.args.get("sort") or "total_eur").strip()
        return jsonify(queries_extra.antinero_contractors_list(
            g.conn, qterm=qterm, sort=sort))

    @app.route("/api/antinero/contractor/<vat>")
    def api_antinero_contractor(vat: str):
        summary = queries_extra.antinero_contractor_summary(g.conn, vat)
        if summary is None:
            abort(404)
        return jsonify({
            "summary": summary,
            "contracts": queries.contractor_contracts(g.conn, vat),
            "partners": queries.consortium_partners(g.conn, vat),
            "signers": queries.contractor_signers(g.conn, vat),
            "location": queries.contractor_location(g.conn, vat),
            "map_data": queries.contractor_map_data(g.conn, vat),
            "yearly": queries.contractor_yearly(_pay_conn(), vat),
        })

    # ------------------------------------------------------------- ΔΑΣΕ

    @app.route("/api/dase/overview")
    def api_dase_overview():
        return jsonify(queries_extra.dase_overview(_dase_conn(), g.conn))

    @app.route("/api/dase/allocation")
    def api_dase_allocation():
        # the works/seats choropleth duo (DATA_DECISIONS 2026-08-24)
        return jsonify(queries_extra.dase_allocation(_dase_conn()))

    @app.route("/api/dase/map")
    def api_dase_map():
        return jsonify(queries_extra.dase_map(_dase_conn(), g.conn))

    @app.route("/api/dase/swarm")
    def api_dase_swarm():
        return jsonify(queries_extra.dase_swarm(_dase_conn()))

    @app.route("/api/dase/contracts")
    def api_dase_contracts():
        qterm = (request.args.get("q") or "").strip() or None
        conn = _dase_conn()
        rows = _trim_titles(dase_queries.list_contracts(conn, q=qterm))
        total = round(sum(r["total_cost_with_vat"] or 0 for r in rows), 2)
        # a search may cite an EXCLUDED contract's ΑΔΑΜ — surface it, badged
        # for the reason it carries (duplicate_of / related_to), never
        # counted in the total
        if qterm:
            rows = rows + _trim_titles(
                queries_extra.dase_excluded_hits(conn, qterm))
        # curated display names replace the registry spellings in the list
        # (search above already ran on the registry strings, so both match)
        disp = queries_extra.dase_contract_display(conn)
        for r in rows:
            r["contractor_names"] = (disp.get(r["reference_number"])
                                     or r["contractor_names"])
        return jsonify({"rows": rows, "total_eur": total})

    @app.route("/api/dase/contract/<adam>")
    def api_dase_contract(adam: str):
        conn = _dase_conn()
        d = queries.contract_detail(conn, adam)
        if d is None:
            abort(404)
        d.pop("raw_json", None)
        d.pop("raw_pretty", None)
        # the same rule as Anti-nero (user, 2026-08-19): the TABLE holds this
        # contract's own records, and the other lots of the procurement —
        # which the registry's adamChain returns — feed the family DIAGRAM
        d["timeline"] = queries_extra.contract_timeline(
            conn, adam, own_records_only=True)
        d["family_acts"] = queries_extra.contract_timeline(conn, adam)
        # the Anti-nero-style radial (user, 2026-08-29): the call at the centre,
        # the family's contracts around it
        d["family"] = queries_extra.dase_contract_family(conn, adam)
        d["gross"] = queries_extra.contract_gross(conn, adam)
        # registry double-postings kept reachable + cross-linked both ways
        d["duplicates"] = [r[0] for r in conn.execute(
            "SELECT reference_number FROM contracts WHERE duplicate_of = ?",
            (adam,))]
        d["geo"] = queries_extra.dase_contract_geo(conn, g.conn, adam)
        # curated display names ADDED per contractor (name keeps the registry
        # spelling — the FamilyTree matches siblings on registry names)
        names = queries_extra.dase_display_names(conn)
        for ct in d["contractors"]:
            disp = names.get(dase_queries.canonical_vat(ct["vat_number"]) or "")
            if disp:
                ct["display_el"], ct["display_en"] = disp["el"], disp["en"]
        # the page mirrors the Anti-nero one (DATA_DECISIONS 2026-08-23): the
        # curated work-type category + its fire context, the version chain
        # from the registry links, the document-stated deadline (and only
        # that), and a date for every payment tick
        d["category"] = queries_extra.contract_category(conn, adam)
        d["fire_context"] = queries_extra.contract_fire_context(conn, adam)
        d["chain"] = queries_extra.dase_contract_chain(conn, adam)
        d["stated_duration"] = queries_extra.contract_stated_duration(conn, adam)
        d["deadlines"] = queries_extra.dase_contract_deadlines(conn, adam)
        pdates = queries_extra.payment_dates(conn, adam)
        for p in d.get("payments") or []:
            p["d"] = pdates.get(p["payment_ref"])
        return jsonify(d)

    @app.route("/api/dase/coops")
    def api_dase_coops():
        qterm = (request.args.get("q") or "").strip() or None
        # display-name aware variant of the frozen list_coops (search
        # matches curated Greek + English names AND the registry spelling)
        return jsonify(queries_extra.dase_coops(_dase_conn(), q=qterm))

    @app.route("/api/dase/coop/<vat>")
    def api_dase_coop(vat: str):
        conn = _dase_conn()
        summary = dase_queries.coop_summary(conn, vat)
        if summary is None:
            abort(404)
        queries_extra._overlay_coop_name(
            summary, queries_extra.dase_display_names(conn))
        # jointly held contracts are split evenly across their partners
        # (DATA_DECISIONS 2026-08-17) — the frozen queries credit each
        # partner with the whole contract
        return jsonify(queries_extra.dase_coop_detail(
            conn, vat, summary,
            dase_queries.coop_contracts(conn, vat),
            dase_queries.coop_yearly(conn, vat),
            dase_queries.coop_units(conn, vat)))

    # ---------------------------------------------------------- anadohoi

    def _dase_names():
        """Curated co-op display names for the executor overlay — empty
        when the ΔΑΣΕ DB is absent (executors then keep act spellings)."""
        try:
            return queries_extra.dase_display_names(_dase_conn())
        except Exception:
            return {}

    @app.route("/api/anadohoi/overview")
    def api_anadohoi_overview():
        out = queries_extra.anadohoi_overview(_anadohoi_conn())
        names = _dase_names()
        for p in out["projects"]:
            queries_extra.overlay_executor_names(p.get("executors"), names)
        return jsonify(out)

    @app.route("/api/anadohoi/crew-flows")
    def api_anadohoi_crew_flows():
        # WHO DID THE WORK as geography (DATA_DECISIONS 2026-08-24): the
        # seats come from the ΔΑΣΕ layer, so degrade honestly without it
        try:
            dase = _dase_conn()
        except Exception:
            dase = None
        return jsonify(queries_extra.anadohoi_crew_flows(_anadohoi_conn(), dase))

    @app.route("/api/anadohoi/project/<ada>")
    def api_anadohoi_project(ada: str):
        p = queries_extra.anadohoi_project(_anadohoi_conn(), ada)
        if p is None:
            abort(404)
        queries_extra.overlay_executor_names(p.get("executors"), _dase_names())
        return jsonify(p)

    # ----------------------------------------------------------- explore

    @app.route("/api/explore")
    def api_explore():
        try:
            dase = _dase_conn()
        except Exception:
            dase = None
        try:
            ana = _anadohoi_conn()
        except Exception:
            ana = None
        return jsonify(queries_extra.explore_rows(g.conn, dase, ana))

    # ----------------------------------------------------------- landing

    @app.route("/api/landing")
    def api_landing():
        """The field of codes on the landing page — every identifier the
        three datasets hold; degrades like /api/meta when a DB is absent."""
        try:
            dase = _dase_conn()
        except Exception:
            dase = None
        try:
            ana = _anadohoi_conn()
        except Exception:
            ana = None
        return jsonify(queries_extra.landing_codes(g.conn, dase, ana))

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
        return jsonify({
            "authorities": queries_extra.authorities_index(g.conn, dase),
            # the rest of the ΥΠΕΝ network — units with no recorded contracts
            "other_units": queries_extra.forest_units_extra(g.conn),
            # the map's other two dot populations (user, 2026-08-25)
            **queries_extra.authorities_map_points(g.conn, dase),
        })

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
        payload["dots"] = queries_extra.state_funded_dots(g.conn, dase)
        return jsonify(payload)

    return app
