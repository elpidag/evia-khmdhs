<script lang="ts">
	import { eurShort } from '$lib/transforms/format';

	export interface BarRow {
		label: string;
		value: number;
		href?: string;
		sublabel?: string;
		/** hover text for the row (inside layout); defaults to the label */
		title?: string;
	}

	interface Props {
		rows: BarRow[];
		fmt?: (v: number) => string;
		color?: string;
		/** shared max for comparable scales across charts; defaults to rows max */
		max?: number;
		/** highlight predicate — highlighted bars get full accent, rest muted */
		highlight?: (r: BarRow) => boolean;
		/** per-row colour (e.g. category ramps); wins over `color` */
		colorOf?: (r: BarRow) => string;
		/** names ON the bars (white) instead of above them; a bar too short
		 *  for its name gets the name right after it in ink instead */
		inside?: boolean;
		/** bar thickness in px */
		barHeight?: number;
	}
	let {
		rows,
		fmt = eurShort,
		color = 'var(--accent)',
		max,
		highlight,
		colorOf,
		inside = false,
		barHeight = 14
	}: Props = $props();

	const maxV = $derived(max ?? Math.max(...rows.map((r) => r.value), 1));

	// inside mode: real text widths (hidden measuring spans) vs bar px widths
	let trackW = $state(0);
	let labelW = $state<number[]>([]);
	let wordW = $state<number[]>([]);
	const RESERVE = 60; // px kept free at the row's end for the value
	const longestWord = (s: string) =>
		s.split(' ').reduce((a, b) => (b.length > a.length ? b : a), '');
	/** 0 = one line · 1 = wrapped to two lines (tall bars) · 2 = outside */
	const tier = $derived(
		rows.map((r, i) => {
			const bar = Math.max(0, trackW - RESERVE) * (r.value / maxV);
			if ((labelW[i] ?? Infinity) + 14 <= bar) return 0;
			// two lines only if the whole label fits in two — the longest word
			// fitting is necessary, not sufficient, and a label that needs a
			// third line was being clipped with an ellipsis (user, 2026-08-22)
			if (
				barHeight >= 26 &&
				(wordW[i] ?? Infinity) + 14 <= bar &&
				(labelW[i] ?? Infinity) / 2 + 14 <= bar
			)
				return 1;
			return 2;
		})
	);
</script>

{#if inside}
	<div class="chart tight" bind:clientWidth={trackW}>
		<div class="measure" aria-hidden="true">
			{#each rows as r, i (i)}<span bind:clientWidth={labelW[i]}>{r.label}</span><span
					bind:clientWidth={wordW[i]}>{longestWord(r.label)}</span
				>{/each}
		</div>
		{#each rows as r, i (i)}
			{@const w = Math.max(0.4, (100 * r.value) / maxV)}
			{@const dim = highlight ? !highlight(r) : false}
			<div class="irow" class:dim>
				<div
					class="bar"
					style:width={`calc((100% - ${RESERVE}px) * ${w / 100})`}
					style:height={`${barHeight}px`}
					style:background={colorOf ? colorOf(r) : color}
				>
					{#if tier[i] < 2}
						<span class="on" class:two={tier[i] === 1} title={r.title ?? r.label}>
							{#if r.href}<a href={r.href}>{r.label}</a>{:else}{r.label}{/if}
						</span>
					{/if}
				</div>
				{#if tier[i] === 2}
					<span class="off">
						{#if r.href}<a href={r.href}>{r.label}</a>{:else}{r.label}{/if}
					</span>
				{/if}
				<span class="value">{fmt(r.value)}</span>
			</div>
		{/each}
	</div>
{:else}
	<div class="chart">
		{#each rows as r, i (i)}
			{@const w = Math.max(0.4, (100 * r.value) / maxV)}
			{@const dim = highlight ? !highlight(r) : false}
			<div class="row" class:dim>
				<div class="label">
					{#if r.href}<a href={r.href}>{r.label}</a>{:else}{r.label}{/if}
					{#if r.sublabel}<small class="sub">{r.sublabel}</small>{/if}
				</div>
				<div class="track">
					<div class="bar" style:width={`${w}%`} style:background={colorOf ? colorOf(r) : color}></div>
					<span class="value">{fmt(r.value)}</span>
				</div>
			</div>
		{/each}
	</div>
{/if}

<style>
	.chart {
		display: grid;
		gap: var(--sp-2);
	}
	.chart.tight {
		position: relative;
		gap: 6px;
	}
	.measure {
		position: absolute;
		visibility: hidden;
		height: 0;
		overflow: hidden;
		white-space: nowrap;
		font-size: var(--fs-12);
	}
	.measure span {
		display: inline-block;
	}
	.irow {
		display: flex;
		align-items: center;
		gap: 6px;
		min-width: 0;
	}
	.irow .bar {
		display: flex;
		align-items: center;
		flex: none;
	}
	.on {
		color: #fff;
		font-size: var(--fs-12);
		padding: 0 6px;
		white-space: nowrap;
		overflow: hidden;
	}
	/* two lines and no more: a long company name wrapped to three inside a
	   30 px bar and was cut mid-letter (user, 2026-08-20) */
	.on.two {
		white-space: normal;
		line-height: 1.08;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	.on a {
		color: #fff;
		text-decoration: none;
	}
	.on a:hover {
		text-decoration: underline;
	}
	.off {
		font-size: var(--fs-13);
		/* a label too long for its bar sits beside it — it may wrap, but it
		   must not push the value off the row (a category name is a whole
		   sentence since the 2026-08-22 curation) */
		min-width: 0;
		line-height: 1.2;
	}
	.off a {
		text-decoration: none;
	}
	.off a:hover {
		text-decoration: underline;
	}
	.row.dim .bar,
	.irow.dim .bar {
		opacity: 0.35;
	}
	.label {
		font-size: var(--fs-14);
		line-height: 1.25;
		margin-bottom: 2px;
	}
	.label a {
		text-decoration: none;
	}
	.label a:hover {
		text-decoration: underline;
	}
	.sub {
		color: var(--ink-faint);
		margin-left: var(--sp-2);
	}
	.track {
		display: flex;
		align-items: center;
		gap: var(--sp-2);
	}
	.bar {
		height: 14px;
		border-radius: 2px;
		min-width: 2px;
	}
	.value {
		font-size: var(--fs-13);
		color: var(--ink-soft);
		white-space: nowrap;
		flex: none;
	}
</style>
