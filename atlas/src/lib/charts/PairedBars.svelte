<script lang="ts">
	import { peEn } from '$lib/transforms/regions';
	import type { ComparePayload } from '$lib/api';
	import { eurShort } from '$lib/transforms/format';

	interface Props {
		rows: ComparePayload['by_pe'];
		top?: number;
		antineroTotal: number;
		daseTotal: number;
	}
	let { rows, top = 15, antineroTotal, daseTotal }: Props = $props();

	const shown = $derived(rows.slice(0, top));
	const maxPct = $derived(
		Math.max(
			...shown.map((r) =>
				Math.max(r.antinero_eur / antineroTotal, r.dase_eur / daseTotal)
			),
			0.01
		)
	);
</script>

<div class="chart">
	<div class="cols-head">
		<span></span>
		<span class="antinero">Anti-nero — % of its total</span>
		<span class="dase">forest co-ops — % of its total</span>
	</div>
	{#each shown as r (r.pe)}
		{@const pa = r.antinero_eur / antineroTotal}
		{@const pd = r.dase_eur / daseTotal}
		<div class="row">
			<span class="pe">{peEn(r.pe)}</span>
			<div class="track left">
				<span class="val">{r.antinero_eur ? eurShort(r.antinero_eur) : '—'}</span>
				<div class="bar antinero" style:width={`${(100 * pa) / maxPct}%`}></div>
			</div>
			<div class="track">
				<div class="bar dase" style:width={`${(100 * pd) / maxPct}%`}></div>
				<span class="val">{r.dase_eur ? eurShort(r.dase_eur) : '—'}</span>
			</div>
		</div>
	{/each}
</div>

<style>
	.cols-head {
		display: grid;
		grid-template-columns: 9rem 1fr 1fr;
		gap: var(--sp-2);
		font-family: var(--font-display);
		font-weight: 700;
		font-size: var(--fs-13);
		margin-bottom: var(--sp-3);
	}
	.cols-head .antinero {
		color: var(--c-antinero);
		text-align: right;
	}
	.cols-head .dase {
		color: var(--c-dase);
	}
	.row {
		display: grid;
		grid-template-columns: 9rem 1fr 1fr;
		gap: var(--sp-2);
		align-items: center;
		margin-bottom: 3px;
	}
	.pe {
		font-size: var(--fs-13);
		text-align: right;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.track {
		display: flex;
		align-items: center;
		gap: var(--sp-1);
		min-height: 14px;
	}
	.track.left {
		justify-content: flex-end;
	}
	.bar {
		height: 14px;
		border-radius: 2px;
		min-width: 1px;
	}
	.bar.antinero {
		background: var(--c-antinero);
	}
	.bar.dase {
		background: var(--c-dase);
	}
	.val {
		font-size: var(--fs-13);
		color: var(--ink-soft);
		white-space: nowrap;
	}
</style>
