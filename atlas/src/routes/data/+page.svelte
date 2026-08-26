<script lang="ts">
	/**
	 * EXPLORE THE DATA — the hub (user mock, 2026-08-27): the title, one
	 * line of caption, the three streams as large symbols and the two tools
	 * beneath them, smaller. The symbols are placeholders until the user's
	 * images arrive; the labels are theirs to rename in lib/datasets.ts.
	 */
	import { SYMBOLS } from '$lib/datasets';
	import DatasetSymbol from '$lib/ui/DatasetSymbol.svelte';
	import Prose from '$lib/ui/Prose.svelte';
	import { BRAND, BRAND_LINE1, BRAND_LINE2 } from '$lib/landing/brand';
	import Intro from '$content/data/intro.md';

	const streams = SYMBOLS.filter((s) => s.rank === 'stream');
	const tools = SYMBOLS.filter((s) => s.rank === 'tool');
</script>

<svelte:head>
	<title>Explore the data — {BRAND}</title>
</svelte:head>

<div class="hub">
	<h1 class="title">
		<span class="l1">{BRAND_LINE1}</span>
		<span class="l2">{BRAND_LINE2}</span>
	</h1>

	<div class="centre">
	<div class="caption">
		<Prose hint="atlas/src/content/data/intro.md"><Intro /></Prose>
	</div>

	<ul class="rank streams">
		{#each streams as s (s.key)}
			<li>
				<a href={s.href}>
					<DatasetSymbol key={s.key} size={190} named />
					<span class="label">{s.label}</span>
				</a>
			</li>
		{/each}
	</ul>

	<ul class="rank tools">
		{#each tools as s (s.key)}
			<li>
				<a href={s.href}>
					<DatasetSymbol key={s.key} size={100} named />
					<span class="label">{s.label}</span>
				</a>
			</li>
		{/each}
	</ul>
	</div>
</div>

<style>
	/* one viewport (the mock): the title top-left, the symbols centred in
	   the room below it */
	.hub {
		display: flex;
		flex-direction: column;
		min-height: calc(100dvh - 60px - var(--sp-6) - var(--sp-12));
		padding-top: var(--sp-8);
	}
	.centre {
		flex: 1;
		display: flex;
		flex-direction: column;
		justify-content: center;
		padding-bottom: 8vh;
	}
	.title {
		margin: 0 0 var(--sp-8);
		line-height: 1;
	}
	.l1,
	.l2 {
		display: block;
		white-space: nowrap;
	}
	.l1 {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: clamp(2rem, 4.2vw, 4.25rem);
		letter-spacing: 0.005em;
	}
	.l2 {
		font-family: var(--font-ui);
		font-weight: 400;
		font-size: clamp(1.2rem, 2.6vw, 2.6rem);
		letter-spacing: 0.32em;
		margin-top: 0.1em;
	}
	.caption {
		display: flex;
		justify-content: center;
		margin-bottom: var(--sp-6);
	}
	.caption :global(.prose) {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: var(--fs-16);
		text-align: center;
	}
	.rank {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		justify-content: center;
		gap: var(--sp-12);
	}
	.rank.tools {
		margin-top: var(--sp-12);
		gap: var(--sp-8);
	}
	.rank a {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--sp-3);
		text-decoration: none;
		color: var(--ink);
		max-width: 190px;
	}
	.label {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: var(--fs-13);
		text-align: center;
		line-height: 1.25;
	}
	@media (max-width: 900px) {
		.rank {
			flex-wrap: wrap;
			gap: var(--sp-6);
		}
	}
</style>
