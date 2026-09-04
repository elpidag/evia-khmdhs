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
	import ChartBand from '$lib/story/ChartBand.svelte';
	import { mount, unmount } from 'svelte';
	import StoryFigure from '$lib/story/StoryFigure.svelte';
	import StoryNotes from '$lib/story/StoryNotes.svelte';
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
	/** the methodology, the bibliography and the sources read ALONE: no
	 *  figure beside them (the one in force is not carried into them) and
	 *  the text in the middle of the page; KEY FINDINGS keeps its pair with
	 *  the rail card (the author, 2026-09-04) */
	const figureOff = $derived(
		activeSection === 'methodology' ||
			activeSection === 'bibliography' ||
			activeSection === 'sources'
	);
	/** the timeline SPREADS when the CHRONOLOGY title DOCKS level with the
	 *  TIMELINE title (the author, 2026-09-02 — not when its first paragraph
	 *  peeks in at the viewport's bottom), and folds back once the section's
	 *  end passes the band */
	let chronoDocked = $state(false);
	$effect(() => {
		if (typeof IntersectionObserver === 'undefined') return;
		const el = document.getElementById('chronology');
		if (!el) return;
		// the docking line: the header plus the page's top padding, where the
		// sticky section titles pin (--story-top in the layout)
		const st = Math.round(85 + Math.min(40, Math.max(20, window.innerHeight * 0.037)));
		const io = new IntersectionObserver(
			(es) => {
				for (const e of es) chronoDocked = e.isIntersecting;
			},
			{ rootMargin: `-${st}px 0px ${st + 4 - window.innerHeight}px 0px`, threshold: 0 }
		);
		io.observe(el);
		return () => io.disconnect();
	});
	const expanded = $derived(chronoDocked);

	/** the introduction's STAGED REVEAL (the author, 2026-09-02): stage 0
	 *  until the reader scrolls at all (a 1 px sentinel at the document's
	 *  very top — no scroll listener, the page keeps none), stage 1 until
	 *  the «Greece is part of the wider Mediterranean Basin …» paragraph
	 *  docks at the title, stage 2 after */
	let scrolledAny = $state(false);
	let greecePassed = $state(false);
	let topSentinel = $state<HTMLElement | null>(null);
	$effect(() => {
		const el = topSentinel;
		if (!el || typeof IntersectionObserver === 'undefined') return;
		const io = new IntersectionObserver((es) => {
			for (const e of es) scrolledAny = !e.isIntersecting;
		});
		io.observe(el);
		return () => io.disconnect();
	});
	$effect(() => {
		if (typeof IntersectionObserver === 'undefined') return;
		const b = BLOCKS.find((x) =>
			x.text.startsWith('Greece is part of the wider Mediterranean Basin')
		);
		const el = b ? document.getElementById(b.id) : null;
		if (!el) return;
		const st = Math.round(85 + Math.min(40, Math.max(20, window.innerHeight * 0.037)));
		const io = new IntersectionObserver(
			(es) => {
				for (const e of es) {
					greecePassed = e.isIntersecting || e.boundingClientRect.top <= st;
				}
			},
			{ rootMargin: `-${st}px 0px ${st + 4 - window.innerHeight}px 0px`, threshold: 0 }
		);
		io.observe(el);
		return () => io.disconnect();
	});
	const introStage = $derived(greecePassed ? 2 : scrolledAny ? 1 : 0);
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

	/** the KPI cards appear once the KEY FINDINGS title has docked AND the
	 *  section's first paragraph has reached the top of the column too (the
	 *  author, 2026-09-04) — the same docking observer as the introduction's */
	let kfDocked = $state(false);
	$effect(() => {
		if (typeof IntersectionObserver === 'undefined') return;
		const b = BLOCKS.find((x) => x.section === 'keyfindingandopenquestions');
		const el = b ? document.getElementById(b.id) : null;
		if (!el) return;
		const st = Math.round(85 + Math.min(40, Math.max(20, window.innerHeight * 0.037)));
		const io = new IntersectionObserver(
			(es) => {
				for (const e of es) kfDocked = e.boundingClientRect.top <= st + 2;
			},
			{ rootMargin: `-${st}px 0px ${st + 4 - window.innerHeight}px 0px`, threshold: 0 }
		);
		io.observe(el);
		return () => io.disconnect();
	});

	/** the FULL-WIDTH chart in the narrative's flow (the author, 2026-09-04):
	 *  the author's `[CHART: state-funded]` line renders as a placeholder;
	 *  the band mounts into it, full-bleed — `--nar-left` (the column's
	 *  distance from the window's edge) and `--page-w` (the window without
	 *  its scrollbar) are measured here */
	let narrativeEl = $state<HTMLElement | null>(null);
	let narLeft = $state(0);
	let pageW = $state(0);
	$effect(() => {
		const el = narrativeEl;
		if (!el) return;
		const measure = () => {
			narLeft = el.getBoundingClientRect().left;
			pageW = document.documentElement.clientWidth;
		};
		measure();
		const ro = new ResizeObserver(measure);
		ro.observe(document.documentElement);
		const cols = el.parentElement;
		cols?.addEventListener('transitionend', measure);
		const tick = setInterval(measure, 700);
		return () => {
			ro.disconnect();
			cols?.removeEventListener('transitionend', measure);
			clearInterval(tick);
		};
	});
	$effect(() => {
		const host = narrativeEl?.querySelector<HTMLElement>('.chartmark[data-chart="state-funded"]');
		if (!host) return;
		const app = mount(ChartBand, { target: host, props: { c: data.cmp } });
		// no fading of the rail: the band sits ABOVE the rail in stacking and
		// simply slides over the sticky cards as the reader scrolls, the way
		// any content passes a sticky panel (a fade hid the cards at the very
		// moment they appeared, the band's top being 479 px down at the dock)
		return () => unmount(app);
	});

	/** only the footnotes of the paragraphs on screen, in document order */
	const shownNotes = $derived.by(() => {
		const out: {
			n: number;
			dist: number;
			sec: string;
			parts: { text: string; href?: string }[];
		}[] = [];
		for (const id of visList) {
			const b = BLOCKS[BLOCK_INDEX.get(id) ?? -1];
			if (!b) continue;
			const dist = Math.abs((BLOCK_INDEX.get(id) ?? 0) - Math.max(0, atBlock));
			for (const n of b.sups) {
				const e = NOTES.get(n);
				if (e) out.push({ n, dist, sec: b.section, parts: e.parts });
			}
		}
		return out.sort((a, b) => a.n - b.n);
	});
	/** the left block carries the INTRODUCTION's own notes only — a
	 *  chronology note peeking in at the bottom waits for the spread */
	const introNotes = $derived(shownNotes.filter((x) => x.sec === 'introduction'));

	/** EVERY note presents on the timeline column's lower part — where
	 *  notes 1 and 2 were shown (the author's switch, 2026-09-03); the
	 *  figure column keeps figures only. Collapsed, the intro's own notes
	 *  wait for stage 2; spread, the visible paragraphs' notes. */
	let railH = $state(0);
	let railW = $state(0);

	/** the timeline's FOCUS VIEW (the author, 2026-09-03): a click on the
	 *  rail opens the whole drawing, enlarged and centred, as the only thing
	 *  on the page; Esc, the ✕ or the margin closes it, a bullet closes it
	 *  and goes to the passage. The page behind keeps its scroll. */
	let tlOpen = $state(false);
	$effect(() => {
		if (!tlOpen) return;
		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') tlOpen = false;
		};
		window.addEventListener('keydown', onKey);
		const prev = document.body.style.overflow;
		document.body.style.overflow = 'hidden';
		return () => {
			window.removeEventListener('keydown', onKey);
			document.body.style.overflow = prev;
		};
	});
	const railNotes = $derived(
		!timelineOn ? [] : expanded ? shownNotes : introStage >= 2 ? introNotes : []
	);

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
	<div class="topsent" bind:this={topSentinel} aria-hidden="true"></div>
	{#if tlOpen}
		<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
		<div
			class="tlmodal"
			role="dialog"
			tabindex="-1"
			aria-label="the timeline"
			onclick={(e) => {
				if (e.target === e.currentTarget) tlOpen = false;
			}}
		>
			<button class="tlclose" type="button" aria-label="close the timeline" onclick={() => (tlOpen = false)}
				>✕</button
			>
			<!-- 130 % of the rail's width (the author, 2026-09-03): wider read
			     as disproportionate; this shows a bigger span of time at once -->
			<div class="tlbig" style:width={`${Math.round((railW || 500) * 1.3)}px`}>
				<StoryTimeline
					expanded
					whole
					maxK={2}
					{activeIds}
					onSelect={(ev) => {
						tlOpen = false;
						goToEvent(ev);
					}}
					note={timelineNote()}
				/>
			</div>
		</div>
	{/if}
	<div class="cols" class:centred={!timelineOn} class:solo={figureOff}>
		<!-- TIMELINE is a grid sibling sticky at the SAME height as the section
		     titles, so the two columns start aligned; it withdraws with its
		     rail once the reader leaves the chronology -->
		<h2 class="head tl-head" class:off={!timelineOn}>TIMELINE</h2>
		<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions, a11y_no_noninteractive_element_interactions -->
		<aside
			class="rail tl"
			class:off={!timelineOn}
			bind:clientHeight={railH}
			bind:clientWidth={railW}
			title="click to open the timeline"
			onclick={(e) => {
				// the footnotes under the drawing keep their own clicks (links)
				if (!(e.target as HTMLElement).closest('.tlnb')) tlOpen = true;
			}}
		>
			<StoryTimeline
				{expanded}
				{progress}
				{focusDates}
				{activeIds}
				onSelect={goToEvent}
				note={timelineNote()}
			/>
			{#if railNotes.length}
				<!-- the footnotes, on the timeline's lower part (the author) -->
				<div class="tlnb">
					<StoryNotes notes={railNotes} budget={(railH || 0) * 0.44} />
				</div>
			{/if}
		</aside>

		<div
			class="narrative"
			bind:this={narrativeEl}
			style:--nar-left={`${narLeft}px`}
			style:--page-w={pageW ? `${pageW}px` : null}
		>
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

		<aside class="rail fig" class:off={figureOff}>
			{#if kfAt > 0 || (kfAt === 0 && kfDocked)}
				{#key kfAt}
					<KeyFindings c={data.cmp} i={kfAt} />
				{/key}
			{:else if !figureOff && kfAt < 0}
				<!-- the methodology, bibliography and sources stand alone — no
				     figure beside them (author, 2026-09-04); and inside KEY FINDINGS
				     nothing shows before the cards dock — the chronology's last
				     figure used to be carried in (author's report, 2026-09-04);
				     the figure column keeps FIGURES only since the notes moved
				     left (2026-09-03) -->
				<StoryFigure {figure} notes={[]} stage={introStage} />
			{/if}
		</aside>
	</div>

	<!-- the page's bottom breathes: a paper band the columns stop short of;
	     its twin covers the strip between the header and the docked titles -->
	<div class="bband" aria-hidden="true"></div>
	<div class="tcover" aria-hidden="true"></div>
</div>

<style>
	.topsent {
		position: absolute;
		top: 0;
		left: 0;
		width: 1px;
		height: 1px;
	}
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
	   trims of 2026-09-02/03 down to the author's 556 — the half-frame
	   measure of the dataset pages — and its EQUAL 94 px gutters either
	   side. The fr values are
	   READ AS PIXELS AT 1920, which holds only while they sum to 1784 (the
	   content width inside the page margins) — keep that sum when retuning. */
	.cols {
		display: grid;
		grid-template-columns:
			minmax(0, 500fr) minmax(0, 94fr) minmax(0, 556fr)
			minmax(0, 94fr) minmax(0, 540fr);
		align-items: start; /* `stretch` would make the rails full-height and kill sticky */
		transition:
			grid-template-columns 0.6s cubic-bezier(0.2, 0.7, 0.2, 1),
			padding-right 0.6s cubic-bezier(0.2, 0.7, 0.2, 1);
	}
	/* once the timeline withdraws (methodology onward) the text and the
	   figure column CENTRE at the explore-more pages' 1152 px (the author,
	   2026-09-03): 556 + 56 + 540 = 1152, with 260+56 = 316 of whitespace
	   on the left and the same as padding on the right */
	.cols.centred {
		grid-template-columns:
			minmax(0, 260fr) minmax(0, 56fr) minmax(0, 556fr)
			minmax(0, 56fr) minmax(0, 540fr);
		padding-right: 17.713%; /* 316 / 1784 */
	}
	/* a section read ALONE (methodology, bibliography, sources — the author,
	   2026-09-04): the text column in the middle of the page, the rails'
	   tracks closed — 614 + 556 + 614 = 1784 */
	.cols.solo {
		grid-template-columns:
			minmax(0, 614fr) minmax(0, 0fr) minmax(0, 556fr)
			minmax(0, 0fr) minmax(0, 614fr);
		padding-right: 0;
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
	/* the timeline yields its lower part to the introduction's notes: the
	   drawing flexes above, the notes stack under it (the author, 2026-09-02) */
	.rail.tl {
		display: flex;
		flex-direction: column;
	}
	.rail.tl > :global(.tl) {
		height: auto;
		flex: 1 1 auto;
		min-height: 0;
	}
	.tlnb {
		flex: none;
		margin-top: var(--sp-4);
	}
	.rail.tl.off,
	.rail.fig.off {
		opacity: 0;
		pointer-events: none;
	}
	/* the full-width chart's place in the narrative: as wide as the window
	   (without its scrollbar), pulled left by the column's own offset; in
	   stacking ABOVE the rails (no z-index of their own) and BELOW the docked
	   section titles (z 3) and the TIMELINE head (5) */
	.narrative :global(.chartmark) {
		position: relative;
		z-index: 2;
		width: var(--page-w, 100vw);
		margin: var(--sp-6) 0 var(--sp-6) calc(-1 * var(--nar-left, 0px));
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
		/* a stacking context ABOVE the rails (which have none): the full-width
		   chart band inside it must paint over the sticky figure card, and the
		   rails come later in the DOM (2026-09-04) */
		position: relative;
		z-index: 1;
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

	/* the rail invites the click that opens the focus view */
	.rail.tl {
		cursor: zoom-in;
	}
	/* the timeline's FOCUS VIEW: the page's paper over everything, header
	   included, the whole drawing at 130 % of the rail's width, centred,
	   scrolling inside the view */
	.tlmodal {
		position: fixed;
		inset: 0;
		z-index: 300;
		background: var(--paper);
		overflow: auto;
		overscroll-behavior: contain;
		cursor: zoom-out;
	}
	.tlbig {
		max-width: 92vw;
		margin: 48px auto 64px;
		cursor: default;
	}
	.tlclose {
		position: fixed;
		top: 18px;
		right: 22px;
		z-index: 301;
		width: 40px;
		height: 40px;
		border: 0;
		border-radius: 50%;
		background: var(--ink);
		color: var(--paper);
		font-size: 18px;
		line-height: 1;
		cursor: pointer;
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
