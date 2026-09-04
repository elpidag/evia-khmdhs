<script lang="ts">
	/**
	 * The story's right column — the author's Page01 artboard, FOLLOWING THE
	 * READER: the figure IN FORCE at the passage being read (it changes at
	 * the author's own `[FIGURE xx: name]` markers) with the caption under it.
	 *
	 * The caption TEXT is the author's own `content/story/captions.md`
	 * (their request, 2026-09-03) — as long as they like, one entry per
	 * carousel slide where a figure has several images, falling back to the
	 * marker's short name where the file says nothing.
	 *
	 * ONE PLACEMENT FOR EVERY FIGURE (the author, 2026-09-03): the figure
	 * block sits on the column's vertical centre SET 60 PX LOWER, its caption
	 * 7 px below the image — grid, single, carousel, live drawing and the
	 * placeholder square alike. The one exception is a figure marked `lift`
	 * (figure 23, the same day): its block starts at the column's TOP, so a
	 * long caption gets the room below.
	 *
	 * A `slider` figure (figure 23's two land-use maps) shows both images at
	 * once — the second underneath, the first to the LEFT of a handle the
	 * reader drags across; a transparent range input under the pointer does
	 * the dragging, and gives the keyboard and touch for free.
	 *
	 * A figure shows, in order of preference: its LIVE drawing
	 * (`lib/story/figures.ts`), the author's DELIVERED image(s)
	 * (`lib/story/figureImages.ts` — figure 01 as packs of nine, figure 02 as
	 * a CAROUSEL with a small arrow, the rest single), or the named
	 * placeholder square. The footnotes moved to the timeline column
	 * (2026-09-03, `StoryNotes.svelte`); the packing machinery below lies
	 * DORMANT (`notes={[]}`), kept for any return.
	 */
	import { FIGURES } from '$lib/story/figures';
	import { FIGURE_IMAGES } from '$lib/story/figureImages';
	import { captionFor, figureLabel, renderCaption } from '$lib/story/captions';

	interface Props {
		figure: { n: number; name: string } | null;
		notes: { n: number; dist: number; parts: { text: string; href?: string }[] }[];
		/** the introduction's staged reveal (the author, 2026-09-02): 0 = the
		 *  grid shows nothing yet, 1 = its first pack of nine, 2 = the second
		 *  pack replacing it. Figures other than the grid ignore it. */
		stage?: number;
	}
	let { figure, notes, stage = 2 }: Props = $props();

	/** the author's delivered image(s) for the figure in force, if any */
	const img = $derived(figure ? (FIGURE_IMAGES[figure.n] ?? null) : null);
	/** NO WHITE FILLER (the author, 2026-09-03): an image box is the image's
	 *  own size — never the artboard's square with paper around a landscape —
	 *  so the caption sits 7 px under the image itself; a live figure may
	 *  ask the same (`frame: 'auto'`); the grid and the placeholder keep
	 *  their shapes */
	const natural = $derived(
		img ? img.kind !== 'grid' : Boolean(figure && FIGURES[figure.n]?.frame === 'auto')
	);

	/** the carousel's position — back to the first image on a figure change */
	let pairIdx = $state(0);
	/** the slider's handle, as a percentage of the width from the left */
	let split = $state(50);
	/** the slider ENLARGED and centred, the only thing on the page — the
	 *  timeline's focus view for a figure (the author, 2026-09-04); the
	 *  handle is shared, so the reader continues where they were */
	let figOpen = $state(false);
	/** the enlarged view is PORTALED to <body>: inside the sticky rail's own
	 *  stacking context it could never cover the header. Svelte delegates
	 *  click and input from the app's root, which a node moved to <body> no
	 *  longer bubbles through — so the action wires the two itself. */
	function portal(node: HTMLElement, h: { close: () => void; split: (v: number) => void }) {
		document.body.appendChild(node);
		const onClick = (e: MouseEvent) => {
			const t = e.target as HTMLElement;
			if (t === node || t.closest('.figclose')) h.close();
		};
		const onInput = (e: Event) => {
			const t = e.target as HTMLInputElement;
			if (t.classList.contains('range')) h.split(Number(t.value));
		};
		node.addEventListener('click', onClick);
		node.addEventListener('input', onInput);
		return {
			destroy() {
				node.removeEventListener('click', onClick);
				node.removeEventListener('input', onInput);
				node.remove();
			}
		};
	}
	$effect(() => {
		if (!figOpen) return;
		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') figOpen = false;
		};
		window.addEventListener('keydown', onKey);
		const prev = document.body.style.overflow;
		document.body.style.overflow = 'hidden';
		return () => {
			window.removeEventListener('keydown', onKey);
			document.body.style.overflow = prev;
		};
	});
	const lifted = $derived(Boolean(img?.lift));
	/** which image of a multi-image figure is showing: a, b, … — the letter
	 *  the captions file keys a slide's own caption by (the grid's two packs
	 *  count the same way) */
	const slot = $derived(
		img?.kind === 'grid'
			? stage < 2
				? 'a'
				: 'b'
			: img?.kind === 'pair'
				? String.fromCharCode(97 + pairIdx)
				: undefined
	);
	/** the caption's paragraphs: the author's own text, else the marker's name */
	const caption = $derived.by(() => {
		if (!figure) return [] as string[];
		const own = captionFor(figure.n, slot);
		if (own) return own;
		return figure.name ? [figure.name] : [];
	});
	/** the grid's captions name their own figure range, so they take no
	 *  «Figure NN _ » prefix; every other figure does — and a carousel's
	 *  prefix carries the letter of the image on show, «Figure 19a _ »,
	 *  «Figure 19b _ », following the reader through the arrow (the user,
	 *  2026-09-03). The displayed number itself is `figureLabel`'s rule. */
	const prefix = $derived(
		figure && img?.kind !== 'grid'
			? `Figure ${figureLabel(figure.n, img?.kind === 'pair' ? slot : undefined)} _ `
			: ''
	);
	$effect(() => {
		void figure?.n;
		pairIdx = 0;
		split = 50;
		figOpen = false;
	});

	/**
	 * A caption too long for the page SCROLLS INSIDE ITSELF; one that fits
	 * shows no scroll (the user, 2026-09-03 — figure 23's caption ran off
	 * the column). The block keeps its one placement — centred CENTRE_DROP
	 * px low — so the room a caption may take is what is left between the
	 * block's bottom and the column's: the column's height less twice the
	 * drop (the block's centre sits that far below the column's), the
	 * image, the gap under it and a live figure's credit line. Measured
	 * live, so a window resize or a taller image re-fits it.
	 */
	const CENTRE_DROP = 60; // the .stack transform below
	const CAP_GAP = 7; // .cap margin-top
	const CREDIT_GAP = 2; // .credit margin-top
	const CAP_MIN = 34; // two lines at fs-12/1.35: never less than that
	let stackH = $state(0);
	let boxH = $state(0);
	let creditH = $state(0);
	const hasCredit = $derived(Boolean(figure && FIGURES[figure.n]?.credit));
	const capMax = $derived.by(() => {
		if (!stackH || !boxH) return null;
		// a lifted block starts at the top: the whole column below the image
		const drop = lifted ? 0 : CENTRE_DROP;
		const room = stackH - 2 * drop - boxH - CAP_GAP - (hasCredit ? creditH + CREDIT_GAP : 0);
		return Math.max(CAP_MIN, Math.floor(room));
	});
	/** the caption's text at its natural height — the scroll switches on
	 *  ONLY when that exceeds the room. (`overflow: auto` alone grew a bar
	 *  under a two-line caption that fit: 16,2 px lines make a 32,4 px
	 *  block, and Chrome's rounding read it as overflowing itself.) */
	let capH = $state(0);
	const scrolls = $derived(capMax !== null && capH > capMax);

	/**
	 * WHOLE NOTES ONLY, PACKED BY NOTE — the fitting machinery of the
	 * one-time figure-column footnotes; dormant since the notes moved to the
	 * timeline column (`StoryNotes.svelte` carries the same logic there).
	 */
	const GAP = 28; // --sp-7, the column gap
	const LI_MARGIN = 8; // --sp-2, under each note
	let availH = $state(0);
	let availW = $state(0);
	let measureEl = $state<HTMLUListElement | null>(null);
	let measureWideEl = $state<HTMLUListElement | null>(null);
	let packed = $state<{
		left: number[];
		right: number[];
		spread: number[];
		spreadH: number;
	} | null>(null);
	const colW = $derived(Math.max(80, (availW - GAP) / 2));
	$effect(() => {
		const el = measureEl;
		const H = availH;
		const list = notes;
		void colW; // re-measure when the column width changes
		if (!el || !H || !list.length) {
			packed = null;
			return;
		}
		const heights = new Map<number, number>();
		[...el.children].forEach((li, i) => {
			const nt = list[i];
			if (nt) heights.set(nt.n, li.getBoundingClientRect().height + LI_MARGIN);
		});
		const heightsWide = new Map<number, number>();
		if (measureWideEl) {
			[...measureWideEl.children].forEach((li, i) => {
				const nt = list[i];
				if (nt) heightsWide.set(nt.n, li.getBoundingClientRect().height + LI_MARGIN);
			});
		}
		const byNeed = [...list].sort((a, b) => a.dist - b.dist || a.n - b.n);
		const hOf = (n: number) => heights.get(n) ?? 0;
		const split = (set: number[], cap: number): { left: number[]; right: number[] } | null => {
			const seq = [...set].sort((a, b) => a - b);
			const hs = seq.map(hOf);
			// the LARGEST left run that fits: the left column fills first — the
			// author's screenshot had a lone note parked right with the left
			// empty, because the empty-left cut was tried first (2026-09-03)
			for (let cut = seq.length; cut >= 0; cut--) {
				const hL = hs.slice(0, cut).reduce((s, x) => s + x, 0);
				const hR = hs.slice(cut).reduce((s, x) => s + x, 0);
				if (hL <= cap && hR <= cap) {
					return { left: seq.slice(0, cut), right: seq.slice(cut) };
				}
			}
			return null;
		};
		let spread: number[] = [];
		let spreadH = 0;
		let stackH = H;
		const minDist = byNeed.length ? byNeed[0].dist : 0;
		const actives = list.filter((nt) => nt.dist === minDist).map((nt) => nt.n);
		if (actives.length && !split(actives, H)) {
			spread = [...actives].sort((a, b) => a - b);
			const tot = spread.reduce(
				(s, n) => s + (heightsWide.get(n) ?? Math.ceil(hOf(n) / 2) + 12),
				0
			);
			spreadH = Math.min(H, tot + 4);
			stackH = Math.max(0, H - spreadH - LI_MARGIN);
		}
		let best: { left: number[]; right: number[] } = { left: [], right: [] };
		const taken: number[] = [];
		for (const nt of byNeed) {
			if (spread.includes(nt.n)) continue;
			const attempt = split([...taken, nt.n], stackH);
			if (attempt) {
				taken.push(nt.n);
				best = attempt;
			}
		}
		packed = { left: best.left, right: best.right, spread, spreadH };
	});
	const columns = $derived.by(() => {
		const p = packed;
		if (!p) return [notes, [] as typeof notes];
		const pick = (ns: number[]) => ns.map((n) => notes.find((nt) => nt.n === n)!).filter(Boolean);
		return [pick(p.left), pick(p.right)];
	});
	const spreadNotes = $derived(
		(packed?.spread ?? []).map((n) => notes.find((nt) => nt.n === n)!).filter(Boolean)
	);
</script>

{#snippet sliderBlock(srcs: string[], name: string, big: boolean)}
	<div class="slider" style:--split="{split}%">
		<img class="whole under" src={srcs[1]} alt={`${name} — second of two`} />
		<img class="whole over" src={srcs[0]} alt={`${name} — first of two`} />
		<div class="knife" aria-hidden="true"><span>‹›</span></div>
		<input
			class="range"
			type="range"
			min="0"
			max="100"
			step="0.5"
			value={split}
			oninput={(e) => (split = Number(e.currentTarget.value))}
			aria-label="drag to compare the two maps"
		/>
		{#if !big}
			<button class="grow" type="button" aria-label="enlarge" onclick={() => (figOpen = true)}
				>⤢</button
			>
		{/if}
	</div>
{/snippet}

<div class="fig">
	{#if figOpen && img?.kind === 'slider' && figure}
		<!-- the slider ENLARGED and centred, the only thing on the page; the
		     margin, the ✕ or Esc closes it (the author, 2026-09-04) -->
		<div
			class="figmodal"
			role="dialog"
			tabindex="-1"
			aria-label={`figure ${figureLabel(figure.n)} enlarged`}
			use:portal={{ close: () => (figOpen = false), split: (v) => (split = v) }}
		>
			<button class="figclose" type="button" aria-label="close">✕</button>
			<div class="figbig">{@render sliderBlock(img.srcs, figure.name, true)}</div>
		</div>
	{/if}
	<!-- every figure on ONE placement: centred 60 px low, caption 7 px under -->
	<div class="stack" class:lifted style:--img-scale={img?.scale ?? null} bind:clientHeight={stackH}>
		<div class="box" class:gridbox={img?.kind === 'grid'} class:natural bind:clientHeight={boxH}>
			{#if figure}
				{#key figure.n}
					{@const live = FIGURES[figure.n]}
					{#if live}
						<live.component />
					{:else if img?.kind === 'grid'}
						<!-- the author's 18 squares in packs of NINE (the second pack
						     REPLACES the first; the full grid never shows) -->
						{#if stage >= 1}
							<div class="cells">
								{#each img.srcs.slice(stage < 2 ? 0 : 9, stage < 2 ? 9 : 18) as src, gi (src)}
									<img
										{src}
										alt={`${figure.name} — ${(stage < 2 ? 1 : 10) + gi} of ${img.srcs.length}`}
										loading="lazy"
									/>
								{/each}
							</div>
						{/if}
					{:else if img?.kind === 'pair'}
						<!-- figure 02 as a CAROUSEL: one image at a time, a small
						     arrow to interchange (the author, 2026-09-03) -->
						<div class="carousel">
							{#key pairIdx}
								<img
									class="whole"
									src={img.srcs[pairIdx]}
									alt={`${figure.name} — ${pairIdx + 1} of ${img.srcs.length}`}
								/>
							{/key}
							<button
								class="adv"
								type="button"
								aria-label="next image"
								onclick={() => (pairIdx = (pairIdx + 1) % (img?.srcs.length ?? 1))}>›</button
							>
							<div class="dots" aria-hidden="true">
								{#each img.srcs as _, di (di)}
									<span class:on={di === pairIdx}></span>
								{/each}
							</div>
						</div>
					{:else if img?.kind === 'slider'}
						<!-- figure 23's two maps as an IMAGE SLIDER (the author,
						     2026-09-03): the second map underneath, the first shown
						     LEFT of the handle; the corner button opens it enlarged -->
						{@render sliderBlock(img.srcs, figure.name, false)}
					{:else if img}
						<img class="whole" src={img.srcs[0]} alt={figure.name} />
					{:else}
						<span class="ph">figure {figureLabel(figure.n)} · {figure.name}</span>
					{/if}
				{/key}
			{/if}
		</div>
		<div class="cap" class:scrolls style:max-height={scrolls ? `${capMax}px` : null}>
			<div class="capin" bind:clientHeight={capH}>
				{#if figure && !(img?.kind === 'grid' && stage < 1)}
					{#each caption as para, i (i)}
						<p>{#if i === 0}{prefix}{/if}{@html renderCaption(para)}</p>
					{/each}
				{/if}
			</div>
		</div>
		{#if figure && FIGURES[figure.n]?.credit}
			<p class="credit" bind:clientHeight={creditH}>{FIGURES[figure.n].credit}</p>
		{/if}
	</div>
	{#if notes.length}
		<div class="fnblock" bind:clientHeight={availH} bind:clientWidth={availW}>
			{#if spreadNotes.length}
				<ul class="notes spread" style:height={`${packed?.spreadH ?? 0}px`}>
					{#each spreadNotes as sn (sn.n)}
						<li>{sn.n}.
							{#each sn.parts as p, i (i)}{#if p.href}<a
										href={p.href}
										target="_blank"
										rel="noopener">{p.text}</a
									>{:else}{p.text}{/if}{/each}
						</li>
					{/each}
				</ul>
			{/if}
			<div class="cols2">
				{#each columns as col, c (c)}
					<ul class="notes">
						{#each col as n (n.n)}
							<li>{n.n}.
								{#each n.parts as p, i (i)}{#if p.href}<a href={p.href} target="_blank" rel="noopener"
										>{p.text}</a
									>{:else}{p.text}{/if}{/each}
							</li>
						{/each}
					</ul>
				{/each}
			</div>
			<ul class="notes measure" bind:this={measureEl} style:width={`${colW}px`} aria-hidden="true">
				{#each notes as n (n.n)}
					<li>{n.n}.
						{#each n.parts as p, i (i)}{#if p.href}<a href={p.href}>{p.text}</a>{:else}{p.text}{/if}{/each}
					</li>
				{/each}
			</ul>
			<ul class="notes measure" bind:this={measureWideEl} aria-hidden="true">
				{#each notes as n (n.n)}
					<li>{n.n}.
						{#each n.parts as p, i (i)}{#if p.href}<a href={p.href}>{p.text}</a>{:else}{p.text}{/if}{/each}
					</li>
				{/each}
			</ul>
		</div>
	{/if}
</div>

<style>
	.fig {
		position: relative;
		width: 100%;
		height: 100%;
		/* caption and notes are set to the IMAGE's width, not the column's */
		--fig-w: min(100%, 540px);
	}
	/* the one placement (the author, 2026-09-03): the block rides the
	   column's vertical centre 60 px LOW, the caption 7 px under the image */
	.stack {
		position: absolute;
		inset: 0;
		display: flex;
		flex-direction: column;
		justify-content: center;
		transform: translateY(60px);
	}
	/* a lifted figure starts at the column's top (figure 23: the caption
	   needs the room below — the author, 2026-09-03) */
	.stack.lifted {
		justify-content: flex-start;
		transform: none;
	}
	.box {
		/* the artboard's square, inset in its column — PAPER behind it, so a
		   non-square image sits in white, never in grey bars (author,
		   2026-09-03) */
		width: var(--fig-w);
		aspect-ratio: 1;
		background: var(--paper);
		display: grid;
		place-items: center;
		position: relative;
	}
	.box.gridbox {
		aspect-ratio: auto;
		background: none;
	}
	/* an image box is the image's own size: the image shrinks into the
	   540 square keeping its shape, and the box wraps it — no paper bars */
	.box.natural {
		aspect-ratio: auto;
		/* a FLEX column, not the grid: a grid item's percentage max-width
		   resolved against its own centred area (a 0.85 scale drew as 0.85
		   squared, in a box taller than its image); in a flex column the
		   percentage is the slot's width, and the box is exactly the image */
		display: flex;
		flex-direction: column;
		align-items: center;
	}
	.box.natural img.whole {
		width: auto;
		height: auto;
		max-width: calc(100% * var(--img-scale, 1));
		/* the artboard's square as the height cap, in px: a percentage
		   height against an auto-height box would resolve to nothing */
		max-height: calc(540px * var(--img-scale, 1));
	}
	.carousel {
		position: relative;
		width: fit-content;
		max-width: 100%;
	}
	.cells {
		width: 100%;
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		grid-auto-rows: max-content;
		gap: 4px;
	}
	.cells img {
		width: 100%;
		height: auto;
		aspect-ratio: 1;
		object-fit: cover;
		display: block;
		animation: figfade 0.45s ease;
	}
	@keyframes figfade {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}
	.box img.whole {
		width: 100%;
		height: 100%;
		object-fit: contain;
		display: block;
		animation: figfade 0.45s ease;
	}
	/* the image slider: both maps fill the square, the first clipped to the
	   left of the handle; the range input lies invisible over the whole
	   square so a press anywhere takes the handle there and drags it */
	.slider {
		position: relative;
		width: fit-content;
		max-width: 100%;
	}
	.slider img.under {
		display: block;
	}
	.slider img.over {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		clip-path: inset(0 calc(100% - var(--split)) 0 0);
	}
	.knife {
		position: absolute;
		top: 0;
		bottom: 0;
		left: var(--split);
		width: 0;
		border-left: 2px solid rgba(0, 0, 0, 0.62);
		transform: translateX(-1px);
		pointer-events: none;
	}
	.knife span {
		position: absolute;
		top: 50%;
		left: 0;
		transform: translate(-50%, -50%);
		width: 30px;
		height: 30px;
		border-radius: 50%;
		background: rgba(0, 0, 0, 0.62);
		color: #fff;
		font-size: 15px;
		line-height: 30px;
		text-align: center;
		letter-spacing: 1px;
	}
	.slider:focus-within .knife {
		border-color: rgba(0, 0, 0, 0.85);
	}
	.slider:focus-within .knife span {
		background: rgba(0, 0, 0, 0.85);
	}
	.range {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		margin: 0;
		opacity: 0;
		cursor: ew-resize;
	}
	/* the corner button that opens the slider enlarged — above the range
	   input, in the carousel arrow's dress */
	.grow {
		position: absolute;
		top: 8px;
		right: 8px;
		width: 30px;
		height: 30px;
		border: 0;
		border-radius: 50%;
		background: rgba(0, 0, 0, 0.62);
		color: #fff;
		font-size: 16px;
		line-height: 1;
		cursor: zoom-in;
		display: grid;
		place-items: center;
		padding: 0;
	}
	.grow:hover {
		background: rgba(0, 0, 0, 0.85);
	}
	/* the enlarged view: the page's paper over everything, header
	   included, the slider centred at the window's size */
	.figmodal {
		position: fixed;
		inset: 0;
		z-index: 300;
		background: var(--paper);
		display: grid;
		place-items: center;
		cursor: zoom-out;
	}
	.figbig {
		cursor: default;
	}
	.figbig .slider img.under {
		width: auto;
		height: auto;
		max-width: 92vw;
		max-height: 88vh;
	}
	.figclose {
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
	/* the carousel's small arrow, riding the image's right edge — dark, so
	   it reads on the author's white map images (2026-09-03) */
	.adv {
		position: absolute;
		right: 8px;
		top: 50%;
		transform: translateY(-50%);
		width: 30px;
		height: 30px;
		border: 0;
		border-radius: 50%;
		background: rgba(0, 0, 0, 0.62);
		color: #fff;
		font-size: 20px;
		line-height: 1;
		cursor: pointer;
		display: grid;
		place-items: center;
		padding: 0 0 3px;
	}
	.adv:hover {
		background: rgba(0, 0, 0, 0.85);
	}
	/* which of the pack is on show */
	.dots {
		position: absolute;
		bottom: 8px;
		left: 50%;
		transform: translateX(-50%);
		display: flex;
		gap: 6px;
	}
	.dots span {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background: rgba(0, 0, 0, 0.25);
	}
	.dots span.on {
		background: rgba(0, 0, 0, 0.8);
	}
	.cap {
		margin: 7px 0 0;
		/* a scaled image's caption is no wider than the image, and sits
		   under it (the author, 2026-09-03, on figure 25) */
		width: calc(var(--fig-w) * var(--img-scale, 1));
		max-width: var(--fig-w);
		align-self: center;
		font-size: var(--fs-12);
		line-height: 1.35;
		color: var(--ink-soft);
		min-height: 1.35em;
	}
	/* a caption longer than its room scrolls inside itself (max-height set
	   inline from the measured room); one that fits is never a scroller —
	   and the wheel never runs on into the page from the caption's end */
	.cap.scrolls {
		overflow-y: auto;
		overscroll-behavior: contain;
		scrollbar-width: thin;
	}
	/* an extensive caption may run to several paragraphs (the author writes
	   them as blank lines in captions.md) */
	.cap p {
		margin: 0;
	}
	.cap p + p {
		margin-top: 0.5em;
	}
	/* the caption's links come from the author's markdown through {@html},
	   so the selector must reach past Svelte's scoping */
	.cap :global(a) {
		color: inherit;
		text-decoration: underline;
		text-underline-offset: 2px;
		text-decoration-thickness: 0.5px;
	}
	.ph {
		font-size: var(--fs-12);
		color: var(--ink-faint);
	}
	/* a live figure's attributions, under the author's caption */
	.credit {
		margin: 2px 0 0;
		max-width: var(--fig-w);
		font-size: 10px;
		line-height: 1.3;
		color: var(--ink-faint);
	}

	/* ── the dormant footnote block (the notes live on the timeline column
	      since 2026-09-03; `notes={[]}` keeps this unrendered) ── */
	.fnblock {
		position: relative;
		max-width: var(--fig-w);
		min-height: 0;
		margin-top: var(--sp-3);
		overflow: hidden;
	}
	.spread {
		overflow-y: auto;
		margin-bottom: var(--sp-2);
	}
	.measure {
		position: absolute;
		top: 0;
		left: 0;
		visibility: hidden;
	}
	.cols2 {
		display: grid;
		grid-template-columns: 1fr 1fr;
		column-gap: var(--sp-7);
		align-items: start;
	}
	.notes {
		margin: 0;
		padding-left: 0;
		list-style: none;
		font-size: var(--fs-12);
		line-height: 1.3;
		font-weight: 300;
		color: var(--ink-soft);
	}
	.notes li {
		margin-bottom: var(--sp-2);
		padding-left: 1.5em;
		text-indent: -1.5em;
		overflow-wrap: anywhere;
	}
	.notes a {
		color: inherit;
		text-decoration: underline;
		text-underline-offset: 2px;
		text-decoration-thickness: 0.5px;
	}
</style>
