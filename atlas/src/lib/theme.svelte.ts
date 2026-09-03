/**
 * The LIVE THEME bridge (author's Theme Lab round, 2026-09-03).
 *
 * Every chart palette is a CSS string over the tokens (`var(--…)` /
 * `color-mix(…)`), so SVG fills and CSS surfaces follow a token change
 * by themselves. Two things cannot: a CANVAS needs a concrete colour,
 * and luminance math needs channels. Both come through here —
 * `resolveCssColor` resolves any CSS colour expression against the live
 * tokens via a probe element, and `themeTick()` is the reactive signal
 * the Theme Lab bumps (a `themelab:change` window event) so a mounted
 * canvas redraws and a cached resolution is dropped.
 *
 * On the server everything degrades honestly: the tick is 0 forever and
 * `resolveCssColor` returns the expression unresolved — the canvas
 * charts only draw in the browser anyway.
 */
import { browser } from '$app/environment';

let tick = $state(0);
const cache = new Map<string, string>();

if (browser) {
	window.addEventListener('themelab:change', () => {
		cache.clear();
		tick += 1;
	});
}

/** reactive: read inside $derived/$effect to follow Theme Lab changes */
export function themeTick(): number {
	return tick;
}

let probe: HTMLElement | null = null;

/** resolve any CSS colour expression (var chains, color-mix, hex) to the
 *  browser's own `rgb(…)` — usable as a canvas fillStyle and parseable.
 *  Reads the tick, so any template expression, $derived or $effect that
 *  resolves a colour re-runs by itself when the Theme Lab changes one. */
export function resolveCssColor(expr: string): string {
	void tick;
	if (!browser) return expr;
	const hit = cache.get(expr);
	if (hit) return hit;
	if (!probe) {
		probe = document.createElement('span');
		probe.style.display = 'none';
		document.documentElement.appendChild(probe);
	}
	probe.style.color = '';
	probe.style.color = expr;
	const out = getComputedStyle(probe).color || expr;
	cache.set(expr, out);
	return out;
}

let parseCtx: CanvasRenderingContext2D | null = null;

/** the resolved channels of any CSS colour, 0-255 (null when unreadable).
 *  Chrome serialises a resolved color-mix as `color(srgb …)` or
 *  `oklab(…)`, so anything the regexes miss goes through a 1×1 canvas —
 *  the browser's own parser, whatever the serialisation. */
export function cssRgb(expr: string): [number, number, number] | null {
	const c = resolveCssColor(expr);
	const m = /^#?([0-9a-f]{6})$/i.exec(c);
	if (m) {
		const v = parseInt(m[1], 16);
		return [(v >> 16) & 255, (v >> 8) & 255, v & 255];
	}
	const r = /^rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)/.exec(c);
	if (r) return [Number(r[1]), Number(r[2]), Number(r[3])];
	if (!browser) return null;
	try {
		if (!parseCtx) {
			const cv = document.createElement('canvas');
			cv.width = cv.height = 1;
			parseCtx = cv.getContext('2d', { willReadFrequently: true });
		}
		if (!parseCtx) return null;
		parseCtx.fillStyle = '#000';
		parseCtx.fillStyle = c;
		parseCtx.fillRect(0, 0, 1, 1);
		const d = parseCtx.getImageData(0, 0, 1, 1).data;
		return [d[0], d[1], d[2]];
	} catch {
		return null;
	}
}

/** perceived luminance 0..1 of any CSS colour (0.299/0.587/0.114 —
 *  the convention the site's ink-on-fill pickers already use) */
export function cssLuminance(expr: string): number {
	const rgb = cssRgb(expr);
	if (!rgb) return 0;
	return (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255;
}
