<script lang="ts">
	import '$lib/styles/base.css';
	import favicon from '$lib/assets/favicon.svg';
	import { page } from '$app/state';
	import { eurShort } from '$lib/transforms/format';
	import type { LayoutData } from './$types';

	let { data, children }: { data: LayoutData; children: import('svelte').Snippet } = $props();

	// `color`: the dataset hue the tab turns into when active (replaces the
	// underline); tabs without one keep the accent underline.
	const NAV: { href: string; label: string; color?: string }[] = [
		{ href: '/anadohoi', label: 'SPONSORED WORKS', color: 'var(--c-anadohoi)' },
		{ href: '/', label: 'ANTINERO WORKS', color: 'var(--c-antinero)' },
		{ href: '/dase', label: 'FOREST CO-OP WORKS', color: 'var(--c-dase)' },
		{ href: '/explore', label: 'EXPLORE', color: 'var(--c-antinero)' }
	];
	// secondary pages under the MENU dropdown (ΑΡΩΓΗ kept reachable here)
	const MENU = [
		{ href: '/arogi', label: 'ΑΡΩΓΗ' },
		{ href: '/compare', label: 'COMPARE' },
		{ href: '/connections', label: 'CONNECTIONS' },
		{ href: '/authorities', label: 'AUTHORITIES' },
		{ href: '/methodology', label: 'METHODOLOGY' }
	];

	let menuOpen = $state(false);
	let menuEl = $state<HTMLElement | null>(null);
	const menuActive = $derived(MENU.some((m) => isActive(m.href)));

	// sticky header compacts to a single slim row once the page is scrolled
	let scrolled = $state(false);

	const embed = $derived(page.url.searchParams.get('embed') === '1');
	function isActive(href: string): boolean {
		if (href === '/') return page.url.pathname === '/' || page.url.pathname.startsWith('/antinero');
		return page.url.pathname === href || page.url.pathname.startsWith(href + '/');
	}
</script>

<svelte:window
	onclick={(e) => {
		if (menuOpen && menuEl && !menuEl.contains(e.target as Node)) menuOpen = false;
	}}
	onkeydown={(e) => {
		if (e.key === 'Escape') menuOpen = false;
	}}
	onscroll={() => (scrolled = window.scrollY > 60)}
/>

<svelte:head>
	<link rel="icon" href={favicon} />
	<link rel="stylesheet" href="/fonts/fonts.css" />
	<meta property="og:site_name" content="FORESTRY WORKS TRACKER" />
	<meta property="og:type" content="website" />
	<meta name="twitter:card" content="summary" />
</svelte:head>

{#if !embed}
	<header class:scrolled>
		<div class="inner">
			<a class="brand" href="/">
				<span class="brand-title">FORESTRY WORKS TRACKER</span>
			</a>
			<nav>
				{#each NAV as item (item.href)}
					<a
						href={item.href}
						class:active={isActive(item.href)}
						class:tinted={!!item.color}
						style:color={isActive(item.href) && item.color ? item.color : null}
					>
						{item.label}
					</a>
				{/each}
				<div class="menu" bind:this={menuEl}>
					<button
						class="menu-btn"
						class:active={menuActive}
						aria-haspopup="true"
						aria-expanded={menuOpen}
						onclick={() => (menuOpen = !menuOpen)}
					>
						MENU ▾
					</button>
					{#if menuOpen}
						<div class="dropdown">
							{#each MENU as item (item.href)}
								<a
									href={item.href}
									class:active={isActive(item.href)}
									onclick={() => (menuOpen = false)}
								>
									{item.label}
								</a>
							{/each}
						</div>
					{/if}
				</div>
			</nav>
		</div>
	</header>
{/if}

<main class:embed>
	{@render children()}
</main>

{#if !embed}
	<footer>
		<div class="inner">
			{#if data.meta}
				<p>
					{#if data.meta.anadohoi}
						Ανάδοχοι: {data.meta.anadohoi.n_projects} projects &nbsp;·&nbsp;
					{/if}
					Anti-nero: {data.meta.antinero.n_contracts} contracts · {eurShort(
						data.meta.antinero.total_eur
					)} stated
					{#if data.meta.dase}
						&nbsp;·&nbsp; ΔΑΣΕ: {data.meta.dase.n_contracts} contracts · {eurShort(
							data.meta.dase.total_eur
						)} stated
					{/if}
				</p>
				<p class="fine">
					Source: ΚΗΜΔΗΣ (KHMDHS) open data + Διαύγεια · data as of
					{(data.meta.generated ?? '').slice(0, 10)} · all € net of ΦΠΑ · joint contracts count in
					full for each partner on Anti-nero, split evenly on co-op works ·
					<a href="/methodology">methodology</a>
				</p>
			{:else}
				<p class="fine">API unavailable — start it with <code>python -m atlas_api</code>.</p>
			{/if}
		</div>
	</footer>
{/if}

<style>
	header {
		/* option B: pinned while scrolling, compacts past 60px (see onscroll) */
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
		align-items: baseline;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: var(--sp-2) var(--sp-6);
		transition: padding 0.2s ease;
	}
	.brand {
		text-decoration: none;
		display: flex;
		align-items: baseline;
		gap: var(--sp-2);
	}
	.brand-title {
		font-family: var(--font-display);
		/* Obviously Black; the kit serves Bold (700) until the Black cut
		   is added to the Adobe web project, then this picks it up */
		font-weight: 900;
		font-size: var(--fs-28);
		letter-spacing: 0.01em;
		transition: font-size 0.2s ease;
	}
	nav {
		display: flex;
		/* tabs align on their vertical centre: the enlarged selected tab
		   grows equally upwards and downwards */
		align-items: center;
		gap: var(--sp-4);
		flex-wrap: wrap;
	}
	nav a,
	.menu-btn {
		text-decoration: none;
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-15);
		letter-spacing: 0.02em;
		color: #9e9e9e; /* dimmed inactive tabs */
	}
	/* selected tab: its assigned colour (inline style on the dataset tabs,
	   black otherwise) and 1.3× lettering */
	nav a.active,
	.menu-btn.active {
		color: var(--c-antinero);
		font-size: calc(var(--fs-15) * 1.3);
	}
	.menu {
		position: relative;
	}
	.menu-btn {
		background: none;
		border: none;
		padding: 0;
		cursor: pointer;
		line-height: inherit;
	}
	.dropdown {
		position: absolute;
		top: calc(100% + 6px);
		right: 0;
		display: flex;
		flex-direction: column;
		gap: var(--sp-2);
		background: var(--paper);
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		box-shadow: var(--shadow-paper);
		padding: var(--sp-3) var(--sp-4);
		min-width: max-content;
		z-index: 60;
	}
	main {
		max-width: var(--content-w);
		margin: 0 auto;
		padding: var(--sp-8) var(--sp-4) var(--sp-12);
	}
	main.embed {
		padding: var(--sp-2);
	}
	footer {
		border-top: 1px solid var(--line-strong);
		background: var(--paper-2);
	}
	footer p {
		margin: 0 0 var(--sp-1);
		font-size: var(--fs-13);
		color: var(--ink-soft);
	}
	.fine {
		font-size: var(--fs-12);
		color: var(--ink-faint);
	}
</style>
