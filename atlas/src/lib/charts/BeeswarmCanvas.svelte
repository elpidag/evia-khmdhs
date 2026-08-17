<script lang="ts" module>
	// dodge layout memo across navigations — the payload object identity is
	// stable thanks to the client fetch cache, so revisiting the page skips
	// the ~60ms layout for 2,018 points
	const layoutCache = new WeakMap<
		object,
		{ width: number; xs: number[]; ys: number[]; r: number; h: number }
	>();
</script>

<script lang="ts">
	import type { DaseSwarm } from '$lib/api';
	import { goto } from '$app/navigation';
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
		plotHeight = $bindable(0)
	}: { data: DaseSwarm; edges: number[]; plotHeight?: number } = $props();

	// margins must match LogHistogram's exactly — the shared axis is defined
	// in pixels, not just in value space
	const M = { top: 26, right: 8, bottom: 34, left: 8 };
	let width = $state(900);
	const R = 2.6;
	const MIN_H = 320;
	const MAX_H = 560;

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
	const x = $derived((v: number) => binPosition(v, edges, M.left, bw));
	const layout = $derived.by(() => {
		let cached = layoutCache.get(data);
		if (cached && Math.abs(cached.width - width) <= 2) return cached;
		const xs = valid.map((i) => x(data.eur[i]!));
		// same-priced contracts stack into tall columns; size the canvas to
		// the tallest one (the fixed-height version clipped ~1/3 of it) and
		// only shrink the dots when a narrow viewport would exceed the cap
		let r = R;
		let ys = dodge(xs, r + 0.4);
		let half = Math.max(...ys.map(Math.abs)) + r + 2;
		while (M.top + M.bottom + 2 * half > MAX_H && r > 1.5) {
			r = Math.max(1.5, r * 0.85);
			ys = dodge(xs, r + 0.4);
			half = Math.max(...ys.map(Math.abs)) + r + 2;
		}
		const h = Math.round(Math.max(MIN_H, M.top + M.bottom + 2 * half));
		cached = { width, xs, ys, r, h };
		layoutCache.set(data, cached);
		return cached;
	});
	const height = $derived(layout.h);
	$effect(() => {
		plotHeight = height;
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
			ctx.fillStyle = yearColor(data.year[d.i]);
			ctx.globalAlpha = 0.85;
			ctx.fill();
		}
		if (hover) {
			ctx.globalAlpha = 1;
			ctx.beginPath();
			ctx.arc(hover.x, hover.y, layout.r + 1.5, 0, 2 * Math.PI);
			ctx.strokeStyle = '#2a2118';
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
		if (hover) goto(`/dase/contract/${data.ref[hover.i]}`);
	}

	const median = $derived.by(() => {
		const vs = valid.map((i) => data.eur[i]!).sort((a, b) => a - b);
		return vs[Math.floor(vs.length / 2)] ?? 0;
	});
	const biggest = $derived(dots.reduce((m, d) => (d.eur > m.eur ? d : m), dots[0]));
	// round decades that fall inside the bracket axis' own span
	const axisTicks = $derived(
		[100, 1e3, 1e4, 1e5, 1e6].filter((v) => v >= edges[1] && v <= edges[edges.length - 1])
	);

	const dmy = (iso: string | null | undefined) =>
		iso ? `${iso.slice(8, 10)}.${iso.slice(5, 7)}.${iso.slice(0, 4)}` : '—';
	// dark ink on the light year swatches, white on the deep ones
	function tipInk(hex: string): string {
		const n = parseInt(hex.slice(1), 16);
		const lum = (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255;
		return lum > 0.55 ? '#1c221f' : '#ffffff';
	}
	const hoverColor = $derived(hover ? yearColor(data.year[hover.i]) : '');
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
		<line class="median" x1={x(median)} x2={x(median)} y1={M.top} y2={height - M.bottom} />
		<text class="median-label" x={x(median)} y={M.top - 8} text-anchor="middle">
			median {eurShort(median)}
		</text>
		{#if biggest}
			<text class="note" x={biggest.x - 6} y={biggest.y - 10} text-anchor="end">
				largest: {eurShort(biggest.eur)}
			</text>
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
		fill: var(--ink-faint);
		text-anchor: middle;
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
		fill: var(--ink-soft);
		font-style: italic;
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
