<script lang="ts">
	import type { Snippet } from 'svelte';

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
	}
	let { title = '', subtitle = '', caveat = '', anchor = '', methodology = '', children, footer, titleColor = '' }: Props = $props();
	const methodHref = $derived(`/methodology#${methodology || anchor}`);
</script>

<figure class="frame" id={anchor || undefined}>
	<figcaption>
		{#if title}
			<h2 class="finding" style:color={titleColor || null}>
				{title}
				{#if anchor}<a class="hash" href={`#${anchor}`} aria-label="Link to this chart">#</a>{/if}
			</h2>
		{/if}
		{#if subtitle}<p class="topic">{subtitle}</p>{/if}
	</figcaption>

	<div class="body">{@render children()}</div>

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
		margin-bottom: var(--sp-1);
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
		margin-bottom: var(--sp-4);
	}
	.body {
		margin-bottom: var(--sp-2);
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
