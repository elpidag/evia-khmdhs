<script lang="ts">
	/**
	 * The story's footnotes, on the LOWER PART OF THE TIMELINE COLUMN — the
	 * author's switch of 2026-09-03: every note presents where notes 1 and 2
	 * were shown, and the figure column keeps figures only (StoryFigure's own
	 * block lies dormant).
	 *
	 * The fitting is the figure column's proven machinery, given a HEIGHT
	 * BUDGET by the page instead of a grid row: whole notes only, measured in
	 * hidden copies, admitted nearest-to-the-reading-line first by true fit,
	 * packed in NUMBER ORDER into two stacks (one cut — left run, right run);
	 * the reading paragraph's own notes, when they cannot all stack whole, go
	 * together to one full-width flow that may scroll inside.
	 */
	interface Props {
		notes: { n: number; dist: number; parts: { text: string; href?: string }[] }[];
		/** the vertical room the rail grants — the stacks never take more */
		budget: number;
		/** the room the READING paragraph's own notes may stretch to when
		 *  they do not fit the budget (2026-09-18) — every px is a line
		 *  fewer behind the scroll */
		budgetMax?: number;
	}
	let { notes, budget, budgetMax }: Props = $props();

	const GAP = 28; // --sp-7, the column gap
	const LI_MARGIN = 8; // --sp-2, under each note
	let availW = $state(0);
	let measureEl = $state<HTMLUListElement | null>(null);
	let measureWideEl = $state<HTMLUListElement | null>(null);
	let packed = $state<{
		left: number[];
		right: number[];
		spread: number[];
		spreadH: number;
		/** the flow holds more than its box: the scroll is shown */
		spreadScrolls: boolean;
	} | null>(null);
	const colW = $derived(Math.max(80, (availW - GAP) / 2));
	$effect(() => {
		const el = measureEl;
		const H = budget;
		const HMAX = Math.max(H, budgetMax ?? H);
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
		// the reading paragraph's own notes are a unit: when they cannot all
		// stack whole they go together to the full-width flow
		let spread: number[] = [];
		let spreadH = 0;
		let spreadScrolls = false;
		let stackH = H;
		const minDist = byNeed.length ? byNeed[0].dist : 0;
		const actives = list.filter((nt) => nt.dist === minDist).map((nt) => nt.n);
		if (actives.length && !split(actives, H)) {
			spread = [...actives].sort((a, b) => a - b);
			const tot = spread.reduce(
				(s, n) => s + (heightsWide.get(n) ?? Math.ceil(hOf(n) / 2) + 12),
				0
			);
			spreadH = Math.min(HMAX, tot + 4);
			spreadScrolls = tot + 4 > HMAX;
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
		packed = { left: best.left, right: best.right, spread, spreadH, spreadScrolls };
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

<div class="nblock" bind:clientWidth={availW}>
	{#if spreadNotes.length}
		<ul
			class="notes spread"
			class:scrolls={packed?.spreadScrolls}
			style:height={`${packed?.spreadH ?? 0}px`}
		>
			{#each spreadNotes as sn (sn.n)}
				<li>{sn.n}.
					{#each sn.parts as p, i (i)}{#if p.href}<a href={p.href} target="_blank" rel="noopener"
								>{p.text}</a
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
	<!-- the hidden measurers: stack-column width, then full width -->
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

<style>
	.nblock {
		position: relative; /* anchors the hidden measurers */
		overflow: hidden; /* backstop only — the fit keeps whole notes */
	}
	.spread {
		overflow-y: auto;
		margin-bottom: var(--sp-2);
		/* the scroll is SHOWN (the author, 2026-09-18: the overlay bar
		   Chrome hides until a hover read as a note cut off): a thin bar
		   in the ink's faint tone and a fade at the bottom edge that sits
		   over the text until the last line is reached */
		scrollbar-width: thin;
		scrollbar-color: var(--ink-faint) transparent;
		scrollbar-gutter: stable;
	}
	/* the fade is IN FLOW at the end of the notes: while there is more
	   below it sticks to the box's bottom edge over the text, and at the
	   end of the scroll it sits under the last line, never over it */
	.spread.scrolls::after {
		content: '';
		position: sticky;
		bottom: 0;
		display: block;
		height: 18px;
		background: linear-gradient(to bottom, transparent, var(--paper));
		pointer-events: none;
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
		/* the number hangs; long unbroken strings wrap inside the column */
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
