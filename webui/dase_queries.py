"""Read-only SQL for the ΔΑΣΕ (forest-cooperative) dataset pages.

Everything here runs against data/processed/dase.sqlite — a SEPARATE
database from the Anti-nero khmdhs.sqlite (only `compare_payload` sees
both, read-only). Conventions (DATA_DECISIONS 2026-07-27):

- **Stated values, deduplicated** (`live_filter`): no payment orders are
  harvested for ΔΑΣΕ, so aggregates sum stated `total_cost_with_vat`
  after excluding cancelled rows and rows whose `next_reference_no`
  resolves to a stored successor (the successor restates the contract).
- **Co-ops key on the canonical VAT** (first 8–9-digit run, zero-padded
  to 9): the registry stores the same co-op under whitespace/spelling
  variants. Display names come from the curated `dase_contractors`.
- **Awarding organizations group by normalised name, never VAT** (VAT
  090273987 carries both ΥΠΕΝ and ΑΠΔ ΘΣΕ rows).
- Consortium contracts attribute the full value to each partner (same
  max-exposure convention as the Anti-nero pages).
"""
from __future__ import annotations

import re
import sqlite3

from khmdhs.greek_regions import canonical_pe
from webui import queries
from webui.queries import (
    _bin_values, _matches, _phonetic_fold, _search_norm, _year_of,
)

# ---------------------------------------------------------------------------
# Core fragments
# ---------------------------------------------------------------------------

def live_filter(alias: str = "co") -> str:
    """The ΔΑΣΕ analogue of scope_filter: non-cancelled rows that no
    stored successor supersedes. (dase.sqlite has no contract_scope.)"""
    return (f"{alias}.cancelled = 0 AND NOT EXISTS ("
            f"SELECT 1 FROM contracts nx "
            f"WHERE nx.reference_number = {alias}.next_reference_no)")


_VAT_RUN = re.compile(r"\d{8,9}")


def canonical_vat(vat: str | None) -> str | None:
    """First 8–9-digit run, zero-padded to 9 — collapses the registry's
    whitespace/accent/«ΚΑΙ»-glued keying variants onto one key."""
    m = _VAT_RUN.search(vat or "")
    return m.group(0).zfill(9) if m else None


_WS = re.compile(r"\s+")


def _org_key(name: str | None) -> str:
    """Awarding-org grouping key: collapse whitespace, unify dashes."""
    s = _WS.sub(" ", (name or "").strip())
    return s.replace("–", "-").replace("—", "-").replace(" - ", "-")


def coop_directory(conn: sqlite3.Connection) -> dict[str, dict]:
    """canonical VAT -> {name, form} from the curated dase_contractors."""
    out: dict[str, dict] = {}
    for r in conn.execute("SELECT vat_number, name, form FROM dase_contractors"):
        cv = canonical_vat(r["vat_number"])
        if cv and cv not in out:
            out[cv] = {"name": r["name"], "form": r["form"]}
    return out


def _percentile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = min(len(sorted_vals) - 1, int(q * len(sorted_vals)))
    return sorted_vals[idx]


# ---------------------------------------------------------------------------
# Dashboard aggregates
# ---------------------------------------------------------------------------

def kpis(conn: sqlite3.Connection) -> dict:
    rows = conn.execute(f"""
        SELECT co.total_cost_with_vat AS eur, co.procedure_type,
               co.organization_name, co.units_operator_name
        FROM contracts co WHERE {live_filter()}
    """).fetchall()
    values = sorted((r["eur"] or 0.0) for r in rows)
    n = len(rows)
    n_direct = sum(1 for r in rows
                   if (r["procedure_type"] or "").startswith("Απευθείας"))
    gross = conn.execute("""
        SELECT COUNT(*) AS n, ROUND(SUM(total_cost_with_vat), 2) AS eur,
               SUM(cancelled) AS n_cancelled
        FROM contracts
    """).fetchone()
    n_superseded = conn.execute(f"""
        SELECT COUNT(*) FROM contracts co
        WHERE co.cancelled = 0 AND EXISTS (SELECT 1 FROM contracts nx
              WHERE nx.reference_number = co.next_reference_no)
    """).fetchone()[0]
    coop_vats = {canonical_vat(r["vat_number"])
                 for r in conn.execute(f"""
                     SELECT c.vat_number FROM contractors c
                     JOIN contracts co USING (reference_number)
                     WHERE {live_filter()}
                 """)}
    coop_vats &= set(coop_directory(conn))
    return {
        "n_contracts": n,
        "total_eur": round(sum(values), 2),
        "n_coops": len(coop_vats),
        "n_orgs": len({_org_key(r["organization_name"]) for r in rows}),
        "n_units": len({_WS.sub(" ", (r["units_operator_name"] or "").strip())
                        for r in rows}),
        "pct_direct": round(100.0 * n_direct / n, 1) if n else 0,
        "median_eur": _percentile(values, 0.5),
        "p90_eur": _percentile(values, 0.9),
        "gross_n": gross["n"],
        "gross_eur": gross["eur"] or 0,
        "n_cancelled": gross["n_cancelled"],
        "n_superseded": n_superseded,
    }


def yearly_totals(conn: sqlite3.Connection) -> list[dict]:
    """Stated € and contract count per signature year (live rows)."""
    years: dict[str, dict] = {}
    for r in conn.execute(f"""
        SELECT co.contract_signed_date, co.submission_date,
               co.total_cost_with_vat AS eur
        FROM contracts co WHERE {live_filter()}
    """):
        y = _year_of(r["contract_signed_date"], r["submission_date"])
        if y is None:
            continue
        b = years.setdefault(y, {"year": y, "n": 0, "eur": 0.0})
        b["n"] += 1
        b["eur"] += r["eur"] or 0.0
    out = sorted(years.values(), key=lambda b: b["year"])
    for b in out:
        b["eur"] = round(b["eur"], 2)
    return out


def _coop_rows(conn: sqlite3.Connection) -> list[dict]:
    """One merged row per canonical co-op VAT over the live population."""
    directory = coop_directory(conn)
    rows = conn.execute(f"""
        SELECT c.vat_number, c.name, c.reference_number,
               co.total_cost_with_vat AS eur, co.procedure_type,
               co.units_operator_name
        FROM contractors c JOIN contracts co USING (reference_number)
        WHERE {live_filter()}
    """).fetchall()
    agg: dict[str, dict] = {}
    for r in rows:
        cv = canonical_vat(r["vat_number"])
        if cv is None:
            continue
        cur = directory.get(cv, {})
        a = agg.setdefault(cv, {
            "vat": cv,
            "name": cur.get("name") or r["name"],
            "form": cur.get("form"),
            "is_curated": cv in directory,
            "n_contracts": 0, "total_eur": 0.0,
            "n_direct": 0, "units": set(), "refs": set(),
        })
        if r["reference_number"] in a["refs"]:
            continue
        a["refs"].add(r["reference_number"])
        a["n_contracts"] += 1
        a["total_eur"] += r["eur"] or 0.0
        if (r["procedure_type"] or "").startswith("Απευθείας"):
            a["n_direct"] += 1
        a["units"].add(_WS.sub(" ", (r["units_operator_name"] or "").strip()))
    out = []
    for a in agg.values():
        a["total_eur"] = round(a["total_eur"], 2)
        a["n_units"] = len(a.pop("units"))
        a["pct_direct"] = (round(100.0 * a["n_direct"] / a["n_contracts"], 1)
                           if a["n_contracts"] else 0)
        a.pop("refs")
        out.append(a)
    return out


def top_coops(conn: sqlite3.Connection, limit: int = 10) -> list[dict]:
    return sorted(_coop_rows(conn), key=lambda a: -a["total_eur"])[:limit]


def list_coops(conn: sqlite3.Connection, q: str | None = None,
               sort: str = "total_eur") -> list[dict]:
    out = _coop_rows(conn)
    if q:
        needle = _search_norm(q)
        fold = _phonetic_fold(needle)
        out = [a for a in out if _matches(needle, fold, a["vat"], a["name"])]
    key = sort if sort in ("total_eur", "n_contracts", "name") else "total_eur"
    if key == "name":
        return sorted(out, key=lambda a: a["name"] or "")
    return sorted(out, key=lambda a: -(a[key] or 0))


# ---------------------------------------------------------------------------
# Co-op detail
# ---------------------------------------------------------------------------

def _vat_refs(conn: sqlite3.Connection, vat: str) -> list[str]:
    """All contract refs whose contractor VAT canonicalises to `vat`."""
    cv = canonical_vat(vat)
    if cv is None:
        return []
    refs = []
    for r in conn.execute(
            "SELECT reference_number, vat_number FROM contractors "
            "WHERE vat_number LIKE ?", (f"%{cv.lstrip('0')}%",)):
        if canonical_vat(r["vat_number"]) == cv:
            refs.append(r["reference_number"])
    return sorted(set(refs))


def coop_summary(conn: sqlite3.Connection, vat: str) -> dict | None:
    cv = canonical_vat(vat)
    refs = _vat_refs(conn, vat)
    if not refs:
        return None
    directory = coop_directory(conn)
    placeholders = ",".join("?" * len(refs))
    row = conn.execute(f"""
        SELECT COUNT(*) AS n_all,
               SUM(CASE WHEN {live_filter()} THEN 1 ELSE 0 END) AS n_live,
               ROUND(SUM(CASE WHEN {live_filter()}
                         THEN co.total_cost_with_vat ELSE 0 END), 2) AS eur,
               MIN(co.contract_signed_date) AS first_date,
               MAX(co.contract_signed_date) AS last_date
        FROM contracts co
        WHERE co.reference_number IN ({placeholders})
    """, refs).fetchone()
    names = [r[0] for r in conn.execute(f"""
        SELECT DISTINCT name FROM contractors
        WHERE reference_number IN ({placeholders}) ORDER BY name
    """, refs)]
    cur = directory.get(cv, {})
    return {
        "vat": cv,
        "name": cur.get("name") or (names[0] if names else cv),
        "form": cur.get("form"),
        "name_variants": names,
        "n_contracts": row["n_all"],
        "n_live": row["n_live"],
        "total_eur": row["eur"] or 0,
        "first_date": row["first_date"],
        "last_date": row["last_date"],
    }


def coop_contracts(conn: sqlite3.Connection, vat: str) -> list[dict]:
    """Live contracts only — superseded/cancelled registry rows stay out
    (coop_summary still reports the total registry-row count)."""
    refs = _vat_refs(conn, vat)
    if not refs:
        return []
    placeholders = ",".join("?" * len(refs))
    rows = conn.execute(f"""
        SELECT co.reference_number, co.title, co.contract_signed_date,
               co.total_cost_with_vat, co.procedure_type,
               co.units_operator_name, co.organization_name
        FROM contracts co
        WHERE co.reference_number IN ({placeholders}) AND {live_filter()}
        ORDER BY co.contract_signed_date DESC, co.reference_number DESC
    """, refs).fetchall()
    return [dict(r) for r in rows]


def coop_yearly(conn: sqlite3.Connection, vat: str) -> list[dict]:
    refs = _vat_refs(conn, vat)
    if not refs:
        return []
    placeholders = ",".join("?" * len(refs))
    years: dict[str, dict] = {}
    for r in conn.execute(f"""
        SELECT co.contract_signed_date, co.submission_date,
               co.total_cost_with_vat AS eur
        FROM contracts co
        WHERE co.reference_number IN ({placeholders}) AND {live_filter()}
    """, refs):
        y = _year_of(r["contract_signed_date"], r["submission_date"])
        if y is None:
            continue
        b = years.setdefault(y, {"year": y, "n": 0, "eur": 0.0})
        b["n"] += 1
        b["eur"] = round(b["eur"] + (r["eur"] or 0.0), 2)
    return sorted(years.values(), key=lambda b: b["year"])


def coop_units(conn: sqlite3.Connection, vat: str) -> list[dict]:
    refs = _vat_refs(conn, vat)
    if not refs:
        return []
    placeholders = ",".join("?" * len(refs))
    rows = conn.execute(f"""
        SELECT co.units_operator_name AS unit,
               co.organization_name AS org,
               COUNT(*) AS n_contracts,
               ROUND(SUM(co.total_cost_with_vat), 2) AS total_eur
        FROM contracts co
        WHERE co.reference_number IN ({placeholders}) AND {live_filter()}
        GROUP BY co.units_operator_name, co.organization_name
        ORDER BY total_eur DESC
    """, refs).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Awarders, mixes, histogram, regions
# ---------------------------------------------------------------------------

def top_orgs(conn: sqlite3.Connection, limit: int = 10) -> list[dict]:
    groups: dict[str, dict] = {}
    for r in conn.execute(f"""
        SELECT co.organization_name AS name, COUNT(*) AS n,
               ROUND(SUM(co.total_cost_with_vat), 2) AS eur
        FROM contracts co
        WHERE co.organization_name IS NOT NULL AND {live_filter()}
        GROUP BY co.organization_name
    """):
        key = _org_key(r["name"])
        g = groups.setdefault(key, {"name": r["name"], "n_contracts": 0,
                                    "total_eur": 0.0, "_top": 0})
        g["n_contracts"] += r["n"]
        g["total_eur"] = round(g["total_eur"] + (r["eur"] or 0.0), 2)
        if r["n"] > g["_top"]:                    # most frequent raw spelling
            g["_top"], g["name"] = r["n"], r["name"]
    out = sorted(groups.values(), key=lambda g: -g["total_eur"])[:limit]
    for g in out:
        g.pop("_top")
    return out


def top_units(conn: sqlite3.Connection, limit: int = 10) -> list[dict]:
    rows = conn.execute(f"""
        SELECT co.units_operator_name AS name,
               COUNT(*) AS n_contracts,
               ROUND(SUM(co.total_cost_with_vat), 2) AS total_eur
        FROM contracts co
        WHERE co.units_operator_name IS NOT NULL AND {live_filter()}
        GROUP BY co.units_operator_name
        ORDER BY total_eur DESC
        LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def procedure_mix(conn: sqlite3.Connection) -> list[dict]:
    """Same canonical grouping as queries.procedure_mix, stated values."""
    rows = conn.execute(f"""
        SELECT co.procedure_type, COUNT(*) AS n,
               ROUND(SUM(co.total_cost_with_vat), 2) AS eur
        FROM contracts co WHERE {live_filter()}
        GROUP BY co.procedure_type
    """).fetchall()
    groups: dict[str, dict] = {}
    for r in rows:
        raw = (r["procedure_type"] or "").strip()
        if raw.startswith("Απευθείας"):
            label = "Απευθείας ανάθεση"
        elif "Διαπραγμάτευση" in raw:
            label = "Διαπραγμάτευση χωρίς δημοσίευση"
        elif raw.startswith("Ανοιχτή") or raw.startswith("Ανοικτή"):
            label = "Ανοιχτή διαδικασία"
        else:
            label = raw or "Άγνωστη"
        g = groups.setdefault(label, {"label": label, "n_contracts": 0, "eur": 0.0})
        g["n_contracts"] += r["n"]
        g["eur"] = round(g["eur"] + (r["eur"] or 0.0), 2)
    return sorted(groups.values(), key=lambda g: -g["n_contracts"])


def type_mix(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(f"""
        SELECT COALESCE(co.contract_type, 'Άγνωστος') AS label,
               COUNT(*) AS n_contracts,
               ROUND(SUM(co.total_cost_with_vat), 2) AS eur
        FROM contracts co WHERE {live_filter()}
        GROUP BY co.contract_type
        ORDER BY n_contracts DESC
    """).fetchall()
    return [dict(r) for r in rows]


# 386 contracts carry CPV 66519300-4 «ασφαλιστικές υπηρεσίες» — a mass
# registry keying error on υλοτομικά contracts (DATA_DECISIONS 2026-07-26).
NOISE_CPVS = {"66519300-4"}


def cpv_mix(conn: sqlite3.Connection, limit: int = 12) -> list[dict]:
    rows = conn.execute(f"""
        SELECT cc.cpv_code AS cpv, MIN(cc.cpv_description) AS label,
               COUNT(DISTINCT cc.reference_number) AS n_contracts
        FROM contract_cpvs cc
        JOIN contracts co ON co.reference_number = cc.reference_number
        WHERE {live_filter()}
        GROUP BY cc.cpv_code
        ORDER BY n_contracts DESC
        LIMIT ?
    """, (limit,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["noise"] = d["cpv"] in NOISE_CPVS
        out.append(d)
    return out


# Doubling bins scaled to the ΔΑΣΕ distribution (median €7.4k, max €3.1M).
DASE_BIN_EDGES = (
    0, 1_000, 2_000, 4_000, 8_000, 16_000, 32_000, 64_000,
    125_000, 250_000, 500_000, 1_000_000, 2_000_000,
)


def _short_eur(v: float) -> str:
    if v >= 1_000_000:
        return f"{v / 1_000_000:g}M".replace(".", ",")
    return f"{v // 1000:g}k".replace(".0", "")


def _bin_labels(edges: tuple) -> list[str]:
    return ([f"≤{_short_eur(edges[1])}"] +
            [f"{_short_eur(edges[i])}–{_short_eur(edges[i + 1])}"
             for i in range(1, len(edges) - 1)] +
            [f"≥{_short_eur(edges[-1])}"])


def value_histogram(conn: sqlite3.Connection) -> dict:
    values = [r[0] or 0.0 for r in conn.execute(f"""
        SELECT co.total_cost_with_vat FROM contracts co WHERE {live_filter()}
    """)]
    h = _bin_values(values, DASE_BIN_EDGES)
    values.sort()
    h["median"] = values[len(values) // 2] if values else 0
    h["labels"] = _bin_labels(DASE_BIN_EDGES)
    return h


def money_by_pe(conn: sqlite3.Connection) -> dict:
    """Stated € and contract count per Π.Ε. (dase_contract_regions), plus
    the honest unresolved bucket (contracts with no derivable region)."""
    rows = conn.execute(f"""
        SELECT r.region_pe, COUNT(*) AS n,
               ROUND(SUM(co.total_cost_with_vat), 2) AS eur
        FROM contracts co
        LEFT JOIN dase_contract_regions r USING (reference_number)
        WHERE {live_filter()}
        GROUP BY r.region_pe
    """).fetchall()
    out, unresolved = [], {"n": 0, "eur": 0.0}
    for r in rows:
        if r["region_pe"] is None:
            unresolved = {"n": r["n"], "eur": r["eur"] or 0.0}
            continue
        pe = canonical_pe(r["region_pe"]) or r["region_pe"]
        out.append({"pe": pe, "n_contracts": r["n"], "eur": r["eur"] or 0.0})
    out.sort(key=lambda a: -a["eur"])
    return {"regions": out, "unresolved": unresolved}


# ---------------------------------------------------------------------------
# Contracts list
# ---------------------------------------------------------------------------

def list_contracts(conn: sqlite3.Connection, q: str | None = None) -> list[dict]:
    """Live ΔΑΣΕ contracts only (cancelled and superseded versions are
    excluded — the deduplicated population every aggregate uses), newest
    first; free-text search matches ADAM, title, co-op names, awarding
    unit and organization (accent/Greeklish-tolerant)."""
    rows = conn.execute(f"""
        SELECT co.reference_number, co.title, co.contract_signed_date,
               co.total_cost_with_vat,
               co.units_operator_name, co.organization_name,
               (SELECT GROUP_CONCAT(c.name, ' | ')
                  FROM contractors c
                 WHERE c.reference_number = co.reference_number)
                   AS contractor_names
        FROM contracts co
        WHERE {live_filter()}
        ORDER BY co.contract_signed_date DESC, co.reference_number DESC
    """).fetchall()
    out = [dict(r) for r in rows]
    if q:
        needle = _search_norm(q)
        fold = _phonetic_fold(needle)
        out = [r for r in out
               if _matches(needle, fold, r["reference_number"], r["title"],
                           r["contractor_names"], r["units_operator_name"],
                           r["organization_name"])]
    return out


# ---------------------------------------------------------------------------
# Anti-nero vs ΔΑΣΕ comparison (reads BOTH databases, read-only)
# ---------------------------------------------------------------------------

# One shared log2 edge set so the two size distributions are directly
# comparable (Anti-nero lots €1.5–8M vs ΔΑΣΕ median €7.4k).
COMPARE_BIN_EDGES = (
    0, 1_000, 2_000, 4_000, 8_000, 16_000, 32_000, 64_000, 125_000,
    250_000, 500_000, 1_000_000, 2_000_000, 4_000_000, 8_000_000, 16_000_000,
)


def compare_payload(kh_conn: sqlite3.Connection,
                    dase_conn: sqlite3.Connection) -> dict:
    kh_kpis = queries.kpis(kh_conn)
    d_kpis = kpis(dase_conn)

    kh_values = sorted(r[0] or 0.0 for r in kh_conn.execute(f"""
        SELECT {queries.effective_cost(kh_conn, 'k')} FROM contracts k
        WHERE {queries.scope_filter(kh_conn, 'k.reference_number')}
    """))
    d_values = sorted(r[0] or 0.0 for r in dase_conn.execute(f"""
        SELECT co.total_cost_with_vat FROM contracts co WHERE {live_filter()}
    """))

    kh_hist = _bin_values(kh_values, COMPARE_BIN_EDGES)
    d_hist = _bin_values(d_values, COMPARE_BIN_EDGES)

    def pct(counts, n):
        return [round(100.0 * c / n, 2) if n else 0 for c in counts]

    kh_yearly = queries.antinero_yearly(kh_conn)
    d_yearly = yearly_totals(dase_conn)
    all_years = sorted({b["year"] for b in kh_yearly} |
                       {b["year"] for b in d_yearly})
    kh_by_year = {b["year"]: b for b in kh_yearly}
    d_by_year = {b["year"]: b for b in d_yearly}

    kh_pe = {r["pe"]: r for r in queries.money_by_project_region(kh_conn)}
    d_pe_data = money_by_pe(dase_conn)
    d_pe = {r["pe"]: r for r in d_pe_data["regions"]}
    pes = sorted(set(kh_pe) | set(d_pe),
                 key=lambda p: -((kh_pe.get(p, {}).get("split_eur") or 0) +
                                 (d_pe.get(p, {}).get("eur") or 0)))
    by_pe = [{
        "pe": p,
        "antinero_eur": round(kh_pe.get(p, {}).get("split_eur") or 0.0, 2),
        "antinero_n": kh_pe.get(p, {}).get("n_contracts") or 0,
        "dase_eur": round(d_pe.get(p, {}).get("eur") or 0.0, 2),
        "dase_n": d_pe.get(p, {}).get("n_contracts") or 0,
    } for p in pes]

    kh_total = kh_kpis["total_eur"] or 0
    d_total = d_kpis["total_eur"] or 0
    return {
        "antinero": {
            **kh_kpis,
            "mean_eur": round(kh_total / kh_kpis["n_contracts"], 2)
                        if kh_kpis["n_contracts"] else 0,
            "median_eur": kh_values[len(kh_values) // 2] if kh_values else 0,
        },
        "dase": {
            **d_kpis,
            "mean_eur": round(d_total / d_kpis["n_contracts"], 2)
                        if d_kpis["n_contracts"] else 0,
        },
        "ratio": round(kh_total / d_total, 1) if d_total else None,
        "years": all_years,
        "yearly": {
            "antinero": [round(kh_by_year.get(y, {}).get("total_eur", 0.0), 2)
                         for y in all_years],
            "dase": [round(d_by_year.get(y, {}).get("eur", 0.0), 2)
                     for y in all_years],
        },
        "by_pe": by_pe,
        "dase_unresolved": d_pe_data["unresolved"],
        "hist": {
            "edges": list(COMPARE_BIN_EDGES),
            "labels": _bin_labels(COMPARE_BIN_EDGES),
            "antinero_pct": pct(kh_hist["counts"], kh_hist["n"]),
            "dase_pct": pct(d_hist["counts"], d_hist["n"]),
            "antinero_n": kh_hist["n"],
            "dase_n": d_hist["n"],
            "antinero_median": kh_values[len(kh_values) // 2] if kh_values else 0,
            "dase_median": d_values[len(d_values) // 2] if d_values else 0,
        },
    }
