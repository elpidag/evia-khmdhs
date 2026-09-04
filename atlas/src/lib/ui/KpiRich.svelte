<script lang="ts">
	/**
	 * The sponsored card's KPI row, set from the user's own edit of the
	 * exported page (2026-08-27): unequal cards in the dataset hue, each a
	 * HEADLINE of Obviously Bold numbers (36 px) and words (13 px) on one
	 * baseline, then the sentence in Futura 12 px on the ROWS the user
	 * broke it into. A card may close with a second sentence and a large
	 * value right after it, on its last line.
	 *
	 * Our cut of Obviously and our Futura (Book, not Light) run wider than
	 * the faces the user's file was set in, so every headline and every
	 * row is MEASURED at its base size and scaled down only where it would
	 * not fit its card — the rows and their breaks are never changed.
	 * Every number is passed in already computed; nothing here is typed.
	 */
	export interface RichKpi {
		/** the headline, alternating big numbers and small words */
		parts: { num?: string; word?: string }[];
		/** the sentence under the headline, one string per ROW */
		lines?: string[];
		/** a closing sentence (one string per row) and the value after it */
		tailLines?: string[];
		big?: string;
		/** width weight in the row (the user's 190 / 190 / 299,4) */
		w: number;
	}
	let {
		cards,
		color = 'var(--ink)',
		columns = 0
	}: { cards: RichKpi[]; color?: string; /** cards per row; 0 = one row */ columns?: number } =
		$props();
	const gridCols = $derived(
		columns > 0 ? `repeat(${columns}, minmax(0, 1fr))` : cards.map((c) => `${c.w}fr`).join(' ')
	);

	let boxW = $state<number[]>([]);
	let headW = $state<number[]>([]);
	// the rows' widths keyed «card:row» — a nested array cannot be bound
	// into before it exists
	let rowW = $state<Record<string, number>>({});
	let tailW = $state<Record<string, number>>({});
	let bigW = $state<number[]>([]);
	const widest = (m: Record<string, number>, i: number, n: number) => {
		let w = 0;
		for (let j = 0; j < n; j++) w = Math.max(w, m[`${i}:${j}`] ?? 0);
		return w;
	};
	/** the headline's scale: 1 where it fits, less where it would not */
	const hs = (i: number) => (boxW[i] && headW[i] ? Math.min(1, boxW[i] / headW[i]) : 1);
	const ts = (i: number, n: number) => {
		const w = widest(rowW, i, n);
		return boxW[i] && w ? Math.min(1, boxW[i] / w) : 1;
	};
	/** the closing row: sentence + gap + value must share the width */
	const bs = (i: number, n: number) => {
		const need = widest(tailW, i, n) + 4 + (bigW[i] ?? 0);
		return boxW[i] && need ? Math.min(1, boxW[i] / need) : 1;
	};
</script>

<div class="kpirow" style:grid-template-columns={gridCols}>
	{#each cards as c, i (i)}
		<div
			class="kcard"
			style:--card-c={color}
			style:--hs={hs(i)}
			style:--ts={ts(i, c.lines?.length ?? 0)}
			style:--bs={bs(i, c.tailLines?.length ?? 0)}
		>
			<div class="inner" bind:clientWidth={boxW[i]}>
				<!-- the measuring copies, at the base sizes -->
				<div class="measure" aria-hidden="true">
					<span class="head m" bind:clientWidth={headW[i]}>
						{#each c.parts as p, j (j)}
							{#if p.num}<span class="num">{p.num}</span>{/if}{#if p.word}<span class="word">{p.word}</span>{/if}
						{/each}
					</span>
					{#each c.lines ?? [] as ln, j (j)}
						<span class="row m" bind:clientWidth={rowW[`${i}:${j}`]}>{ln}</span>
					{/each}
					{#each c.tailLines ?? [] as ln, j (j)}
						<span class="row m" bind:clientWidth={tailW[`${i}:${j}`]}>{ln}</span>
					{/each}
					{#if c.big}<span class="big m" bind:clientWidth={bigW[i]}>{c.big}</span>{/if}
				</div>
				<p class="head">
					{#each c.parts as p, j (j)}
						{#if p.num}<span class="num">{p.num}</span>{/if}{#if p.word}<span class="word"
								>{p.word}</span
							>{/if}
					{/each}
				</p>
				{#if c.lines?.length}
					<p class="text">
						{#each c.lines as ln, j (j)}<span class="row">{ln}</span>{/each}
					</p>
				{/if}
				{#if c.big}
					<p class="bigrow">
						{#if c.tailLines?.length}
							<span class="text tail">
								{#each c.tailLines as ln, j (j)}<span class="row">{ln}</span>{/each}
							</span>
						{/if}
						<span class="big">{c.big}</span>
					</p>
				{/if}
			</div>
		</div>
	{/each}
</div>

<style>
	.kpirow {
		display: grid;
		grid-auto-rows: minmax(0, 1fr);
		/* the user's edit: 15,8 px between cards; a second row of cards sits
		   the column's own gap below the first */
		gap: var(--kpi-row-gap, clamp(8px, 0.82vw, 15.8px)) clamp(8px, 0.82vw, 15.8px);
		height: 100%;
	}
	.kcard {
		background: var(--card-c, var(--ink));
		box-sizing: border-box;
		min-width: 0;
		/* the user's file: the headline's baseline 54,6 px under the card's
		   top (a 36 px line from 25 px down), the text 14 px in */
		padding: clamp(13px, 2.31vh, 25px) clamp(4px, 0.26vw, 5px) clamp(7px, 0.93vh, 10px)
			clamp(9px, 0.73vw, 14px);
		border-radius: 4px;
		color: var(--paper);
		overflow: hidden;
	}
	.inner {
		position: relative;
		display: flex;
		flex-direction: column;
		height: 100%;
		min-width: 0;
	}
	.measure {
		position: absolute;
		visibility: hidden;
		height: 0;
		overflow: hidden;
		white-space: nowrap;
	}
	/* each measuring copy is exactly as wide as its own content — a flex
	   head would otherwise stretch to the widest row beside it */
	.measure > * {
		display: inline-block;
		width: max-content;
	}
	.measure .head {
		display: inline-flex;
		width: max-content;
	}
	/* the numbers and the words share one baseline, on ONE line */
	.head {
		margin: 0;
		display: flex;
		flex-wrap: nowrap;
		align-items: baseline;
		white-space: nowrap;
		line-height: 1;
		min-width: 0;
		/* the whitespace between the spans would otherwise become flex items
		   of its own and widen the line past the card */
		font-size: 0;
	}
	.head > * + * {
		margin-left: 4px;
	}
	.num {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: calc(clamp(20px, 1.875vw, 36px) * var(--hs, 1));
		line-height: 1;
	}
	.word {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: calc(clamp(9px, 0.68vw, 13px) * var(--hs, 1));
		line-height: 1.1;
	}
	.measure .num {
		font-size: clamp(20px, 1.875vw, 36px);
	}
	.measure .word {
		font-size: clamp(9px, 0.68vw, 13px);
	}
	/* the sentence: Futura 12 px on 1,2 lines, near-white, one span per
	   row — the rows are the user's, the size the one that fits them */
	.text {
		margin: clamp(5px, 0.83vh, 9px) 0 0;
		font-family: var(--font-ui);
		font-weight: 400;
		font-size: calc(clamp(8.5px, 0.625vw, 12px) * var(--ts, 1));
		line-height: 1.2;
		color: color-mix(in srgb, var(--ink) 5.8%, var(--paper));
	}
	.row {
		display: block;
		white-space: nowrap;
	}
	.measure .row {
		font-family: var(--font-ui);
		font-weight: 400;
		font-size: clamp(8.5px, 0.625vw, 12px);
	}
	/* the closing row: the sentence at the inset, the value right after it,
	   sharing its last baseline, ~16 px above the card's foot */
	.bigrow {
		margin: auto 0 clamp(8px, 1.48vh, 16px);
		display: flex;
		align-items: flex-end;
		align-items: last baseline;
		justify-content: flex-start;
		gap: 4px;
		min-width: 0;
	}
	/* «those acts amount / to a value of» is centred in the user's file:
	   its second row starts 13 px in, half the difference of the two */
	.bigrow .tail {
		margin: 0;
		flex: none;
		font-size: calc(clamp(8.5px, 0.625vw, 12px) * var(--bs, 1));
		text-align: center;
	}
	.big {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: calc(clamp(20px, 1.875vw, 36px) * var(--bs, 1));
		line-height: 1;
		white-space: nowrap;
	}
	.measure .big {
		font-size: clamp(20px, 1.875vw, 36px);
	}
	@media (max-width: 1100px) {
		.kpirow {
			grid-template-columns: 1fr !important;
			gap: var(--sp-3);
		}
	}
</style>
