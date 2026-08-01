<script lang="ts">
	import { eurShort, grInt } from '$lib/transforms/format';

	interface YearRow {
		year: string;
		paid_eur?: number;
		stated_eur?: number;
		eur?: number;
		n?: number;
		n_payments?: number;
	}
	interface Props {
		rows: YearRow[];
		color?: string;
	}
	let { rows, color = 'var(--accent)' }: Props = $props();

	const val = (r: YearRow) => (r.eur ?? 0) + (r.paid_eur ?? 0) + (r.stated_eur ?? 0);
	const maxV = $derived(Math.max(...rows.map(val), 1));
	const hasSplit = $derived(rows.some((r) => r.paid_eur !== undefined));
</script>

<div class="chart">
	{#each rows as r (r.year)}
		<div class="row">
			<span class="year">{r.year}</span>
			<div class="track">
				{#if hasSplit}
					<div
						class="bar"
						style:background={color}
						style:width={`${(88 * (r.paid_eur ?? 0)) / maxV}%`}
						title="paid"
					></div>
					<div
						class="bar stated"
						style:width={`${(88 * (r.stated_eur ?? 0)) / maxV}%`}
						title="stated, unpaid"
					></div>
				{:else}
					<div class="bar" style:background={color} style:width={`${(88 * val(r)) / maxV}%`}></div>
				{/if}
				<span class="val">
					{val(r) ? eurShort(val(r)) : '—'}
					{#if r.n}<small>· {grInt(r.n)}</small>{/if}
					{#if r.n_payments}<small>· {grInt(r.n_payments)} orders</small>{/if}
				</span>
			</div>
		</div>
	{/each}
	{#if hasSplit}
		<p class="note">solid = paid via payment orders · hatched = stated value of unpaid contracts</p>
	{/if}
</div>

<style>
	.row {
		display: flex;
		align-items: center;
		gap: var(--sp-2);
		margin-bottom: 4px;
	}
	.year {
		width: 3rem;
		font-size: var(--fs-13);
		color: var(--ink-soft);
	}
	.track {
		flex: 1;
		display: flex;
		align-items: center;
		gap: 2px;
	}
	.bar {
		height: 14px;
		border-radius: 2px;
		min-width: 1px;
	}
	.bar.stated {
		background: repeating-linear-gradient(
			45deg,
			var(--ink-faint),
			var(--ink-faint) 3px,
			transparent 3px,
			transparent 6px
		);
	}
	.val {
		font-size: var(--fs-12);
		color: var(--ink-soft);
		white-space: nowrap;
		margin-left: var(--sp-1);
	}
	.note {
		font-size: var(--fs-12);
		color: var(--ink-faint);
		font-style: italic;
		margin-top: var(--sp-1);
	}
</style>
