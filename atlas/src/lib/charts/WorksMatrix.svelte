<script lang="ts">
	/**
	 * TYPES OF WORK as a matrix (trial, user 2026-08-22): one row per main
	 * category (one per contract), one column per work the titles NAME
	 * (multi-label) plus «none named»; each cell the number of contracts,
	 * the fill a grey by count, the number printed. Reads both ways at once:
	 * what a category's contracts do, and where a work's contracts were
	 * filed. The row's € (the only honest €) and count close each row.
	 */
	import { eurShort, grInt } from '$lib/transforms/format';

	interface Cat {
		key: string;
		label: string;
		n: number;
		eur: number;
		/** contracts of this category naming at least one work */
		n_named: number;
		names: { theme: string; n: number }[];
	}
	interface Work {
		theme: string;
		label: string;
	}
	interface Props {
		cats: Cat[];
		works: Work[];
	}
	let { cats, works }: Props = $props();

	const cell = (c: Cat, theme: string) => c.names.find((w) => w.theme === theme)?.n ?? 0;
	const none = (c: Cat) => c.n - c.n_named;
	const maxCell = $derived(
		Math.max(1, ...cats.flatMap((c) => [...works.map((w) => cell(c, w.theme)), none(c)]))
	);
	// a grey by count — white for 0, black at the largest cell; ink flips
	// to white past mid-grey
	function fill(v: number): string {
		if (!v) return '#ffffff';
		const t = Math.sqrt(v / maxCell); // gentle: most cells are small
		const g = Math.round(240 - t * 220);
		return `rgb(${g},${g},${g})`;
	}
	const ink = (v: number) => (v && Math.sqrt(v / maxCell) > 0.55 ? '#fff' : '#111');
	// short column heads: the work's first words
	const head = (s: string) => (s.length > 22 ? s.slice(0, 21).replace(/[ ,]+$/, '') + '…' : s);
</script>

<div class="wrap">
	<table class="mx">
		<thead>
			<tr>
				<th class="corner"></th>
				{#each works as w (w.theme)}
					<th class="colh" title={w.label}><span>{head(w.label)}</span></th>
				{/each}
				<th class="colh none" title="contracts whose title names no specific work"><span>no work named</span></th>
				<th class="tot">contracts</th>
				<th class="tot">stated €</th>
			</tr>
		</thead>
		<tbody>
			{#each cats as c (c.key)}
				{@const u = none(c)}
				<tr>
					<th class="rowh" title={c.label}>{c.label}</th>
					{#each works as w (w.theme)}
						{@const v = cell(c, w.theme)}
						<td style:background={fill(v)} style:color={ink(v)} title={`${c.label} · ${w.label}: ${grInt(v)} contracts`}>{v || ''}</td>
					{/each}
					<td class="none" style:background={fill(u)} style:color={ink(u)} title={`${c.label}: ${grInt(u)} contracts name no specific work`}>{u || ''}</td>
					<td class="tot">{grInt(c.n)}</td>
					<td class="tot">{eurShort(c.eur)}</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>

<style>
	.wrap {
		overflow-x: auto;
	}
	.mx {
		border-collapse: separate;
		border-spacing: 2px;
		font-size: var(--fs-12);
		width: 100%;
	}
	.mx td,
	.mx th {
		padding: 0;
	}
	.mx td {
		height: 30px;
		min-width: 44px;
		text-align: center;
		font-variant-numeric: tabular-nums;
		border-radius: 2px;
	}
	.colh {
		height: 6.2rem;
		vertical-align: bottom;
		white-space: nowrap;
		font-weight: 400;
		color: var(--ink-soft);
	}
	.colh span {
		display: inline-block;
		transform: rotate(-60deg);
		transform-origin: left bottom;
		width: 1.2rem;
		white-space: nowrap;
	}
	.rowh {
		text-align: right;
		font-weight: 400;
		padding-right: var(--sp-2);
		white-space: nowrap;
		max-width: 19rem;
		overflow: hidden;
		text-overflow: ellipsis;
		color: var(--ink);
	}
	.tot {
		text-align: right;
		padding-left: var(--sp-3);
		white-space: nowrap;
		color: var(--ink-soft);
		font-weight: 400;
	}
	.none {
		font-style: italic;
	}
</style>
