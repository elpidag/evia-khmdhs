# -*- coding: utf-8 -*-
"""Regenerate the in-browser polygon editor for the Β. Εύβοια works zones.

The zones' committed source of truth is the user's pixel-space vertex set
(khmdhs/data/evia_works_zones_digitised.json) over the two Δ/νση Δασών
Ευβοίας map sheets. This script (re)creates:

  data/processed/zone_sheets/sheet_4_1.jpg / sheet_4_2.jpg
      the sheets' embedded full-resolution JPEGs (4872x3681 — the exact
      raster the pixel coordinates refer to), carved from the PDFs in
      data/raw (gitignored, regenerable);
  zone_editor.html
      a standalone editor (open via file://) with the CURRENT vertices
      embedded: pan/zoom, drag vertices, click an edge to insert,
      right-click to delete; autosaves in the browser; «Export» downloads
      a full evia_works_zones_digitised.json to hand back — then run
      scripts/build_evia_zones.py to rebuild the geojson (both copies).

Run: python scripts/make_zone_editor.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "khmdhs/data/evia_works_zones_digitised.json"
SHEET_DIR = ROOT / "data/processed/zone_sheets"
OUT = ROOT / "zone_editor.html"

PDFS = {
    "sheet_4_1.jpg": ROOT / "data/raw/XARTHS_ERGON_DAS_LIMNHS_4.1.pdf",
    "sheet_4_2.jpg": ROOT / "data/raw/XARTHS_ERGON_DAS_ISTIAIAS_4.2.pdf",
}
SHEET_IMG = {"limni": "sheet_4_1.jpg", "istiaia": "sheet_4_2.jpg"}


def carve_jpeg(pdf: Path) -> bytes:
    """largest embedded JPEG stream — each sheet PDF is a single raster"""
    data = pdf.read_bytes()
    best = b""
    i = 0
    while True:
        s = data.find(b"\xff\xd8\xff", i)
        if s < 0:
            break
        e = data.find(b"\xff\xd9", s)
        if e < 0:
            break
        cand = data[s:e + 2]
        if len(cand) > len(best):
            best = cand
        i = e + 2
    if len(best) < 100_000:
        raise SystemExit(f"{pdf.name}: no embedded JPEG found")
    return best


def main() -> None:
    SHEET_DIR.mkdir(exist_ok=True)
    for name, pdf in PDFS.items():
        target = SHEET_DIR / name
        if not target.exists():
            target.write_bytes(carve_jpeg(pdf))
            print(f"extracted {name}")

    doc = json.loads(SRC.read_text(encoding="utf-8"))
    payload = json.dumps(doc, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.replace("__DATA__", payload)
    OUT.write_text(html, encoding="utf-8")
    print(f"editor → {OUT.name} (open via file://, images from data/processed/zone_sheets/)")


TEMPLATE = """<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="utf-8">
<title>Β. Εύβοια Zone Editor</title>
<style>
  :root { --panel:#f2f2f2; --ink:#1c221f; --soft:#5c6862; --line:#d8ddd9;
          --accent:#52b788; --deep:#2a4a38; }
  * { box-sizing: border-box; }
  body { margin:0; font-family:"Segoe UI",system-ui,sans-serif; color:var(--ink);
         display:flex; flex-direction:column; height:100vh; overflow:hidden; }
  header { padding:8px 14px; display:flex; gap:10px; align-items:center; flex-wrap:wrap;
           border-bottom:1px solid var(--line); background:#fff; }
  header b { font-size:15px; }
  .note { color:var(--soft); font-size:12px; max-width:52ch; }
  select, button { font:inherit; padding:6px 10px; border-radius:7px;
                   border:1.5px solid var(--line); background:#fff; cursor:pointer; }
  button.primary { background:var(--accent); border-color:var(--accent); color:#fff; font-weight:700; }
  #wrap { flex:1; position:relative; overflow:hidden; background:#888; cursor:grab; }
  #wrap.dragging { cursor:grabbing; }
  canvas { position:absolute; inset:0; }
  #zones { display:flex; gap:6px; flex-wrap:wrap; }
  #zones button.on { outline:2.5px solid var(--deep); font-weight:700; }
</style>
</head>
<body>
<header>
  <b>Zone editor</b>
  <select id="sheetSel"></select>
  <span id="zones"></span>
  <button class="primary" onclick="doExport()">Export JSON</button>
  <button onclick="if(confirm('Reset ALL edits (both sheets)?')){localStorage.removeItem(LS);location.reload()}">Reset</button>
  <span class="note">drag = pan · wheel = zoom · drag a vertex to move it ·
    click ON an edge of the ACTIVE zone to insert a vertex · right-click a vertex to delete ·
    edits autosave; export and hand the file back</span>
</header>
<div id="wrap"><canvas id="cv"></canvas></div>
<script>
const DOC = __DATA__;
const LS = "evia_zone_editor_v1";
const IMGS = { limni: "data/processed/zone_sheets/sheet_4_1.jpg",
               istiaia: "data/processed/zone_sheets/sheet_4_2.jpg" };
const COLORS = ["#e63946","#457b9d","#2a9d8f","#e9c46a","#9b5de5","#f3722c","#43aa8b","#577590","#f94144"];

let sheets = JSON.parse(localStorage.getItem(LS) || "null") || structuredClone(DOC.sheets);
const save = () => localStorage.setItem(LS, JSON.stringify(sheets));

let sheet = Object.keys(sheets)[0];
let zoneKeys = () => Object.keys(sheets[sheet]);
let active = zoneKeys()[0];
let img = new Image();
let view = { s: 0.2, tx: 0, ty: 0 };
let drag = null;   // {type:'pan'|'vertex', ...}

const wrap = document.getElementById("wrap");
const cv = document.getElementById("cv");
const ctx = cv.getContext("2d");

const sheetSel = document.getElementById("sheetSel");
for (const k of Object.keys(sheets)) {
  const o = document.createElement("option");
  o.value = k;
  o.textContent = k === "limni" ? "Φύλλο 4.1 — Δασαρχείο Λίμνης" : "Φύλλο 4.2 — Δασαρχείο Ιστιαίας";
  sheetSel.appendChild(o);
}
sheetSel.onchange = () => { sheet = sheetSel.value; active = zoneKeys()[0]; loadImg(); zoneBtns(); };

function zoneBtns() {
  const box = document.getElementById("zones");
  box.innerHTML = "";
  zoneKeys().forEach((k, i) => {
    const b = document.createElement("button");
    const meta = (DOC.zones_meta || {})[k] || {};
    b.textContent = meta.name || k;
    b.style.borderColor = COLORS[i % COLORS.length];
    if (k === active) b.classList.add("on");
    b.onclick = () => { active = k; zoneBtns(); draw(); };
    box.appendChild(b);
  });
}

function loadImg() {
  img = new Image();
  img.onload = () => { fit(); draw(); };
  img.src = IMGS[sheet];
}
function fit() {
  const r = wrap.getBoundingClientRect();
  cv.width = r.width; cv.height = r.height;
  view.s = Math.min(r.width / img.width, r.height / img.height);
  view.tx = (r.width - img.width * view.s) / 2;
  view.ty = (r.height - img.height * view.s) / 2;
}
const toImg = (mx, my) => [(mx - view.tx) / view.s, (my - view.ty) / view.s];

function draw() {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, cv.width, cv.height);
  ctx.setTransform(view.s, 0, 0, view.s, view.tx, view.ty);
  if (img.complete && img.width) ctx.drawImage(img, 0, 0);
  zoneKeys().forEach((k, i) => {
    const col = COLORS[i % COLORS.length];
    const on = k === active;
    for (const ring of sheets[sheet][k]) {
      ctx.beginPath();
      ring.forEach(([x, y], j) => (j ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
      ctx.closePath();
      ctx.lineWidth = (on ? 3 : 1.6) / view.s;
      ctx.strokeStyle = col;
      ctx.globalAlpha = on ? 1 : 0.55;
      ctx.stroke();
      ctx.globalAlpha = 1;
      if (on) {
        const r = 5 / view.s;
        for (const [x, y] of ring) {
          ctx.fillStyle = "#fff";
          ctx.fillRect(x - r, y - r, 2 * r, 2 * r);
          ctx.strokeStyle = col;
          ctx.lineWidth = 1.5 / view.s;
          ctx.strokeRect(x - r, y - r, 2 * r, 2 * r);
        }
      }
    }
  });
}

function hitVertex(ix, iy) {
  const tol = 7 / view.s;
  const rings = sheets[sheet][active];
  for (let ri = 0; ri < rings.length; ri++)
    for (let vi = 0; vi < rings[ri].length; vi++) {
      const [x, y] = rings[ri][vi];
      if (Math.abs(x - ix) <= tol && Math.abs(y - iy) <= tol) return { ri, vi };
    }
  return null;
}
function hitEdge(ix, iy) {
  const tol = 6 / view.s;
  const rings = sheets[sheet][active];
  let best = null;
  for (let ri = 0; ri < rings.length; ri++) {
    const ring = rings[ri];
    for (let vi = 0; vi < ring.length; vi++) {
      const [x1, y1] = ring[vi], [x2, y2] = ring[(vi + 1) % ring.length];
      const dx = x2 - x1, dy = y2 - y1, L2 = dx * dx + dy * dy;
      if (!L2) continue;
      let t = ((ix - x1) * dx + (iy - y1) * dy) / L2;
      t = Math.max(0, Math.min(1, t));
      const px = x1 + t * dx, py = y1 + t * dy;
      const d = Math.hypot(ix - px, iy - py);
      if (d <= tol && (!best || d < best.d)) best = { ri, vi, d, px, py };
    }
  }
  return best;
}

wrap.addEventListener("pointerdown", (e) => {
  const [ix, iy] = toImg(e.offsetX, e.offsetY);
  const v = hitVertex(ix, iy);
  if (v && e.button === 0) drag = { type: "vertex", ...v, moved: false };
  else if (e.button === 0) drag = { type: "pan", x: e.clientX, y: e.clientY, moved: false };
  wrap.classList.add("dragging");
  wrap.setPointerCapture(e.pointerId);
});
wrap.addEventListener("pointermove", (e) => {
  if (!drag) return;
  drag.moved = true;
  if (drag.type === "pan") {
    view.tx += e.clientX - drag.x; view.ty += e.clientY - drag.y;
    drag.x = e.clientX; drag.y = e.clientY;
  } else {
    const [ix, iy] = toImg(e.offsetX, e.offsetY);
    sheets[sheet][active][drag.ri][drag.vi] =
      [Math.round(ix * 10) / 10, Math.round(iy * 10) / 10];
  }
  draw();
});
wrap.addEventListener("pointerup", (e) => {
  if (drag && !drag.moved && drag.type === "pan") {
    const [ix, iy] = toImg(e.offsetX, e.offsetY);
    const edge = hitEdge(ix, iy);
    if (edge) {
      sheets[sheet][active][edge.ri].splice(edge.vi + 1, 0,
        [Math.round(edge.px * 10) / 10, Math.round(edge.py * 10) / 10]);
      draw();
    }
  }
  if (drag && drag.type === "vertex") save();
  if (drag && drag.type === "pan" && !drag.moved) save();
  drag = null;
  wrap.classList.remove("dragging");
});
wrap.addEventListener("contextmenu", (e) => {
  e.preventDefault();
  const [ix, iy] = toImg(e.offsetX, e.offsetY);
  const v = hitVertex(ix, iy);
  if (v && sheets[sheet][active][v.ri].length > 3) {
    sheets[sheet][active][v.ri].splice(v.vi, 1);
    save(); draw();
  }
});
wrap.addEventListener("wheel", (e) => {
  e.preventDefault();
  const f = e.deltaY < 0 ? 1.15 : 1 / 1.15;
  const [ix, iy] = toImg(e.offsetX, e.offsetY);
  view.s *= f;
  view.tx = e.offsetX - ix * view.s;
  view.ty = e.offsetY - iy * view.s;
  draw();
}, { passive: false });
window.addEventListener("resize", () => { fit(); draw(); });

function doExport() {
  const out = structuredClone(DOC);
  out.sheets = sheets;
  const blob = new Blob([JSON.stringify(out, null, 1)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "evia_works_zones_digitised.json";
  a.click();
}

zoneBtns();
loadImg();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
