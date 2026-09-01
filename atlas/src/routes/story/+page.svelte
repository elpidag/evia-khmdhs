<script lang="ts">
	/**
	 * THE STORY — the scroll behind START HERE, rebuilt to the author's two
	 * artboards (2026-09-01). Three columns: the TIMELINE on the left, the
	 * NARRATIVE in the middle, and on the right the IMAGE with its caption and
	 * the passage's FOOTNOTES. The chapter strip is gone; the heading row names
	 * the chapter the reader is in, and the timeline is the navigation.
	 *
	 * PHASE 1 is the shell: the columns at the artboard's geometry, the scroll
	 * wiring, and the timeline's structure with no events on it. The passages
	 * are still the ten chapter placeholders; the author's own text, its
	 * footnotes, the images and the timeline's events come next.
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
	import StoryFigure, { type FigureBlock } from '$lib/story/StoryFigure.svelte';
	import { createSteps } from '$lib/story/steps';
	import type { Component } from 'svelte';
	import type { PageData } from './$types';
	import RefreshLine from '$lib/ui/RefreshLine.svelte';

	let { data }: { data: PageData } = $props();

	// every chapter's markdown, by id — a missing file is an empty chapter
	const texts = import.meta.glob('/src/content/story/*.md', {
		eager: true,
		import: 'default'
	}) as Record<string, Component>;
	const textOf = (id: string): Component | null => texts[`/src/content/story/${id}.md`] ?? null;

	// Phase 1: a chapter stands in for a beat, so nothing breaks while the
	// author writes. Phase 3 replaces this with their own marked passages.
	const BEATS = CHAPTERS;
	const IDS = BEATS.map((b) => b.id);
	const INDEX = new Map(IDS.map((id, i) => [id, i]));

	let active = $state<string | null>(null);
	const steps = createSteps({ order: IDS, onActive: (id) => (active = id) });
	$effect(() => () => steps.stop());

	/** the chapter printed over the middle column, in place of the old strip */
	const here = $derived(BEATS.find((b) => b.id === active) ?? BEATS[0]);

	/**
	 * The timeline spreads once the reader's text reaches the first dated event.
	 * With no events yet, the second passage stands in for that moment so the
	 * movement can be judged.
	 */
	const EXPAND_AT = 1;
	const expanded = $derived((active ? (INDEX.get(active) ?? -1) : -1) >= EXPAND_AT);

	const blocks: FigureBlock[] = BEATS.map((b, i) => ({
		id: b.id,
		caption: `Figure ${String(i + 1).padStart(2, '0')} — the picture for ${b.title.toLowerCase()}`,
		notes: [
			{ n: i * 2 + 1, text: 'The footnotes of this passage will print here, in two columns.' },
			{ n: i * 2 + 2, text: 'They arrive with the text, and follow the reader down the page.' }
		]
	}));
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
			<StoryTimeline {expanded} />
		</aside>

		<div class="narrative">
			{#each BEATS as b (b.id)}
				<section class="beat" id={b.id} use:steps.step={b.id}>
					<!-- the chapter is named ONCE, by the heading row above the column
					     (the artboard prints it there, not again over the text) -->
					<Prose hint={`atlas/src/content/story/${b.id}.md`}>
						{@const Text = textOf(b.id)}
						{#if Text}<Text />{/if}
					</Prose>
					{#if b.id === 'findings'}
						<p class="note">
							The KEY FINDINGS charts stay below for now; they move into the right column, at its
							width, with your own text beside them.
						</p>
					{/if}
				</section>
			{/each}
			<RefreshLine />
		</div>

		<aside class="rail fig">
			<StoryFigure {blocks} {active}>
				{#snippet placeholder(b: FigureBlock)}
					<span class="ph">image · {b.id}</span>
				{/snippet}
			</StoryFigure>
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
		top: var(--header-h, 85px);
		z-index: 4;
		background: var(--paper);
		padding-bottom: var(--sp-2);
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
		top: calc(var(--header-h, 85px) + 3.2rem);
		height: calc(100dvh - var(--header-h, 85px) - 3.2rem - var(--story-pad-b, 20px));
		overflow: hidden;
	}
	.tl {
		grid-column: 1;
	}
	.fig {
		grid-column: 5;
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
		/* PHASE 1 ONLY: the author's passages are many paragraphs each, so a
		   beat fills most of a screen. The placeholders are one line, and
		   without this the whole story fits above the reading line and the
		   timeline can never be seen collapsed. The real text removes it. */
		min-height: 62vh;
	}
	.note {
		margin: var(--sp-4) 0 0;
		font-size: var(--fs-13);
		color: var(--ink-faint);
	}
	.ph {
		font-size: var(--fs-12);
		color: var(--ink-faint);
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
