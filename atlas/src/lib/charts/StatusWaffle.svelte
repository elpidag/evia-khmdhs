<script lang="ts">
	import type { Snippet } from 'svelte';
	import { COLOR, NODATE_COLOR, noDate, type GanttProject } from './ganttTheme';

	/** One square per project, coloured by outcome — the headline visual.
	 *  Categories, colours and wording follow the TIMELINE (ganttTheme +
	 *  GanttLegend): actives split into dated / no-implementation-dates. */
	interface Props {
		statuses: Record<string, number>;
		/** prose block rendered to the right of the colour legend */
		explanation?: Snippet;
		/** just the squares — the caller provides legend and prose */
		bare?: boolean;
		/** bare mode: one NAMED square per project (category-ordered,
		 *  chronological inside each category) — enables the hover link */
		projects?: GanttProject[];
		/** externally-driven highlight (e.g. hovering the map dot) */
		hotAda?: string | null;
		/** square hover events out (ada + mouse position), null on leave */
		onCellHover?: (ada: string | null, e?: MouseEvent) => void;
	}
	let {
		statuses,
		explanation,
		bare = false,
		projects,
		hotAda = null,
		onCellHover
	}: Props = $props();

	const ORDER: [string, string, string][] = [
		['completed', 'with identified completion act', COLOR.completed],
		['active', 'within deadline — no completion act identified', COLOR.active],
		['nodate', 'without specific dates for implementation', NODATE_COLOR],
		['no_completion_recorded', 'past deadline — no completion act identified', COLOR.no_completion_recorded],
		['revoked', 'revoked', COLOR.revoked]
	];
	const CAT_COLOR: Record<string, string> = Object.fromEntries(
		ORDER.map(([k, , c]) => [k, c])
	);
	const RANK: Record<string, number> = Object.fromEntries(ORDER.map(([k], i) => [k, i]));
	const keyOf = (p: GanttProject) => (noDate(p) ? 'nodate' : p.status);
	/** per-project cells, in the categories' legend order */
	const pcells = $derived.by(() => {
		if (!projects) return null;
		return [...projects]
			.sort(
				(a, b) =>
					(RANK[keyOf(a)] ?? 9) - (RANK[keyOf(b)] ?? 9) ||
					(a.start0 ?? a.start ?? '').localeCompare(b.start0 ?? b.start ?? '')
			)
			.map((p) => ({ ada: p.ada, name: p.company, color: CAT_COLOR[keyOf(p)] ?? '#999' }));
	});
	const cells = $derived(
		ORDER.flatMap(([k, label, color]) =>
			Array.from({ length: statuses[k] ?? 0 }, () => ({
				k,
				color,
				tip: `${statuses[k]} ${label}`
			}))
		)
	);
</script>

{#if bare}
	{#if pcells}
		<div class="waffle" role="img" aria-label="One square per project, coloured by outcome">
			{#each pcells as c (c.ada)}
				<a
					class="cell"
					class:hot={c.ada === hotAda}
					style:background={c.color}
					href={`/anadohoi/project/${c.ada}`}
					aria-label={c.name}
					onmouseenter={(e) => onCellHover?.(c.ada, e)}
					onmouseleave={() => onCellHover?.(null)}
				></a>
			{/each}
		</div>
	{:else}
		<div class="waffle" role="img" aria-label="Project outcomes as one square each">
			{#each cells as c, i (i)}
				<span class="cell" style:background={c.color} data-tip={c.tip}></span>
			{/each}
		</div>
	{/if}
{:else}
<div class="wrap">
	<div class="waffle" role="img" aria-label="Project outcomes as one square each">
		{#each cells as c, i (i)}
			<span class="cell" style:background={c.color} data-tip={c.tip}></span>
		{/each}
	</div>
	<div class="side">
		<ul class="legend">
			{#each ORDER as [k, label, color] (k)}
				{#if statuses[k]}
					<li><i style:background={color}></i>{label}</li>
				{/if}
			{/each}
		</ul>
		{#if explanation}
			<div class="expl">{@render explanation()}</div>
		{/if}
	</div>
</div>
{/if}

<style>
	.wrap {
		/* left column mirrors the hero cards / fitted-title width (4fr of 12) */
		display: grid;
		grid-template-columns: minmax(240px, 4fr) 8fr;
		gap: var(--sp-4) var(--sp-12);
		align-items: start;
	}
	.waffle {
		display: grid;
		grid-template-columns: repeat(14, 1fr);
		gap: 3px;
	}
	.cell {
		aspect-ratio: 1;
		border-radius: 2px;
		position: relative;
		display: block;
	}
	.cell:hover,
	.cell.hot {
		outline: 2px solid var(--ink);
		outline-offset: 1px;
	}
	/* instant tooltip (native title needs a ~1s still hover) */
	.cell[data-tip]:hover::after {
		content: attr(data-tip);
		position: absolute;
		bottom: calc(100% + 6px);
		left: 50%;
		transform: translateX(-50%);
		background: var(--ink);
		color: #fff;
		font-size: var(--fs-12);
		line-height: 1.3;
		padding: 3px 8px;
		border-radius: 4px;
		white-space: nowrap;
		pointer-events: none;
		z-index: 5;
	}
	.side {
		display: grid;
		/* legend at its natural width; the explanation starts right after it */
		grid-template-columns: max-content 1fr;
		gap: var(--sp-6);
		align-items: start;
	}
	.legend {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: var(--sp-2);
		font-size: var(--fs-14);
		color: var(--ink-soft);
	}
	.expl {
		font-size: var(--fs-14);
		color: var(--ink-soft);
		line-height: 1.5;
	}
	.expl :global(p) {
		margin: 0 0 var(--sp-2);
	}
	.expl :global(p:last-child) {
		margin-bottom: 0;
	}
	.legend i {
		display: inline-block;
		width: 12px;
		height: 12px;
		border-radius: 2px;
		margin-right: 8px;
	}
	@media (max-width: 900px) {
		.wrap,
		.side {
			grid-template-columns: 1fr;
		}
	}
</style>
