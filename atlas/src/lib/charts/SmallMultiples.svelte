<script lang="ts">
	import type { PeYearly } from '$lib/api';
	import { eurShort } from '$lib/transforms/format';

	interface Props {
		data: PeYearly;
		top?: number;
		/** href builder for a facet click (e.g. map drill permalink) */
		hrefOf?: (pe: string) => string;
	}
	let { data, top = 20, hrefOf }: Props = $props();

	const facets = $derived(data.pes.slice(0, top));
	// SHARED scale across every facet — that is the point of small multiples
	const maxYear = $derived(
		Math.max(...facets.flatMap((f) => Object.values(f.years)), 1)
	);
	const years = $derived(data.years);
</script>

<div class="grid">
	{#each facets as f (f.pe)}
		{@const inner = years.map((y) => ({ y, v: f.years[y] ?? 0 }))}
		<a class="facet" href={hrefOf?.(f.pe) ?? undefined}>
			<div class="head">
				<span class="pe">{f.pe.replace('Π.Ε. ', '')}</span>
				<span class="total">{eurShort(f.total_eur)}</span>
			</div>
			<svg viewBox="0 0 120 46">
				{#each inner as { y, v }, i (y)}
					{@const h = (40 * v) / maxYear}
					<rect
						x={i * (120 / years.length) + 2}
						y={42 - h}
						width={120 / years.length - 4}
						height={h}
						fill="var(--accent)"
						opacity={v > 0 ? 0.85 : 0}
					/>
				{/each}
				<line x1="0" x2="120" y1="42" y2="42" stroke="var(--line-strong)" stroke-width="0.6" />
			</svg>
			<div class="years">
				<span>{years[0]?.slice(2)}</span>
				<span>{years.at(-1)?.slice(2)}</span>
			</div>
		</a>
	{/each}
</div>

<style>
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(9.5rem, 1fr));
		gap: var(--sp-3) var(--sp-4);
	}
	.facet {
		text-decoration: none;
		border-top: 2px solid var(--line-strong);
		padding-top: var(--sp-1);
	}
	.facet:hover .pe {
		color: var(--accent);
	}
	.head {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: var(--sp-2);
	}
	.pe {
		font-size: var(--fs-13);
		font-weight: 600;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.total {
		font-size: var(--fs-12);
		color: var(--ink-soft);
		white-space: nowrap;
	}
	svg {
		display: block;
		width: 100%;
	}
	.years {
		display: flex;
		justify-content: space-between;
		font-size: 10px;
		color: var(--ink-faint);
	}
</style>
