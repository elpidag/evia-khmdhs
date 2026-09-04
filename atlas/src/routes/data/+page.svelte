<script lang="ts">
	/**
	 * EXPLORE THE DATA — the hub (Artboard 3, user 2026-08-27): the title
	 * where the landing menu has it, one line of caption in Obviously Narrow
	 * Bold, the three streams as 186 px symbols 50 px apart and the two
	 * tools as 98 px symbols under them, the group centred on x 905 of the
	 * 1920 frame; labels in Obviously Condensed Bold 24 px. The symbols are
	 * placeholders until the user's images arrive; the labels are theirs to
	 * rename in lib/datasets.ts.
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
						<DatasetSymbol key={s.key} size="clamp(150px, 13.1vw, 251px)" named />
						<span class="label" style:color={s.color}>{s.label}</span>
					</a>
				</li>
			{/each}
		</ul>

		<ul class="rank tools">
			{#each tools as s (s.key)}
				<li>
					<a href={s.href}>
						<DatasetSymbol key={s.key} size="clamp(80px, 6.9vw, 132px)" named />
						<span class="label" style:color={s.color}>{s.label}</span>
					</a>
				</li>
			{/each}
		</ul>
	</div>
</div>

<style>
	/* one viewport under the header: the artboard has the title's cap line
	   218 px down and 110 px in; the symbol group is centred on x 905, i.e.
	   a content box from 110 to 1700 */
	.hub {
		display: flex;
		flex-direction: column;
		min-height: calc(100dvh - var(--header-h, 85px));
		margin: calc(-1 * var(--card-pad-t, 0px)) calc(-1 * var(--card-pad-r, 0px))
			calc(-1 * var(--card-pad-b, 0px)) calc(-1 * var(--card-pad-l, 0px));
		/* the title 80 px higher than the artboard's cap line, and smaller
		   (the author, 2026-09-04) */
		padding: max(24px, calc(12.5vh - 80px)) 11.46vw 4vh 5.73vw;
		box-sizing: border-box;
	}
	.centre {
		display: flex;
		flex-direction: column;
		align-items: center;
		/* the caption's cap line 100 px under the subtitle */
		padding-top: 9.3vh;
	}
	.title {
		margin: 0;
		line-height: 1;
	}
	.l1,
	.l2 {
		display: block;
		white-space: nowrap;
	}
	.l1 {
		font-family: var(--font-display-narrow);
		font-weight: 900;
		font-size: clamp(27px, 2.8vw, 54px);
		letter-spacing: 0.05em;
	}
	.l2 {
		font-family: var(--font-display-narrow);
		font-weight: 500;
		font-size: clamp(18px, 1.875vw, 36px);
		letter-spacing: 0.26em;
	}
	.centre .caption :global(.prose),
	.centre .caption :global(.prose p) {
		font-family: var(--font-display-narrow);
		font-weight: 700;
		font-size: clamp(14px, 1.25vw, 24px);
		line-height: 1.2;
		text-align: center;
		color: var(--ink);
	}
	.rank {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		justify-content: center;
		align-items: flex-start;
	}
	.rank.streams {
		margin-top: 2.9vh;
		gap: 2.6vw;
	}
	.rank.tools {
		margin-top: 8.3vh;
		gap: 2.1vw;
	}
	.rank a {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 14px;
		text-decoration: none;
		color: var(--ink);
	}
	.rank.streams a {
		max-width: clamp(150px, 13.1vw, 251px);
	}
	.rank.tools a {
		max-width: clamp(80px, 6.9vw, 132px);
		gap: 10px;
	}
	/* the name in the stream's own colour, shown on HOVER only (the author,
	   2026-09-04) — kept in the layout, so nothing moves when it appears */
	.label {
		font-family: var(--font-display-cond);
		font-weight: 700;
		font-size: clamp(14px, 1.25vw, 24px);
		text-align: center;
		line-height: 1.2;
		opacity: 0;
		transition: opacity 0.25s ease;
	}
	.rank a:hover .label,
	.rank a:focus-visible .label {
		opacity: 1;
	}
	/* a short window: the artboard's vertical gaps tighten so the hub still
	   composes one viewport (it ran 19 px over at 1280×720) */
	@media (max-height: 840px) {
		.hub {
			padding-top: 8vh;
			padding-bottom: 2vh;
		}
		.centre {
			padding-top: 5vh;
		}
		.rank.tools {
			margin-top: 5vh;
		}
	}
	@media (max-width: 900px) {
		.hub {
			padding: var(--sp-6) var(--sp-4);
		}
		.rank {
			flex-wrap: wrap;
			gap: var(--sp-6) !important;
		}
	}
</style>
