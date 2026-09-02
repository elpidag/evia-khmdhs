<script lang="ts">
	/**
	 * The story's right column — the author's Page01 artboard, FOLLOWING THE
	 * READER: the figure IN FORCE at the passage being read (it changes at
	 * the author's own `[FIGURE xx: name]` markers) with the caption under it.
	 *
	 * ONE PLACEMENT FOR EVERY FIGURE (the author, 2026-09-03): the figure
	 * block sits on the column's vertical centre SET 60 PX LOWER, its caption
	 * 7 px below the image — grid, single, carousel, live drawing and the
	 * placeholder square alike.
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

	interface Props {
		figure: { n: number; name: string } | null;
		notes: { n: number; dist: number; parts: { text: string; href?: string }[] }[];
		/** the introduction's staged reveal (the author, 2026-09-02): 0 = the
		 *  grid shows nothing yet, 1 = its first pack of nine, 2 = the second
		 *  pack replacing it. Figures other than the grid ignore it. */
		stage?: number;
	}
	let { figure, notes, stage = 2 }: Props = $props();

	const pad = (n: number) => String(n).padStart(2, '0');
	/** the DISPLAYED figure number (the author, 2026-09-03): the grid's 18
	 *  images are figures 1-18, so every later figure prints its marker
	 *  number + 17 — marker 02 shows as Figure 19, marker 13 as Figure 30.
	 *  The author's own [FIGURE xx] markers keep their numbering. */
	const dispN = (n: number) => n + 17;
	/** the author's delivered image(s) for the figure in force, if any */
	const img = $derived(figure ? (FIGURE_IMAGES[figure.n] ?? null) : null);

	/** the carousel's position — back to the first image on a figure change */
	let pairIdx = $state(0);
	$effect(() => {
		void figure?.n;
		pairIdx = 0;
	});

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

<div class="fig">
	<!-- every figure on ONE placement: centred 60 px low, caption 7 px under -->
	<div class="stack">
		<div class="box" class:gridbox={img?.kind === 'grid'}>
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
					{:else if img}
						<img class="whole" src={img.srcs[0]} alt={figure.name} />
					{:else}
						<span class="ph">figure {pad(dispN(figure.n))} · {figure.name}</span>
					{/if}
				{/key}
			{/if}
		</div>
		<p class="cap">
			{#if figure && img?.kind === 'grid'}
				{#if stage >= 1}
					{stage < 2
						? 'Figures 1 to 9: Images from media coverage of fires in Greece.'
						: 'Figures 10 to 18: Images from fires worldwide.'}
					All images are credited to their corresponding authors <a href="#sources">here</a>.
				{/if}
			{:else if figure}
				{`Figure ${pad(dispN(figure.n))} _ ${figure.name}`}
			{/if}
		</p>
		{#if figure && FIGURES[figure.n]?.credit}
			<p class="credit">{FIGURES[figure.n].credit}</p>
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
	.box {
		/* the artboard's square, inset in its column */
		width: var(--fig-w);
		aspect-ratio: 1;
		background: var(--paper-2);
		display: grid;
		place-items: center;
		position: relative;
	}
	.box.gridbox {
		aspect-ratio: auto;
		background: none;
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
		max-width: var(--fig-w);
		font-size: var(--fs-12);
		line-height: 1.35;
		color: var(--ink-soft);
		min-height: 1.35em;
	}
	.cap a {
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
