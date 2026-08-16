<script lang="ts" module>
	export interface Quote {
		/** which fact this excerpt backs (English label) */
		label: string;
		/** the verbatim excerpt */
		text: string;
		/** source document code (ΑΔΑ/ΑΔΑΜ) and its PDF href */
		code?: string | null;
		href?: string | null;
		note?: string | null;
	}
</script>

<script lang="ts">
	/**
	 * EXTRACTED QUOTES FROM DOCUMENTS (user template, 2026-08-17): the
	 * verbatim evidence excerpts that back the curated facts, each with
	 * its field label and source document link. Greek quotes stay Greek —
	 * they are quotations, never translated.
	 */
	interface Props {
		quotes: Quote[];
		heading?: string;
	}
	let { quotes, heading = 'EXTRACTED QUOTES FROM DOCUMENTS' }: Props = $props();
</script>

{#if quotes.length}
	<section class="quotes">
		<h2>{heading}</h2>
		{#each quotes as q (q.label + (q.code ?? '') + q.text.slice(0, 24))}
			<div class="q">
				<div class="qlabel">
					{q.label}
					{#if q.code}
						·
						{#if q.href}
							<a class="tabular" href={q.href} target="_blank" rel="noopener">{q.code}</a>
						{:else}
							<span class="tabular">{q.code}</span>
						{/if}
					{/if}
				</div>
				<blockquote>«{q.text}»</blockquote>
				{#if q.note}<p class="qnote">{q.note}</p>{/if}
			</div>
		{/each}
	</section>
{/if}

<style>
	/* same breather the document trail gets after the facts header */
	.quotes {
		margin-top: var(--sp-8);
	}
	.quotes h2 {
		font-family: var(--font-display);
		font-weight: 900;
		text-transform: uppercase;
		font-size: var(--fs-18);
	}
	.q {
		margin-bottom: var(--sp-4);
	}
	.qlabel {
		font-size: var(--fs-12);
		font-weight: 700;
		color: var(--ink-soft);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}
	blockquote {
		margin: 4px 0 0;
		padding-left: var(--sp-3);
		border-left: 3px solid var(--line-strong, var(--line));
		font-size: var(--fs-13);
		color: var(--ink);
		max-width: 80ch;
	}
	.qnote {
		margin: 2px 0 0;
		font-size: var(--fs-12);
		color: var(--ink-faint);
	}
</style>
