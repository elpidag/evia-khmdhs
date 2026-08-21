<script lang="ts">
	/**
	 * TYPES OF WORK as BUNDLES (user, 2026-08-22, after the flow read best
	 * but the drawing had to differ from MONEY FLOW's, and a bubble grid read
	 * as a matrix): the contracts grouped by the COMBINATION of works their
	 * signed title names — an UpSet-style plot.
	 *
	 * A bar per combination (how many contracts name exactly that set of
	 * works), and under it a row of dots saying which works are in the set,
	 * joined by a line. It answers the question the catch-all hid — «what do
	 * these contracts actually do?» — with the real bundles: «firebreaks +
	 * clearing + forest roads» 33, «firebreaks + mixed zones» 22, and so on.
	 * One column per work, ordered by how many contracts name it; the
	 * contracts naming no specific work stand as their own bar, dotless.
	 *
	 * Counts only: no price per work exists inside a bundled contract.
	 */
	import { grInt } from '$lib/transforms/format';

	interface Combo {
		/** theme keys in the set, in the column order */
		themes: string[];
		n: number;
	}
	interface Work {
		theme: string;
		label: string;
		n: number;
	}
	interface Props {
		combos: Combo[];
		works: Work[];
		/** how many bundles to draw; the rest are summed into a last bar */
		top?: number;
	}
	let { combos, works, top = 12 }: Props = $props();

	const COL = 26; // one column per work
	const ROW = 26; // one row per bundle
	const M = { left: 300, top: 16, gap: 14, bottom: 8 };
	const BAR = 240; // the count bars' own width

	const shown = $derived([...combos].sort((a, b) => b.n - a.n).slice(0, top));
	const restN = $derived(
		[...combos].sort((a, b) => b.n - a.n).slice(top).reduce((s, c) => s + c.n, 0)
	);
	const rows = $derived(restN ? [...shown, { themes: [], n: restN, rest: true }] : shown);
	const maxN = $derived(Math.max(1, ...rows.map((r) => r.n)));

	const gridLeft = $derived(M.left + BAR + M.gap);
	const width = $derived(gridLeft + works.length * COL + 12);
	const height = $derived(M.top + rows.length * ROW + 96);
	const cx = (i: number) => gridLeft + i * COL + COL / 2;
	const cy = (i: number) => M.top + i * ROW + ROW / 2;

	let hot = $state<number | null>(null);
	const inSet = (r: { themes: string[] }, theme: string) => r.themes.includes(theme);
	function label(r: { themes: string[]; rest?: boolean }): string {
		if ((r as { rest?: boolean }).rest) return 'all other combinations';
		if (!r.themes.length) return 'no specific work named';
		return r.themes.map((k) => works.find((w) => w.theme === k)?.label ?? k).join(' + ');
	}
</script>

<div class="wrap">
	<svg viewBox="0 0 {width} {height}" style:min-width="{width}px" role="img" aria-label="Contracts by the combination of works their title names">
		{#each rows as r, i (i)}
			{@const hotRow = hot === i}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<g class="row" class:hot={hotRow} onmouseenter={() => (hot = i)} onmouseleave={() => (hot = null)}>
				<rect class="hit" x="0" y={M.top + i * ROW} width={width} height={ROW} />
				<!-- the bundle in words, then its bar and count -->
				<text class="lbl" x={M.left - 10} y={cy(i) + 4} text-anchor="end">{label(r)}</text>
				<rect class="bar" x={M.left} y={cy(i) - 7} width={(BAR * r.n) / maxN} height="14" />
				<text class="n" x={M.left + (BAR * r.n) / maxN + 6} y={cy(i) + 4}>{grInt(r.n)}</text>
				<!-- the dot row: which works are in this bundle -->
				{#each works as w, ci (w.theme)}
					<circle class="dot" class:on={inSet(r, w.theme)} cx={cx(ci)} cy={cy(i)} r={inSet(r, w.theme) ? 5 : 2.6} />
				{/each}
				{#if r.themes.length > 1}
					{@const idx = works.map((w, ci) => (inSet(r, w.theme) ? ci : -1)).filter((x) => x >= 0)}
					<line class="join" x1={cx(idx[0])} x2={cx(idx[idx.length - 1])} y1={cy(i)} y2={cy(i)} />
				{/if}
			</g>
		{/each}

		<!-- the works, named under their columns -->
		{#each works as w, ci (w.theme)}
			<line class="colrule" x1={cx(ci)} x2={cx(ci)} y1={M.top} y2={M.top + rows.length * ROW + 4} />
			<text class="colh" transform={`translate(${cx(ci)} ${M.top + rows.length * ROW + 12}) rotate(55)`}>{w.label} ({grInt(w.n)})</text>
		{/each}
	</svg>
</div>

<style>
	.wrap {
		overflow-x: auto;
	}
	svg {
		display: block;
		width: 100%;
		height: auto;
	}
	.hit {
		fill: transparent;
	}
	.row.hot .hit {
		fill: #f4f4f4;
	}
	.lbl {
		font-size: 12px;
		fill: var(--ink);
	}
	.bar {
		fill: #2b2b2b;
	}
	.row.hot .bar {
		fill: #000;
	}
	.n {
		font-size: 11px;
		fill: var(--ink-soft);
		font-variant-numeric: tabular-nums;
	}
	.dot {
		fill: #d5d5d5;
	}
	.dot.on {
		fill: #2b2b2b;
	}
	.row.hot .dot.on {
		fill: #000;
	}
	.join {
		stroke: #2b2b2b;
		stroke-width: 2;
	}
	.colrule {
		stroke: var(--line);
		stroke-width: 0.5;
	}
	.colh {
		font-size: 10px;
		fill: var(--ink-soft);
		text-anchor: start;
	}
</style>
