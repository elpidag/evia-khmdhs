"""Export a region of the running Atlas as a VECTOR SVG (2026-09-04).

    python scripts/export_svg.py <url> <target> <out.svg> [--width 1920 --height 1080]

`target` is a CSS selector, or `tile:<TITLE>` for a dataset card's tile by its
label. Needs the dev server (:5173) and the API (:5050) running.

What it does: walks the target's DOM and writes what the browser painted as
SVG primitives — backgrounds and borders as rects, every text node as a
<text> per rendered line (the computed font, size, weight, tracking and
colour carried over; the Adobe Typekit families are named, so Illustrator
with the author's fonts sets them as on the site), inline <svg> elements
copied with their computed fills and strokes, a chart canvas as CIRCLES
where the component exposes its dots (`canvas.__dots`, the beeswarms) and
as an embedded PNG otherwise (the landing's code field), <img> and mask
glyphs as images. Elements at opacity 0 (hover-only names, notes) are left
out, as are those outside the target's box.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

from playwright.sync_api import sync_playwright

SERIALISE = r"""
(target) => {
  const root = typeof target === 'string' ? document.querySelector(target) : target;
  if (!root) return { error: 'target not found' };
  const R = root.getBoundingClientRect();
  const out = [];
  const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const num = (v) => Math.round(v * 100) / 100;
  const rel = (r) => ({ x: num(r.left - R.left), y: num(r.top - R.top), w: num(r.width), h: num(r.height) });
  const inside = (r) => r.right > R.left - 1 && r.left < R.right + 1 && r.bottom > R.top - 1 && r.top < R.bottom + 1;
  const transparent = (c) => !c || c === 'transparent' || /rgba\(\s*\d+,\s*\d+,\s*\d+,\s*0\)/.test(c);

  const textOf = (node, cs) => {
    // one <text> per rendered line: characters grouped by their line box
    const s = node.textContent;
    if (!s.trim()) return;
    const fs = parseFloat(cs.fontSize);
    const fam = cs.fontFamily.replace(/"/g, "'");
    const tf = cs.textTransform;
    const range = document.createRange();
    const lines = [];
    let cur = null;
    for (let i = 0; i < s.length; i++) {
      range.setStart(node, i); range.setEnd(node, i + 1);
      const rects = range.getClientRects();
      if (!rects.length) continue;
      const r = rects[0];
      if (r.width === 0 && /\s/.test(s[i])) { if (cur) cur.text += s[i]; continue; }
      if (!cur || Math.abs(r.top - cur.top) > fs * 0.5) {
        cur = { top: r.top, left: r.left, bottom: r.bottom, text: s[i] };
        lines.push(cur);
      } else {
        cur.text += s[i];
        cur.left = Math.min(cur.left, r.left);
        cur.bottom = Math.max(cur.bottom, r.bottom);
      }
    }
    for (const l of lines) {
      let t = l.text.replace(/\s+/g, ' ').trim();
      if (!t) continue;
      if (tf === 'uppercase') t = t.toUpperCase();
      else if (tf === 'lowercase') t = t.toLowerCase();
      // the baseline sits about 0.8 em below the line box's top for these faces
      const lh = l.bottom - l.top;
      const y = l.top - R.top + (lh - fs) / 2 + fs * 0.8;
      const attrs = [
        `x="${num(l.left - R.left)}"`, `y="${num(y)}"`,
        `font-family="${esc(fam)}"`, `font-size="${num(fs)}"`, `font-weight="${cs.fontWeight}"`,
        cs.fontStyle !== 'normal' ? `font-style="${cs.fontStyle}"` : '',
        cs.letterSpacing !== 'normal' ? `letter-spacing="${cs.letterSpacing}"` : '',
        `fill="${cs.color}"`,
        cs.textDecorationLine && cs.textDecorationLine !== 'none' ? `text-decoration="${cs.textDecorationLine}"` : ''
      ].filter(Boolean).join(' ');
      out.push(`<text ${attrs} xml:space="preserve">${esc(t)}</text>`);
    }
  };

  const svgOf = (el, q) => {
    // copy an inline svg, its computed presentation carried as attributes
    const clone = el.cloneNode(true);
    const orig = el.querySelectorAll('*'); const copy = clone.querySelectorAll('*');
    for (let i = 0; i < orig.length; i++) {
      const cs = getComputedStyle(orig[i]);
      const c = copy[i];
      if (cs.display === 'none' || parseFloat(cs.opacity) === 0) { c.setAttribute('display', 'none'); continue; }
      for (const [prop, attr] of [['fill', 'fill'], ['stroke', 'stroke'], ['strokeWidth', 'stroke-width'], ['strokeDasharray', 'stroke-dasharray'],
                                  ['fillOpacity', 'fill-opacity'], ['strokeOpacity', 'stroke-opacity'], ['opacity', 'opacity'],
                                  ['fontFamily', 'font-family'], ['fontSize', 'font-size'], ['fontWeight', 'font-weight'],
                                  ['textAnchor', 'text-anchor'], ['letterSpacing', 'letter-spacing'], ['dominantBaseline', 'dominant-baseline']]) {
        const v = cs[prop];
        if (v && v !== 'normal' && v !== 'none' || (attr === 'fill' || attr === 'stroke')) c.setAttribute(attr, v);
      }
      c.removeAttribute('class'); c.removeAttribute('style');
    }
    clone.removeAttribute('class'); clone.removeAttribute('style');
    clone.setAttribute('x', q.x); clone.setAttribute('y', q.y);
    clone.setAttribute('width', q.w); clone.setAttribute('height', q.h);
    if (!clone.getAttribute('viewBox')) clone.setAttribute('viewBox', `0 0 ${q.w} ${q.h}`);
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    out.push(clone.outerHTML);
  };

  const walk = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return;
    const r = el.getBoundingClientRect();
    if (!inside(r)) return;
    const q = rel(r);
    const hasBox = r.width > 0 && r.height > 0;
    if (hasBox) {
      const mask = cs.maskImage !== 'none' ? cs.maskImage : (cs.webkitMaskImage && cs.webkitMaskImage !== 'none' ? cs.webkitMaskImage : null);
      if (mask) {
        const m = /url\("?([^")]+)"?\)/.exec(mask);
        if (m) out.push(`<image x="${q.x}" y="${q.y}" width="${q.w}" height="${q.h}" href="${esc(m[1])}" preserveAspectRatio="xMidYMid meet"/>`);
        return;
      }
      if (!transparent(cs.backgroundColor) && el.tagName !== 'CANVAS')
        out.push(`<rect x="${q.x}" y="${q.y}" width="${q.w}" height="${q.h}" rx="${num(parseFloat(cs.borderTopLeftRadius) || 0)}" fill="${cs.backgroundColor}"/>`);
      const bgi = cs.backgroundImage;
      if (bgi && bgi.startsWith('linear-gradient')) {
        const cols = bgi.match(/rgba?\([^)]*\)/g) || [];
        if (cols.length >= 2) {
          const id = 'g' + out.length;
          out.push(`<defs><linearGradient id="${id}" x1="0" y1="0" x2="1" y2="0">${cols.map((c, i) => `<stop offset="${(100 * i / (cols.length - 1)).toFixed(0)}%" stop-color="${c}"/>`).join('')}</linearGradient></defs>`);
          out.push(`<rect x="${q.x}" y="${q.y}" width="${q.w}" height="${q.h}" fill="url(#${id})"/>`);
        }
      }
      // borders, per side
      const sides = [['Top', 0, 0, q.w, 0], ['Right', q.w, 0, q.w, q.h], ['Bottom', 0, q.h, q.w, q.h], ['Left', 0, 0, 0, q.h]];
      for (const [side, x1, y1, x2, y2] of sides) {
        const bw = parseFloat(cs[`border${side}Width`]);
        if (bw > 0 && cs[`border${side}Style`] !== 'none' && !transparent(cs[`border${side}Color`])) {
          const off = bw / 2; const dx = side === 'Left' ? off : side === 'Right' ? -off : 0; const dy = side === 'Top' ? off : side === 'Bottom' ? -off : 0;
          out.push(`<line x1="${num(q.x + x1 + dx)}" y1="${num(q.y + y1 + dy)}" x2="${num(q.x + x2 + dx)}" y2="${num(q.y + y2 + dy)}" stroke="${cs[`border${side}Color`]}" stroke-width="${bw}"${cs[`border${side}Style`] === 'dashed' ? ' stroke-dasharray="4 3"' : ''}/>`);
        }
      }
    }
    if (el.tagName === 'CANVAS') {
      if (!hasBox) return;
      const dots = el.__dots;
      if (Array.isArray(dots) && dots.length) {
        const k = r.width / (el.clientWidth || r.width);
        for (const d of dots) out.push(`<circle cx="${num(q.x + d.x * k)}" cy="${num(q.y + d.y * k)}" r="${num(d.r * k)}" fill="${d.fill}" fill-opacity="0.85"/>`);
      } else {
        try { out.push(`<image x="${q.x}" y="${q.y}" width="${q.w}" height="${q.h}" href="${el.toDataURL('image/png')}"/>`); } catch (e) { /* tainted */ }
      }
      return;
    }
    if (el instanceof SVGSVGElement) { if (hasBox) svgOf(el, q); return; }
    if (el.tagName === 'IMG') { if (hasBox) out.push(`<image x="${q.x}" y="${q.y}" width="${q.w}" height="${q.h}" href="${esc(el.currentSrc || el.src)}" preserveAspectRatio="xMidYMid meet"/>`); return; }
    if (el.tagName === 'INPUT' || el.tagName === 'SELECT') return;
    for (const n of el.childNodes) {
      if (n.nodeType === 3) textOf(n, cs);
      else if (n.nodeType === 1) walk(n);
    }
  };
  walk(root);
  return { w: num(R.width), h: num(R.height), body: out.join('\n') };
}
"""

FIND_TILE = r"""
(title) => {
  const all = [...document.querySelectorAll('*')].filter((e) => e.childElementCount === 0 && e.textContent.trim() === title);
  for (const t of all) {
    let el = t;
    while (el && el !== document.body) {
      if (el.matches('.tile, [class*="tile"]')) return el;
      el = el.parentElement;
    }
  }
  return null;
}
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("target", help="CSS selector, or tile:<TITLE>")
    ap.add_argument("out")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--settle", type=int, default=3500, help="ms to wait after load (charts, fonts)")
    a = ap.parse_args()
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": a.width, "height": a.height})
        pg.goto(a.url, wait_until="load", timeout=120000)
        pg.wait_for_timeout(a.settle)
        pg.evaluate("() => document.fonts.ready")
        if a.target.startswith("tile:"):
            handle = pg.evaluate_handle(FIND_TILE, a.target[5:])
            if handle.json_value() is None:
                sys.exit(f"no tile titled {a.target[5:]!r}")
            res = pg.evaluate(SERIALISE, handle)
        else:
            res = pg.evaluate(SERIALISE, a.target)
        b.close()
    if "error" in res:
        sys.exit(res["error"])
    svg = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{res["w"]}" height="{res["h"]}" viewBox="0 0 {res["w"]} {res["h"]}">\n'
        f'<rect width="{res["w"]}" height="{res["h"]}" fill="#ffffff"/>\n{res["body"]}\n</svg>\n'
    )
    out = pathlib.Path(a.out)
    out.write_text(svg, encoding="utf-8")
    n_circle = svg.count("<circle"); n_text = svg.count("<text"); n_img = svg.count("<image")
    print(f"{out} — {res['w']}×{res['h']}, {len(svg)//1024} KB: {n_circle} circles, {n_text} texts, {n_img} images")


if __name__ == "__main__":
    main()
