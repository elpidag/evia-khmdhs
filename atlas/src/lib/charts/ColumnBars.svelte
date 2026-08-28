<script lang="ts">
	/**
	 * One column per row — the vertical form of BarH for a narrow slot
	 * (Artboard 6's MONEY PER YEAR, user 2026-08-27; the Anti-nero card's
	 * AWARD PROCEDURES beside DIRECT AWARDS, user 2026-08-28): the value
	 * above each column in 9,3 px with an optional second line under it,
	 * the label beneath the column in 10 px WRAPPED on words to the slot's
	 * width — as many rows as the longest name takes, the band sized to it.
	 * `highlight` keeps the named columns at full strength and dims the
	 * rest, BarH's own rule. Pure SVG, sized to its box.
	 */
	import { eurShort } from '$lib/transforms/format';
	interface Row {
		label: string;
		value: number;
		sub?: string;
	}
	let {
		rows,
		color = 'var(--ink)',
		width = 0,
		height = 0,
		fmt = eurShort,
		highlight = null,
		ariaLabel = 'Columns'
	}: {
		rows: Row[];
		color?: string;
		width?: number;
		height?: number;
		fmt?: (v: number) => string;
		/** the columns drawn at full strength; the rest fade to 35 % */
		highlight?: ((r: Row) => boolean) | null;
		ariaLabel?: string;
	} = $props();
	const VAL = 11; // the value line
	const SUB = 11; // its second line, where any row has one
	const LAB = 12; // one row of the 10 px labels
	const CHAR = 4.7; // the ui face at 10 px, per character
	const max = $derived(Math.max(1, ...rows.map((r) => r.value)));
	const n = $derived(Math.max(1, rows.length));
	/** bars 80 px at most, evenly spaced across the width */
	const slot = $derived(width / n);
	const barW = $derived(Math.min(80, slot * 0.78));
	const hasSub = $derived(rows.some((r) => r.sub));
	const top = $derived(VAL + (hasSub ? SUB : 0) + 4);
	/** the name under a column, WHOLE: wrapped on words to the slot's width */
	const wrap = (s: string): string[] => {
		const per = Math.max(6, Math.floor((slot - 4) / CHAR));
		const out: string[] = [];
		let cur = '';
		for (const w of s.split(/\s+/)) {
			if (cur && (cur + ' ' + w).length > per) {
				out.push(cur);
				cur = w;
			} else cur = cur ? cur + ' ' + w : w;
		}
		if (cur) out.push(cur);
		return out;
	};
	const labels = $derived(rows.map((r) => wrap(r.label)));
	const bottom = $derived(6 + Math.max(1, ...labels.map((l) => l.length)) * LAB);
	const plotH = $derived(Math.max(10, height - top - bottom));
</script>

{#if width && height}
	<svg {width} {height} viewBox="0 0 {width} {height}" role="img" aria-label={ariaLabel}>
		{#each rows as r, i (r.label)}
			{@const h = (plotH * r.value) / max}
			{@const x = slot * i + (slot - barW) / 2}
			{@const cx = x + barW / 2}
			{@const dim = highlight ? !highlight(r) : false}
			<g class:dim>
				<rect {x} y={top + plotH - h} width={barW} height={Math.max(1, h)} rx="2" fill={color} />
				<text x={cx} y={top + plotH - h - (r.sub ? 4 + SUB : 4)} class="val">{fmt(r.value)}</text>
				{#if r.sub}
					<text x={cx} y={top + plotH - h - 4} class="sub">{r.sub}</text>
				{/if}
				{#each labels[i] as line, j (j)}
					<text x={cx} y={top + plotH + 10 + j * LAB} class="lab">{line}</text>
				{/each}
			</g>
		{/each}
	</svg>
{/if}

<style>
	svg {
		display: block;
	}
	.dim rect {
		opacity: 0.35;
	}
	.val {
		font-family: var(--font-ui);
		font-size: 10px;
		font-weight: 700;
		fill: var(--ink);
		text-anchor: middle;
	}
	.sub {
		font-family: var(--font-ui);
		font-size: 9.32px;
		fill: var(--ink-soft);
		text-anchor: middle;
	}
	.lab {
		font-family: var(--font-ui);
		font-size: 10px;
		fill: var(--ink);
		text-anchor: middle;
	}
</style>
