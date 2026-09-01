<script lang="ts">
	/**
	 * THE STORY — the scroll behind START HERE, on the author's artboards.
	 * Three columns: the TIMELINE on the left, the NARRATIVE in the middle,
	 * the FIGURE with its caption and footnotes on the right.
	 *
	 * Everything follows the reader at PARAGRAPH granularity (the author's
	 * ruling, 2026-09-02): the rendered paragraphs are paired one-to-one with
	 * the parsed BLOCKS of the author's own .md files (`lib/story/content`),
	 * so the figure in force changes at their `[FIGURE xx: name]` markers, the
	 * right rail shows only the footnotes of the paragraphs on screen (nothing
	 * scrolls), and the timeline pans to the passage being read — its events
	 * lit through the curated needle bindings (`lib/story/bindings`), a bullet
	 * click scrolling to the exact paragraph.
	 *
	 * RULE THE MARKUP MUST KEEP: the beats TILE the column — vertical rhythm
	 * lives in padding inside `.beat`, never in margin between beats. A gap lets
	 * the reading line fall between two passages and the active one flickers.
	 */
	import { CHAPTERS } from '$lib/story/chapters';
	import KeyFindings from '$lib/sections/KeyFindings.svelte';
	import Prose from '$lib/ui/Prose.svelte';
	import { BRAND } from '$lib/landing/brand';
	import StoryTimeline from '$lib/story/StoryTimeline.svelte';
	import StoryFigure from '$lib/story/StoryFigure.svelte';
	import { EVENTS, type StoryEvent } from '$lib/story/events';
	import { BLOCKS, BLOCK_INDEX, NOTES, figureAt, timelineNote } from '$lib/story/content';
	import { resolveBindings } from '$lib/story/bindings';
	import { createSteps } from '$lib/story/steps';
	import type { Component } from 'svelte';
	import type { PageData } from './$types';
	import RefreshLine from '$lib/ui/RefreshLine.svelte';

	let { data }: { data: PageData } = $props();

	// every section's markdown, by id — a missing file is an empty section
	const texts = import.meta.glob('/src/content/story/*.md', {
		eager: true,
		import: 'default'
	}) as Record<string, Component>;
	const textOf = (id: string): Component | null => texts[`/src/content/story/${id}.md`] ?? null;

	/* ── the bindings: which paragraph each timeline event belongs beside ── */
	const bound = resolveBindings();
	const eventsAtBlock = new Map<string, StoryEvent[]>();
	for (const e of EVENTS) {
		const b = bound.get(e.id);
		if (!b) continue;
		const list = eventsAtBlock.get(b.id) ?? [];
		list.push(e);
		eventsAtBlock.set(b.id, list);
	}
	/** the timeline spreads when the text reaches its first dated event */
	const EXPAND_BLOCK = Math.min(
		...[...bound.values()].map((b) => BLOCK_INDEX.get(b.id) ?? Infinity)
	);

	/* ── the reading position, one paragraph at a time ── */
	let activeBlock = $state<string | null>(null);
	const blockSteps = createSteps({
		order: BLOCKS.map((b) => b.id),
		onActive: (id) => (activeBlock = id)
	});
	$effect(() => () => blockSteps.stop());

	/** the paragraphs currently anywhere on screen — the footnotes' window */
	let visList = $state<string[]>([]);

	/**
	 * Pair the RENDERED paragraphs with the parsed blocks, in order: give each
	 * element its block's id, register it on the reading-line observer, and on
	 * a visibility observer for the footnote window. The correspondence is
	 * p/h3 elements only — the hidden markers, rules and note lists don't
	 * count on either side.
	 */
	$effect(() => {
		if (typeof IntersectionObserver === 'undefined') return;
		const els: HTMLElement[] = [];
		for (const c of CHAPTERS) {
			const beat = document.getElementById(c.id);
			if (!beat) continue;
			els.push(...beat.querySelectorAll<HTMLElement>('.prose > p, .prose > h3'));
		}
		if (els.length !== BLOCKS.length) {
			console.warn(`story: ${els.length} rendered blocks vs ${BLOCKS.length} parsed`);
		}
		const n = Math.min(els.length, BLOCKS.length);
		const seen = new Set<string>();
		const io = new IntersectionObserver(
			(entries) => {
				for (const e of entries) {
					const id = (e.target as HTMLElement).id;
					if (e.isIntersecting) seen.add(id);
					else seen.delete(id);
				}
				visList = BLOCKS.filter((b) => seen.has(b.id)).map((b) => b.id);
			},
			{ threshold: 0 }
		);
		const actions: { destroy(): void }[] = [];
		for (let i = 0; i < n; i++) {
			els[i].id = BLOCKS[i].id;
			io.observe(els[i]);
			actions.push(blockSteps.step(els[i], BLOCKS[i].id));
		}
		return () => {
			io.disconnect();
			for (const a of actions) a.destroy();
		};
	});

	/* ── what follows from the reading position ── */
	const atBlock = $derived(activeBlock ? (BLOCK_INDEX.get(activeBlock) ?? -1) : -1);
	const activeSection = $derived(atBlock >= 0 ? BLOCKS[atBlock].section : null);
	const here = $derived(CHAPTERS.find((c) => c.id === activeSection) ?? CHAPTERS[0]);
	const expanded = $derived(atBlock >= EXPAND_BLOCK);
	const progress = $derived(BLOCKS.length > 1 ? Math.max(0, atBlock) / (BLOCKS.length - 1) : 0);

	/** the figure IN FORCE — the author's own marker, carried forward */
	const figure = $derived(figureAt(Math.max(0, atBlock)));

	/** only the footnotes of the paragraphs on screen, in document order */
	const shownNotes = $derived.by(() => {
		const out: { n: number; text: string }[] = [];
		for (const id of visList) {
			const b = BLOCKS[BLOCK_INDEX.get(id) ?? -1];
			if (!b) continue;
			for (const n of b.sups) out.push({ n, text: NOTES.get(n) ?? '' });
		}
		return out.sort((a, b) => a.n - b.n);
	});

	/** the events the active paragraph names — lit on the timeline */
	const activeIds = $derived(activeBlock ? (eventsAtBlock.get(activeBlock) ?? []).map((e) => e.id) : []);

	/** the date the rail centres on; it holds position between bound passages */
	let focusDate = $state<string | null>(null);
	$effect(() => {
		const evs = activeBlock ? eventsAtBlock.get(activeBlock) : undefined;
		if (evs?.length) focusDate = evs[0].date;
		else if (!activeBlock) focusDate = null;
	});

	/** a bullet was clicked: go to the exact paragraph that tells it */
	function goToEvent(e: StoryEvent) {
		const b = bound.get(e.id);
		if (!b) return;
		document
			.getElementById(b.id)
			?.scrollIntoView({ behavior: reduced() ? 'auto' : 'smooth', block: 'center' });
	}
	const reduced = () =>
		typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
</script>

<svelte:head>
	<title>The story — {BRAND}</title>
</svelte:head>

<div class="storyp">
	<div class="heads">
		<h2 class="head">TIMELINE</h2>
		<h2 class="head mid">{here.title}</h2>
	</div>

	<div class="cols">
		<aside class="rail tl">
			<StoryTimeline
				{expanded}
				{progress}
				{focusDate}
				{activeIds}
				onSelect={goToEvent}
				note={timelineNote()}
			/>
		</aside>

		<div class="narrative">
			{#each CHAPTERS as c (c.id)}
				<section class="beat" id={c.id}>
					<!-- the section is named ONCE, by the heading row above the column -->
					<Prose hint={`atlas/src/content/story/${c.id}.md`}>
						{@const Text = textOf(c.id)}
						{#if Text}<Text />{/if}
					</Prose>
				</section>
			{/each}
			<RefreshLine />
		</div>

		<aside class="rail fig">
			<StoryFigure {figure} notes={shownNotes} />
		</aside>
	</div>

	<div class="coda" id="findings-charts">
		<KeyFindings c={data.cmp} />
	</div>
</div>

<style>
	/* The artboard's own numbers, so the file documents itself:
	   timeline 60→580 · gutter 30 · text 610→1180 · gutter 70 · figure 1250→1844 */
	.heads,
	.cols {
		display: grid;
		grid-template-columns:
			minmax(0, 520fr) minmax(0, 30fr) minmax(0, 570fr)
			minmax(0, 70fr) minmax(0, 594fr);
		align-items: start; /* `stretch` would make the rails full-height and kill sticky */
	}
	.heads {
		position: sticky;
		/* pinned at the exact height they first render (header + the story
		   page's own top padding) — the author: the titles must NOT move up
		   when the text scrolls */
		top: var(--story-top, calc(var(--header-h, 85px) + 100px));
		z-index: 4;
		background: var(--paper);
		padding-bottom: var(--sp-2);
	}
	/* the strip between the black header and the pinned titles: paper, so the
	   narrative never shows through while it scrolls past */
	.heads::before {
		content: '';
		position: absolute;
		bottom: 100%;
		left: -20px;
		right: -20px;
		height: 80px;
		background: var(--paper);
	}
	/* the column titles are the dataset card's own name style — the same face,
	   weight, size ramp, line-height and tracking as «ANTI-NERO PROGRAMME»
	   (`ui/DatasetCard.svelte` .bigname), so the two pages speak once */
	.head {
		grid-column: 1;
		margin: 0;
		font-family: var(--font-display-narrow);
		font-weight: 900;
		font-size: clamp(15px, 1.25vw, 24px);
		line-height: 1.2;
		letter-spacing: 0.02em;
		text-transform: uppercase;
	}
	.head.mid {
		grid-column: 3;
	}

	.rail {
		position: sticky;
		top: calc(var(--story-top, calc(var(--header-h, 85px) + 100px)) + 3.2rem);
		height: calc(
			100dvh - var(--story-top, calc(var(--header-h, 85px) + 100px)) - 3.2rem -
				var(--story-pad-b, 20px)
		);
		overflow: hidden;
	}
	.tl {
		grid-column: 1;
	}
	.fig {
		grid-column: 5;
		/* risen so the rectangle's top aligns with the TITLES — both pinned at
		   --story-top; the 3.2rem is the heading row the other rails allow for */
		top: var(--story-top, calc(var(--header-h, 85px) + 100px));
		margin-top: -3.2rem;
		height: calc(
			100dvh - var(--story-top, calc(var(--header-h, 85px) + 100px)) -
				var(--story-pad-b, 20px)
		);
	}
	.narrative {
		grid-column: 3;
		/* the tail that lets the LAST passage reach the reading line */
		padding-bottom: 45vh;
	}

	/* beats tile: the rhythm is inside them, never between them */
	.beat {
		padding: var(--sp-8) 0;
		scroll-margin-top: 120px;
	}
	/* the methodology's sub-chapters stay in the text face, modest —
	   sub-chapters of METHODOLOGY, not titles of their own */
	.beat :global(h3) {
		margin: var(--sp-6) 0 var(--sp-3);
		font-family: var(--font-ui);
		font-weight: 700;
		font-size: var(--fs-16);
		line-height: 1.35;
		letter-spacing: 0;
		text-transform: none;
	}
	/* the narrative column hides what the right rail presents: the figure
	   markers (the caption is written under the image, as the artboard does)
	   and the section-end footnote lists (shown per visible paragraph under
	   the figure) — both stay in the author's .md files as the source */
	.beat :global(.figmark),
	.beat :global(hr),
	.beat :global(hr ~ ol) {
		display: none;
	}
	/* the author's footnote marks */
	.beat :global(sup) {
		font-size: 0.68em;
		line-height: 0;
		color: var(--ink-soft);
	}
	/* the paragraphs are scroll targets for the timeline's bullets */
	.beat :global(p) {
		scroll-margin-top: 160px;
	}

	.coda {
		max-width: var(--content-w);
		margin: var(--sp-12) auto 0;
	}

	@media (max-width: 1100px) {
		/* released, as the dataset cards release at the same width */
		.heads,
		.cols {
			grid-template-columns: minmax(0, 1fr);
		}
		.head,
		.head.mid,
		.tl,
		.fig,
		.narrative {
			grid-column: 1;
		}
		.heads {
			position: static;
		}
		.rail {
			position: static;
			height: auto;
			overflow: visible;
		}
		.tl {
			height: 420px;
			margin-bottom: var(--sp-8);
		}
		.narrative {
			padding-bottom: var(--sp-12);
		}
	}
</style>
