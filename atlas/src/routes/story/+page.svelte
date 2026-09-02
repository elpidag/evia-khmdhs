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

	/* ── the reading position, one paragraph at a time ── */
	let activeBlock = $state<string | null>(null);
	const blockSteps = createSteps({
		order: BLOCKS.map((b) => b.id),
		onActive: (id) => (activeBlock = id)
	});
	$effect(() => () => blockSteps.stop());

	/** the paragraphs currently on screen BELOW the pinned band — the
	 *  footnotes' window, and what the section title answers to */
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
			// the top inset keeps the band's own strip out: a paragraph does not
			// count as visible while it is still hidden under the pinned titles
			{ threshold: 0, rootMargin: '-150px 0px 0px 0px' }
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
	/** the timeline serves the introduction and the chronology; once the
	 *  reader is in the methodology it withdraws (the author, 2026-09-02) */
	const activeSection = $derived(atBlock >= 0 ? BLOCKS[atBlock].section : null);
	const timelineOn = $derived(
		!activeSection || activeSection === 'introduction' || activeSection === 'chronology'
	);
	/** the timeline is SPREAD for as long as the chronology is on the page
	 *  (the author, 2026-09-02) — the moment its first paragraph appears the
	 *  lanes open, and they stay open until its last paragraph has left */
	const expanded = $derived(visList.some((id) => id.startsWith('chronology-')));
	const progress = $derived(BLOCKS.length > 1 ? Math.max(0, atBlock) / (BLOCKS.length - 1) : 0);

	/** the figure IN FORCE — the author's own marker, carried forward */
	const figure = $derived(figureAt(Math.max(0, atBlock)));

	/** KEY FINDINGS charts live in the figure column while the reader is in
	 *  that section (the author, 2026-09-02): its five paragraphs advance
	 *  through the five chart items one-to-one */
	const kfAt = $derived.by(() => {
		if (atBlock < 0 || BLOCKS[atBlock]?.section !== 'keyfindingandopenquestions') return -1;
		let n = 0;
		for (let j = 0; j < atBlock; j++) {
			if (BLOCKS[j].section === 'keyfindingandopenquestions') n++;
		}
		return Math.min(n, 4);
	});

	/** only the footnotes of the paragraphs on screen, in document order */
	const shownNotes = $derived.by(() => {
		const out: { n: number; dist: number; parts: { text: string; href?: string }[] }[] = [];
		for (const id of visList) {
			const b = BLOCKS[BLOCK_INDEX.get(id) ?? -1];
			if (!b) continue;
			const dist = Math.abs((BLOCK_INDEX.get(id) ?? 0) - Math.max(0, atBlock));
			for (const n of b.sups) {
				const e = NOTES.get(n);
				if (e) out.push({ n, dist, parts: e.parts });
			}
		}
		return out.sort((a, b) => a.n - b.n);
	});

	/** the events the active paragraph names — lit on the timeline */
	const activeIds = $derived(activeBlock ? (eventsAtBlock.get(activeBlock) ?? []).map((e) => e.id) : []);

	/** the ACTIVE paragraph's event dates — the rail frames the whole range;
	 *  it holds position between bound passages */
	let focusDates = $state<string[]>([]);
	$effect(() => {
		const evs = activeBlock ? eventsAtBlock.get(activeBlock) : undefined;
		if (evs?.length) focusDates = evs.map((e) => e.date);
		else if (!activeBlock) focusDates = [];
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
	<div class="cols" class:centred={!timelineOn}>
		<!-- TIMELINE is a grid sibling sticky at the SAME height as the section
		     titles, so the two columns start aligned; it withdraws with its
		     rail once the reader leaves the chronology -->
		<h2 class="head tl-head" class:off={!timelineOn}>TIMELINE</h2>
		<aside class="rail tl" class:off={!timelineOn}>
			<StoryTimeline
				{expanded}
				{progress}
				{focusDates}
				{activeIds}
				onSelect={goToEvent}
				note={timelineNote()}
			/>
		</aside>

		<div class="narrative">
			{#each CHAPTERS as c (c.id)}
				<section class="beat" id={c.id}>
					<!-- the section announces itself in the flow, docks at the band and
					     is pushed out by the next one — the handoff IS the transition -->
					<h2 class="sect-title">{c.title}</h2>
					<Prose hint={`atlas/src/content/story/${c.id}.md`}>
						{@const Text = textOf(c.id)}
						{#if Text}<Text />{/if}
					</Prose>
				</section>
			{/each}
			<RefreshLine />
		</div>

		<aside class="rail fig">
			{#if kfAt >= 0}
				{#key kfAt}
					<KeyFindings c={data.cmp} i={kfAt} />
				{/key}
			{:else if activeSection !== 'bibliography'}
				<!-- the bibliography stands alone — no figure beside it (author) -->
				<StoryFigure {figure} notes={shownNotes} />
			{/if}
		</aside>
	</div>

	<!-- the page's bottom breathes: a paper band the columns stop short of;
	     its twin covers the strip between the header and the docked titles -->
	<div class="bband" aria-hidden="true"></div>
	<div class="tcover" aria-hidden="true"></div>
</div>

<style>
	.storyp {
		/* the breathing band: every column stops this short of the window's
		   bottom edge, and the page pads by it so the end is reachable */
		--story-band: 48px;
		padding-bottom: var(--story-band);
	}
	/* The five tracks, retuned by the author (2026-09-02) from the artboard's
	   520/30/570/70/594: the figure track is exactly its content's 540 px —
	   image, caption and notes then share both edges, the right one on the
	   page margin — and the spare went to the narrative, less the author's
	   6 px trim of 2026-09-02 and its EQUAL 38 px gutters either side. The fr values are
	   READ AS PIXELS AT 1920, which holds only while they sum to 1784 (the
	   content width inside the page margins) — keep that sum when retuning. */
	.cols {
		display: grid;
		grid-template-columns:
			minmax(0, 500fr) minmax(0, 38fr) minmax(0, 668fr)
			minmax(0, 38fr) minmax(0, 540fr);
		align-items: start; /* `stretch` would make the rails full-height and kill sticky */
		transition:
			grid-template-columns 0.6s cubic-bezier(0.2, 0.7, 0.2, 1),
			padding-right 0.6s cubic-bezier(0.2, 0.7, 0.2, 1);
	}
	/* once the timeline withdraws (methodology onward) the text and the
	   figure column CENTRE (the author, 2026-09-02): the first track gives
	   up its rail width, the right padding balances it — 231+38 = 269 both
	   sides of the 668+38+540 pair, the fr values still px at 1920 */
	.cols.centred {
		grid-template-columns:
			minmax(0, 231fr) minmax(0, 38fr) minmax(0, 668fr)
			minmax(0, 38fr) minmax(0, 540fr);
		padding-right: 15.0785%; /* 269 / 1784 */
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
	/* TIMELINE: same grid row as the columns, sticky at the same height as the
	   section titles — the two starts cannot misalign */
	.tl-head {
		grid-row: 1;
		align-self: start;
		position: sticky;
		top: var(--story-top, calc(var(--header-h, 85px) + 100px));
		z-index: 5;
		background: var(--paper);
		padding-bottom: var(--sp-2);
		transition: opacity 0.4s ease;
	}
	.tl-head.off {
		opacity: 0;
		pointer-events: none;
	}
	/* a section's own title: sticky at the band, full column width in paper so
	   the text scrolls under it, pushed out by the next section's title */
	.sect-title {
		position: sticky;
		top: var(--story-top, calc(var(--header-h, 85px) + 100px));
		z-index: 3;
		margin: 0 0 var(--sp-4);
		padding-bottom: var(--sp-2);
		background: var(--paper);
		font-family: var(--font-display-narrow);
		font-weight: 900;
		font-size: clamp(15px, 1.25vw, 24px);
		line-height: 1.2;
		letter-spacing: 0.02em;
		text-transform: uppercase;
	}

	.rail {
		position: sticky;
		top: calc(var(--story-top, calc(var(--header-h, 85px) + 100px)) + 3.2rem);
		height: calc(
			100dvh - var(--story-top, calc(var(--header-h, 85px) + 100px)) - 3.2rem -
				var(--story-band, 48px)
		);
		overflow: hidden;
	}
	.tl {
		grid-column: 1;
		grid-row: 1;
		transition: opacity 0.4s ease;
	}
	.rail.tl.off {
		opacity: 0;
		pointer-events: none;
	}
	.fig {
		grid-column: 5;
		grid-row: 1;
		/* the rectangle's top aligns with the titles — pinned at --story-top */
		top: var(--story-top, calc(var(--header-h, 85px) + 100px));
		height: calc(
			100dvh - var(--story-top, calc(var(--header-h, 85px) + 100px)) -
				var(--story-band, 48px)
		);
	}
	.narrative {
		grid-column: 3;
		grid-row: 1;
		/* the tail that lets the LAST passage reach the reading line */
		padding-bottom: 45vh;
	}

	/* beats tile: the rhythm is inside them, never between them */
	.beat {
		padding: var(--sp-8) 0;
		scroll-margin-top: 120px;
	}
	/* the first section starts level with TIMELINE */
	.beat:first-of-type {
		padding-top: 0;
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
	/* the narrative sets like the printed page (the author, 2026-09-02):
	   justified with the first line indented — and NO hyphenation (their
	   second ruling): the base word gap is tightened a touch so the
	   justification stretches from lower, and `text-wrap: pretty` lets the
	   browser pick line breaks that keep the gaps even */
	.beat :global(.prose > p) {
		text-align: justify;
		text-indent: 2em;
		hyphens: manual;
		word-spacing: -0.02em;
		text-wrap: pretty;
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
	/* the bibliography reads as apparatus, not narrative: two sizes under
	   the 16 px main text (the author, 2026-09-02) */
	#bibliography :global(.prose) {
		font-size: var(--fs-13);
		line-height: 1.5;
	}

	.bband {
		position: fixed;
		left: 0;
		right: 0;
		bottom: 0;
		height: var(--story-band, 48px);
		background: var(--paper);
		z-index: 40;
		pointer-events: none;
	}
	/* the strip between the header and the docked titles: a pushed-out title
	   slides under it and vanishes cleanly */
	.tcover {
		position: fixed;
		left: 0;
		right: 0;
		top: var(--header-h, 85px);
		height: calc(
			var(--story-top, calc(var(--header-h, 85px) + 100px)) - var(--header-h, 85px)
		);
		background: var(--paper);
		z-index: 40;
		pointer-events: none;
	}

	@media (max-width: 1100px) {
		/* released, as the dataset cards release at the same width */
		.cols {
			grid-template-columns: minmax(0, 1fr);
		}
		.tl-head,
		.tl,
		.fig,
		.narrative {
			grid-column: 1;
			grid-row: auto;
		}
		.tl-head {
			position: static;
		}
		.bband,
		.tcover {
			display: none;
		}
		.sect-title {
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
