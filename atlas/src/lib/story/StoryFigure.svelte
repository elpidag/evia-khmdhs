<script lang="ts">
	/**
	 * The story's right column — the author's Page01 artboard, FOLLOWING THE
	 * READER (their ruling, 2026-09-02): a square image slot showing the
	 * figure IN FORCE at the passage being read (it changes at the author's
	 * own `[FIGURE xx: name]` markers), the «Figure xx _ …» caption written
	 * under it, and under that ONLY the footnotes of the paragraphs currently
	 * on screen, in two columns behind a small «Footnote» label — never more
	 * than the screen's own notes, so nothing scrolls.
	 *
	 * A figure shows, in order of preference: its LIVE drawing
	 * (`lib/story/figures.ts`), the author's DELIVERED image(s)
	 * (`lib/story/figureImages.ts` — figure 01 as their 6×3 grid of 18
	 * filling the column, figure 02 as its a+b pair, the rest single), or
	 * the named placeholder square. For a LIVE figure
	 * (keyed by the author's own figure number):
	 * then the square mounts that drawing while its figure is in force, and
	 * the figure's credit line (imagery and data attributions) prints under
	 * the author's caption.
	 */
	import { FIGURES } from '$lib/story/figures';
	import { FIGURE_IMAGES } from '$lib/story/figureImages';

	interface Props {
		figure: { n: number; name: string } | null;
		notes: { n: number; dist: number; parts: { text: string; href?: string }[] }[];
		/** the introduction's staged reveal (the author, 2026-09-02): 0 = the
		 *  grid shows nothing yet, 1 = its first pack of nine at full width,
		 *  2 = all eighteen. Figures other than the grid ignore it. */
		stage?: number;
	}
	let { figure, notes, stage = 2 }: Props = $props();

	const pad = (n: number) => String(n).padStart(2, '0');
	/** the author's delivered image(s) for the figure in force, if any */
	const img = $derived(figure ? (FIGURE_IMAGES[figure.n] ?? null) : null);

	/**
	 * WHOLE NOTES ONLY, PACKED BY NOTE (the author, 2026-09-02; refit the
	 * same day after their «8 and 2» report): a note never breaks across the
	 * two columns — CSS `columns` split notes mid-sentence, which read badly.
	 * Every candidate is measured at column width in a hidden copy, admission
	 * is nearest-to-the-reading-line first by TRUE FIT (a note that cannot
	 * fit is skipped, never a reason to drop its neighbours), the packing
	 * preserves number order (one cut: left run, right run), and the
	 * READING paragraph's own notes, when they cannot all stack whole,
	 * go TOGETHER to ONE full-width flow that may scroll (the author's
	 * one-column ruling for text-heavy notes, 2026-09-02) — the only
	 * exception to no-scroll, because the alternative was notes that
	 * never appeared at all (5-7 total twice the block).
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
		// the same notes at FULL width — what the one-column spread will use
		const heightsWide = new Map<number, number>();
		if (measureWideEl) {
			[...measureWideEl.children].forEach((li, i) => {
				const nt = list[i];
				if (nt) heightsWide.set(nt.n, li.getBoundingClientRect().height + LI_MARGIN);
			});
		}
		// admit nearest-first, by TRUE FIT (the author's report, 2026-09-02:
		// the old farthest-drop cascaded one oversized note into an EMPTY
		// block): a candidate joins only if the admitted set plus it still
		// packs — one that cannot fit is SKIPPED, never a reason to drop
		// its neighbours. Packing preserves NUMBER ORDER: the admitted
		// notes, sorted by n, are cut ONCE — the first run reads down the
		// left stack, the rest down the right.
		const byNeed = [...list].sort((a, b) => a.dist - b.dist || a.n - b.n);
		const hOf = (n: number) => heights.get(n) ?? 0;
		const split = (
			set: number[],
			cap: number
		): { left: number[]; right: number[] } | null => {
			const seq = [...set].sort((a, b) => a - b);
			const hs = seq.map(hOf);
			for (let cut = 0; cut <= seq.length; cut++) {
				const hL = hs.slice(0, cut).reduce((s, x) => s + x, 0);
				const hR = hs.slice(cut).reduce((s, x) => s + x, 0);
				if (hL <= cap && hR <= cap) {
					return { left: seq.slice(0, cut), right: seq.slice(cut) };
				}
			}
			return null;
		};
		// the READING paragraph's own notes are a UNIT: when they cannot all
		// stack whole (one taller than a column, or an essay-sized pile like
		// notes 5-7 on one paragraph), they ALL go to the spread flow —
		// number order, two columns, scrolling inside that block alone —
		// because the alternative was notes that never appeared at all
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

<div class="fig" class:tall={img?.kind === 'grid'}>
	<div class="box" class:gridbox={img?.kind === 'grid'} class:pairbox={img?.kind === 'pair'}>
		{#if figure}
			{#key figure.n}
				{@const live = FIGURES[figure.n]}
				{#if live}
					<live.component />
				{:else if img?.kind === 'grid'}
					<!-- the author's 18 squares in packs of NINE (their ruling: the
					     second pack REPLACES the first, the full grid never shows):
					     3×3 at full width, centred on the column's height -->
					{#if stage >= 1}
						<div class="grid18">
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
					{#each img.srcs as src, pi (src)}
						<img class="half" {src} alt={`${figure.name} — ${pi + 1} of 2`} />
					{/each}
				{:else if img}
					<img class="whole" src={img.srcs[0]} alt={figure.name} />
				{:else}
					<span class="ph">figure {pad(figure.n)} · {figure.name}</span>
				{/if}
			{/key}
		{/if}
	</div>
	<!-- the caption line the artboard writes under the image; the grid's
	     packs carry the author's own wording, the range following the pack -->
	<div>
		<p class="cap">
			{#if figure && img?.kind === 'grid'}
				{#if stage >= 1}
					{stage < 2
						? 'Figures 1 to 9: Images from media coverage of fires in Greece.'
						: 'Figures 10 to 18: Images from fires worldwide.'}
					All images are credited to their corresponding authors <a href="#sources">here</a>.
				{/if}
			{:else}
				{figure ? `Figure ${pad(figure.n)} _ ${figure.name}` : ''}
			{/if}
		</p>
		{#if figure && FIGURES[figure.n]?.credit}
			<p class="credit">{FIGURES[figure.n].credit}</p>
		{/if}
	</div>
	{#if notes.length}
		<div class="fnblock" bind:clientHeight={availH} bind:clientWidth={availW}>
			{#if spreadNotes.length}
				<!-- the reading paragraph's notes when they cannot stack whole:
				     ONE full-width column, scrolling inside if it must -->
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
			<!-- two stacks packed BY NOTE — a note never splits across the gap;
			     numbers inline, each citation chunk a link to its URL -->
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
			<!-- the hidden measurers: every candidate at the stack column's
			     width, and once more at the block's full width for the spread -->
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
		display: grid;
		grid-template-rows: auto auto minmax(0, 1fr);
		row-gap: var(--sp-2); /* the caption sits close under the rectangle */
		width: 100%;
		height: 100%;
		/* caption and notes are set to the IMAGE's width, not the column's */
		--fig-w: min(100%, 540px);
	}
	/* no alignment tricks: the page grid gives this column exactly the
	   content's 540 px (the author, 2026-09-02), so image, caption and
	   notes share both edges and the right one sits on the page margin */
	.box {
		/* the artboard's square, inset in its column */
		width: var(--fig-w);
		aspect-ratio: 1;
		background: var(--paper-2);
		display: grid;
		place-items: center;
	}
	/* figure 01's grid takes the WHOLE column height (the author,
	   2026-09-02: its footnotes moved under the timeline to make the
	   room): square cells sized by the six rows, centred */
	.fig.tall {
		grid-template-rows: minmax(0, 1fr) auto auto;
	}
	.box.gridbox {
		aspect-ratio: auto;
		height: 100%;
		background: none;
		place-items: stretch;
		/* the grid overlays the box absolutely: a percentage height chained
		   through grid items never resolved (the grid grew to its content,
		   1.084 px over an 875 px box, and drew over the caption) */
		position: relative;
	}
	/* one pack of nine at a time: 3×3 at the column's full width — the
	   author's squares stay square (177 px, width-driven) — vertically
	   CENTRED on the column's height (the author, 2026-09-02) */
	.grid18 {
		position: absolute;
		inset: 0;
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		grid-auto-rows: max-content;
		align-content: center;
		gap: 4px;
	}
	.grid18 img {
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
	@media (prefers-reduced-motion: reduce) {
		.grid18 img {
			animation: none;
		}
	}
	/* figure 02's a + b side by side, each its own square */
	.box.pairbox {
		aspect-ratio: auto;
		grid-template-columns: 1fr 1fr;
		gap: 4px;
		background: none;
	}
	.box img.half {
		width: 100%;
		aspect-ratio: 1;
		object-fit: cover;
		display: block;
	}
	.box img.whole {
		width: 100%;
		height: 100%;
		object-fit: contain;
		display: block;
	}
	.cap {
		margin: 0;
		max-width: var(--fig-w);
		font-size: var(--fs-12);
		line-height: 1.35;
		color: var(--ink-soft);
		min-height: 1.35em;
	}
	/* the artboard's footnote block: a small «Footnote» label, then the notes
	   in TWO columns to the image's width, 12 px light. Only the visible
	   paragraphs' notes print, so the set stays short by construction. */
	.fnblock {
		position: relative; /* anchors the hidden measurer */
		max-width: var(--fig-w);
		min-height: 0;
		margin-top: var(--sp-3);
		overflow: hidden; /* backstop only — the fit keeps whole notes */
	}
	.measure {
		position: absolute;
		top: 0;
		left: 0;
		visibility: hidden;
		columns: auto;
		column-gap: 0;
	}
	.cols2 {
		display: grid;
		grid-template-columns: 1fr 1fr;
		column-gap: var(--sp-7);
		align-items: start;
	}
	/* the text-heavy state reads as ONE full-width column (the author,
	   2026-09-02) — no mid-sentence jump across a gap; it scrolls inside
	   only when even the whole block cannot hold it */
	.spread {
		overflow-y: auto;
		margin-bottom: var(--sp-2);
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
		/* the number hangs; long unbroken strings wrap inside the column */
		padding-left: 1.5em;
		text-indent: -1.5em;
		overflow-wrap: anywhere;
	}
	/* a note that carries its source: the whole text is the link */
	.notes a {
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

	@media (max-width: 1100px) {
		/* released: the rail becomes a plain block under the text */
		.fig {
			height: auto;
		}
	}
</style>
