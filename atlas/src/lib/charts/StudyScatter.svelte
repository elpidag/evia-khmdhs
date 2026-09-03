<script lang="ts">
	import { eurShort } from '$lib/transforms/format';
	import { scaleLog } from 'd3-scale';
	import { CAT_COLORS, CAT_ORDER } from './catColors';

	/**
	 * Every stated study fee against its contract's value, log–log (user,
	 * 2026-08-22): the top-10 bars listed ten long Greek titles nobody
	 * could read; the scatter needs no labels at all. The diagonals are
	 * fixed SHARES of the contract value, the median share drawn solid —
	 * so the «the study is ~1–2% of the contract» claim is the picture.
	 */
	export interface StudyPoint {
		ref: string;
		/** the stated study fee, net € */
		s: number;
		/** the contract's value (the share's denominator), net € */
		c: number | null;
		share: number | null;
		t: string;
		/** the contract's main category — the dot's colour */
		cat?: string | null;
	}
	interface Props {
		points: StudyPoint[];
		/** the median share, e.g. 0.014 — the emphasized diagonal */
		medianShare?: number | null;
		/** category key → short label, for the key and the card */
		catLabels?: Record<string, string>;
	}
	let { points, medianShare = null, catLabels = {} }: Props = $props();
	// the dots wear their contract's main category in the page's shared
	// palette (user, 2026-08-23) — the same colour a category has on the
	// chord and the timeline's type lens
	const cats = $derived(CAT_ORDER.filter((k) => points.some((p) => p.cat === k)));
	const hue = (c?: string | null) => CAT_COLORS[c ?? ''] ?? 'color-mix(in srgb, var(--ink) 44.5%, var(--paper))';

	let width = $state(900);
	const height = 420;
	const M = { top: 18, right: 26, bottom: 44, left: 66 };

	const usable = $derived(points.filter((p) => p.s > 0 && (p.c ?? 0) > 0));
	const xDom = $derived.by(() => {
		const vs = usable.map((p) => p.c!) as number[];
		return [Math.min(...vs), Math.max(...vs)] as [number, number];
	});
	const yDom = $derived.by(() => {
		const vs = usable.map((p) => p.s);
		return [Math.min(...vs), Math.max(...vs)] as [number, number];
	});
	const x = $derived(scaleLog(xDom, [M.left, width - M.right]).nice());
	const y = $derived(scaleLog(yDom, [height - M.bottom, M.top]).nice());

	// guide diagonals: fixed shares of the contract value
	const GUIDES = [0.005, 0.01, 0.02, 0.05];
	const diag = $derived.by(() => {
		const [x0, x1] = x.domain() as [number, number];
		return (share: number) => {
			// clip the segment to the y-domain so the label sits on-chart
			const [yLo, yHi] = y.domain() as [number, number];
			const cLo = Math.max(x0, yLo / share);
			const cHi = Math.min(x1, yHi / share);
			if (cLo >= cHi) return null;
			return {
				x1: x(cLo), y1: y(cLo * share),
				x2: x(cHi), y2: y(cHi * share)
			};
		};
	});

	const ticksOf = (dom: [number, number]) =>
		[1e3, 1e4, 1e5, 1e6, 1e7, 1e8].filter((v) => v >= dom[0] && v <= dom[1]);

	let tip = $state<string | null>(null);
	const show = (p: StudyPoint) => {
		tip =
			`<strong>${eurShort(p.s)}</strong> study fee — ${p.share != null ? (p.share * 100).toFixed(1) + '% of ' : ''}${eurShort(p.c ?? 0)}` +
			(p.cat ? `<br><span style="color:var(--ink-faint)">${catLabels[p.cat] ?? p.cat}</span>` : '') +
			`<br>${p.t}`;
	};
</script>

<div class="wrap" bind:clientWidth={width}>
	{#if cats.length}
		<ul class="key">
			{#each cats as c (c)}
				<li><i style:background={hue(c)}></i>{catLabels[c] ?? c}</li>
			{/each}
		</ul>
	{/if}
	<svg viewBox="0 0 {width} {height}" style:height="{height}px" role="img" aria-label="Stated study fees against contract values">
		{#each ticksOf(x.domain() as [number, number]) as t (t)}
			<line class="grid" x1={x(t)} x2={x(t)} y1={M.top} y2={height - M.bottom} />
			<text class="axis" x={x(t)} y={height - M.bottom + 16} text-anchor="middle">{eurShort(t)}</text>
		{/each}
		{#each ticksOf(y.domain() as [number, number]) as t (t)}
			<line class="grid" x1={M.left} x2={width - M.right} y1={y(t)} y2={y(t)} />
			<text class="axis" x={M.left - 6} y={y(t) + 3} text-anchor="end">{eurShort(t)}</text>
		{/each}

		{#each GUIDES as g (g)}
			{@const d = diag(g)}
			{#if d}
				<line class="guide" x1={d.x1} y1={d.y1} x2={d.x2} y2={d.y2} />
				<text class="guide-label" x={d.x2 - 2} y={d.y2 - 4} text-anchor="end">{g * 100}%</text>
			{/if}
		{/each}
		{#if medianShare}
			{@const d = diag(medianShare)}
			{#if d}
				<line class="median" x1={d.x1} y1={d.y1} x2={d.x2} y2={d.y2} />
				<text class="median-label" x={d.x1 + 4} y={d.y1 - 6}>median {(medianShare * 100).toFixed(1)}%</text>
			{/if}
		{/if}

		{#each usable as p (p.ref)}
			<a href={`/antinero/contract/${p.ref}`} aria-label={`${p.ref}: ${eurShort(p.s)}`}>
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<circle
					class="pt"
					cx={x(p.c!)}
					cy={y(p.s)}
					r="4.5"
					fill={hue(p.cat)}
					onmouseenter={() => show(p)}
					onmouseleave={() => (tip = null)}
				/>
			</a>
		{/each}

		<text class="axis-name" x={width - M.right} y={height - 6} text-anchor="end">contract value (net €)</text>
		<text class="axis-name" transform={`translate(12 ${M.top}) rotate(90)`}>study fee (net €)</text>
	</svg>

	{#if tip}
		<div class="tip">
			<!-- eslint-disable-next-line svelte/no-at-html-tags -->
			{@html tip}
		</div>
	{/if}
</div>

<style>
	.wrap {
		position: relative;
	}
	svg {
		display: block;
		width: 100%;
	}
	.grid {
		stroke: var(--rule-soft, color-mix(in srgb, var(--ink) 7.6%, var(--paper)));
		stroke-width: 0.5;
	}
	.axis {
		font-size: 10px;
		fill: var(--ink-faint);
	}
	.axis-name {
		font-size: 11px;
		fill: var(--ink-soft);
	}
	.guide {
		stroke: var(--line);
		stroke-dasharray: 3 4;
	}
	.guide-label {
		font-size: 10px;
		fill: var(--ink-faint);
	}
	.median {
		stroke: var(--ink);
		stroke-width: 1.2;
	}
	.median-label {
		font-size: 10px;
		font-weight: 700;
		fill: var(--ink);
	}
	.pt {
		opacity: 0.78;
		stroke: var(--paper);
		stroke-width: 0.6;
		cursor: pointer;
	}
	.pt:hover {
		opacity: 1;
		stroke: var(--ink);
	}
	/* the MAP legend's dress, as on the other category keys */
	.key {
		list-style: none;
		margin: 0 0 var(--sp-2);
		box-sizing: border-box;
		padding: var(--sp-2) var(--sp-3);
		background: color-mix(in srgb, var(--ink) 5.8%, var(--paper));
		border-radius: 6px;
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 4px var(--sp-6, 1.5rem);
		font-size: var(--fs-14);
		color: var(--ink-soft);
	}
	.key li {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.key li i {
		width: 12px;
		height: 12px;
		border-radius: 3px;
		flex: none;
	}
	.tip {
		position: absolute;
		top: 0;
		right: 0;
		max-width: 26rem;
		background: color-mix(in srgb, var(--paper) 94%, transparent);
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		padding: var(--sp-2) var(--sp-3);
		font-size: var(--fs-13);
		pointer-events: none;
		box-shadow: var(--shadow-paper);
	}
</style>
