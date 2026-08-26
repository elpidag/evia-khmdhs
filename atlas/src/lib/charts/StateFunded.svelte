<script lang="ts">
	import { mulberry32 } from '$lib/transforms/prng';
	/**
	 * STATE-FUNDED — the /compare opening animation (user, 2026-08-25;
	 * revised the same day: the mass is a loose SCATTER, not a packed
	 * circle; the separation runs YEAR BY YEAR with the year printed
	 * while it happens; the two destinations are named from the start
	 * and their numbers appear only once the dots have divided).
	 *
	 * Three steps over one canvas (2.243 dots — canvas per the site rule):
	 *   1 · a scattered field: every contract a dot, area ∝ stated €,
	 *       one colour — all of it public money;
	 *   2 · the dots take their programme's colour where they lie;
	 *   3 · year by year (2021 → 2026) the dots drift to their side —
	 *       private companies left, forest workers' co-operatives right.
	 *
	 * The scatter is a SEEDED random rejection layout (deterministic, so
	 * every reader sees the same field); the shared € scale carries a
	 * radius floor, admitted in the caveat. Auto-plays once in view;
	 * stepper + replay; reduced motion gets the final state. Dots link
	 * to their contract pages.
	 */
	import { eur, eurShort, grInt } from '$lib/transforms/format';

	export interface DotsPayload {
		antinero: { ref: string[]; eur: number[]; year: (number | null)[]; total_eur: number };
		dase: { ref: string[]; eur: number[]; year: (number | null)[]; total_eur: number };
	}
	interface Props {
		dots: DotsPayload;
		/** recipient counts for the destination labels */
		nCompanies: number;
		nCoops: number;
	}
	let { dots, nCompanies, nCoops }: Props = $props();

	const W = 1120;
	const H = 560;
	const INK = '#2b2b2b';
	const GREEN_RAW = '#52b788';
	const NEUTRAL = '#8f8f8f';
	const R_FLOOR = 1.3;
	const R_MAX = 21;
	/** the strips start just below the label band */
	const PAD_TOP_CLUSTER = 64;

	interface Dot {
		ref: string;
		eur: number;
		side: 'a' | 'd';
		year: number;
		r: number;
		x0: number;
		y0: number;
		x1: number;
		y1: number;
	}


	const built = $derived.by(() => {
		const maxEur = Math.max(dots.antinero.eur[0] ?? 1, dots.dase.eur[0] ?? 1);
		const k = R_MAX / Math.sqrt(maxEur);
		const rOf = (e: number) => Math.max(R_FLOOR, k * Math.sqrt(Math.max(e, 0)));
		const all: Dot[] = [];
		const push = (s: DotsPayload['antinero'], side: 'a' | 'd') =>
			s.ref.forEach((ref, i) =>
				all.push({
					ref, eur: s.eur[i], side, year: s.year[i] ?? 2026,
					r: rOf(s.eur[i]), x0: 0, y0: 0, x1: 0, y1: 0
				})
			);
		push(dots.antinero, 'a');
		push(dots.dase, 'd');

		// THE SCATTER: seeded rejection sampling over the whole field,
		// biggest dots first so they always find room; a dot that cannot
		// place after 60 tries accepts its least-bad spot
		const rand = mulberry32(20260825);
		const placed: Dot[] = [];
		// clear of the destination labels and the sweep year at the top,
		// and off the frame edges — the field floats, it does not fill
		const PADX = 90;
		const PAD_TOP = 64;
		const PAD_BOT = 24;
		const sorted = [...all].sort((p, q) => q.r - p.r);
		// spatial grid for the overlap test
		const CELL = 56;
		const grid = new Map<string, Dot[]>();
		const cellsOf = (x: number, y: number, r: number) => {
			const out: string[] = [];
			for (let gx = Math.floor((x - r) / CELL); gx <= Math.floor((x + r) / CELL); gx++)
				for (let gy = Math.floor((y - r) / CELL); gy <= Math.floor((y + r) / CELL); gy++)
					out.push(`${gx}|${gy}`);
			return out;
		};
		for (const d of sorted) {
			let bx = 0, by = 0, bo = Infinity;
			for (let tr = 0; tr < 60; tr++) {
				const x = PADX + d.r + rand() * (W - 2 * (PADX + d.r));
				const y = PAD_TOP + d.r + rand() * (H - PAD_TOP - PAD_BOT - 2 * d.r);
				let worst = 0;
				for (const c of cellsOf(x, y, d.r + 2)) {
					for (const o of grid.get(c) ?? []) {
						const overlap = o.r + d.r + 1.2 - Math.hypot(x - o.x0, y - o.y0);
						if (overlap > worst) worst = overlap;
					}
				}
				if (worst <= 0) { bx = x; by = y; bo = 0; break; }
				if (worst < bo) { bo = worst; bx = x; by = y; }
			}
			d.x0 = bx;
			d.y0 = by;
			placed.push(d);
			for (const c of cellsOf(bx, by, d.r)) {
				const arr = grid.get(c) ?? [];
				arr.push(d);
				grid.set(c, arr);
			}
		}

		// THE DESTINATIONS: the dots ACCUMULATE by year — one horizontal
		// strip per year, 2021 at the BOTTOM and 2026 on top (user,
		// 2026-08-25 third round: the accumulation grows upward like
		// sediment), each dot SCATTERED at random inside its year's strip
		// with the same seeded rejection sampling as the opening field —
		// the shelf-wrapped rows read as forced. One overlap grid spans
		// all strips, so dots of neighbouring years may touch across the
		// strip line; only dot-on-dot overlap is refused. Each strip takes
		// the height its own year needs (from its dots' area at a safe
		// random-packing density) — fixed slices made 2025 spill.
		const years = [...new Set(all.map((d) => d.year))].sort();
		const rand2 = mulberry32(20260826);
		const grid2 = new Map<string, Dot[]>();
		const packStrip = (list: Dot[], colX: number, colW: number, top: number, h: number) => {
			for (const d of [...list].sort((p, q) => q.r - p.r)) {
				const ymin = h >= 2 * d.r ? top + d.r : top + h / 2;
				const yspan = Math.max(0, h - 2 * d.r);
				let bx = 0, by = 0, bo = Infinity;
				for (let tr = 0; tr < 120; tr++) {
					const x = colX + d.r + rand2() * (colW - 2 * d.r);
					const y = ymin + rand2() * yspan;
					let worst = 0;
					for (const c of cellsOf(x, y, d.r + 2)) {
						for (const o of grid2.get(c) ?? []) {
							const overlap = o.r + d.r + 0.6 - Math.hypot(x - o.x1, y - o.y1);
							if (overlap > worst) worst = overlap;
						}
					}
					if (worst <= 0) { bx = x; by = y; bo = 0; break; }
					if (worst < bo) { bo = worst; bx = x; by = y; }
				}
				d.x1 = bx;
				d.y1 = by;
				for (const c of cellsOf(bx, by, d.r)) {
					const arr = grid2.get(c) ?? [];
					arr.push(d);
					grid2.set(c, arr);
				}
			}
		};
		// packing density a rejection layout reliably reaches before jamming
		const EFF = 0.42;
		const needOf = (list: Dot[], colW: number) =>
			list.reduce((s, d) => s + Math.PI * d.r * d.r, 0) / (EFF * colW);
		const bands: { year: number; top: number; h: number }[] = [];
		let cursor = PAD_TOP_CLUSTER;
		for (const yr of [...years].reverse()) {
			const la = all.filter((d) => d.side === 'a' && d.year === yr);
			const ld = all.filter((d) => d.side === 'd' && d.year === yr);
			const maxR = Math.max(...la.map((d) => d.r), ...ld.map((d) => d.r), 0);
			const h = Math.max(needOf(la, 446), needOf(ld, 424), 2 * maxR + 2, 24);
			packStrip(la, 116, 446, cursor, h);
			packStrip(ld, 626, 424, cursor, h);
			bands.push({ year: yr, top: cursor, h });
			cursor += h;
		}
		const canvasH = Math.max(H, cursor + 6);

		return { all, years, bands, canvasH };
	});

	// ---- the steps -------------------------------------------------------
	const CAPTIONS = $derived([
		`${grInt(built.all.length)} state-funded forestry contracts since September 2021, every dot represents a contract, area ∝ its stated value.`,
		`Contracts that are included in the Anti-nero programme are coloured black.`,
		`Allocation of state funding via different contracts.`
	]);
	let step = $state(0);
	let played = $state(false);
	let t = $state(1);
	let raf = 0;
	const DUR = [900, 900, 4200]; // the year sweep takes its time
	const ease = (u: number) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);

	/** step-3 sweep: each year's dots move in their own window of t */
	const moveOf = (d: Dot, tt: number) => {
		const n = built.years.length;
		const i = Math.max(0, built.years.indexOf(d.year));
		const u = (tt * (n + 0.6) - i) / 1.6; // overlapping year windows
		return ease(Math.max(0, Math.min(1, u)));
	};
	const sweepYear = $derived.by(() => {
		if (step !== 2 || t >= 1) return null;
		const n = built.years.length;
		const i = Math.min(n - 1, Math.floor(t * (n + 0.6)));
		return built.years[i];
	});
	const done = $derived(step === 2 && t >= 1);

	function goTo(next: number) {
		step = next;
		cancelAnimationFrame(raf);
		const from = performance.now();
		const run = (now: number) => {
			t = Math.min(1, (now - from) / DUR[next]);
			draw();
			if (t < 1) raf = requestAnimationFrame(run);
		};
		t = 0;
		raf = requestAnimationFrame(run);
	}

	function autoplay() {
		if (played) return;
		played = true;
		if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
			step = 2;
			t = 1;
			draw();
			return;
		}
		goTo(0);
		setTimeout(() => goTo(1), 1600);
		setTimeout(() => goTo(2), 3200);
	}

	// ---- canvas ----------------------------------------------------------
	let canvas = $state<HTMLCanvasElement | null>(null);
	let wrap = $state<HTMLDivElement | null>(null);

	function draw() {
		if (!canvas) return;
		const ctx = canvas.getContext('2d');
		if (!ctx) return;
		const dpr = window.devicePixelRatio || 1;
		if (canvas.width !== W * dpr || canvas.height !== built.canvasH * dpr) {
			canvas.width = W * dpr;
			canvas.height = built.canvasH * dpr;
		}
		ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
		ctx.clearRect(0, 0, W, built.canvasH);
		const green = getComputedStyle(canvas).getPropertyValue('--c-dase').trim() || GREEN_RAW;
		const e = ease(t);
		const colourMix = step === 0 ? 0 : step === 1 ? e : 1;
		for (const d of built.all) {
			const m = step === 2 ? moveOf(d, t) : 0;
			const x = d.x0 + (d.x1 - d.x0) * m;
			const y = d.y0 + (d.y1 - d.y0) * m;
			const target = d.side === 'a' ? INK : green;
			ctx.beginPath();
			ctx.arc(x, y, d.r, 0, Math.PI * 2);
			if (colourMix >= 1) ctx.fillStyle = target;
			else if (colourMix <= 0) ctx.fillStyle = NEUTRAL;
			else {
				ctx.fillStyle = NEUTRAL;
				ctx.fill();
				ctx.globalAlpha = colourMix;
				ctx.fillStyle = target;
			}
			ctx.fill();
			ctx.globalAlpha = 1;
		}
		// the year, printed where its axis label will sit
		if (sweepYear != null) {
			const b = built.bands.find((bb) => bb.year === sweepYear);
			ctx.font = '700 26px sofia-sans, sans-serif';
			ctx.fillStyle = 'rgba(43,43,43,0.35)';
			ctx.textAlign = 'right';
			ctx.fillText(String(sweepYear), 96, (b ? b.top + b.h / 2 : 64) + 9);
		}
		// the y axis appears only once the dots have settled
		if (step === 2 && t >= 1) {
			ctx.font = '600 15px sofia-sans, sans-serif';
			ctx.fillStyle = 'rgba(43,43,43,0.62)';
			ctx.textAlign = 'right';
			for (const b of built.bands) ctx.fillText(String(b.year), 96, b.top + b.h / 2 + 5);
		}
	}

	$effect(() => {
		void built;
		draw();
	});

	$effect(() => {
		if (!wrap) return;
		const io = new IntersectionObserver(
			(es) => {
				if (es.some((x) => x.isIntersecting)) autoplay();
			},
			{ threshold: 0.35 }
		);
		io.observe(wrap);
		return () => io.disconnect();
	});

	// ---- hover: nearest dot at its CURRENT resting position --------------
	let hover = $state<{ d: Dot; x: number; y: number } | null>(null);
	function onMove(ev: MouseEvent) {
		if (!canvas || t < 1) return;
		const rect = canvas.getBoundingClientRect();
		const mx = ((ev.clientX - rect.left) / rect.width) * W;
		const my = ((ev.clientY - rect.top) / rect.height) * built.canvasH;
		const moved = step === 2 ? 1 : 0;
		let best: Dot | null = null;
		let bd = Infinity;
		for (const d of built.all) {
			const x = d.x0 + (d.x1 - d.x0) * moved;
			const y = d.y0 + (d.y1 - d.y0) * moved;
			const dist = Math.hypot(mx - x, my - y) - d.r;
			if (dist < bd) {
				bd = dist;
				best = d;
			}
		}
		hover = best && bd < 4 ? { d: best, x: mx, y: my } : null;
	}
	function onClick() {
		if (!hover) return;
		const d = hover.d;
		location.href = d.side === 'a' ? `/antinero/contract/${d.ref}` : `/dase/contract/${d.ref}`;
	}
</script>

<div class="sf" bind:this={wrap}>
	<div class="bar">
		<div class="steps" role="group" aria-label="Animation steps">
			{#each CAPTIONS as _, i (i)}
				<button
					class="stepdot"
					class:on={step === i}
					aria-label={`Step ${i + 1}`}
					onclick={() => goTo(i)}
				></button>
			{/each}
			<button
				class="replay"
				aria-label="Replay the animation"
				title="Replay"
				onclick={() => { played = false; autoplay(); }}>↻</button
			>
		</div>
		<p class="caption">{CAPTIONS[step]}</p>
	</div>

	<!-- the two destinations, named from the START; their numbers appear
	     only once the dots have divided (user, 2026-08-25) -->
	<div class="lab a" style:left="29.3%">
		private companies
		{#if done}<span class="num">{grInt(nCompanies)} · {eurShort(dots.antinero.total_eur)}</span>{/if}
	</div>
	<div class="lab d" style:left="74.3%">
		forest workers' co-operatives
		{#if done}<span class="num">{grInt(nCoops)} · {eurShort(dots.dase.total_eur)}</span>{/if}
	</div>

	<!-- svelte-ignore a11y_no_static_element_interactions a11y_click_events_have_key_events -->
	<canvas
		bind:this={canvas}
		style:width="100%"
		style:aspect-ratio={`${W} / ${built.canvasH}`}
		onmousemove={onMove}
		onmouseleave={() => (hover = null)}
		onclick={onClick}
		class:pointer={!!hover}
	></canvas>

	{#if hover}
		<div
			class="tip"
			style:left={`${(hover.x / W) * 100}%`}
			style:top={`${(hover.y / built.canvasH) * 100}%`}
			style:background={hover.d.side === 'a' ? INK : GREEN_RAW}
		>
			<strong>{eur(hover.d.eur)}</strong> · {hover.d.year}<br />{hover.d.ref}
		</div>
	{/if}
</div>

<style>
	.sf {
		position: relative;
	}
	.bar {
		display: flex;
		align-items: flex-start;
		gap: var(--sp-4);
		margin-bottom: var(--sp-2);
	}
	.steps {
		display: flex;
		align-items: center;
		gap: 7px;
		flex: none;
		padding-top: 3px;
	}
	.stepdot {
		width: 11px;
		height: 11px;
		border-radius: 50%;
		border: 1.4px solid var(--ink-soft);
		background: var(--paper);
		padding: 0;
		cursor: pointer;
	}
	.stepdot.on {
		background: var(--ink);
		border-color: var(--ink);
	}
	.replay {
		font: inherit;
		font-size: 17px;
		line-height: 1;
		border: 0;
		background: none;
		color: var(--ink-faint);
		cursor: pointer;
		padding: 0 0 2px;
	}
	.replay:hover {
		color: var(--ink);
	}
	.caption {
		margin: 0;
		font-size: var(--fs-14);
		color: var(--ink-soft);
		max-width: 46rem;
		line-height: 1.4;
		min-height: 2.9em;
	}
	canvas {
		display: block;
	}
	canvas.pointer {
		cursor: pointer;
	}
	.lab {
		position: absolute;
		top: 3.6em;
		transform: translateX(-50%);
		font-size: var(--fs-14);
		color: var(--ink-soft);
		white-space: nowrap;
		pointer-events: none;
		text-align: center;
	}
	.lab .num {
		display: block;
		color: var(--ink);
		font-weight: 700;
	}
	.tip {
		position: absolute;
		transform: translate(10px, 10px);
		color: #fff;
		font-size: var(--fs-12);
		padding: 4px 8px;
		border-radius: 4px;
		pointer-events: none;
		white-space: nowrap;
	}
</style>
