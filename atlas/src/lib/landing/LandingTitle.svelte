<script lang="ts">
	/**
	 * The site's name over the field — Artboard 1 (user, 2026-08-27):
	 * Obviously Narrow Black 60 px tracked .2em over Obviously Narrow
	 * Medium 48 px tracked .32em, the second baseline 61.6 px under the
	 * first, the pair centred a little above the middle of the frame.
	 * Fades in when `on` turns true; a button while the field is up.
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
		padding: 0 0 3vh;
		background: none;
		border: none;
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
		font-family: var(--font-display-narrow);
		font-weight: 900;
		/* 60 px on the 1920 artboard */
		font-size: clamp(28px, 3.125vw, 60px);
		letter-spacing: 0.2em;
	}
	.l2 {
		font-family: var(--font-display-narrow);
		font-weight: 500;
		/* 48 px, its baseline 61.6 px under the first */
		font-size: clamp(22px, 2.5vw, 48px);
		letter-spacing: 0.32em;
		margin-top: 0.28em;
	}
</style>
