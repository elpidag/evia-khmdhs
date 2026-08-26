<script lang="ts">
	import '$lib/styles/base.css';
	import favicon from '$lib/assets/favicon.svg';
	import { page } from '$app/state';
	import { SYMBOLS, symbolOfPath } from '$lib/datasets';
	import { BRAND, BRAND_LINE1, BRAND_LINE2 } from '$lib/landing/brand';
	import DatasetSymbol from '$lib/ui/DatasetSymbol.svelte';
	import type { LayoutData } from './$types';

	let { children }: { data: LayoutData; children: import('svelte').Snippet } = $props();

	// The header since 2026-08-27 (user mocks): the brand on two lines, the
	// site's five symbols — the three streams and the two tools — and
	// METHODOLOGY. The landing page at `/` carries no chrome at all.
	const isLanding = $derived(page.url.pathname === '/');
	// the three dataset CARDS and the hub compose one viewport, so their
	// page is as wide as the window; a card's unfolded part returns to the
	// article width
	const isCard = $derived(['/anadohoi', '/antinero', '/dase', '/data'].includes(page.url.pathname));
	const current = $derived(symbolOfPath(page.url.pathname));
	const methodologyActive = $derived(page.url.pathname.startsWith('/methodology'));

	// sticky header compacts to a single slim row once the page is scrolled
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
					{#each SYMBOLS as s (s.key)}
						<li>
							<a
								href={s.href}
								class="sym"
								class:active={current === s.key}
								title={s.label}
								aria-current={current === s.key ? 'page' : undefined}
							>
								<DatasetSymbol key={s.key} size={30} active={current === s.key} />
								<span class="sr">{s.label}</span>
							</a>
						</li>
					{/each}
				</ul>
				<a class="text" href="/methodology" class:active={methodologyActive}>METHODOLOGY</a>
			</nav>
		</div>
	</header>
{/if}

<main class:embed class:landing={isLanding} class:card={isCard}>
	{@render children()}
</main>

<style>
	header {
		/* pinned while scrolling, compacts past 60px (see onscroll) */
		position: sticky;
		top: 0;
		z-index: 100;
		background: var(--paper);
		transition: box-shadow 0.2s ease;
	}
	header.scrolled {
		box-shadow:
			0 1px 0 var(--line),
			0 8px 24px rgba(0, 0, 0, 0.06);
	}
	header.scrolled .inner {
		padding-top: var(--sp-2);
		padding-bottom: var(--sp-2);
	}
	.inner {
		max-width: var(--content-w);
		margin: 0 auto;
		padding: var(--sp-3) var(--sp-4);
	}
	header .inner {
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: var(--sp-2) var(--sp-6);
		transition: padding 0.2s ease;
	}
	/* the brand: the site's name on two lines, small */
	.brand {
		text-decoration: none;
		color: var(--ink);
		display: flex;
		flex-direction: column;
		line-height: 1;
	}
	.brand .l1 {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-18);
		letter-spacing: 0.01em;
	}
	.brand .l2 {
		font-family: var(--font-ui);
		font-weight: 400;
		font-size: var(--fs-12);
		letter-spacing: 0.3em;
		margin-top: 3px;
	}
	nav {
		display: flex;
		align-items: center;
		gap: var(--sp-8);
		flex-wrap: wrap;
	}
	.symbols {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		align-items: center;
		gap: var(--sp-3);
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
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-15);
		letter-spacing: 0.02em;
		color: #9e9e9e; /* dimmed until active */
	}
	nav a.text.active {
		color: var(--ink);
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
	/* a dataset card is a viewport composition: window-wide, the mock's
	   margins; the unfolded frames below re-centre at the article width */
	main.card {
		--header-h: 60px;
		max-width: none;
		padding: var(--sp-4) var(--sp-8);
	}
</style>
