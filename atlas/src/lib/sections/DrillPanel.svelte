<script lang="ts">
	import { eur, eurShort } from '$lib/transforms/format';

	interface Props {
		pe: string;
		side: 'works' | 'home';
		contracts: { ref: string; title: string; eur: number }[];
		contractors: { vat: string; name: string; eur: number; n: number }[];
		onReset: () => void;
	}
	let { pe, side, contracts, contractors, onReset }: Props = $props();

	const totalC = $derived(contracts.reduce((s, c) => s + c.eur, 0));
	let showAll = $state(false);
	const shown = $derived(showAll ? contracts : contracts.slice(0, 12));
</script>

<div class="drill">
	<div class="head">
		<h3>
			{#if side === 'works'}
				{pe}: {contracts.length} contracts, {eurShort(totalC)} of works
			{:else}
				Contractors based in {pe}: {contractors.length} firms, {eurShort(totalC)} of works held
			{/if}
		</h3>
		<button class="reset" onclick={onReset}>✕ All of Greece</button>
	</div>

	<div class="cols">
		<div>
			<h4>Contracts{side === 'works' ? ` in ${pe}` : ''} ({contracts.length})</h4>
			<table>
				<tbody>
					{#each shown as c (c.ref)}
						<tr>
							<td><a href={`/antinero/contract/${c.ref}`}>{c.title}</a></td>
							<td class="num">{eur(c.eur)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
			{#if contracts.length > 12 && !showAll}
				<button class="more" onclick={() => (showAll = true)}>
					Show all {contracts.length}
				</button>
			{/if}
		</div>
		<div>
			<h4>
				{side === 'works' ? `Contractors working in ${pe}` : `Contractors based in ${pe}`}
				({contractors.length})
			</h4>
			<table>
				<tbody>
					{#each contractors as c (c.vat)}
						<tr>
							<td><a href={`/antinero/contractor/${c.vat}`}>{c.name}</a></td>
							<td class="num muted">{c.n}×</td>
							<td class="num">{eur(c.eur)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</div>
</div>

<style>
	.drill {
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		background: var(--paper-2);
		padding: var(--sp-4);
		margin-top: var(--sp-4);
	}
	.head {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: var(--sp-4);
		flex-wrap: wrap;
	}
	h3 {
		margin: 0 0 var(--sp-3);
	}
	h4 {
		font-family: var(--font-ui);
		font-size: var(--fs-14);
		color: var(--ink-soft);
		margin: 0 0 var(--sp-2);
	}
	.cols {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(20rem, 1fr));
		gap: var(--sp-6);
	}
	td a {
		text-decoration: none;
	}
	td a:hover {
		text-decoration: underline;
	}
	.reset {
		font: inherit;
		font-size: var(--fs-13);
		border: 1px solid var(--line-strong);
		border-radius: 999px;
		background: var(--paper);
		padding: var(--sp-1) var(--sp-3);
		cursor: pointer;
	}
	.more {
		font: inherit;
		font-size: var(--fs-13);
		color: var(--ink-soft);
		background: none;
		border: 0;
		text-decoration: underline;
		cursor: pointer;
		padding: var(--sp-1) 0;
	}
	.muted {
		color: var(--ink-faint);
	}
</style>
