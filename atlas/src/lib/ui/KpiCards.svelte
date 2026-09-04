<script lang="ts">
	/**
	 * The KPI card recipe the four heroes used to hand-roll (a copy-paste
	 * lineage from the sponsored-works page), extracted once: a hue block,
	 * the number in the display black, the label under it. `direction`
	 * stacks them (the old 268 px column) or lays them in a row (the
	 * dataset cards, user mock 2026-08-27).
	 */
	export interface KpiCard {
		num: string;
		label: string;
		/** a second, smaller line under the label */
		sub?: string;
		/** a per-card hue; the group's `color` otherwise */
		color?: string;
		/** a note shown on HOVER (and keyboard focus) as the site's black
		 *  card under the KPI — the record-kinds note on the contracts card,
		 *  the author, 2026-09-04 */
		hover?: string;
	}
	let {
		cards,
		color = 'var(--ink)',
		direction = 'row'
	}: { cards: KpiCard[]; color?: string; direction?: 'row' | 'column' } = $props();
</script>

<div class="cards" class:column={direction === 'column'}>
	{#each cards as c, i (i)}
		<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
		<div class="card" class:hashover={!!c.hover} style:--card-c={c.color ?? color} tabindex={c.hover ? 0 : undefined}>
			<div class="num">{c.num}</div>
			<div class="lbl">
				{c.label}
				{#if c.sub}<br /><span class="sub">{c.sub}</span>{/if}
			</div>
			{#if c.hover}
				<div class="hov" role="note">{c.hover}</div>
			{/if}
		</div>
	{/each}
</div>

<style>
	.cards {
		display: grid;
		grid-auto-flow: column;
		grid-auto-columns: 1fr;
		gap: var(--sp-4);
	}
	.cards.column {
		grid-auto-flow: row;
		grid-template-rows: repeat(3, 1fr);
		width: 268px;
	}
	.card {
		background: var(--card-c, var(--ink));
		color: var(--paper);
		padding: var(--sp-4);
		border-radius: 10px;
		display: flex;
		flex-direction: column;
		gap: var(--sp-4);
		min-height: 7.5rem;
	}
	.num {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: clamp(28px, 3.2vw, 36px);
		line-height: 0.95;
	}
	.lbl {
		font-family: var(--font-display);
		font-weight: 400;
		font-size: var(--fs-13);
		line-height: 1.2;
		margin-top: auto;
	}
	.sub {
		opacity: 0.85;
	}
	/* the hover note: the site's black card, under the KPI, on hover or focus */
	.card.hashover {
		position: relative;
		cursor: help;
	}
	.card .hov {
		position: absolute;
		left: 0;
		top: calc(100% + 6px);
		z-index: 5;
		width: max(100%, 300px);
		max-width: 420px;
		padding: var(--sp-3) var(--sp-4);
		background: var(--ink);
		color: var(--paper);
		font-family: var(--font-ui);
		font-size: var(--fs-12);
		line-height: 1.4;
		border-radius: 6px;
		opacity: 0;
		pointer-events: none;
		transition: opacity 0.15s ease;
	}
	.card.hashover:hover .hov,
	.card.hashover:focus-visible .hov {
		opacity: 1;
	}
	@media (max-width: 900px) {
		.cards {
			grid-auto-flow: row;
		}
		.cards.column {
			width: auto;
		}
	}
</style>
