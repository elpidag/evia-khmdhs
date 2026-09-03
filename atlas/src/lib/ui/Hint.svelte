<script lang="ts">
	/**
	 * A small hover card for the explanation behind a value (user,
	 * 2026-08-19): the detail cards state the fact and nothing else, and
	 * what needs saying about it — which document said it, why a figure was
	 * assumed, why a municipality sits outside the region — appears on
	 * hover in the same black rectangle the maps and charts use.
	 *
	 * Keyboard-reachable (the marker is a button), and the card is plain
	 * text, never load-bearing: everything it says is also in the evidence
	 * block below the facts.
	 */
	interface Props {
		text: string;
		/** which way the card opens — to the RIGHT of the marker by default
		 *  (user, 2026-08-20). It overlaps the map slot beside the facts,
		 *  which is what a tooltip is for; nothing clips it. */
		align?: 'left' | 'right';
		/** the marker LEADS the text it belongs to (before a heading), so its
		 *  margin sits on the right instead of the left */
		lead?: boolean;
		/** override the shared 200 px — a legend needs its own measure */
		width?: string;
		/** open UPWARDS from the marker instead of downwards */
		up?: boolean;
		/** the marker belongs to a heading: it takes the heading's own face,
		 *  size and weight instead of the small inline one (user, 2026-08-20) */
		heading?: boolean;
	}
	let {
		text,
		align = 'right',
		lead = false,
		width,
		up = false,
		heading = false
	}: Props = $props();
	let open = $state(false);
</script>

<span class="hint" class:lead class:heading>
	<button
		type="button"
		class:on={open}
		aria-label={text}
		onmouseenter={() => (open = true)}
		onmouseleave={() => (open = false)}
		onfocus={() => (open = true)}
		onblur={() => (open = false)}>i</button
	>
	{#if open}
		<span class="card" class:left={align === 'left'} class:up style:width>{text}</span>
	{/if}
</span>

<style>
	.hint {
		position: relative;
		display: inline-block;
		vertical-align: baseline;
	}
	.hint.lead button {
		margin-left: 0;
		margin-right: 6px;
	}
	button {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		font-family: var(--font-ui);
		font-size: 9px;
		font-weight: 700;
		line-height: 1;
		width: 13px;
		height: 13px;
		padding: 0;
		margin-left: 4px;
		border: 1px solid var(--line-strong);
		border-radius: 999px;
		background: var(--paper);
		color: var(--ink-soft);
		cursor: help;
	}
	/* in a heading the marker IS heading lettering: same face, size, weight
	   and letter-spacing, in a circle scaled to it */
	.hint.heading button {
		font: inherit;
		font-size: inherit;
		letter-spacing: 0;
		line-height: 1;
		width: 1.15em;
		height: 1.15em;
		/* the glyph is drawn a touch high inside the display face's box */
		padding-bottom: 0.08em;
		color: var(--ink);
		border-color: var(--ink);
	}
	/* while its card is open the marker IS the card: black fill, white
	   letter — the ink token is a warm dark brown and read as grey beside
	   the card's black (user, 2026-08-20) */
	.hint button.on,
	.hint button:hover,
	.hint button:focus-visible {
		background: var(--ink);
		border-color: var(--ink);
		color: var(--paper);
	}
	/* every card is the same 200 px wide and grows downwards for a longer
	   text (user, 2026-08-20) — cards that sized to their sentence read as a
	   different component each time. Text at 14 px, like the values. */
	.card {
		position: absolute;
		z-index: 5;
		/* cards grow DOWNWARDS from the marker: centring them vertically made
		   a long one straddle the marker and cover the rows above */
		top: -4px;
		left: calc(100% + 6px);
		width: 200px;
		max-width: 80vw;
		background: var(--ink);
		color: var(--paper);
		border-radius: 4px;
		padding: var(--sp-2) var(--sp-3);
		/* the card carries its OWN typography: inside a CAPS display heading
		   it inherited caps, 900 weight and letter-spacing, and printed the
		   whole explanation in block capitals (user, 2026-08-20) */
		font-family: var(--font-ui);
		font-weight: 400;
		font-size: var(--fs-14);
		line-height: 1.45;
		text-transform: none;
		letter-spacing: normal;
		text-align: left;
		/* a card may be written as lines — the timeline's legend is one line
		   per symbol (user, 2026-08-20) */
		white-space: pre-line;
		pointer-events: none;
	}
	.card.left {
		left: auto;
		right: calc(100% + 6px);
	}
	/* bottom-anchored on the marker: the card stands above it, to the side */
	.card.up {
		top: auto;
		bottom: -4px;
	}
</style>
