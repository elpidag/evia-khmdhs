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
	import { onMount } from 'svelte';
	import { SYMBOLS } from '$lib/datasets';
	import { apiGetCached, type Landing } from '$lib/api';
	import CodeField from '$lib/landing/CodeField.svelte';
	import { fitBrand } from '$lib/landing/fitBrand';
	import DatasetSymbol from '$lib/ui/DatasetSymbol.svelte';
	import Prose from '$lib/ui/Prose.svelte';
	import { BRAND, BRAND_LINE1, BRAND_LINE2 } from '$lib/landing/brand';
	import Intro from '$content/data/intro.md';

	const streams = SYMBOLS.filter((s) => s.rank === 'stream');
	const tools = SYMBOLS.filter((s) => s.rank === 'tool');
	/** the drawings differ in shape (a wide digger, a tall hand), so each is
	 *  sized to the SAME AREA — the longer side grows with the square root
	 *  of the shape's elongation — and the row stands them on one baseline
	 *  (the author, 2026-09-04: «organise the symbols better») */
	const sizeFor = (s: (typeof SYMBOLS)[number], base: string) =>
		s.aspect ? `calc(${base} * ${(Math.sqrt(Math.max(s.aspect, 1 / s.aspect)) * 0.72).toFixed(3)})` : base;

	/** the landing's field of codes, under the title in the column the
	 *  title's own width makes (the author, 2026-09-25) — fetched after
	 *  hydration like the landing does, never in the load */
	let codes = $state.raw<Landing | null>(null);
	onMount(() => {
		apiGetCached<Landing>(fetch, '/api/landing').then((v) => (codes = v));
	});
</script>

<svelte:head>
	<title>Explore the data — {BRAND}</title>
</svelte:head>

<div class="hub">
	<div class="left">
		<h1 class="title" use:fitBrand>
			<span class="l1">{BRAND_LINE1}</span>
			<span class="l2">{BRAND_LINE2}</span>
		</h1>
		<div class="field" aria-hidden="true">
			<CodeField {codes} seed={20260925} hole={0.25} />
		</div>
	</div>

	<div class="centre">
		<div class="caption">
			<Prose hint="atlas/src/content/data/intro.md"><Intro /></Prose>
		</div>

		<ul class="rank streams">
			{#each streams as s (s.key)}
				<li>
					<a href={s.href}>
						<DatasetSymbol key={s.key} size={sizeFor(s, 'clamp(150px, 13.1vw, 251px)')} named />
						<span class="label" style:color={s.color}>{s.label}</span>
					</a>
				</li>
			{/each}
		</ul>

		<ul class="rank tools">
			{#each tools as s (s.key)}
				<li>
					<a href={s.href}>
						<DatasetSymbol key={s.key} size={sizeFor(s, 'clamp(105px, 9.1vw, 174px)')} named />
						<span class="label" style:color={s.color}>{s.label}</span>
					</a>
				</li>
			{/each}
		</ul>
	</div>
</div>

<style>
	/* one viewport under the header: the artboard has the title's cap line
	   218 px down and 110 px in. The artboard's content box ran from 110 to
	   1700 (the symbol group centred on x 905); since 2026-09-25 the right
	   padding equals the left, so the group sits on the WINDOW's centre
	   (the author: «the icons are not centred») */
	.hub {
		display: grid;
		/* the title's own width makes the left column; the field of codes
		   fills it under the title (the author, 2026-09-25) */
		grid-template-columns: max-content minmax(0, 1fr);
		column-gap: 3vw;
		min-height: calc(100dvh - var(--header-h, 85px));
		margin: calc(-1 * var(--card-pad-t, 0px)) calc(-1 * var(--card-pad-r, 0px))
			calc(-1 * var(--card-pad-b, 0px)) calc(-1 * var(--card-pad-l, 0px));
		/* the title 80 px higher than the artboard's cap line, and smaller
		   (the author, 2026-09-04) */
		/* the author's edited export of 2026-09-25 (1920 × 1080): the title
		   a third larger with its cap line at 45, the caption's first line at
		   305, the drawings' baseline at 568 and the tools' at 791, the group
		   centred near x 1250 — so the right padding returns to the
		   artboard's 10.9 vw */
		--hub-pt: max(20px, calc(12.5vh - 100px));
		--hub-pb: 4vh;
		padding: var(--hub-pt) 10.9vw var(--hub-pb) 5.73vw;
		box-sizing: border-box;
	}
	.left {
		position: relative;
		min-height: 0;
	}
	/* the field runs from the page's top edge to its bottom edge, as on the
	   landing (the author, 2026-09-25): it escapes the hub's vertical
	   paddings, and the title sits over it with the landing's paper halo */
	.field {
		position: absolute;
		top: calc(-1 * var(--hub-pt));
		bottom: calc(-1 * var(--hub-pb));
		left: 0;
		right: 0;
		overflow: hidden;
	}
	.title {
		position: relative;
		z-index: 1;
	}
	.l1,
	.l2 {
		text-shadow:
			0 0 12px var(--paper),
			0 0 24px var(--paper);
	}
	.centre {
		display: flex;
		flex-direction: column;
		align-items: center;
		/* the caption 263 px under the hub's top edge on the author's export */
		padding-top: 24.3vh;
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
		font-size: clamp(36px, 3.7vw, 71px);
		letter-spacing: 0.05em;
	}
	.l2 {
		font-family: var(--font-display-narrow);
		font-weight: 500;
		font-size: clamp(24px, 2.47vw, 47.5px);
		letter-spacing: 0.26em;
	}
	/* the caption on TWO balanced lines (the author, 2026-09-04) */
	.centre .caption {
		max-width: 22em;
		font-size: clamp(14px, 1.25vw, 24px);
	}
	.centre .caption :global(.prose),
	.centre .caption :global(.prose p) {
		font-family: var(--font-display-narrow);
		font-weight: 700;
		font-size: clamp(14px, 1.25vw, 24px);
		line-height: 1.2;
		text-align: center;
		text-wrap: balance;
		color: var(--ink);
	}
	.rank {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		justify-content: center;
		/* the drawings stand on one baseline, their names on one line under */
		align-items: flex-end;
	}
	.rank.streams {
		margin-top: 1.2vh;
		gap: 3vw;
		/* the author set the drawings' row 47 px right of the caption's centre
		   at 1920 (the digger's mass sits left): half the shift as padding */
		padding-left: 4.9vw;
	}
	.rank.tools {
		margin-top: 5.9vh;
		gap: 3.6vw;
	}
	.rank li {
		flex: 0 0 auto;
	}
	/* the link is exactly the drawing's box, so the row's gaps are the gaps
	   and the drawings stand on one baseline whatever their names' length;
	   the name hangs under it out of the flow (2026-09-25) */
	.rank a {
		position: relative;
		display: block;
		text-decoration: none;
		color: var(--ink);
	}
	.rank.streams a {
		--label-top: 14px;
	}
	.rank.tools a {
		--label-top: 10px;
	}
	/* the name in the stream's own colour, shown on HOVER only (the author,
	   2026-09-04) — kept in the layout, so nothing moves when it appears */
	.label {
		position: absolute;
		top: calc(100% + var(--label-top, 12px));
		left: 50%;
		transform: translateX(-50%);
		white-space: nowrap;
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
			--hub-pt: 8vh;
			--hub-pb: 2vh;
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
			grid-template-columns: 1fr;
		}
		.field {
			display: none;
		}
		.rank {
			flex-wrap: wrap;
			gap: var(--sp-6) !important;
		}
	}
</style>
