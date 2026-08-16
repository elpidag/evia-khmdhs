# -*- coding: utf-8 -*-
"""Extraction phase of the public-bodies registry (DATA_DECISIONS 2026-08-16).

Sweeps every distinct AWARDING-organization string across the three DBs
(khmdhs contracts, dase contracts, anadohoi decisions), groups spellings
into proposed bodies (by ΑΦΜ where stored, else by folded name), proposes
a kind/scope by name stems, matches municipal bodies onto
greek_municipalities.json (genitive fold, compact match) and CROSS-CHECKS
the match against the Π.Ε. of the body's own contracts
(dase_contract_regions) — duplicate municipality names resolve by Π.Ε.
agreement, never by name alone (the Ηρακλείου lesson, CLAUDE.md #17).

Outputs:
  data/processed/public_bodies_worksheet.json  (gitignored)
  public_bodies_curator.html                   (committed; user reviews,
                                                exports verdict JSON)

Proposals are NEVER final — every verdict is the user's.
"""
from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KH = ROOT / "data/processed/khmdhs.sqlite"
DA = ROOT / "data/processed/dase.sqlite"
AN = ROOT / "data/processed/anadohoi.sqlite"
MUNI = ROOT / "khmdhs/data/greek_municipalities.json"
OUT = ROOT / "data/processed/public_bodies_worksheet.json"
CURATOR = ROOT / "public_bodies_curator.html"

# ΑΦΜ known to be SHARED across distinct bodies — never group by these
SHARED_VATS = {"090273987"}  # ΥΠΕΝ + ΑΠΔ Θεσσαλίας-Στερεάς post-reform rows

_LAT2GR = str.maketrans("ABEZHIKMNOPTYXΑ", "ΑΒΕΖΗΙΚΜΝΟΡΤΥΧΑ")


def fold(s: str) -> str:
    """accent-strip, uppercase, Latin homoglyphs→Greek, punctuation→space."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").upper()
    s = s.translate(_LAT2GR)
    s = re.sub(r"[^\w]+", " ", s, flags=re.UNICODE)
    return re.sub(r"\s+", " ", s).strip()


def compact(s: str) -> str:
    return fold(s).replace(" ", "")


TRANSLIT = {
    "Α": "a", "Β": "v", "Γ": "g", "Δ": "d", "Ε": "e", "Ζ": "z", "Η": "i",
    "Θ": "th", "Ι": "i", "Κ": "k", "Λ": "l", "Μ": "m", "Ν": "n", "Ξ": "x",
    "Ο": "o", "Π": "p", "Ρ": "r", "Σ": "s", "Τ": "t", "Υ": "y", "Φ": "f",
    "Χ": "ch", "Ψ": "ps", "Ω": "o", "Σ": "s",
}


def slugify(name: str) -> str:
    out = []
    for c in fold(name):
        if c == " ":
            out.append("-")
        elif c in TRANSLIT:
            out.append(TRANSLIT[c])
        elif c.isascii() and c.isalnum():
            out.append(c.lower())
    slug = re.sub(r"-+", "-", "".join(out)).strip("-")
    return slug[:60]


# ---------------------------------------------------------------- kinds
# stems match on TOKEN boundaries («ΔΗΜΟΣΙΑ ΥΠΗΡΕΣΙΑ…» must not hit ΔΗΜΟΣ);
# multi-token stems match as phrases; compact stems (ΔΕΥΑ) also match the
# dotted spellings («Δ.Ε.Υ.Α ΛΑΓΚΑΔΑ»)
KIND_RULES = [
    ("decentralized_administration", ["ΑΠΟΚΕΝΤΡΩΜΕΝΗ"]),
    ("ministry", ["ΥΠΟΥΡΓΕΙΟ"]),
    ("state_vehicle", ["ΤΑΙΠΕΔ", "ΕΕΣΥΠ", "ΕΤΑΙΡΕΙΑ ΣΥΜΜΕΤΟΧΩΝ"]),
    # entity stems BEFORE the bare region/municipality stems
    ("municipal_entity", ["ΔΕΥΑ", "ΔΗΜΟΤΙΚΗ", "ΔΗΜΟΤΙΚΟ", "ΣΧΟΛΙΚΕΣ ΕΠΙΤΡΟΠΕΣ"]),
    ("other_public", ["ΠΕΡΙΦΕΡΕΙΑΚΟ ΤΑΜΕΙΟ", "ΠΕΡΙΦΕΡΕΙΑΚΗ ΕΝΩΣΗ",
                      "ΥΠΗΡΕΣΙΑ ΑΠΑΣΧΟΛΗΣΗΣ", "ΠΡΑΣΙΝΟ ΤΑΜΕΙΟ", "ΔΥΠΕ",
                      "ΠΑΝΕΠΙΣΤΗΜΙΑΚΩΝ ΔΑΣΩΝ"]),
    ("region", ["ΠΕΡΙΦΕΡΕΙΑ", "ΠΕΡΙΦΕΡΕΙΑΣ"]),
    ("municipality", ["ΔΗΜΟΣ", "ΔΗΜΟΥ", "ΔΗΜΟ"]),
    ("other_public", ["ΝΟΣΟΚΟΜΕΙΟ", "ΠΑΝΕΠΙΣΤΗΜΙΟ", "ΑΡΙΣΤΟΤΕΛΕΙΟ",
                      "ΕΦΟΡΕΙΑ", "ΟΣΕ", "ΣΙΔΗΡΟΔΡΟΜΩΝ", "ΑΔΜΗΕ",
                      "ΔΙΑΧΕΙΡΙΣΤΗΣ", "ΛΙΜΕΝΟΣ", "ΛΙΜΕΝΙΚΟ",
                      "ΓΕΝΙΚΟ ΕΠΙΤΕΛΕΙΟ", "ΠΟΛΕΜΙΚΗ ΑΕΡΟΠΟΡΙΑ", "ΙΔΡΥΜΑ",
                      "ΟΡΓΑΝΙΣΜΟΣ", "ΤΑΜΕΙΟ", "ΚΕΝΤΡΟ"]),
]
SCOPE_OF_KIND = {
    "municipality": "municipal", "municipal_entity": "municipal",
    "region": "regional", "ministry": "national",
    "decentralized_administration": "national", "state_vehicle": "national",
    "other_public": "seat",
}
# municipal-entity / municipality prefixes stripped before toponym matching
TOPO_STRIP = [
    "ΔΗΜΟΤΙΚΗ ΕΠΙΧΕΙΡΗΣΗ ΥΔΡΕΥΣΗΣ ΑΠΟΧΕΤΕΥΣΗΣ", "ΔΗΜΟΤΙΚΟ ΛΙΜΕΝΙΚΟ ΤΑΜΕΙΟ",
    "ΔΕΥΑ", "Δ Ε Υ Α", "ΔΗΜΟΣ", "ΔΗΜΟΥ", "ΔΗΜΟ",
]


# municipalities renamed/split AFTER the Kallikratis layer we key on —
# proposals map onto the containing 325-layer municipality, user confirms
POST_KALLIKRATIS = {
    "ΜΕΤΕΩΡΩΝ": "ΚΑΛΑΜΠΑΚΑΣ",              # renamed 2018
    "ΜΥΤΙΛΗΝΗΣ": "ΛΕΣΒΟΥ",                  # split 2019
    "ΔΥΤΙΚΗΣΛΕΣΒΟΥ": "ΛΕΣΒΟΥ",
    "ΒΕΛΒΕΝΤΟΥ": "ΣΕΡΒΙΩΝΒΕΛΒΕΝΤΟΥ",        # split 2019
    "ΑΝΑΤΟΛΙΚΗΣΣΑΜΟΥ": "ΣΑΜΟΥ",
    "ΔΥΤΙΚΗΣΣΑΜΟΥ": "ΣΑΜΟΥ",
    "ΚΕΝΤΡΙΚΗΣΚΕΡΚΥΡΑΣ": "ΚΕΡΚΥΡΑΣ",
    "ΒΟΡΕΙΑΣΚΕΡΚΥΡΑΣ": "ΚΕΡΚΥΡΑΣ",
    "ΝΟΤΙΑΣΚΕΡΚΥΡΑΣ": "ΚΕΡΚΥΡΑΣ",
}


def propose_kind(folded: str) -> str:
    tokens = folded.split()
    cpt = folded.replace(" ", "")
    for kind, stems in KIND_RULES:
        for st in stems:
            if " " in st:
                if st in folded:
                    return kind
            elif st in tokens or (st == "ΔΕΥΑ" and cpt.startswith("ΔΕΥΑ")):
                return kind
    return "review"


def toponym_candidates(folded: str) -> list[str]:
    """candidate toponym strings, best-first: after a strip-prefix, after a
    mid-string «ΔΗΜΟΥ», the last two tokens, the last token"""
    out = []
    t = folded
    for st in sorted(TOPO_STRIP, key=len, reverse=True):
        if t.startswith(st + " "):
            out.append(t[len(st):].strip())
            break
    tokens = [tk for tk in folded.split() if tk not in ("Α", "Ε", "ΑΕ")]
    if "ΔΗΜΟΥ" in tokens:
        i = tokens.index("ΔΗΜΟΥ")
        if i + 1 < len(tokens):
            out.append(" ".join(tokens[i + 1:]))
    if len(tokens) >= 2:
        out.append(" ".join(tokens[-2:]))
    if tokens:
        out.append(tokens[-1])
    # post-Kallikratis renames map onto the 325-layer name
    out += [POST_KALLIKRATIS[compact(c)] for c in list(out)
            if compact(c) in POST_KALLIKRATIS]
    return out


def main() -> None:
    munis = json.loads(MUNI.read_text(encoding="utf-8"))
    # compact genitive name → [(code, pe)]
    muni_ix: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for code, m in munis.items():
        muni_ix[compact(m["name"])].append((code, m["pe"]))

    # ---- collect spellings ------------------------------------------------
    # spelling → {datasets, n, net, vats, org_keys}
    spell: dict[str, dict] = {}

    def add(name: str, ds: str, n: int, net: float, vat: str | None, okey: str | None):
        e = spell.setdefault(name, {
            "datasets": set(), "n": 0, "net": 0.0,
            "vats": Counter(), "org_keys": Counter()})
        e["datasets"].add(ds)
        e["n"] += n
        e["net"] += net or 0.0
        if vat:
            e["vats"][vat] += n
        if okey:
            e["org_keys"][okey] += n

    for db, ds in ((KH, "antinero"), (DA, "dase")):
        conn = sqlite3.connect(db)
        for name, n, net, raws in conn.execute(
                """SELECT organization_name, COUNT(*),
                          SUM(CASE WHEN cancelled=1 THEN 0
                                   ELSE COALESCE(total_cost_without_vat,0) END),
                          MIN(raw_json)
                   FROM contracts WHERE organization_name IS NOT NULL
                   GROUP BY organization_name"""):
            j = json.loads(raws)
            vat = j.get("organizationVatNumber")
            okey = (j.get("organization") or {}).get("key")
            add(name, ds, n, net, vat, okey)
        conn.close()

    an = sqlite3.connect(AN)
    for name, n in an.execute(
            "SELECT org, COUNT(*) FROM decisions "
            "WHERE org IS NOT NULL AND TRIM(org) != '' GROUP BY org"):
        add(name, "anadohoi", n, 0.0, None, None)
    an.close()

    # Π.Ε. profile per spelling (dase curated regions — the cross-check basis)
    da = sqlite3.connect(DA)
    pe_of: dict[str, Counter] = defaultdict(Counter)
    for name, pe, n in da.execute(
            """SELECT c.organization_name, r.region_pe, COUNT(*)
               FROM contracts c JOIN dase_contract_regions r
                 ON r.reference_number = c.reference_number
               WHERE c.organization_name IS NOT NULL
               GROUP BY c.organization_name, r.region_pe"""):
        pe_of[name][pe] += n
    da.close()

    # ---- group spellings into proposed bodies -----------------------------
    # primary key: usable ΑΦΜ; fallback: compact folded name
    groups: dict[str, list[str]] = defaultdict(list)
    for name, e in spell.items():
        vat = e["vats"].most_common(1)[0][0] if e["vats"] else None
        gkey = f"afm:{vat}" if vat and vat not in SHARED_VATS else f"name:{compact(name)}"
        groups[gkey].append(name)

    bodies = []
    for gkey, names in groups.items():
        names.sort(key=lambda s: -spell[s]["n"])
        canon = names[0]
        folded = fold(canon)
        kind = propose_kind(folded)
        scope = SCOPE_OF_KIND.get(kind, "review")
        vats = Counter()
        n = 0
        net = 0.0
        datasets: set[str] = set()
        pes: Counter = Counter()
        for s in names:
            e = spell[s]
            vats.update(e["vats"])
            n += e["n"]
            net += e["net"]
            datasets |= e["datasets"]
            pes.update(pe_of.get(s, {}))
        afm = vats.most_common(1)[0][0] if vats else None

        # municipality match with Π.Ε. cross-check (first candidate that
        # resolves cleanly wins; ambiguity resolves by Π.Ε. agreement)
        muni_code = None
        muni_status = None
        if kind in ("municipality", "municipal_entity"):
            modal_pe = pes.most_common(1)[0][0] if pes else None
            muni_status = "unmatched"
            for cand in toponym_candidates(folded):
                cands = muni_ix.get(compact(cand), [])
                if not cands:
                    continue
                if len(cands) == 1:
                    muni_code = cands[0][0]
                    muni_status = ("pe_confirmed" if modal_pe == cands[0][1]
                                   else "pe_mismatch" if modal_pe else "no_pe_check")
                else:
                    agreeing = [c for c in cands if c[1] == modal_pe]
                    if len(agreeing) == 1:
                        muni_code = agreeing[0][0]
                        muni_status = "pe_disambiguated"
                    else:
                        muni_status = "ambiguous"
                        continue  # try a finer candidate
                break

        bodies.append({
            "slug": slugify(canon),
            "canonical": canon,
            "aliases": names,
            "kind": kind,
            "scope": scope,
            "afm": afm,
            "all_vats": dict(vats),
            "datasets": sorted(datasets),
            "n_contracts": n,
            "net_eur": round(net, 2),
            "municipality_code": muni_code,
            "municipality_status": muni_status,
            "contract_pes": dict(pes.most_common()),
        })

    bodies.sort(key=lambda b: (-b["n_contracts"], b["canonical"]))
    OUT.write_text(json.dumps({"bodies": bodies}, ensure_ascii=False, indent=1),
                   encoding="utf-8")

    kinds = Counter(b["kind"] for b in bodies)
    mstat = Counter(b["municipality_status"] for b in bodies if b["municipality_status"])
    print(f"{len(spell)} spellings → {len(bodies)} proposed bodies → {OUT.relative_to(ROOT)}")
    print("kinds:", dict(kinds))
    print("municipality matches:", dict(mstat))
    no_afm = sum(1 for b in bodies if not b["afm"])
    print(f"without ΑΦΜ: {no_afm}")

    write_curator(bodies, munis)
    print(f"curator → {CURATOR.name}")


def write_curator(bodies: list[dict], munis: dict) -> None:
    muni_opts = [{"code": c, "label": f"{m['name']} ({c}) — {m['pe']}"}
                 for c, m in sorted(munis.items(), key=lambda kv: kv[1]["name"])]
    payload = json.dumps({"bodies": bodies, "munis": muni_opts}, ensure_ascii=False)
    html = CURATOR_TEMPLATE.replace("__DATA__", payload.replace("</", "<\\/"))
    CURATOR.write_text(html, encoding="utf-8")


CURATOR_TEMPLATE = """<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Public Bodies Curator</title>
<style>
  :root { --paper:#fff; --panel:#f2f2f2; --ink:#1c221f; --soft:#5c6862;
          --line:#d8ddd9; --accent:#52b788; --deep:#2a4a38; --hl:#e3efe8; --warn:#b3552e; }
  * { box-sizing: border-box; }
  body { background:var(--paper); color:var(--ink); font-family:"Segoe UI",system-ui,sans-serif;
         margin:0; padding:32px 18px 80px; line-height:1.45; }
  .wrap { max-width: 900px; margin: 0 auto; }
  .brand { font-weight:900; font-size:12px; letter-spacing:.1em; color:var(--soft); }
  h1 { font-weight:900; font-size:26px; margin:4px 0 2px; }
  .sub { color:var(--soft); font-size:14px; margin:0 0 14px; max-width:70ch; }
  .progress { font-size:13px; color:var(--soft); margin-bottom:10px; }
  .card { background:var(--panel); border-radius:12px; padding:16px 18px; margin-top:12px; }
  .card.flag { outline:2px solid var(--warn); }
  .head { display:flex; gap:10px; align-items:baseline; flex-wrap:wrap; }
  .canon { font-weight:800; font-size:16px; }
  .meta { font-family:Consolas,ui-monospace,monospace; font-size:12px; color:var(--soft); }
  .aliases { margin:6px 0 8px; padding-left:18px; font-size:13px; color:var(--soft); }
  .rowc { display:flex; gap:10px; flex-wrap:wrap; align-items:flex-end; }
  label { display:block; font-size:11px; font-weight:700; letter-spacing:.05em;
          text-transform:uppercase; color:var(--deep); margin:8px 0 3px; }
  input[type=text] { padding:8px 10px; font-size:14px; font-family:inherit;
          border:1.5px solid var(--line); border-radius:8px; background:var(--paper); }
  input.canonin { width: 420px; max-width:100%; }
  input.muniin { width: 320px; }
  input.notein { width: 100%; }
  select { font:inherit; padding:7px 9px; border-radius:8px; border:1.5px solid var(--line);
           background:var(--paper); }
  .stat { font-size:12px; color:var(--soft); }
  .stat.bad { color:var(--warn); font-weight:700; }
  .exportrow { position:sticky; bottom:0; background:var(--paper); padding:12px 0;
               border-top:1px solid var(--line); margin-top:24px; display:flex; gap:10px;
               align-items:center; flex-wrap:wrap; }
  button.btn { font:inherit; font-weight:700; padding:9px 16px; border-radius:8px;
               cursor:pointer; border:1.5px solid var(--line); background:var(--paper); }
  button.btn.primary { background:var(--accent); border-color:var(--accent); color:#fff; }
  .note { font-size:12.5px; color:var(--soft); max-width:64ch; }
</style>
</head>
<body>
<div class="wrap">
  <div class="brand">FORESTRY WORKS TRACKER · PUBLIC BODIES REGISTRY</div>
  <h1>Awarding-bodies curator</h1>
  <p class="sub">One card per proposed body (grouped spellings). Confirm or fix the
  canonical name, kind, scope and municipality; add a note for judgment calls.
  Orange cards need attention (unmatched/ambiguous municipality, kind = review).
  Progress autosaves in this browser; export the JSON and hand it back.</p>
  <div class="progress" id="prog"></div>
  <div id="cards"></div>
  <div class="exportrow">
    <button class="btn primary" onclick="doExport()">Export verdicts JSON</button>
    <button class="btn" onclick="if(confirm('Reset all edits?')){localStorage.removeItem(LS);location.reload()}">Reset</button>
    <span class="note">Scope: municipal = its municipality is its area · regional = its region ·
    national = never infer a place from it · seat = its own premises.</span>
  </div>
</div>
<datalist id="munilist"></datalist>
<script>
const DATA = __DATA__;
const LS = "public_bodies_curator_v1";
const KINDS = ["ministry","decentralized_administration","region","municipality",
               "municipal_entity","state_vehicle","other_public","review"];
const SCOPES = ["municipal","regional","national","seat","review"];
let state = JSON.parse(localStorage.getItem(LS) || "{}");

const dl = document.getElementById("munilist");
for (const m of DATA.munis) {
  const o = document.createElement("option");
  o.value = m.label;
  dl.appendChild(o);
}
const muniByCode = Object.fromEntries(DATA.munis.map(m => [m.code, m.label]));

function get(slug) { return state[slug] || {}; }
function set(slug, patch) {
  state[slug] = Object.assign({}, state[slug], patch);
  localStorage.setItem(LS, JSON.stringify(state));
  prog();
}
function needsAttention(b, s) {
  const kind = s.kind || b.kind, mc = "municipality_code" in s ? s.municipality_code : b.municipality_code;
  if (kind === "review") return true;
  if ((kind === "municipality" || kind === "municipal_entity") && !mc) return true;
  if (b.municipality_status === "pe_mismatch" && !("municipality_code" in s)) return true;
  return false;
}
function prog() {
  const open = DATA.bodies.filter(b => needsAttention(b, get(b.slug))).length;
  document.getElementById("prog").textContent =
    DATA.bodies.length + " bodies · " + open + " still need attention";
  document.querySelectorAll(".card").forEach((el, i) =>
    el.classList.toggle("flag", needsAttention(DATA.bodies[i], get(DATA.bodies[i].slug))));
}
function euro(v){ return v ? (Math.round(v/1000).toLocaleString("el-GR") + " χιλ. €") : "—"; }

const root = document.getElementById("cards");
DATA.bodies.forEach(b => {
  const s = get(b.slug);
  const card = document.createElement("div");
  card.className = "card";
  const pes = Object.entries(b.contract_pes).map(([k,v]) => k.replace("Π.Ε. ","")+" ×"+v).join(", ");
  card.innerHTML = `
    <div class="head"><span class="canon">${b.canonical}</span>
      <span class="meta">ΑΦΜ ${b.afm || "—"} · ${b.datasets.join("+")} · ${b.n_contracts} contracts · ${euro(b.net_eur)}</span></div>
    ${b.aliases.length > 1 ? `<ul class="aliases">${b.aliases.map(a => `<li>${a}</li>`).join("")}</ul>` : ""}
    <div class="stat ${b.municipality_status === "pe_mismatch" || b.municipality_status === "ambiguous" || b.municipality_status === "unmatched" ? "bad" : ""}">
      ${b.municipality_status ? "municipality: " + b.municipality_status + " · " : ""}${pes ? "contract Π.Ε.: " + pes : ""}</div>
    <div class="rowc">
      <div><label>Canonical name</label>
        <input type="text" class="canonin" value="${(s.name ?? b.canonical).replace(/"/g,'&quot;')}"
          oninput="set('${b.slug}',{name:this.value})"></div>
      <div><label>Kind</label><select onchange="set('${b.slug}',{kind:this.value})">
        ${KINDS.map(k => `<option ${k === (s.kind || b.kind) ? "selected" : ""}>${k}</option>`).join("")}</select></div>
      <div><label>Scope</label><select onchange="set('${b.slug}',{scope:this.value})">
        ${SCOPES.map(k => `<option ${k === (s.scope || b.scope) ? "selected" : ""}>${k}</option>`).join("")}</select></div>
      <div><label>Municipality</label>
        <input type="text" class="muniin" list="munilist"
          value="${muniByCode[("municipality_code" in s ? s.municipality_code : b.municipality_code)] || ""}"
          onchange="const m = DATA.munis.find(x => x.label === this.value);
                    set('${b.slug}',{municipality_code: m ? m.code : null})"></div>
    </div>
    <label>Note</label>
    <input type="text" class="notein" value="${(s.note || "").replace(/"/g,'&quot;')}"
      oninput="set('${b.slug}',{note:this.value})">`;
  root.appendChild(card);
});
prog();

function doExport() {
  const out = DATA.bodies.map(b => {
    const s = get(b.slug);
    return {
      key: b.slug, name: s.name ?? b.canonical, kind: s.kind || b.kind,
      scope: s.scope || b.scope, afm: b.afm,
      municipality_code: "municipality_code" in s ? s.municipality_code : b.municipality_code,
      aliases: b.aliases, datasets: b.datasets, note: s.note || null };
  });
  const blob = new Blob([JSON.stringify({bodies: out}, null, 1)], {type: "application/json"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "public_bodies_verdicts.json";
  a.click();
}
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
