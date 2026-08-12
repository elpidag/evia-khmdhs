<script lang="ts">
	/** The sponsor-project hover card (the TIMELINE row card), shared by
	 *  the map dots and the METRICS waffle. Fixed-positioned; `anchor`
	 *  hangs it left of the point (timeline style) or right of it. */
	import type { CardData } from './projectCard';

	interface Props {
		x: number;
		y: number;
		anchor?: 'left' | 'right';
		card: CardData;
	}
	let { x, y, anchor = 'left', card }: Props = $props();
</script>

<div
	class="pcard"
	class:right={anchor === 'right'}
	style:left={`${x}px`}
	style:top={`${y}px`}
	style:background={card.color}
	style:color={card.ink}
>
	<div class="pc-name">{card.name}</div>
	{#each card.lines as ln, i (i)}
		<div>{ln}</div>
	{/each}
</div>

<style>
	.pcard {
		/* fixed width, content-driven height; right-edge midpoint anchored
		   on the point's left-edge midpoint (anchor="left"), or hanging
		   just right of it (anchor="right") */
		position: fixed;
		transform: translate(-100%, -50%);
		width: 270px;
		font-size: 12px;
		line-height: 1.5;
		padding: 8px 12px;
		border-radius: 5px;
		pointer-events: none;
		z-index: 120;
		box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
	}
	.pcard.right {
		transform: translate(14px, -50%);
	}
	.pc-name {
		font-weight: 700;
		margin-bottom: 2px;
	}
</style>
