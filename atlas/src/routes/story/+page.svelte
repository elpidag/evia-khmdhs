<script lang="ts">
	/**
	 * THE STORY — the scroll behind START HERE (user, 2026-08-27). Phase 1
	 * is the skeleton: a chapter menu, one section per chapter with its
	 * markdown, and KEY FINDINGS carrying the frames that were /compare.
	 * The chapters' text and their scroll-driven charts come next.
	 */
	import { CHAPTERS } from '$lib/story/chapters';
	import KeyFindings from '$lib/sections/KeyFindings.svelte';
	import Prose from '$lib/ui/Prose.svelte';
	import { BRAND } from '$lib/landing/brand';
	import type { Component } from 'svelte';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	// every chapter's markdown, by id — a missing file is an empty chapter
	const texts = import.meta.glob('/src/content/story/*.md', {
		eager: true,
		import: 'default'
	}) as Record<string, Component>;
	const textOf = (id: string): Component | null => texts[`/src/content/story/${id}.md`] ?? null;
</script>

<svelte:head>
	<title>The story — {BRAND}</title>
</svelte:head>

<div class="story">
	<nav class="chapters" aria-label="Chapters">
		{#each CHAPTERS as ch (ch.id)}
			<a href={`#${ch.id}`}>{ch.title}</a>
		{/each}
	</nav>

	{#each CHAPTERS as ch (ch.id)}
		{@const Text = textOf(ch.id)}
		<section class="chapter" id={ch.id}>
			<h2>{ch.title}</h2>
			<Prose hint={`atlas/src/content/story/${ch.id}.md`}>
				{#if Text}<Text />{/if}
			</Prose>
			{#if ch.id === 'findings'}
				<KeyFindings c={data.cmp} />
			{/if}
		</section>
	{/each}
</div>

<style>
	.chapters {
		position: sticky;
		top: 85px; /* under the header band */
		z-index: 5;
		display: flex;
		flex-wrap: wrap;
		gap: var(--sp-2) var(--sp-4);
		padding: var(--sp-2) 0;
		background: var(--paper);
		border-bottom: 1px solid var(--line);
		margin-bottom: var(--sp-8);
	}
	.chapters a {
		text-decoration: none;
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-13);
		letter-spacing: 0.04em;
		color: #9e9e9e;
	}
	.chapters a:hover {
		color: var(--ink);
	}
	.chapter {
		scroll-margin-top: 120px;
		margin-bottom: var(--sp-12);
		min-height: 20vh;
	}
	.chapter h2 {
		font-family: var(--font-display);
		font-weight: 900;
		text-transform: uppercase;
		font-size: var(--fs-24);
		letter-spacing: 0.02em;
		margin: 0 0 var(--sp-4);
	}
</style>
