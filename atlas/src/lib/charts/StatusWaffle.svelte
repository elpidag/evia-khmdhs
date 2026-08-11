<script lang="ts">
	import type { Snippet } from 'svelte';
	import { COLOR, NODATE_COLOR } from './ganttTheme';

	/** One square per project, coloured by outcome — the headline visual.
	 *  Categories, colours and wording follow the TIMELINE (ganttTheme +
	 *  GanttLegend): actives split into dated / no-implementation-dates. */
	interface Props {
		statuses: Record<string, number>;
		/** prose block rendered to the right of the colour legend */
		explanation?: Snippet;
	}
	let { statuses, explanation }: Props = $props();

	const ORDER: [string, string, string][] = [
		['completed', 'with identified completion act', COLOR.completed],
		['active', 'within deadline — no completion act identified', COLOR.active],
		['nodate', 'without specific dates for implementation', NODATE_COLOR],
		['no_completion_recorded', 'past deadline — no completion act identified', COLOR.no_completion_recorded],
		['revoked', 'revoked', COLOR.revoked]
	];
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
	}
	.cell:hover {
		outline: 2px solid var(--ink);
		outline-offset: 1px;
	}
	/* instant tooltip (native title needs a ~1s still hover) */
	.cell:hover::after {
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
