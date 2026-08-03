<script lang="ts">
	import '$lib/styles/base.css';
	import favicon from '$lib/assets/favicon.svg';
	import { page } from '$app/state';
	import { eurShort } from '$lib/transforms/format';
	import type { LayoutData } from './$types';

	let { data, children }: { data: LayoutData; children: import('svelte').Snippet } = $props();

	const NAV = [
		{ href: '/anadohoi', label: 'Ανάδοχοι' },
		{ href: '/', label: 'Anti-nero' },
		{ href: '/dase', label: 'ΔΑΣΕ' },
		{ href: '/explore', label: 'Explore' },
		{ href: '/compare', label: 'Compare' },
		{ href: '/connections', label: 'Connections' },
		{ href: '/authorities', label: 'Authorities' },
		{ href: '/methodology', label: 'Methodology' }
	];

	const embed = $derived(page.url.searchParams.get('embed') === '1');
	function isActive(href: string): boolean {
		if (href === '/') return page.url.pathname === '/' || page.url.pathname.startsWith('/antinero');
		return page.url.pathname === href || page.url.pathname.startsWith(href + '/');
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<link rel="stylesheet" href="/fonts/fonts.css" />
	<meta property="og:site_name" content="Atlas — Greek wildfire-prevention money" />
	<meta property="og:type" content="website" />
	<meta name="twitter:card" content="summary" />
</svelte:head>

{#if !embed}
	<header>
		<div class="inner">
			<a class="brand" href="/">
				<span class="brand-title">Atlas</span>
				<span class="brand-sub">Greek wildfire-prevention money</span>
			</a>
			<nav>
				{#each NAV as item (item.href)}
					<a href={item.href} class:active={isActive(item.href)}>{item.label}</a>
				{/each}
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
					{(data.meta.generated ?? '').slice(0, 10)} · all € net of ΦΠΑ · consortium contract
					values are counted in full for each partner · <a href="/methodology">methodology</a>
				</p>
			{:else}
				<p class="fine">API unavailable — start it with <code>python -m atlas_api</code>.</p>
			{/if}
		</div>
	</footer>
{/if}

<style>
	header {
		border-bottom: 2px solid var(--ink);
		background: var(--paper);
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
	}
	.brand {
		text-decoration: none;
		display: flex;
		align-items: baseline;
		gap: var(--sp-2);
	}
	.brand-title {
		font-family: var(--font-serif);
		font-weight: 700;
		font-size: var(--fs-20);
	}
	.brand-sub {
		color: var(--ink-faint);
		font-size: var(--fs-13);
	}
	nav {
		display: flex;
		gap: var(--sp-4);
		flex-wrap: wrap;
	}
	nav a {
		text-decoration: none;
		font-size: var(--fs-14);
		color: var(--ink-soft);
		padding-bottom: 2px;
	}
	nav a.active {
		color: var(--ink);
		font-weight: 600;
		border-bottom: 2px solid var(--accent);
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
