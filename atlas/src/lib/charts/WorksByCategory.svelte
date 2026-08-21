<script lang="ts">
	/**
	 * TYPES OF WORK: the works as ROWS, each bar split by the main category
	 * of the contracts naming it (user, 2026-08-22 — the work names are long,
	 * so they must be row labels; every column-headed drawing failed).
	 *
	 * Two modes of the same row: `unit = false` a stacked bar (one segment per
	 * category, greys), `unit = true` one small square per contract coloured
	 * by its category — the same numbers, counted or measured. Both say in
	 * one picture what the one-category-per-contract rule flattens: the
	 * contracts naming «firebreaks» sit in general prevention AND in mixed
	 * firebreaks AND in archaeological protection.
	 *
	 * Counts only — no price per work exists inside a bundled contract.
	 */
	import { grInt } from '$lib/transforms/format';

	export interface WorkRow {
		theme: string;
		label: string;
		n: number;
		/** contracts naming it, by main category — biggest first */
		by: { key: string; label: string; n: number }[];
	}
	interface Props {
		rows: WorkRow[];
		/** category key → grey */
		colorOf: (key: string) => string;
		/** one square per contract instead of a stacked bar */
		unit?: boolean;
	}
	let { rows, colorOf, unit = false }: Props = $props();

	const maxN = $derived(Math.max(1, ...rows.map((r) => r.n)));
	const SQ = 11; // unit square + its gap
	let hot = $state<string | null>(null);
</script>

<div class="works">
	{#each rows as r (r.theme)}
		<div class="row" class:hot={hot === r.theme}>
			<div class="lbl">{r.label}</div>
			<div class="track">
				{#if unit}
					<!-- one square per contract, in category order -->
					<div class="units" style:width={`${(100 * r.n) / maxN}%`}>
						{#each r.by as seg (seg.key)}
							{#each Array(seg.n) as _, i (seg.key + i)}
								<!-- svelte-ignore a11y_no_static_element_interactions -->
								<i
									class="u"
									style:background={colorOf(seg.key)}
									title={`${r.label} · ${seg.label}`}
									onmouseenter={() => (hot = r.theme)}
									onmouseleave={() => (hot = null)}
								></i>
							{/each}
						{/each}
					</div>
				{:else}
					<div class="bar" style:width={`${(100 * r.n) / maxN}%`}>
						{#each r.by as seg (seg.key)}
							<!-- svelte-ignore a11y_no_static_element_interactions -->
							<span
								class="seg"
								style:width={`${(100 * seg.n) / r.n}%`}
								style:background={colorOf(seg.key)}
								title={`${r.label} · ${seg.label}: ${grInt(seg.n)} contract${seg.n === 1 ? '' : 's'}`}
								onmouseenter={() => (hot = r.theme)}
								onmouseleave={() => (hot = null)}
							></span>
						{/each}
					</div>
				{/if}
				<span class="n">{grInt(r.n)}</span>
			</div>
		</div>
	{/each}
</div>

<style>
	.works {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.row {
		display: grid;
		grid-template-columns: 22rem minmax(0, 1fr);
		align-items: center;
		gap: var(--sp-3);
	}
	@media (max-width: 760px) {
		.row {
			grid-template-columns: 1fr;
			gap: 2px;
		}
	}
	.lbl {
		font-size: var(--fs-13);
		color: var(--ink);
		text-align: right;
		line-height: 1.25;
	}
	.row.hot .lbl {
		font-weight: 700;
	}
	.track {
		display: flex;
		align-items: center;
		gap: var(--sp-2);
		min-width: 0;
	}
	.bar {
		display: flex;
		height: 20px;
		border-radius: 2px;
		overflow: hidden;
	}
	.seg {
		display: block;
		height: 100%;
	}
	.units {
		display: flex;
		flex-wrap: wrap;
		gap: 2px;
	}
	.u {
		display: block;
		width: 9px;
		height: 9px;
		border-radius: 1px;
	}
	.n {
		font-size: var(--fs-12);
		color: var(--ink-soft);
		font-variant-numeric: tabular-nums;
		flex: none;
	}
</style>
