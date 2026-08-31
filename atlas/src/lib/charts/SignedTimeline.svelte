<script lang="ts">
	/**
	 * EVERY CONTRACT BY THE DAY IT WAS SIGNED (user, 2026-08-29, second
	 * round): one EQUAL dot per contract of either programme — the size says
	 * nothing here, the colour says the programme (ink Anti-nero, green the
	 * co-operatives) — in ONE swarm on ONE time axis, dodged around a single
	 * centreline so a busy week piles up and a quiet month lies flat. The
	 * fire season (1 May – 31 October) is shaded in the site's one season
	 * tint under the dots; the year rules carry their year centred at the
	 * bottom. Canvas, because 2,257 marks; the lettering and the hover card
	 * are DOM. Third round (user): the dots are BIGGER and never leave the
	 * frame — so they sit on a lattice whose column is ONE WEEK (fourth
	 * round) and a week whose column is full spills into the neighbouring
	 * weeks; the frame reports the largest such displacement, computed. The
	 * Anti-nero dot is a little bigger than the co-operatives' (user).
	 */
	import { goto } from '$app/navigation';
	import { eur, grInt, dmy } from '$lib/transforms/format';
	import type { ComparePayload } from '$lib/api';

	type DotsPayload = ComparePayload['dots'];
	interface Props {
		dots: DotsPayload;
		/** the axis start; the co-op dataset begins in September 2021 */
		axisStart?: string;
		/** the axis end — the pages' «today» */
		today?: string;
		/** OUT: the largest displacement (days) a full column forced — for the caveat */
		maxShiftDays?: number;
	}
	let { dots, axisStart = '2021-09-01', today, maxShiftDays = $bindable(0) }: Props = $props();
	$effect(() => {
		maxShiftDays = built.maxShiftDays;
	});

	const W = 1120;
	const H = 460;
	const PADL = 10;
	const PADR = 10;
	const INK = '#2b2b2b';
	const GREEN = '#52b788';
	/** the lattice: ONE WEEK per column (user, fourth round), rows this tall;
	 *  the Anti-nero dot a little bigger than the co-operatives' */
	const DAYS_PER_COL = 7;
	const CELL_H = 4.4;
	const R_A = 2.0;
	const R_D = 1.55;
	/** the one band; the year labels sit under it */
	const BAND = { top: 46, bottom: 416 };
	const LABEL_Y = 442;

	interface Dot {
		ref: string;
		eur: number;
		d: string;
		side: 'a' | 'd';
		r: number;
		x: number;
		y: number;
	}

	/** the axis opens on the first day of the earliest signature's month —
	 *  a co-op contract signed in July 2021 and posted in September is in
	 *  the dataset — or on `axisStart`, whichever is earlier */
	const t0 = $derived.by(() => {
		const all = [...dots.antinero.d, ...dots.dase.d].filter((d): d is string => !!d);
		const first = all.length ? all.reduce((m, d) => (d < m ? d : m)) : axisStart;
		const t = Math.min(Date.parse(axisStart), Date.parse(first.slice(0, 7) + '-01'));
		return t;
	});
	const t1 = $derived(Date.parse(today ?? new Date().toISOString().slice(0, 10)) + 5 * 864e5);
	const x = (t: number) => PADL + ((t - t0) / (t1 - t0)) * (W - PADL - PADR);

	/** the one swarm on a lattice: every dated contract at the column of its
	 *  day, at the free row nearest the centreline; a full column spills to
	 *  the nearest column with room, alternating sides, so nothing ever
	 *  leaves the band. `maxShiftDays` = the largest such displacement. */
	const built = $derived.by(() => {
		const meta: { ref: string; eur: number; d: string; side: 'a' | 'd'; t: number }[] = [];
		const take = (side: DotsPayload['antinero'], tag: 'a' | 'd') =>
			side.ref.forEach((ref, i) => {
				const d = side.d[i];
				if (d) meta.push({ ref, eur: side.eur[i], d, side: tag, t: Date.parse(d) });
			});
		take(dots.antinero, 'a');
		take(dots.dase, 'd');
		meta.sort((p, q) => p.t - q.t);
		const pxPerDay = (W - PADL - PADR) / ((t1 - t0) / 864e5);
		const CELL_W = DAYS_PER_COL * pxPerDay;
		const cols = Math.floor((W - PADL - PADR) / CELL_W);
		const rows = Math.floor((BAND.bottom - BAND.top) / CELL_H);
		const mid = Math.floor(rows / 2);
		const filled: boolean[][] = Array.from({ length: cols }, () => new Array<boolean>(rows).fill(false));
		const colOf = (t: number) => Math.min(cols - 1, Math.max(0, Math.floor((x(t) - PADL) / CELL_W)));
		const freeRow = (c: number): number => {
			for (let k = 0; k < rows; k++) {
				for (const r of k === 0 ? [mid] : [mid - k, mid + k]) {
					if (r >= 0 && r < rows && !filled[c][r]) return r;
				}
			}
			return -1;
		};
		let maxShift = 0;
		const all: Dot[] = meta.map((m) => {
			const c0 = colOf(m.t);
			let c = c0;
			let r = freeRow(c);
			for (let k = 1; r < 0 && k < cols; k++) {
				for (const cc of [c0 + k, c0 - k]) {
					if (cc < 0 || cc >= cols) continue;
					const rr = freeRow(cc);
					if (rr >= 0) { c = cc; r = rr; break; }
				}
			}
			if (r < 0) { c = c0; r = mid; }
			filled[c][r] = true;
			const cx = PADL + (c + 0.5) * CELL_W;
			maxShift = Math.max(maxShift, Math.abs(cx - x(m.t)) / pxPerDay);
			return { ...m, r: m.side === 'a' ? R_A : R_D, x: cx, y: BAND.top + (r + 0.5) * CELL_H };
		});
		return { all, maxShiftDays: Math.round(maxShift), daysPerColumn: DAYS_PER_COL };
	});

	/** year rules on 1 January, and the fire seasons 1 May – 31 October */
	const years = $derived.by(() => {
		const out: { y: number; x: number }[] = [];
		const y0 = new Date(t0).getUTCFullYear();
		const y1 = new Date(t1).getUTCFullYear();
		for (let y = y0; y <= y1 + 1; y++) {
			const t = Date.UTC(y, 0, 1);
			if (t >= t0 && t <= t1) out.push({ y, x: x(t) });
		}
		return out;
	});
	const seasons = $derived.by(() => {
		const out: { key: number; x0: number; x1: number }[] = [];
		const y0 = new Date(t0).getUTCFullYear();
		const y1 = new Date(t1).getUTCFullYear();
		for (let y = y0; y <= y1; y++) {
			const s = Math.max(Date.UTC(y, 4, 1), t0);
			const e = Math.min(Date.UTC(y, 9, 31, 23, 59), t1);
			if (e > s) out.push({ key: y, x0: x(s), x1: x(e) });
		}
		return out;
	});

	/** hit-testing on a coarse grid, like the card beeswarm */
	const CELL = 24;
	const grid = $derived.by(() => {
		const m = new Map<string, Dot[]>();
		for (const d of built.all) {
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
		let bd = Infinity;
		for (let dx = -1; dx <= 1; dx++)
			for (let dy = -1; dy <= 1; dy++)
				for (const d of grid.get(`${cx + dx}:${cy + dy}`) ?? []) {
					const dist = Math.hypot(d.x - px, d.y - py) - d.r;
					if (dist < bd && dist < 4) {
						bd = dist;
						best = d;
					}
				}
		return best;
	}

	let canvas = $state<HTMLCanvasElement | null>(null);
	let hover = $state<Dot | null>(null);
	let width = $state(W);

	$effect(() => {
		if (!canvas) return;
		const dpr = window.devicePixelRatio || 1;
		canvas.width = W * dpr;
		canvas.height = H * dpr;
		const ctx = canvas.getContext('2d')!;
		ctx.scale(dpr, dpr);
		ctx.clearRect(0, 0, W, H);
		for (const d of built.all) {
			ctx.beginPath();
			ctx.arc(d.x, d.y, d.r, 0, 2 * Math.PI);
			ctx.fillStyle = d.side === 'a' ? INK : GREEN;
			ctx.globalAlpha = 0.85;
			ctx.fill();
		}
		if (hover) {
			ctx.globalAlpha = 1;
			ctx.beginPath();
			ctx.arc(hover.x, hover.y, hover.r + 1.6, 0, 2 * Math.PI);
			ctx.strokeStyle = hover.side === 'a' ? INK : GREEN;
			ctx.lineWidth = 1.4;
			ctx.stroke();
		}
	});

	function onMove(ev: MouseEvent) {
		const rect = canvas!.getBoundingClientRect();
		const sx = W / rect.width;
		hover = nearest((ev.clientX - rect.left) * sx, (ev.clientY - rect.top) * sx);
	}
	function onClick() {
		if (hover) goto(`${hover.side === 'a' ? '/antinero/contract/' : '/dase/contract/'}${hover.ref}`);
	}
</script>

<div class="wrap" bind:clientWidth={width}>
	<!-- the season bands and year rules sit UNDER the dots (the canvas is
	     transparent), the axis and lettering above them -->
	<svg class="under" viewBox="0 0 {W} {H}">
		{#each seasons as s (s.key)}
			<rect class="season" x={s.x0} y={BAND.top - 6} width={s.x1 - s.x0} height={BAND.bottom - BAND.top + 12} />
		{/each}
		{#each years as y (y.y)}
			<line class="rule" x1={y.x} x2={y.x} y1={BAND.top - 6} y2={BAND.bottom + 6} />
		{/each}
	</svg>
	<!-- svelte-ignore a11y_no_static_element_interactions, a11y_click_events_have_key_events -->
	<canvas
		bind:this={canvas}
		style:width="100%"
		style:height="{(H * width) / W}px"
		style:cursor={hover ? 'pointer' : 'default'}
		onmousemove={onMove}
		onmouseleave={() => (hover = null)}
		onclick={onClick}
	></canvas>

	<svg class="overlay" viewBox="0 0 {W} {H}">
		{#if !years.length || years[0].x > PADL + 40}
			<!-- the axis opens mid-year: name that year at its start too -->
			<text class="year" x={PADL + 2} y={LABEL_Y} text-anchor="start">{new Date(t0).getUTCFullYear()}</text>
		{/if}
		{#each years as y (y.y)}
			<!-- the year sits CENTRED on its own rule, under the axis (user) -->
			<text class="year" x={y.x} y={LABEL_Y} text-anchor="middle">{y.y}</text>
		{/each}
		<!-- the key: colour is the programme, every dot the same size -->
		<circle class="key a" cx={PADL + 6} cy={18} r={R_A + 1.2} />
		<text class="lane a" x={PADL + 16} y={22}
			>ANTI-NERO · {grInt(dots.antinero.ref.length)} contracts</text
		>
		<circle class="key d" cx={PADL + 236} cy={18} r={R_D + 1.2} />
		<text class="lane d" x={PADL + 246} y={22}
			>FOREST CO-OPERATIVES · {grInt(dots.dase.ref.length)} contracts</text
		>
	</svg>

	{#if hover}
		<div class="tip" class:green={hover.side === 'd'}>
			<strong>{eur(hover.eur)}</strong><br />
			signed {dmy(hover.d)}<br />
			{hover.ref}
		</div>
	{/if}
</div>

<style>
	.wrap {
		position: relative;
	}
	canvas {
		display: block;
		position: relative;
	}
	.under {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}
	.overlay {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		overflow: visible;
	}
	rect.season {
		/* the page's ONE fire-season colour: the red's light shade */
		fill: var(--c-fire-season);
	}
	line.rule {
		stroke: var(--line);
		stroke-width: 0.8;
	}
	text.year {
		font-size: 12px;
		fill: var(--ink-soft);
		font-family: var(--font-ui);
	}
	text.lane {
		font-size: 11px;
		letter-spacing: 0.04em;
		font-family: var(--font-ui);
		font-weight: 700;
	}
	text.lane.a {
		fill: var(--ink);
	}
	text.lane.d {
		fill: #2e8a5c;
	}
	circle.key.a {
		fill: #2b2b2b;
	}
	circle.key.d {
		fill: #52b788;
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
		background: #1f1f1f;
		color: #fff;
	}
	.tip.green {
		background: #52b788;
		color: #0d2a1c;
	}
</style>
