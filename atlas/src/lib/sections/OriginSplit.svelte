<script lang="ts">
	/**
	 * € of works in the biggest destination regions, split by whether the
	 * winning firm is based in that region. Lifted out of /connections so the
	 * Anti-nero page can carry it (user, 2026-08-20).
	 */
	import { peEn } from '$lib/transforms/regions';
	import { eurShort } from '$lib/transforms/format';

	export interface OriginRow {
		target_pe: string;
		total_eur: number;
		local_eur: number;
		imported_eur: number;
		unknown_eur: number;
	}
	let { rows }: { rows: OriginRow[] } = $props();
</script>

<div class="origins">
	{#each rows as o (o.target_pe)}
		{@const total = o.local_eur + o.imported_eur + o.unknown_eur}
		<div class="orow">
			<span class="olabel">{peEn(o.target_pe)}</span>
			<div class="obar">
				<div class="seg local" style:width={`${(100 * o.local_eur) / total}%`}></div>
				<div class="seg imported" style:width={`${(100 * o.imported_eur) / total}%`}></div>
				<div class="seg unknown" style:width={`${(100 * o.unknown_eur) / total}%`}></div>
			</div>
			<span class="oval">{eurShort(o.total_eur)}</span>
		</div>
	{/each}
	<div class="olegend">
		<span><i class="local"></i>local firms</span>
		<span><i class="imported"></i>out-of-region firms</span>
		<span><i class="unknown"></i>unresolved</span>
	</div>
</div>

<style>
	.origins .orow {
		display: flex;
		align-items: center;
		gap: var(--sp-2);
		margin-bottom: 4px;
	}
	.olabel {
		width: 11rem;
		font-size: var(--fs-13);
		text-align: right;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.obar {
		flex: 1;
		display: flex;
		height: 14px;
		border-radius: 2px;
		overflow: hidden;
		background: var(--paper-2);
	}
	.seg.local {
		background: var(--c-good);
	}
	.seg.imported {
		background: var(--accent);
	}
	.seg.unknown {
		background: var(--line-strong);
	}
	.oval {
		width: 5.5rem;
		font-size: var(--fs-12);
		color: var(--ink-soft);
	}
	.olegend {
		display: flex;
		gap: var(--sp-4);
		font-size: var(--fs-12);
		color: var(--ink-soft);
		margin-top: var(--sp-2);
	}
	.olegend i {
		display: inline-block;
		width: 0.7rem;
		height: 0.7rem;
		margin-right: 4px;
	}
	.olegend i.local {
		background: var(--c-good);
	}
	.olegend i.imported {
		background: var(--accent);
	}
	.olegend i.unknown {
		background: var(--line-strong);
	}
</style>
