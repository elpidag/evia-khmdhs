<script lang="ts">
	/**
	 * The landing page (user mocks, 2026-08-27), three states on one URL:
	 * A — the full-viewport field of every identifier the site holds,
	 *     drifting in columns, each code in its dataset's colour;
	 * B — the title fades in over it;
	 * C — a click on the title collapses the field into the top-left cell
	 *     of the 4×4 menu and the page becomes title, standfirst, credit
	 *     on the left and the grid on the right.
	 * The brand link from inner pages returns straight to C (`?menu=1`),
	 * and a session that has seen C lands on it again (sessionStorage);
	 * ↻ in the field cell replays. Reduced motion opens on C with a still
	 * field.
	 */
	import { onMount, tick, untrack } from 'svelte';
	import { goto } from '$app/navigation';
	import { apiGetCached, type Landing } from '$lib/api';
	import CodeField from '$lib/landing/CodeField.svelte';
	import LandingTitle from '$lib/landing/LandingTitle.svelte';
	import HomeGrid from '$lib/landing/HomeGrid.svelte';
	import { HOME_CELLS } from '$lib/landing/homeCells';
	import { BRAND, BRAND_LINE1, BRAND_LINE2 } from '$lib/landing/brand';
	import Prose from '$lib/ui/Prose.svelte';
	import { legacyAntineroTarget } from '$lib/transforms/legacyRoutes';
	import Standfirst from '$content/landing/standfirst.md';
	import Credit from '$content/landing/credit.md';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const SEEN = 'sf.landing';
	const SEED = 20260827;
	type Stage = 'field' | 'title' | 'menu';
	// the loader's flag decides the INITIAL state only; the page moves on
	// from there by itself
	const menuAtLoad = untrack(() => data.menu);
	let stage = $state<Stage>(menuAtLoad ? 'menu' : 'field');
	/** the full-viewport field is mounted (states A/B and the collapse) */
	let big = $state(!menuAtLoad);
	/** the collapse is running: the stage box flies into the cell */
	let flying = $state(false);
	let box = $state<{ x: number; y: number; sx: number; sy: number } | null>(null);
	let cellEl = $state<HTMLElement | null>(null);
	let codes = $state.raw<Landing | null>(null);
	let replays = $state(0);
	const seed = $derived(SEED + replays);
	let titleTimer = 0;
	let flyTimer = 0;

	onMount(() => {
		// a hash-only permalink of the old front page («/#flows»)
		const t = legacyAntineroTarget(location.search, location.hash);
		if (t) {
			goto(t, { replaceState: true });
			return;
		}
		const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
		let seen = false;
		try {
			seen = sessionStorage.getItem(SEEN) === '1';
		} catch {
			/* storage may be unavailable; the animation simply plays */
		}
		if (menuAtLoad || seen || reduced) {
			stage = 'menu';
			big = false;
		}
		apiGetCached<Landing>(fetch, '/api/landing').then((v) => (codes = v));
		return () => {
			clearTimeout(titleTimer);
			clearTimeout(flyTimer);
		};
	});

	function firstFrame() {
		if (stage !== 'field') return;
		clearTimeout(titleTimer);
		titleTimer = window.setTimeout(() => {
			if (stage === 'field') stage = 'title';
		}, 1800);
	}

	async function open() {
		if (stage === 'menu') return;
		stage = 'menu';
		try {
			sessionStorage.setItem(SEEN, '1');
		} catch {
			/* see above */
		}
		await tick();
		const r = cellEl?.getBoundingClientRect();
		if (!r || matchMedia('(prefers-reduced-motion: reduce)').matches) {
			big = false;
			return;
		}
		box = { x: r.left, y: r.top, sx: r.width / window.innerWidth, sy: r.height / window.innerHeight };
		flying = true;
		flyTimer = window.setTimeout(() => {
			big = false;
			flying = false;
			box = null;
		}, 800);
	}

	function replay() {
		try {
			sessionStorage.removeItem(SEEN);
		} catch {
			/* see above */
		}
		replays += 1;
		big = true;
		flying = false;
		box = null;
		stage = 'field';
	}
</script>

<svelte:head>
	<title>{BRAND}</title>
	<meta
		name="description"
		content="An online platform tracing the changing landscape of forestry works amidst the increasing fires in Greece."
	/>
</svelte:head>

{#if big}
	{#key seed}
		<div
			class="stage"
			class:flying
			style:transform={box
				? `translate(${box.x}px, ${box.y}px) scale(${box.sx}, ${box.sy})`
				: null}
			aria-hidden="true"
		>
			<CodeField {codes} {seed} playing={stage !== 'menu' || flying} onFirstFrame={firstFrame} />
		</div>
	{/key}
	<LandingTitle on={stage === 'title'} onOpen={open} />
{/if}

<div class="home" class:shown={stage === 'menu'} aria-hidden={stage !== 'menu'}>
	<div class="text">
		<h1 class="title">
			<span class="l1">{BRAND_LINE1}</span>
			<span class="l2">{BRAND_LINE2}</span>
		</h1>
		<div class="standfirst">
			<Prose hint="atlas/src/content/landing/standfirst.md"><Standfirst /></Prose>
		</div>
		<div class="credit">
			<Prose hint="atlas/src/content/landing/credit.md"><Credit /></Prose>
		</div>
	</div>
	<div class="menu">
		<HomeGrid cells={HOME_CELLS} onReplay={replay}>
			{#snippet field()}
				<div class="cell" bind:this={cellEl}>
					{#if !big}
						{#key seed}
							<CodeField {codes} {seed} dense />
						{/key}
					{/if}
				</div>
			{/snippet}
		</HomeGrid>
	</div>
</div>

<noscript>
	<p class="noscript">
		<a href="/story">Start here</a> · <a href="/data">Explore the data</a> ·
		<a href="/methodology">Methodology</a>
	</p>
</noscript>

<style>
	/* the field's stage: the whole viewport, flown into the grid cell on
	   the click (a transform, so the canvas never re-lays out mid-flight) */
	.stage {
		position: fixed;
		inset: 0;
		z-index: 2;
		background: var(--paper);
		transform-origin: 0 0;
		will-change: transform;
	}
	.stage.flying {
		transition: transform 0.75s cubic-bezier(0.2, 0.7, 0.2, 1);
	}
	.home {
		display: grid;
		grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
		gap: var(--sp-12);
		min-height: 100dvh;
		padding: var(--sp-8);
		box-sizing: border-box;
		align-items: stretch;
		opacity: 0;
		transition: opacity 0.6s ease;
	}
	.home.shown {
		opacity: 1;
	}
	.text {
		display: flex;
		flex-direction: column;
		padding-top: 12vh;
	}
	.title {
		margin: 0 0 var(--sp-12);
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
	.standfirst :global(.prose) {
		font-size: var(--fs-18);
	}
	.credit {
		margin-top: auto;
	}
	.credit :global(.prose) {
		font-size: var(--fs-13);
		color: var(--ink-soft);
	}
	.menu {
		display: flex;
		align-items: center;
	}
	.menu :global(.grid) {
		max-height: calc(100dvh - 2 * var(--sp-8));
		max-width: calc(100dvh - 2 * var(--sp-8));
		margin-left: auto;
	}
	.cell {
		position: absolute;
		inset: 0;
	}
	.noscript {
		padding: var(--sp-8);
	}
	@media (max-width: 900px) {
		.home {
			grid-template-columns: 1fr;
			gap: var(--sp-8);
			padding: var(--sp-6) var(--sp-4);
		}
		.text {
			padding-top: var(--sp-4);
		}
		.credit {
			margin-top: var(--sp-6);
		}
	}
</style>
