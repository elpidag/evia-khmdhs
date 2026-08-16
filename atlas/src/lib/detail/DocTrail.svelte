<script lang="ts" module>
	export interface TrailRow {
		/** ISO date (any prefix length) or null */
		d: string | null;
		/** English document-type label */
		type: string;
		/** ΑΔΑΜ / ΑΔΑ */
		code: string;
		title: string | null;
		/** href for the PDF proxy, null = no document */
		pdf: string | null;
		/** the page's own document */
		self?: boolean;
		/** small warning chip, e.g. cancelled */
		chip?: string;
	}
</script>

<script lang="ts">
	/**
	 * DOCUMENT TRAIL–TIMELINE (user template, 2026-08-17): the SAME table
	 * on every detail page — date · type of document · document code ·
	 * title · pdf. Callers pass rows with English type labels already
	 * resolved; the row for the viewed document itself is highlighted.
	 */
	import type { Snippet } from 'svelte';

	interface Props {
		rows: TrailRow[];
		heading?: string;
		/** optional strip between the heading and the table (timeline bar) */
		top?: Snippet;
	}
	let { rows, heading = 'DOCUMENT TRAIL–TIMELINE', top }: Props = $props();
	const dmy = (iso: string | null) =>
		iso && iso.length >= 10 ? `${iso.slice(8, 10)}.${iso.slice(5, 7)}.${iso.slice(0, 4)}` : '—';
</script>

<section class="trail">
	<h2>{heading}</h2>
	{#if top}
		{@render top()}
	{/if}
	<table class="listing">
		<thead>
			<tr>
				<th>date</th>
				<th>type of document</th>
				<th>document code</th>
				<th>title</th>
				<th class="pdfcol">pdf</th>
			</tr>
		</thead>
		<tbody>
			{#each rows as r (r.code + r.type)}
				<tr class:self={r.self}>
					<td class="tabular nowrap">{dmy(r.d)}</td>
					<td>{r.type}{#if r.chip}<span class="chip bad">{r.chip}</span>{/if}</td>
					<td class="tabular nowrap">{r.code}</td>
					<td class="ttl">{r.title ?? '—'}</td>
					<td class="pdfcol">
						{#if r.pdf}
							<a href={r.pdf} target="_blank" rel="noopener">PDF</a>
						{:else}
							—
						{/if}
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
</section>

<style>
	.trail h2 {
		font-family: var(--font-display);
		font-weight: 900;
		text-transform: uppercase;
		font-size: var(--fs-18);
	}
	table {
		width: 100%;
		border-collapse: collapse;
		font-size: var(--fs-13);
	}
	th {
		text-align: left;
		font-weight: 400;
		color: var(--ink-soft);
		padding: 6px 10px 6px 0;
		border-bottom: 1px solid var(--line-strong, var(--line));
	}
	td {
		padding: 8px 10px 8px 0;
		border-bottom: 1px solid var(--line);
		vertical-align: top;
	}
	.self td {
		font-weight: 700;
	}
	.nowrap {
		white-space: nowrap;
	}
	.ttl {
		max-width: 46ch;
	}
	.pdfcol {
		text-align: right;
		padding-right: 0;
	}
	.chip {
		margin-left: 6px;
	}
</style>
