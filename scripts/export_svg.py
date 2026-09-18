"""Export a region of the running Atlas as a VECTOR SVG (2026-09-04).

    python scripts/export_svg.py <url> <target> <out.svg> [--width 1920 --height 1080] [--scroll] [--click <selector>]

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
  // EVERY colour leaves as plain #rrggbb + a separate opacity (2026-09-17):
  // the site's token mixes compute to `color(srgb ...)`, which Illustrator
  // does not read - it dropped the sankey ribbons' strokes and painted the
  // grey bars black. One pixel is painted and read back, so any css colour
  // form resolves; `none`, transparent and url() references pass through.
  const _cv = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
  const _cc = new Map();
  const flat = (c) => {
    if (!c || c === 'none' || c === 'transparent') return null;
    if (/^url\(/.test(c)) return { ref: c.replace(/"/g, '') };
    if (_cc.has(c)) return _cc.get(c);
    _cv.clearRect(0, 0, 1, 1); _cv.fillStyle = '#000'; _cv.fillStyle = c; _cv.fillRect(0, 0, 1, 1);
    const px = _cv.getImageData(0, 0, 1, 1).data;
    const res = px[3] === 0 ? null
      : { hex: '#' + [px[0], px[1], px[2]].map((v) => v.toString(16).padStart(2, '0')).join(''), a: Math.round((px[3] / 255) * 1000) / 1000 };
    _cc.set(c, res);
    return res;
  };
  const unit = (v) => String(v).replace(/(-?[\d.]+)px/g, '$1');

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
      if (r.width === 0 && /\s/.test(s[i])) { if (cur) { cur.text += s[i]; cur.rights.push(cur.rights[cur.rights.length - 1] ?? r.left); } continue; }
      if (!cur || Math.abs(r.top - cur.top) > fs * 0.5) {
        cur = { top: r.top, left: r.left, bottom: r.bottom, text: s[i], rights: [r.right] };
        lines.push(cur);
      } else {
        cur.text += s[i];
        cur.rights.push(r.right);
        cur.left = Math.min(cur.left, r.left);
        cur.bottom = Math.max(cur.bottom, r.bottom);
      }
    }
    // lines the page CLIPS are not drawn: the nearest ancestor with a hidden
    // overflow cuts them (a line-clamped title keeps its first N lines and
    // ends in the ellipsis the browser paints — 2026-09-15, the story
    // timeline's titles overprinted their neighbours in the export)
    let clip = null;
    for (let a = node.parentElement; a && a !== root.parentElement; a = a.parentElement) {
      const acs = getComputedStyle(a);
      if (/hidden|clip/.test(acs.overflowY) || /hidden|clip/.test(acs.overflowX)) { clip = a; break; }
    }
    let kept = lines;
    let ellipsis = false;
    if (clip) {
      const cb = clip.getBoundingClientRect();
      kept = lines.filter((l) => (l.top + l.bottom) / 2 < cb.bottom && (l.top + l.bottom) / 2 > cb.top);
      if (kept.length < lines.length && kept.length && cs.webkitLineClamp && cs.webkitLineClamp !== 'none') {
        const last = kept[kept.length - 1];
        const ctx = document.createElement('canvas').getContext('2d');
        ctx.font = cs.font;
        const ew = ctx.measureText('…').width;
        let n = last.text.length;
        while (n > 0 && last.rights[n - 1] + ew > cb.right + 0.5) n--;
        last.text = last.text.slice(0, n).replace(/\s+$/, '');
        ellipsis = true;
      }
    }
    for (const l of kept) {
      let t = l.text.replace(/\s+/g, ' ').trim();
      if (ellipsis && l === kept[kept.length - 1]) t += '…';
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
        cs.letterSpacing !== 'normal' ? `letter-spacing="${unit(cs.letterSpacing)}"` : '',
        `fill="${(flat(cs.color) || { hex: '#000000' }).hex}"`,
        (flat(cs.color) || { a: 1 }).a < 1 ? `fill-opacity="${flat(cs.color).a}"` : '',
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
      for (const [prop, attr] of [['strokeWidth', 'stroke-width'], ['strokeDasharray', 'stroke-dasharray'],
                                  ['strokeLinecap', 'stroke-linecap'], ['strokeLinejoin', 'stroke-linejoin'],
                                  ['opacity', 'opacity'],
                                  ['fontFamily', 'font-family'], ['fontSize', 'font-size'], ['fontWeight', 'font-weight'],
                                  ['textAnchor', 'text-anchor'], ['letterSpacing', 'letter-spacing'], ['dominantBaseline', 'dominant-baseline']]) {
        const v = cs[prop];
        if (v && v !== 'normal' && v !== 'none') c.setAttribute(attr, unit(v));
      }
      // paint: plain hex + its own opacity (the colour's alpha times the css one)
      for (const [prop, attr, oprop] of [['fill', 'fill', 'fillOpacity'], ['stroke', 'stroke', 'strokeOpacity']]) {
        const f = flat(cs[prop]);
        if (!f) { c.setAttribute(attr, 'none'); c.removeAttribute(attr + '-opacity'); continue; }
        if (f.ref) { c.setAttribute(attr, f.ref); continue; }
        c.setAttribute(attr, f.hex);
        const css = parseFloat(cs[oprop]);
        const o = Math.round(f.a * (Number.isFinite(css) ? css : 1) * 1000) / 1000;
        if (o < 1) c.setAttribute(attr + '-opacity', o); else c.removeAttribute(attr + '-opacity');
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
      const bgc = el.tagName !== 'CANVAS' ? flat(cs.backgroundColor) : null;
      if (bgc && bgc.hex)
        out.push(`<rect x="${q.x}" y="${q.y}" width="${q.w}" height="${q.h}" rx="${num(parseFloat(cs.borderTopLeftRadius) || 0)}" fill="${bgc.hex}"${bgc.a < 1 ? ` fill-opacity="${bgc.a}"` : ''}/>`);
      const bgi = cs.backgroundImage;
      if (bgi && bgi.startsWith('linear-gradient')) {
        // the direction (a keyword or an angle; CSS defaults to top → bottom)
        // and the stops — colours in ANY css form (rgb, color(), color-mix
        // over the tokens), each normalised through a canvas so the file
        // carries plain colours (2026-09-17: the fires map's year bar)
        const inner = bgi.slice(bgi.indexOf('(') + 1, bgi.lastIndexOf(')'));
        const parts = []; let depth = 0, cur = '';
        for (const ch of inner) { if (ch === '(') depth++; if (ch === ')') depth--; if (ch === ',' && depth === 0) { parts.push(cur.trim()); cur = ''; } else cur += ch; }
        if (cur.trim()) parts.push(cur.trim());
        let x1 = 0, y1 = 0, x2 = 0, y2 = 1;
        const first = parts[0] || '';
        const dm = /^(-?[\d.]+)deg$/.exec(first); const km = /^to (top|bottom|left|right)/.exec(first);
        if (dm || km) {
          parts.shift();
          const deg = dm ? parseFloat(dm[1]) : { top: 0, right: 90, bottom: 180, left: 270 }[km[1]];
          const a = (deg * Math.PI) / 180; const sx = Math.sin(a) / 2, cy = Math.cos(a) / 2;
          x1 = 0.5 - sx; y1 = 0.5 + cy; x2 = 0.5 + sx; y2 = 0.5 - cy;
        }
        const cvs = document.createElement('canvas').getContext('2d');
        const stops = parts.map((pt) => {
          const m = /\s(-?[\d.]+)%\s*$/.exec(pt);
          const col = m ? pt.slice(0, m.index).trim() : pt;
          // paint one pixel and read it back: the canvas normalises modern
          // colour spaces to oklab() strings, which Illustrator cannot read
          cvs.clearRect(0, 0, 1, 1); cvs.fillStyle = col; cvs.fillRect(0, 0, 1, 1);
          const px = cvs.getImageData(0, 0, 1, 1).data;
          const hex = px[3] ? '#' + [px[0], px[1], px[2]].map((v) => v.toString(16).padStart(2, '0')).join('') : null;
          return { c: hex, p: m ? parseFloat(m[1]) : null };
        }).filter((st) => st.c);
        if (stops.length >= 2) {
          const id = 'g' + out.length;
          const off = (i) => stops[i].p !== null ? stops[i].p : (100 * i) / (stops.length - 1);
          out.push(`<defs><linearGradient id="${id}" x1="${num(x1)}" y1="${num(y1)}" x2="${num(x2)}" y2="${num(y2)}">${stops.map((st, i) => `<stop offset="${off(i).toFixed(1)}%" stop-color="${st.c}"/>`).join('')}</linearGradient></defs>`);
          out.push(`<rect x="${q.x}" y="${q.y}" width="${q.w}" height="${q.h}" rx="${num(parseFloat(cs.borderTopLeftRadius) || 0)}" fill="url(#${id})"/>`);
        }
      }
      // borders, per side
      const sides = [['Top', 0, 0, q.w, 0], ['Right', q.w, 0, q.w, q.h], ['Bottom', 0, q.h, q.w, q.h], ['Left', 0, 0, 0, q.h]];
      for (const [side, x1, y1, x2, y2] of sides) {
        const bw = parseFloat(cs[`border${side}Width`]);
        const bc = bw > 0 && cs[`border${side}Style`] !== 'none' ? flat(cs[`border${side}Color`]) : null;
        if (bc && bc.hex) {
          const off = bw / 2; const dx = side === 'Left' ? off : side === 'Right' ? -off : 0; const dy = side === 'Top' ? off : side === 'Bottom' ? -off : 0;
          out.push(`<line x1="${num(q.x + x1 + dx)}" y1="${num(q.y + y1 + dy)}" x2="${num(q.x + x2 + dx)}" y2="${num(q.y + y2 + dy)}" stroke="${bc.hex}"${bc.a < 1 ? ` stroke-opacity="${bc.a}"` : ''} stroke-width="${bw}"${cs[`border${side}Style`] === 'dashed' ? ' stroke-dasharray="4 3"' : ''}/>`);
        }
      }
    }
    if (el.tagName === 'CANVAS') {
      if (!hasBox) return;
      const dots = el.__dots;
      if (Array.isArray(dots) && dots.length) {
        const k = r.width / (el.clientWidth || r.width);
        for (const d of dots) out.push(`<circle cx="${num(q.x + d.x * k)}" cy="${num(q.y + d.y * k)}" r="${num(d.r * k)}" fill="${(flat(d.fill) || { hex: '#000000' }).hex}" fill-opacity="0.85"/>`);
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
    ap.add_argument("--scroll", action="store_true",
                    help="scroll the whole page first so deferred (below-the-fold) frames mount")
    ap.add_argument("--scroll-to", default=None,
                    help="a CSS selector to scroll into the middle of the viewport before serialising — "
                         "puts the story's reading line on a paragraph so its rails show that passage's charts")
    ap.add_argument("--click", default=None,
                    help="a CSS selector to click after load, before serialising — opens a "
                         "modal such as the story's whole-timeline view (2026-09-15)")
    a = ap.parse_args()
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": a.width, "height": a.height})
        pg.goto(a.url, wait_until="load", timeout=120000)
        pg.wait_for_timeout(a.settle)
        if a.scroll:
            h = pg.evaluate("() => document.documentElement.scrollHeight"); y = 0
            while y < h:
                y += 700
                pg.evaluate(f"() => window.scrollTo(0, {y})")
                pg.wait_for_timeout(350)
                h = pg.evaluate("() => document.documentElement.scrollHeight")
            pg.evaluate("() => window.scrollTo(0, 0)")
            pg.wait_for_timeout(1500)
        if a.scroll_to:
            # WALK down to the element as a reader would (the story's
            # reading-position observers want to see the passages go by; a
            # jump leaves them a passage behind with the rails veiled), then
            # centre it and let the rails settle
            # the element's CENTRE on the viewport's centre (its top there
            # left the reading line, 45 % down, on the passage before)
            target = ("(sel) => { const r = document.querySelector(sel).getBoundingClientRect();"
                      " return r.top + r.height / 2 + window.scrollY - innerHeight / 2; }")
            y = 0
            for _ in range(3):
                # the page GROWS as deferred bands mount on the way down, so the
                # target is re-measured after each walk until it holds still
                target_y = pg.evaluate(target, a.scroll_to)
                while y < target_y - 600:
                    y += 600
                    pg.evaluate(f"() => window.scrollTo(0, {y})")
                    pg.wait_for_timeout(120)
                while y < target_y:
                    y = min(target_y, y + 150)
                    pg.evaluate(f"() => window.scrollTo(0, {y})")
                    pg.wait_for_timeout(250)
                pg.wait_for_timeout(1200)
                if abs(pg.evaluate(target, a.scroll_to) - target_y) < 4:
                    break
            pg.wait_for_timeout(3000)
        if a.click:
            pg.click(a.click)
            pg.wait_for_timeout(1500)
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
