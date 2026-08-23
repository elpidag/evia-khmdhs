<script lang="ts">
	import type { Snippet } from 'svelte';
	import Hint from '$lib/ui/Hint.svelte';

	interface Props {
		/** the FINDING, written as a sentence — not the topic.
		 *  Empty string = the caller renders its own heading above the frame. */
		title?: string;
		/** the topic/units line under the title */
		subtitle?: string;
		/** per-chart caveat, always rendered when provided */
		caveat?: string;
		/** anchor id for permalinks; also links the caveat to /methodology#<anchor> */
		anchor?: string;
		/** methodology anchor override (defaults to `anchor`) */
		methodology?: string;
		children: Snippet;
		/** optional extra footer content (sources, downloads) */
		footer?: Snippet;
		/** optional title colour (defaults to the heading ink) */
		titleColor?: string;
		/** optional ⓘ beside the title — the explanation a reader needs
		 *  before the chart, on hover, as the TIMELINE does (user, 2026-08-20) */
		hint?: string;
		/** optional INSIGHT: a lightbulb LEFT of the title; clicking it opens
		 *  the text in a column on the left of the frame's body instead of
		 *  hiding it in a ⓘ (user, 2026-08-21, ALLOCATION OF FUNDING) */
		insight?: string;
		/** optional controls on the TITLE LINE, right-aligned — a view toggle
		 *  (user, 2026-08-21, RANKING OF COMPANIES) */
		controls?: Snippet;
	}
	let {
		title = '',
		subtitle = '',
		caveat = '',
		anchor = '',
		methodology = '',
		children,
		footer,
		titleColor = '',
		hint = '',
		insight = '',
		controls
	}: Props = $props();
	const methodHref = $derived(`/methodology#${methodology || anchor}`);
	let insightOpen = $state(false);
</script>

<figure class="frame" id={anchor || undefined}>
	<figcaption>
		{#if title}
			<div class="titlerow" class:withcontrols={!!controls}>
			<h2 class="finding" style:color={titleColor || null}>
				{#if insight}
					<button
						class="bulb"
						class:on={insightOpen}
						onclick={() => (insightOpen = !insightOpen)}
						aria-pressed={insightOpen}
						aria-label={insightOpen ? 'Hide the note' : 'How to read this'}
						title={insightOpen ? 'Hide the note' : 'How to read this'}
					>
						<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
							<path
								d="M9 18h6M10 21h4M12 3a6.5 6.5 0 0 0-3.6 11.9c.6.4 1 1.1 1 1.8V17h5.2v-.3c0-.7.4-1.4 1-1.8A6.5 6.5 0 0 0 12 3z"
								fill={insightOpen ? 'currentColor' : 'none'}
								stroke="currentColor"
								stroke-width="1.6"
								stroke-linecap="round"
								stroke-linejoin="round"
							/>
						</svg>
					</button>
				{/if}
				{title}{#if hint}<Hint text={hint} heading width="380px" />{/if}
				{#if anchor}<a class="hash" href={`#${anchor}`} aria-label="Link to this chart">#</a>{/if}
			</h2>
			{#if controls}<div class="controls">{@render controls()}</div>{/if}
			</div>
		{/if}
		{#if subtitle}<p class="topic">{subtitle}</p>{/if}
	</figcaption>

	<div class="body" class:withnote={insight && insightOpen}>
		{#if insight && insightOpen}
			<aside class="insight">{insight}</aside>
		{/if}
		<div class="content">{@render children()}</div>
	</div>

	{#if caveat || footer}
		<div class="foot">
			{#if caveat}
				<p class="caveat">
					{caveat}
					{#if anchor || methodology}<a href={methodHref}>Methodology</a>{/if}
				</p>
			{/if}
			{#if footer}{@render footer()}{/if}
		</div>
	{/if}
</figure>

<style>
	.frame {
		margin: 0 0 var(--sp-12);
	}
	.finding {
		font-size: var(--fs-24);
		margin-bottom: 0;
	}
	/* ONE uniform gap between the head (title, or subtitle when there is
	   one) and whatever follows — chart, toolbar or legend (user,
	   2026-08-22: the old per-element margins left sometimes too much
	   room, sometimes too little) */
	figcaption {
		margin-bottom: var(--sp-4);
	}
	figcaption:not(:has(h2)):not(:has(p)) {
		margin-bottom: 0;
	}
	/* a control on the title line sits at its right end */
	.titlerow.withcontrols {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--sp-4);
	}
	.controls {
		flex: none;
	}
	.hash {
		text-decoration: none;
		color: var(--ink-faint);
		font-family: var(--font-ui);
		font-size: var(--fs-16);
		margin-left: var(--sp-1);
		opacity: 0;
		transition: opacity 0.15s;
	}
	.frame:hover .hash {
		opacity: 1;
	}
	.topic {
		color: var(--ink-soft);
		font-size: var(--fs-14);
		margin-top: var(--sp-1);
		margin-bottom: 0;
	}
	.body {
		margin-bottom: var(--sp-2);
	}
	/* the insight note hangs in the page's LEFT MARGIN, outside the content
	   column, so the charts keep their full width (user, 2026-08-21); where
	   the margin is too narrow to hold it, it flows above the chart instead */
	.body.withnote {
		position: relative;
	}
	.insight {
		position: absolute;
		top: 0;
		right: calc(100% + var(--sp-6));
		/* as wide as the page's left margin allows (the content column is
		   --content-w, centred), between 9 and 15 rem — a 2560-px laptop at
		   150 % scaling is a ~1700-px viewport and must still get the margin */
		width: clamp(9rem, calc((100vw - var(--content-w)) / 2 - var(--sp-6) - 1.5rem), 15rem);
		font-size: var(--fs-14);
		line-height: 1.55;
		color: var(--ink-soft);
		border-left: 2px solid var(--ink);
		padding-left: var(--sp-3);
	}
	/* below ~1500 px the margin cannot hold 9 rem: the note flows above */
	@media (max-width: 1500px) {
		.insight {
			position: static;
			width: auto;
			max-width: 40rem;
			margin-bottom: var(--sp-4);
		}
	}
	/* a frame that shares its row with another (the half-width pairs, the
	   scope/type pairs, the full-bleed bands) has no page margin of its own
	   on the left — its neighbour is there — so its note ALWAYS flows above
	   the chart, at any width (user, 2026-08-23: the AWARD PROCEDURES note
	   fell on DIRECT AWARDS). Kept here, in the frame, so no page can forget. */
	:global(.pair) .insight,
	:global(.scopetype) .insight,
	:global(.firesband) .insight {
		position: static;
		width: auto;
		max-width: 40rem;
		margin-bottom: var(--sp-4);
	}
	.content {
		min-width: 0;
	}
	.bulb {
		display: inline-flex;
		align-items: center;
		vertical-align: -3px;
		margin-right: var(--sp-2);
		padding: 0;
		border: 0;
		background: none;
		color: var(--ink);
		cursor: pointer;
		line-height: 0;
	}
	.bulb:hover,
	.bulb.on {
		color: var(--c-antinero, var(--ink));
	}
	.foot {
		border-top: 1px solid var(--line);
		padding-top: var(--sp-2);
	}
	.caveat {
		color: var(--ink-faint);
		font-size: var(--fs-12);
		margin: 0;
	}
	.caveat a {
		color: var(--ink-faint);
	}
</style>
