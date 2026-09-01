<script lang="ts">
	import '$lib/styles/base.css';
	import favicon from '$lib/assets/favicon.svg';
	import { page } from '$app/state';
	import { SYMBOLS, symbolOfPath } from '$lib/datasets';
	import { BRAND, BRAND_LINE1, BRAND_LINE2 } from '$lib/landing/brand';
	import DatasetSymbol from '$lib/ui/DatasetSymbol.svelte';
	import type { LayoutData } from './$types';

	let { children }: { data: LayoutData; children: import('svelte').Snippet } = $props();

	// The header since 2026-08-27 (Artboard 4, second round): a BLACK 85 px
	// band — the brand in white on two lines, then FIVE filled 59,5 px
	// squares (the three streams, then search and the actor network) each
	// carrying its own name, and METHODOLOGY in white at the right edge.
	// `/` carries no chrome at all.
	const streams = SYMBOLS.filter((s) => s.rank === 'stream');
	const tools = SYMBOLS.filter((s) => s.rank === 'tool');
	const isLanding = $derived(page.url.pathname === '/');
	// the three dataset CARDS and the hub compose one viewport, so their
	// page is as wide as the window; a card's unfolded part returns to the
	// article width
	const isCard = $derived(['/anadohoi', '/antinero', '/dase', '/data'].includes(page.url.pathname));
	// the story composes three columns across the author's 1920 artboard, so it
	// is as wide as the window too — but with its own rhythm, not a card's
	const isStory = $derived(page.url.pathname === '/story');
	const current = $derived(symbolOfPath(page.url.pathname));
	const methodologyActive = $derived(page.url.pathname.startsWith('/methodology'));

	// the sticky band keeps its height; a shadow says the page is scrolled
	let scrolled = $state(false);

	const embed = $derived(page.url.searchParams.get('embed') === '1');
	const chrome = $derived(!embed && !isLanding);
</script>

<svelte:window onscroll={() => (scrolled = window.scrollY > 60)} />

<svelte:head>
	<link rel="icon" href={favicon} />
	<link rel="stylesheet" href="/fonts/fonts.css" />
	<meta property="og:site_name" content={BRAND} />
	<meta property="og:type" content="website" />
	<meta name="twitter:card" content="summary" />
</svelte:head>

{#if chrome}
	<header class:scrolled>
		<div class="inner">
			<a class="brand" href="/?menu=1">
				<span class="l1">{BRAND_LINE1}</span>
				<span class="l2">{BRAND_LINE2}</span>
			</a>
			<nav>
				<ul class="symbols">
					{#each streams as s (s.key)}
						<li>
							<a
								href={s.href}
								class="sym"
								title={s.label}
								aria-current={current === s.key ? 'page' : undefined}
							>
								<DatasetSymbol
									key={s.key}
									size="clamp(36px, 3.1vw, 59.5px)"
									active={current === s.key}
									band
									labelled
								/>
								<span class="sr">{s.label}</span>
							</a>
						</li>
					{/each}
				</ul>
				<ul class="tools">
					{#each tools as s (s.key)}
						<li>
							<a
								href={s.href}
								class="sym"
								title={s.label}
								aria-current={current === s.key ? 'page' : undefined}
							>
								<DatasetSymbol
									key={s.key}
									size="clamp(36px, 3.1vw, 59.5px)"
									active={current === s.key}
									band
									labelled
								/>
								<span class="sr">{s.label}</span>
							</a>
						</li>
					{/each}
				</ul>
				<a class="text method" href="/methodology" class:active={methodologyActive}>METHODOLOGY</a>
			</nav>
		</div>
	</header>
{/if}

<main class:embed class:landing={isLanding} class:card={isCard} class:story={isStory}>
	{@render children()}
</main>

<style>
	header {
		position: sticky;
		top: 0;
		z-index: 100;
		background: #000;
	}
	/* the band: 85 px tall and BLACK, the brand 81 px in, METHODOLOGY off
	   the right edge (Artboard 4, 1920 wide) */
	header .inner {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--sp-4);
		height: var(--header-h, 85px);
		padding: 0 clamp(12px, 0.9vw, 17px) 0 clamp(20px, 4.22vw, 81px);
		box-sizing: border-box;
	}
	.brand {
		text-decoration: none;
		color: #fff;
		display: flex;
		flex-direction: column;
		line-height: 1;
		flex: none;
	}
	.brand .l1 {
		font-family: var(--font-display-narrow);
		font-weight: 900;
		font-size: clamp(14px, 0.94vw, 18px);
		letter-spacing: 0.05em;
	}
	.brand .l2 {
		font-family: var(--font-display-narrow);
		font-weight: 500;
		font-size: clamp(10px, 0.625vw, 12px);
		letter-spacing: 0.27em;
		margin-top: 2px;
	}
	nav {
		display: flex;
		align-items: center;
		min-width: 0;
	}
	.symbols,
	.tools {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		align-items: center;
		gap: clamp(8px, 0.84vw, 16px);
	}
	.symbols li,
	.tools li {
		display: flex;
	}
	/* the artboard's rhythm: the three streams, a 110 px gap, the two
	   tools, then METHODOLOGY */
	.tools {
		margin-left: clamp(16px, 5.75vw, 110px);
	}
	.method {
		margin-left: clamp(20px, 6.7vw, 129px);
	}
	.sym {
		display: inline-flex;
		text-decoration: none;
	}
	.sr {
		position: absolute;
		width: 1px;
		height: 1px;
		overflow: hidden;
		clip: rect(0 0 0 0);
		white-space: nowrap;
	}
	nav a.text {
		text-decoration: none;
		font-family: var(--font-display-narrow);
		font-weight: 500;
		font-size: clamp(10px, 0.625vw, 12px);
		text-transform: uppercase;
		white-space: nowrap;
		color: #fff;
		opacity: 0.75;
	}
	nav a.text.active,
	nav a.text:hover {
		opacity: 1;
	}
	main {
		max-width: var(--content-w);
		margin: 0 auto;
		padding: var(--sp-8) var(--sp-4) var(--sp-12);
	}
	main.embed {
		padding: var(--sp-2);
	}
	/* the landing page owns the whole viewport */
	main.landing {
		max-width: none;
		padding: 0;
	}
	/* a dataset card is a viewport composition: window-wide, the artboard's
	   margins — 20 px above, 20 px right, 22 px below, 81 px left; the hub
	   reads the same paddings to undo them */
	main.card {
		--header-h: 85px;
		/* 25 px under the black band, 17 px at the foot (user, 2026-08-27) */
		--card-pad-t: 25px;
		--card-pad-r: clamp(12px, 1.07vw, 20.5px);
		--card-pad-b: 17px;
		--card-pad-l: clamp(24px, 4.22vw, 81px);
		max-width: none;
		padding: var(--card-pad-t) var(--card-pad-r) var(--card-pad-b) var(--card-pad-l);
	}
	/* the story is the author's 1920 artboard: three columns across the window,
	   letterboxed above 1920 so the reading measure never grows past its design
	   (the middle column is 570 px of 18 px type — about 68 characters) */
	main.story {
		--header-h: 85px;
		--story-pad-b: clamp(12px, 1.85vh, 20px);
		/* where the page's fixed titles sit: the header plus the top padding
		   below — the story pins its heading row there so it never moves */
		--story-top: calc(var(--header-h) + clamp(20px, 3.7vh, 40px));
		max-width: 1920px;
		padding: clamp(20px, 3.7vh, 40px) clamp(20px, 3.958vw, 76px) var(--story-pad-b)
			clamp(20px, 3.125vw, 60px);
	}
	@media (max-width: 900px) {
		header .inner {
			height: auto;
			flex-wrap: wrap;
			padding: var(--sp-3) var(--sp-4);
			gap: var(--sp-2) var(--sp-4);
		}
		nav {
			flex-wrap: wrap;
			gap: var(--sp-3);
		}
		.tools,
		.method {
			margin-left: 0;
		}
	}
</style>
