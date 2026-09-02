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
	 * WHOLE NOTES ONLY, PACKED BY NOTE (the author, 2026-09-02): the block
	 * never cuts a word, and a note never breaks across the two columns — CSS
	 * `columns` split notes mid-sentence, which is what read so badly. Every
	 * candidate is measured at column width in a hidden copy; notes are
	 * admitted nearest-to-the-reading-line first, then PACKED in number order
	 * into the left stack while it has room, then the right; if the packing
	 * overflows, the farthest admitted note is dropped and the pack rerun. A
	 * note that does not fit waits until scrolling gives it room.
	 */
	const GAP = 28; // --sp-7, the column gap
	const LI_MARGIN = 8; // --sp-2, under each note
	let availH = $state(0);
	let availW = $state(0);
	let measureEl = $state<HTMLUListElement | null>(null);
	let packed = $state<{ left: number[]; right: number[] } | null>(null);
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
		// admit nearest-first while twice the column height lasts …
		const byNeed = [...list].sort((a, b) => a.dist - b.dist || a.n - b.n);
		const admitted = new Set<number>();
		let used = 0;
		for (const nt of byNeed) {
			const hh = heights.get(nt.n) ?? 0;
			if (used + hh <= 2 * H) {
				admitted.add(nt.n);
				used += hh;
			}
		}
		// … then pack whole notes in number order: left stack, then right;
		// an overflow drops the farthest admitted note and packs again
		for (let guard = 0; guard < list.length + 1; guard++) {
			const left: number[] = [];
			const right: number[] = [];
			let hL = 0;
			let hR = 0;
			let overflow = false;
			for (const nt of list) {
				if (!admitted.has(nt.n)) continue;
				const hh = heights.get(nt.n) ?? 0;
				if (hL + hh <= H) {
					left.push(nt.n);
					hL += hh;
				} else if (hR + hh <= H) {
					right.push(nt.n);
					hR += hh;
				} else {
					overflow = true;
					break;
				}
			}
			if (!overflow) {
				packed = { left, right };
				return;
			}
			const drop = [...byNeed].reverse().find((nt) => admitted.has(nt.n));
			if (!drop) break;
			admitted.delete(drop.n);
		}
		packed = { left: [], right: [] };
	});
	const columns = $derived.by(() => {
		const p = packed;
		if (!p) return [notes, [] as typeof notes];
		const pick = (ns: number[]) => ns.map((n) => notes.find((nt) => nt.n === n)!).filter(Boolean);
		return [pick(p.left), pick(p.right)];
	});
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
			<!-- the hidden measurer: every candidate at the column's width -->
			<ul class="notes measure" bind:this={measureEl} style:width={`${colW}px`} aria-hidden="true">
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
