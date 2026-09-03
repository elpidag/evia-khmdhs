<script lang="ts" module>
	// dodge layout memo across navigations — the payload object identity is
	// stable thanks to the client fetch cache, so revisiting the page skips
	// the ~60ms layout for 2,018 points
	const layoutCache = new WeakMap<
		object,
		{ width: number; xs: number[]; ys: number[]; r: number; h: number; pad: number; maxH: number }
	>();
</script>

<script lang="ts">
	import type { DaseSwarm } from '$lib/api';
	import { goto } from '$app/navigation';
	import { resolveCssColor, cssLuminance } from '$lib/theme.svelte';
	import { dodge } from '$lib/transforms/beeswarm';
	import { eur, eurShort } from '$lib/transforms/format';
	import { binPosition } from '$lib/transforms/histogram';
	import { yearColor } from './yearColors';

	// the year legend and the explanatory note live on the page: they serve
	// this chart AND the value-bracket view it toggles with. `plotHeight`
	// reports the dodge layout's computed height back out, so that view can
	// draw at the same height and the frame stops jumping on toggle.
	// `edges` are that view's brackets: dots are placed on the bracket axis
	// (one doubling per equal slot == a plain log scale, since
	// `queries_extra.dase_value_histogram` derives pure-doubling edges), so
	// the two modes share ONE scale and every reference line coincides.
	let {
		data,
		edges,
		plotHeight = $bindable(0),
		colors = yearColor,
		ring,
		thresholds = [],
		linkBase = '/dase/contract/',
		minHeight = 320,
		radius = 2.6,
		padLeftFrac = 0,
		medianColor = 'var(--ink)',
		maxHeight = 560
	}: {
		data: DaseSwarm;
		edges: number[];
		plotHeight?: number;
		/** dot colour by signature year — defaults to the ΔΑΣΕ greens */
		colors?: (y: string | null | undefined) => string;
		/** per-row flag drawn as a ring (Anti-nero: single-bid contracts) */
		ring?: (number | null)[];
		/** dashed reference lines on the shared axis (ν.4782 ceilings) */
		thresholds?: { v: number; label: string }[];
		linkBase?: string;
		/** the canvas floor and the dot radius — the Anti-nero frame asks for
		 *  380 px with dots grown to match (user, 2026-08-21); ΔΑΣΕ keeps the
		 *  defaults */
		minHeight?: number;
		radius?: number;
		/** push the plot right by this fraction of the width, the scale
		 *  unchanged — the user's own placing of the card's swarm
		 *  (2026-08-28); what runs past the right edge is clipped */
		padLeftFrac?: number;
		/** the median line's colour (the ink unless a page says otherwise) */
		medianColor?: string;
		/** the tallest the chart may be: the dots shrink until the tallest
		 *  column fits it — a card tile passes its own box, so the axis
		 *  amounts at the foot are never clipped (user, 2026-08-28) */
		maxHeight?: number;
	} = $props();

	// margins must match LogHistogram's exactly — the shared axis is defined
	// in pixels, not just in value space
	const M = { top: 26, right: 8, bottom: 34, left: 8 };
	let width = $state(900);
	const R = $derived(radius);
	const MIN_H = $derived(minHeight);
	const MAX_H = $derived(maxHeight);

	interface Dot {
		i: number;
		x: number;
		y: number;
		eur: number;
	}

	const valid = $derived(
		data.ref.map((_, i) => i).filter((i) => (data.eur[i] ?? 0) > 0)
	);
	// one slot per bracket, exactly as LogHistogram lays them out
	const bw = $derived((width - M.left - M.right) / edges.length);
	const pad = $derived(Math.round(padLeftFrac * width));
	const x = $derived((v: number) => binPosition(v, edges, M.left + pad, bw));
	const layout = $derived.by(() => {
		let cached = layoutCache.get(data);
		if (cached && Math.abs(cached.width - width) <= 2 && cached.pad === pad && cached.maxH === MAX_H)
			return cached;
		const xs = valid.map((i) => x(data.eur[i]!));
		// same-priced contracts stack into tall columns; size the canvas to
		// the tallest one (the fixed-height version clipped ~1/3 of it) and
		// only shrink the dots when a narrow viewport would exceed the cap
		let r = R;
		let ys = dodge(xs, r + 0.4);
		let half = Math.max(...ys.map(Math.abs)) + r + 2;
		while (M.top + M.bottom + 2 * half > MAX_H && r > 0.9) {
			r = Math.max(0.9, r * 0.85);
			ys = dodge(xs, r + 0.4);
			half = Math.max(...ys.map(Math.abs)) + r + 2;
		}
		const h = Math.round(Math.max(MIN_H, M.top + M.bottom + 2 * half));
		cached = { width, xs, ys, r, h, pad, maxH: MAX_H };
		layoutCache.set(data, cached);
		return cached;
	});
	const height = $derived(layout.h);
	$effect(() => {
		plotHeight = height;
	});
	/** the dots as drawn, on the canvas element itself — for an exporter
	 *  that wants circles rather than pixels (2026-08-28); no DOM cost */
	$effect(() => {
		if (canvas)
			(canvas as HTMLCanvasElement & { __dots?: unknown }).__dots = dots.map((d) => ({
				x: d.x,
				y: d.y,
				r: layout.r,
				fill: resolveCssColor(colors(data.year[d.i]))
			}));
	});
	const dots = $derived.by((): Dot[] => {
		const { xs, ys } = layout;
		const cy = M.top + (height - M.top - M.bottom) / 2;
		return valid.map((idx, j) => ({ i: idx, x: xs[j], y: cy + ys[j], eur: data.eur[idx]! }));
	});

	// pixel-grid buckets for hover hit-testing (no quadtree dependency)
	const CELL = 8;
	const grid = $derived.by(() => {
		const m = new Map<string, Dot[]>();
		for (const d of dots) {
			const key = `${Math.floor(d.x / CELL)}:${Math.floor(d.y / CELL)}`;
			const arr = m.get(key);
			if (arr) arr.push(d);
			else m.set(key, [d]);
		}
		return m;
	});

	function nearest(px: number, py: number): Dot | null {
		const cx = Math.floor(px / CELL);
		const cy = Math.floor(py / CELL);
		let best: Dot | null = null;
		let bd = (layout.r + 3) ** 2;
		for (let dx = -1; dx <= 1; dx++)
			for (let dy = -1; dy <= 1; dy++)
				for (const d of grid.get(`${cx + dx}:${cy + dy}`) ?? []) {
					const dist = (d.x - px) ** 2 + (d.y - py) ** 2;
					if (dist < bd) {
						bd = dist;
						best = d;
					}
				}
		return best;
	}

	let canvas = $state<HTMLCanvasElement | null>(null);
	let hover = $state<Dot | null>(null);

	$effect(() => {
		if (!canvas) return;
		const dpr = window.devicePixelRatio || 1;
		canvas.width = width * dpr;
		canvas.height = height * dpr;
		const ctx = canvas.getContext('2d')!;
		ctx.scale(dpr, dpr);
		ctx.clearRect(0, 0, width, height);
		for (const d of dots) {
			ctx.beginPath();
			ctx.arc(d.x, d.y, layout.r, 0, 2 * Math.PI);
			ctx.fillStyle = resolveCssColor(colors(data.year[d.i]));
			ctx.globalAlpha = 0.85;
			ctx.fill();
			if (ring?.[d.i]) {
				ctx.globalAlpha = 1;
				ctx.beginPath();
				ctx.arc(d.x, d.y, layout.r + 0.9, 0, 2 * Math.PI);
				ctx.strokeStyle = resolveCssColor('color-mix(in srgb, var(--ink) 53.3%, black)');
				ctx.lineWidth = 0.9;
				ctx.stroke();
				ctx.globalAlpha = 0.85;
			}
		}
		if (hover) {
			ctx.globalAlpha = 1;
			ctx.beginPath();
			ctx.arc(hover.x, hover.y, layout.r + 1.5, 0, 2 * Math.PI);
			ctx.strokeStyle = resolveCssColor('var(--ink)');
			ctx.lineWidth = 1.5;
			ctx.stroke();
		}
	});

	function onMove(ev: MouseEvent) {
		const rect = canvas!.getBoundingClientRect();
		const sx = width / rect.width;
		hover = nearest((ev.clientX - rect.left) * sx, (ev.clientY - rect.top) * sx);
	}
	function onClick() {
		if (hover) goto(`${linkBase}${data.ref[hover.i]}`);
	}

	const median = $derived.by(() => {
		const vs = valid.map((i) => data.eur[i]!).sort((a, b) => a - b);
		return vs[Math.floor(vs.length / 2)] ?? 0;
	});
	const biggest = $derived(dots.reduce((m, d) => (d.eur > m.eur ? d : m), dots[0]));
	/** where the largest dot's label goes: above every dot under the
	 *  label's own span (it ends over the dot and runs left), so the
	 *  amount never prints over the swarm */
	const noteY = $derived.by(() => {
		if (!biggest) return 0;
		const span = 6.2 * (9 + eurShort(biggest.eur).length) + 6;
		let top = biggest.y;
		for (const d of dots)
			if (d.x <= biggest.x + layout.r + 2 && d.x >= biggest.x - span) top = Math.min(top, d.y);
		return top - layout.r - 8;
	});
	// round decades that fall inside the bracket axis' own span
	const axisTicks = $derived(
		[100, 1e3, 1e4, 1e5, 1e6].filter((v) => v >= edges[1] && v <= edges[edges.length - 1])
	);

	const dmy = (iso: string | null | undefined) =>
		iso ? `${iso.slice(8, 10)}.${iso.slice(5, 7)}.${iso.slice(0, 4)}` : '—';
	// dark ink on the light year swatches, white on the deep ones — the
	// swatch colours are CSS strings over the tokens now, so resolve first
	function tipInk(c: string): string {
		return cssLuminance(c) > 0.55 ? 'var(--ink)' : 'var(--paper)';
	}
	const hoverColor = $derived(hover ? colors(data.year[hover.i]) : '');
</script>

<div class="wrap" bind:clientWidth={width}>
	<!-- svelte-ignore a11y_no_static_element_interactions, a11y_click_events_have_key_events -->
	<canvas
		bind:this={canvas}
		style:width="100%"
		style:height="{height}px"
		style:cursor={hover ? 'pointer' : 'default'}
		onmousemove={onMove}
		onmouseleave={() => (hover = null)}
		onclick={onClick}
	></canvas>

	<svg class="overlay" viewBox="0 0 {width} {height}">
		{#each axisTicks as t (t)}
			<line class="grid" x1={x(t)} x2={x(t)} y1={M.top} y2={height - M.bottom} />
			<text class="axis" x={x(t)} y={height - 12}>{eurShort(t)}</text>
		{/each}
		{#each thresholds as th, i (th.v)}
			{@const tx = x(th.v)}
			{@const next = thresholds[i + 1]}
			{@const left = next !== undefined && x(next.v) - tx < 48}
			<line class="thresh" x1={tx} x2={tx} y1={M.top} y2={height - M.bottom} />
			<!-- two ceilings a doubling apart (€30k, €60k) sit 40-odd px apart:
			     the first label goes LEFT of its line, the next right (user) -->
			<text class="thresh-label" x={left ? tx - 4 : tx + 4} y={M.top + 10} text-anchor={left ? 'end' : 'start'}>{th.label}</text>
		{/each}
		<line class="median" x1={x(median)} x2={x(median)} y1={M.top} y2={height - M.bottom} style:stroke={medianColor} />
		<text class="median-label" x={x(median)} y={M.top - 8} text-anchor="middle">
			median {eurShort(median)}
		</text>
		{#if biggest && noteY > M.top + 4}
			<!-- the largest contract's amount AT its own dot (user, 2026-08-28:
			     «closer to the dot of that contract, and legible»): just above
			     the dots that stand near it, ending over the dot, with a
			     vertical tick down to it — the dot is alone in its column at
			     the far right, so the tick crosses nothing -->
			<line class="notetick" x1={biggest.x} y1={noteY + 3} x2={biggest.x} y2={biggest.y - layout.r - 1} />
			<text class="note" x={biggest.x + layout.r + 1} y={noteY} text-anchor="end"
				>largest: {eurShort(biggest.eur)}</text
			>
		{/if}
	</svg>

	{#if hover}
		<div class="tip" style:background={hoverColor} style:color={tipInk(hoverColor)}>
			<strong>{eur(hover.eur)}</strong><br />
			signed {dmy(data.d?.[hover.i])}<br />
			{data.ref[hover.i]}
		</div>
	{/if}
</div>

<style>
	.wrap {
		position: relative;
	}
	canvas {
		display: block;
	}
	.overlay {
		position: absolute;
		inset: 0;
		width: 100%;
		height: auto;
		pointer-events: none;
	}
	.grid {
		stroke: var(--line);
	}
	.axis {
		font-size: 11px;
		/* the amounts under the grid lines must be read, not guessed
		   (user, 2026-08-28) */
		fill: var(--ink-soft);
		text-anchor: middle;
	}
	.thresh {
		stroke: var(--c-threshold);
		stroke-dasharray: 3 4;
	}
	.thresh-label {
		font-size: 10px;
		fill: var(--c-threshold);
	}
	.median {
		stroke: var(--ink);
		stroke-width: 2.5;
		stroke-dasharray: 7 5;
	}
	.median-label {
		font-size: 12px;
		font-weight: 800;
		fill: var(--ink);
	}
	.note {
		font-size: 11px;
		fill: var(--ink);
		font-style: italic;
	}
	.notetick {
		stroke: var(--ink);
		stroke-width: 0.8;
	}
	.tip {
		position: absolute;
		top: 0;
		right: 0;
		max-width: 24rem;
		border-radius: var(--radius);
		padding: var(--sp-2) var(--sp-3);
		font-size: var(--fs-13);
		pointer-events: none;
		box-shadow: var(--shadow-paper);
	}
</style>
