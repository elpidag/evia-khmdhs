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
	 * The images themselves are still with the author; until they arrive the
	 * square names its figure — except where a LIVE figure exists for the
	 * number (`lib/story/figures.ts`, keyed by the author's own figure number):
	 * then the square mounts that drawing while its figure is in force, and
	 * the figure's credit line (imagery and data attributions) prints under
	 * the author's caption.
	 */
	import { FIGURES } from '$lib/story/figures';

	interface Props {
		figure: { n: number; name: string } | null;
		notes: { n: number; dist: number; parts: { text: string; href?: string }[] }[];
	}
	let { figure, notes }: Props = $props();

	const pad = (n: number) => String(n).padStart(2, '0');

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

<div class="fig">
	<div class="box">
		{#if figure}
			{#key figure.n}
				{@const live = FIGURES[figure.n]}
				{#if live}
					<live.component />
				{:else}
					<span class="ph">figure {pad(figure.n)} · {figure.name}</span>
				{/if}
			{/key}
		{/if}
	</div>
	<!-- the caption line the artboard writes under the image -->
	<div>
		<p class="cap">{figure ? `Figure ${pad(figure.n)} _ ${figure.name}` : ''}</p>
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
