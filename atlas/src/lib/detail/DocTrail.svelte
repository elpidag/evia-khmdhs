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
		/** small chip after the type, e.g. cancelled */
		chip?: string;
		/** false = neutral chip (a fact about the row, not a warning);
		 *  callers derive it with `trailChip` in $lib/transforms/exclusion */
		chipBad?: boolean;
		/** a second link after the pdf one (a payment order's Διαύγεια act) */
		alt?: { href: string; label: string } | null;
	}
</script>

<script lang="ts">
	/**
	 * DOCUMENT TRAIL (user template, 2026-08-17; renamed and unbundled from
	 * the timeline 2026-08-19, which now stands above it as its own section):
	 * the SAME table
	 * on every detail page — date · type of document · document code ·
	 * title · pdf. Callers pass rows with English type labels already
	 * resolved; the row for the viewed document itself is highlighted.
	 */
	import type { Snippet } from 'svelte';

	interface Props {
		rows: TrailRow[];
		/** null prints no heading — the caller wraps the trail in a fold */
		heading?: string | null;
		/** optional strip between the heading and the table (timeline bar) */
		top?: Snippet;
		/** document code whose row is highlighted (timeline-dot hover) */
		highlight?: string | null;
		/** the page's own document row wears the project's timeline-bar
		 *  colour permanently; selfInk sets its lettering colour */
		selfColor?: string | null;
		selfInk?: string;
		/** row hover in/out (document code) — pages mirror it elsewhere */
		onRowHover?: (code: string | null) => void;
	}
	let {
		rows,
		heading = 'DOCUMENT TRAIL',
		top,
		highlight = null,
		selfColor = null,
		selfInk = 'var(--ink)',
		onRowHover
	}: Props = $props();
	const dmy = (iso: string | null) =>
		iso && iso.length >= 10 ? `${iso.slice(8, 10)}.${iso.slice(5, 7)}.${iso.slice(0, 4)}` : '—';
</script>

<section class="trail">
	{#if heading}<h2>{heading}</h2>{/if}
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
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<tr
					class:self={r.self}
					class:hl={highlight !== null && r.code === highlight}
					style:background={r.self && selfColor ? selfColor : undefined}
					style:color={r.self && selfColor ? selfInk : undefined}
					onmouseenter={() => onRowHover?.(r.code)}
					onmouseleave={() => onRowHover?.(null)}
				>
					<td class="tabular nowrap">{dmy(r.d)}</td>
					<td
						>{r.type}{#if r.chip}<span class="chip" class:bad={r.chipBad !== false}
								>{r.chip}</span
							>{/if}</td
					>
					<td class="tabular nowrap">{r.code}</td>
					<td class="ttl">{r.title ?? '—'}</td>
					<td class="pdfcol">
						{#if r.pdf}
							<a href={r.pdf} target="_blank" rel="noopener">PDF</a>
						{:else}
							—
						{/if}
						{#if r.alt}
							· <a href={r.alt.href} target="_blank" rel="noopener">{r.alt.label}</a>
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
	/* the self row wears the bar colour (tr-level style) — its lettering
	   and links inherit the ink chosen for that colour */
	.self td,
	.self td a {
		color: inherit;
	}
	/* timeline-dot hover: the linked act's row goes black, lettering white */
	.hl td,
	.hl td a {
		background: var(--ink);
		color: var(--paper);
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
