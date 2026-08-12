<script lang="ts">
	import type { Snippet } from 'svelte';

	/** Generic one-square-per-project waffle — the CURRENT STATUS OF
	 *  PROJECTS visual grammar (StatusWaffle) for arbitrary categories. */
	export interface WaffleGroup {
		key: string;
		label: string;
		color: string;
		count: number;
	}
	interface Props {
		groups: WaffleGroup[];
		ariaLabel?: string;
		/** prose block rendered to the right of the colour legend */
		explanation?: Snippet;
		/** waffle above, legend below — for half-width placements */
		stacked?: boolean;
	}
	let {
		groups,
		ariaLabel = 'One square per project',
		explanation,
		stacked = false
	}: Props = $props();

	const cells = $derived(
		groups.flatMap((g) =>
			Array.from({ length: g.count }, () => ({
				color: g.color,
				tip: `${g.count} ${g.label}`
			}))
		)
	);
</script>

<div class="wrap" class:stacked>
	<div class="waffle" role="img" aria-label={ariaLabel}>
		{#each cells as c, i (i)}
			<span class="cell" style:background={c.color} data-tip={c.tip}></span>
		{/each}
	</div>
	<div class="side">
		<ul class="legend">
			{#each groups as g (g.key)}
				{#if g.count}
					<li><i style:background={g.color}></i>{g.label}</li>
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
		/* left column mirrors the hero cards width (4fr of 12), like StatusWaffle */
		display: grid;
		grid-template-columns: minmax(240px, 4fr) 8fr;
		gap: var(--sp-4) var(--sp-12);
		align-items: start;
	}
	.wrap.stacked {
		grid-template-columns: 1fr;
		gap: var(--sp-4);
	}
	.wrap.stacked .waffle {
		max-width: 380px;
	}
	.wrap.stacked .side {
		grid-template-columns: 1fr;
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
