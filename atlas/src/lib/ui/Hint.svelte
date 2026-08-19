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
		/** where the card opens: right of the marker by default */
		align?: 'left' | 'right';
	}
	let { text, align = 'right' }: Props = $props();
	let open = $state(false);
</script>

<span class="hint">
	<button
		type="button"
		aria-label={text}
		onmouseenter={() => (open = true)}
		onmouseleave={() => (open = false)}
		onfocus={() => (open = true)}
		onblur={() => (open = false)}>i</button
	>
	{#if open}
		<span class="card" class:left={align === 'left'}>{text}</span>
	{/if}
</span>

<style>
	.hint {
		position: relative;
		display: inline-block;
		vertical-align: baseline;
	}
	button {
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
	button:hover,
	button:focus-visible {
		background: var(--ink);
		border-color: var(--ink);
		color: #fff;
	}
	.card {
		position: absolute;
		z-index: 5;
		top: calc(100% + 6px);
		left: 0;
		width: max-content;
		max-width: 30rem;
		background: #000;
		color: #fff;
		border-radius: 4px;
		padding: var(--sp-2) var(--sp-3);
		font-size: var(--fs-12);
		line-height: 1.45;
		pointer-events: none;
	}
	.card.left {
		left: auto;
		right: 0;
	}
</style>
