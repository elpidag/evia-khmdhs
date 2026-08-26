<script lang="ts">
	/**
	 * The site's name over the field (user mock, 2026-08-27): the heavy
	 * display line over the wide-tracked one. Fades in when `on` turns
	 * true; a button while the field is up — clicking it opens the menu.
	 */
	import { BRAND_LINE1, BRAND_LINE2 } from './brand';
	let { on = false, onOpen }: { on?: boolean; onOpen?: () => void } = $props();
</script>

<button class="title" class:on type="button" onclick={onOpen} tabindex={on ? 0 : -1}>
	<span class="l1">{BRAND_LINE1}</span>
	<span class="l2">{BRAND_LINE2}</span>
</button>

<style>
	.title {
		position: fixed;
		inset: 0;
		z-index: 3;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		background: none;
		border: none;
		padding: 0;
		cursor: pointer;
		color: var(--ink);
		opacity: 0;
		/* slow in over the field, quick out when the menu takes over */
		transition: opacity 0.35s ease;
		pointer-events: none;
	}
	.title.on {
		opacity: 1;
		pointer-events: auto;
		transition: opacity 1.1s ease;
	}
	.l1,
	.l2 {
		display: block;
		white-space: nowrap;
		line-height: 1;
		/* a paper halo keeps the letters legible over the columns */
		text-shadow:
			0 0 12px var(--paper),
			0 0 24px var(--paper);
	}
	.l1 {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: clamp(2.4rem, 6vw, 6rem);
		letter-spacing: 0.005em;
	}
	.l2 {
		font-family: var(--font-ui);
		font-weight: 400;
		font-size: clamp(1.3rem, 3.6vw, 3.6rem);
		letter-spacing: 0.32em;
		margin-top: 0.12em;
	}
</style>
