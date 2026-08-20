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
	let {
		rows,
		selected = null,
		onSelect
	}: {
		rows: OriginRow[];
		/** the region the flow map is focused on — its bar is highlighted */
		selected?: string | null;
		/** click a bar → focus that region on the map beside it */
		onSelect?: (pe: string) => void;
	} = $props();
</script>

<div class="origins">
	{#each rows as o (o.target_pe)}
		{@const total = o.local_eur + o.imported_eur + o.unknown_eur}
		<button
			type="button"
			class="orow"
			class:sel={selected === o.target_pe}
			onclick={() => onSelect?.(o.target_pe)}
		>
			<span class="olabel">{peEn(o.target_pe)}</span>
			<div class="obar">
				<div class="seg local" style:width={`${(100 * o.local_eur) / total}%`}></div>
				<div class="seg imported" style:width={`${(100 * o.imported_eur) / total}%`}></div>
				<div class="seg unknown" style:width={`${(100 * o.unknown_eur) / total}%`}></div>
			</div>
			<span class="oval">{eurShort(o.total_eur)}</span>
		</button>
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
		width: 100%;
		font: inherit;
		background: none;
		border: none;
		padding: 1px 2px;
		cursor: pointer;
		text-align: right;
	}
	.origins .orow:hover {
		background: var(--paper-2);
	}
	.origins .orow.sel {
		background: var(--paper-2);
		outline: 1px solid var(--line-strong);
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
		background: var(--ink);
	}
	.seg.imported {
		background: #c9c9c9;
	}
	.seg.unknown {
		background: repeating-linear-gradient(45deg, #ececec 0 3px, #f8f8f8 3px 6px);
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
		background: var(--ink);
	}
	.olegend i.imported {
		background: #c9c9c9;
	}
	.olegend i.unknown {
		background: repeating-linear-gradient(45deg, #ececec 0 3px, #f8f8f8 3px 6px);
	}
</style>
