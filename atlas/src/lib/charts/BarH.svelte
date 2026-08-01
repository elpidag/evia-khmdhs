<script lang="ts">
	import { eurShort } from '$lib/transforms/format';

	export interface BarRow {
		label: string;
		value: number;
		href?: string;
		sublabel?: string;
	}

	interface Props {
		rows: BarRow[];
		fmt?: (v: number) => string;
		color?: string;
		/** shared max for comparable scales across charts; defaults to rows max */
		max?: number;
		/** highlight predicate — highlighted bars get full accent, rest muted */
		highlight?: (r: BarRow) => boolean;
	}
	let { rows, fmt = eurShort, color = 'var(--accent)', max, highlight }: Props = $props();

	const maxV = $derived(max ?? Math.max(...rows.map((r) => r.value), 1));
</script>

<div class="chart">
	{#each rows as r, i (i)}
		{@const w = Math.max(0.4, (100 * r.value) / maxV)}
		{@const dim = highlight ? !highlight(r) : false}
		<div class="row" class:dim>
			<div class="label">
				{#if r.href}<a href={r.href}>{r.label}</a>{:else}{r.label}{/if}
				{#if r.sublabel}<small class="sub">{r.sublabel}</small>{/if}
			</div>
			<div class="track">
				<div class="bar" style:width={`${w}%`} style:background={color}></div>
				<span class="value">{fmt(r.value)}</span>
			</div>
		</div>
	{/each}
</div>

<style>
	.chart {
		display: grid;
		gap: var(--sp-2);
	}
	.row.dim .bar {
		opacity: 0.35;
	}
	.label {
		font-size: var(--fs-14);
		line-height: 1.25;
		margin-bottom: 2px;
	}
	.label a {
		text-decoration: none;
	}
	.label a:hover {
		text-decoration: underline;
	}
	.sub {
		color: var(--ink-faint);
		margin-left: var(--sp-2);
	}
	.track {
		display: flex;
		align-items: center;
		gap: var(--sp-2);
	}
	.bar {
		height: 14px;
		border-radius: 2px;
		min-width: 2px;
	}
	.value {
		font-size: var(--fs-13);
		color: var(--ink-soft);
		white-space: nowrap;
	}
</style>
