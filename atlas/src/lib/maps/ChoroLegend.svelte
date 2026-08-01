<script lang="ts">
	import { eurShort } from '$lib/transforms/format';

	interface Props {
		ramp: string[];
		max: number;
		title?: string;
		fmt?: (v: number) => string;
	}
	let { ramp, max, title = '', fmt = eurShort }: Props = $props();

	// sqrt scale → the value at each swatch's LOWER edge
	const stops = $derived(
		[0.25, 0.5, 0.75, 1].map((t, i) => ({
			color: ramp[Math.min(ramp.length - 1, Math.floor(t * ramp.length) - 1)],
			label: fmt(max * t * t),
			last: i === 3
		}))
	);
</script>

<div class="legend">
	{#if title}<div class="title">{title}</div>{/if}
	<div class="swatches">
		<span class="swatch" style:background="var(--land-empty)"></span>
		{#each stops as s (s.label)}
			<span class="swatch" style:background={s.color}></span>
		{/each}
	</div>
	<div class="labels">
		<span>0</span>
		<span>{stops[3].label}</span>
	</div>
</div>

<style>
	.title {
		font-weight: 600;
		margin-bottom: 2px;
	}
	.swatches {
		display: flex;
		gap: 1px;
	}
	.swatch {
		width: 1.6rem;
		height: 0.6rem;
		display: inline-block;
	}
	.labels {
		display: flex;
		justify-content: space-between;
		color: var(--ink-soft);
	}
</style>
