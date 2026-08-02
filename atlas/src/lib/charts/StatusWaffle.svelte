<script lang="ts">
	/** One square per project, coloured by outcome — the headline visual. */
	interface Props {
		statuses: Record<string, number>;
	}
	let { statuses }: Props = $props();

	const ORDER: [string, string, string][] = [
		['completed', 'completion act on record', 'var(--c-anadohoi)'],
		['active', 'still inside deadline', '#9a8c74'],
		['no_completion_recorded', 'deadline passed, nothing filed', 'var(--c-antinero)'],
		['revoked', 'revoked', '#7a1f1f']
	];
	const cells = $derived(
		ORDER.flatMap(([k, , color]) =>
			Array.from({ length: statuses[k] ?? 0 }, () => ({ k, color }))
		)
	);
</script>

<div class="waffle" role="img" aria-label="Project outcomes as one square each">
	{#each cells as c, i (i)}
		<span class="cell" style:background={c.color}></span>
	{/each}
</div>
<div class="legend">
	{#each ORDER as [k, label, color] (k)}
		{#if statuses[k]}
			<span><i style:background={color}></i>{statuses[k]} {label}</span>
		{/if}
	{/each}
</div>

<style>
	.waffle {
		display: grid;
		grid-template-columns: repeat(17, 1fr);
		gap: 3px;
		max-width: 420px;
	}
	.cell {
		aspect-ratio: 1;
		border-radius: 2px;
	}
	.legend {
		display: flex;
		flex-wrap: wrap;
		gap: var(--sp-3);
		margin-top: var(--sp-2);
		font-size: var(--fs-13);
		color: var(--ink-soft);
	}
	.legend i {
		display: inline-block;
		width: 10px;
		height: 10px;
		border-radius: 2px;
		margin-right: 5px;
	}
</style>
