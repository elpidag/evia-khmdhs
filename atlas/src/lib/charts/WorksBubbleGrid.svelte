<script lang="ts">
	/**
	 * TYPES OF WORK as a BUBBLE GRID (user, 2026-08-22, after the flow read
	 * best but the drawing had to differ from MONEY FLOW's): one row per main
	 * category (one per contract, so its € is honest), one column per work
	 * the signed titles NAME (multi-label) plus «no specific work named»;
	 * each cell a circle whose AREA is the number of contracts, the number
	 * printed inside where it fits. The bundle is then the picture — the
	 * catch-all row is a run of big circles under forest roads · clearing ·
	 * firebreaks — and it reads both ways at once: what a category's
	 * contracts do, and where a work's contracts were filed.
	 *
	 * Grayscale, one mark, no ribbons; the row's contract count and stated €
	 * close it (the only € the documents support), and a column's total
	 * closes it underneath. Pure SVG on a measured width, no d3 scale.
	 */
	import { eurShort, grInt } from '$lib/transforms/format';

	interface Cat {
		key: string;
		label: string;
		n: number;
		eur: number;
		/** contracts of this category naming at least one work */
		n_named: number;
		names: { theme: string; n: number }[];
	}
	interface Work {
		theme: string;
		label: string;
	}
	interface Props {
		cats: Cat[];
		works: Work[];
		/** row height / column width of the grid, in px */
		cell?: number;
	}
	let { cats, works, cell = 34 }: Props = $props();

	const NONE = '_none';
	const cols = $derived([...works, { theme: NONE, label: 'no specific work named' }]);
	const value = (c: Cat, theme: string) =>
		theme === NONE ? c.n - c.n_named : (c.names.find((w) => w.theme === theme)?.n ?? 0);
	const colTotal = (theme: string) => cats.reduce((s, c) => s + value(c, theme), 0);

	// geometry: labels left, totals right, rotated column heads on top
	const M = { left: 250, right: 132, top: 118, bottom: 26 };
	const width = $derived(M.left + cols.length * cell + M.right);
	const height = $derived(M.top + cats.length * cell + M.bottom);
	const cx = (i: number) => M.left + i * cell + cell / 2;
	const cy = (i: number) => M.top + i * cell + cell / 2;

	const maxV = $derived(
		Math.max(1, ...cats.flatMap((c) => cols.map((w) => value(c, w.theme))))
	);
	// area ∝ count, capped just inside the cell
	const r = (v: number) => (v ? Math.max(2.2, (cell / 2 - 2.5) * Math.sqrt(v / maxV)) : 0);
	// the number prints inside a circle big enough to hold it
	const fits = (v: number) => r(v) >= (String(v).length > 1 ? 9.5 : 7.5);

	let hot = $state<{ cat: string; col: string } | null>(null);
	const rowHot = (k: string) => hot?.cat === k;
	const colHot = (k: string) => hot?.col === k;
</script>

<div class="wrap">
	<svg viewBox="0 0 {width} {height}" style:min-width="{width}px" role="img" aria-label="Contracts by main category and by the works their titles name">
		<!-- column heads, rotated -->
		{#each cols as w, i (w.theme)}
			<text
				class="colh"
				class:none={w.theme === NONE}
				class:hot={colHot(w.theme)}
				transform={`translate(${cx(i)} ${M.top - 10}) rotate(-55)`}>{w.label}</text
			>
		{/each}

		{#each cats as c, ri (c.key)}
			<!-- row rule, then its cells -->
			<line class="rule" x1={M.left - 6} x2={M.left + cols.length * cell} y1={cy(ri) + cell / 2} y2={cy(ri) + cell / 2} />
			<text class="rowh" class:hot={rowHot(c.key)} x={M.left - 12} y={cy(ri) + 4} text-anchor="end">{c.label}</text>
			{#each cols as w, ci (w.theme)}
				{@const v = value(c, w.theme)}
				{#if v}
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<circle
						class="b"
						class:none={w.theme === NONE}
						cx={cx(ci)}
						cy={cy(ri)}
						r={r(v)}
						onmouseenter={() => (hot = { cat: c.key, col: w.theme })}
						onmouseleave={() => (hot = null)}
					>
						<title>{c.label} · {w.label}: {grInt(v)} contract{v === 1 ? '' : 's'}</title>
					</circle>
					{#if fits(v)}
						<text class="bn" x={cx(ci)} y={cy(ri) + 3.4} text-anchor="middle">{v}</text>
					{/if}
				{/if}
			{/each}
			<text class="tot" x={M.left + cols.length * cell + 10} y={cy(ri) + 4}>{grInt(c.n)}</text>
			<text class="tot eur" x={M.left + cols.length * cell + 54} y={cy(ri) + 4}>{eurShort(c.eur)}</text>
		{/each}

		<!-- column totals under the grid -->
		{#each cols as w, i (w.theme)}
			<text class="coltot" x={cx(i)} y={M.top + cats.length * cell + 16} text-anchor="middle">{grInt(colTotal(w.theme))}</text>
		{/each}
		<text class="corner" x={M.left - 12} y={M.top + cats.length * cell + 16} text-anchor="end">contracts naming it</text>
		<text class="corner" x={M.left + cols.length * cell + 10} y={M.top - 24}>contracts</text>
		<text class="corner" x={M.left + cols.length * cell + 54} y={M.top - 24}>stated €</text>
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
	.colh {
		font-size: 11px;
		fill: var(--ink-soft);
		text-anchor: start;
	}
	.colh.none {
		font-style: italic;
		fill: var(--ink-faint);
	}
	.colh.hot,
	.rowh.hot {
		fill: var(--ink);
		font-weight: 700;
	}
	.rowh {
		font-size: 12px;
		fill: var(--ink);
	}
	.rule {
		stroke: var(--line);
		stroke-width: 0.5;
	}
	.b {
		fill: #2b2b2b;
		cursor: default;
	}
	.b.none {
		fill: #ffffff;
		stroke: #8a8a8a;
		stroke-width: 1;
	}
	.b:hover {
		fill: #000;
	}
	.bn {
		font-size: 10px;
		font-weight: 700;
		fill: #fff;
		pointer-events: none;
	}
	.tot {
		font-size: 11px;
		fill: var(--ink-soft);
		font-variant-numeric: tabular-nums;
	}
	.tot.eur {
		fill: var(--ink);
	}
	.coltot {
		font-size: 10px;
		fill: var(--ink-faint);
		font-variant-numeric: tabular-nums;
	}
	.corner {
		font-size: 10px;
		fill: var(--ink-faint);
	}
</style>
