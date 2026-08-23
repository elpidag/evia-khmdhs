<script lang="ts">
	/**
	 * The CPV divisions as VERTICAL columns (user, 2026-08-23): one column
	 * per division, height = the distinct contracts declaring at least one
	 * code under it, the count on top, the division's CPV number under it
	 * (muted, with a «CPV» prefix, so it never reads as a count), the short
	 * English name beneath.
	 *
	 * Click a column and it SPLITS IN PLACE into its classes: the chosen
	 * division's slot widens to hold one thinner black column per class,
	 * the other divisions stay where they are, in grey — and only when the
	 * split needs the room do the SMALLEST of them step aside (the chart
	 * says how many). A line at the top carries the chosen division's full
	 * name and count and the way back; the key under the chart names the
	 * classes in English, each opening into its codes. Every height is a
	 * distinct-contract count; counts overlap across columns (a contract
	 * declares ~16 codes), so nothing is stacked or summed.
	 */
	import { grInt } from '$lib/transforms/format';

	interface Code {
		code: string;
		name_en: string;
		name_el: string;
		n: number;
	}
	interface Cls extends Code {
		codes: Code[];
	}
	interface Division extends Code {
		classes: Cls[];
	}
	interface Props {
		divisions: Division[];
		/** the y-axis ceiling — every in-scope contract */
		total: number;
	}
	let { divisions, total }: Props = $props();

	const W = 1120;
	const PLOT_H = 214; // the bars' own height; the label band below is sized to the names
	const PAD = { l: 48, r: 8, t: 22 };
	const plotW = W - PAD.l - PAD.r;
	const CLS_SLOT = 36; // a class column's slot inside the split
	const CHAR = 5.6; // the display face at 13px, per character
	const ROW = 15; // a row of the 13px names
	// ~5 labelled ticks whatever the dataset's size — the fixed 25/50 pair
	// smeared 40 ticks onto the axis when the ΔΑΣΕ page (total 1.998) took
	// this chart (2026-08-24); Anti-nero (245) still lands on 50
	const step = $derived.by(() => {
		for (const s of [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000])
			if (total / s <= 5.5) return s;
		return 25000;
	});
	const yTop = $derived(Math.ceil(total / step) * step);
	const ticks = $derived(Array.from({ length: yTop / step + 1 }, (_, i) => i * step));
	const y = (v: number) => PAD.t + PLOT_H - (PLOT_H * v) / yTop;

	let selected = $state<string | null>(null);
	let openCls = $state<string | null>(null);
	const chosen = $derived(divisions.find((d) => d.code === selected) ?? null);

	/** the slots: at rest every division gets plotW/n; once one is chosen
	 *  its slot grows to hold its classes and the others keep their rest
	 *  width — the smallest stepping aside only while the room is short */
	const layout = $derived.by(() => {
		const n = divisions.length;
		const restSlot = plotW / Math.max(1, n);
		if (!chosen)
			return { slots: divisions.map((d, i) => ({ d, x0: PAD.l + restSlot * i, w: restSlot })), hidden: 0 };
		const need = Math.max(180, chosen.classes.length * CLS_SLOT);
		const others = divisions.filter((d) => d.code !== chosen.code); // already by count, desc
		// the others may compress down to MIN_OTHER (a number and a short
		// name still fit); only when even that is not enough do the smallest
		// step aside
		const MIN_OTHER = 66;
		let shown = others.length;
		let otherW = Math.min(restSlot, (plotW - need) / Math.max(1, shown));
		while (shown > 0 && otherW < MIN_OTHER) {
			shown -= 1;
			otherW = Math.min(restSlot, (plotW - need) / Math.max(1, shown));
		}
		const keep = new Set(others.slice(0, shown).map((d) => d.code));
		const want = plotW - shown * otherW;
		let x0 = PAD.l;
		const slots = divisions
			.filter((d) => d.code === chosen.code || keep.has(d.code))
			.map((d) => {
				const w = d.code === chosen.code ? want : otherW;
				const s = { d, x0, w };
				x0 += w;
				return s;
			});
		return { slots, hidden: others.length - shown };
	});
	const colW = (slotW: number) => Math.min(64, slotW * 0.6);
	/** a count prints WHITE inside its bar when the bar is tall enough —
	 *  and, for the thin class columns, only when it is also WIDE enough
	 *  («1.406» overflowed the 36px slot when the ΔΑΣΕ page took this
	 *  chart, 2026-08-24) */
	const inside = (n: number, w = Infinity) => y(0) - y(n) >= 20 && grInt(n).length * 7 + 6 <= w;

	/** the name under a column, WHOLE (user, 2026-08-23): wrapped on words
	 *  to the slot's width, as many rows as it takes */
	const wrap = (s: string, slotW: number): string[] => {
		const per = Math.max(8, Math.floor((slotW - 6) / CHAR));
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
	/** the label band is as tall as the tallest name on show */
	const labels = $derived(
		layout.slots.map((s) => ({ code: s.d.code, rows: wrap(s.d.name_en, s.w) }))
	);
	const bandH = $derived(18 + Math.max(1, ...labels.map((l) => l.rows.length)) * ROW + 26);
	const H = $derived(PAD.t + PLOT_H + bandH);
	const pick = (code: string) => {
		selected = selected === code ? null : code;
		openCls = null;
	};
	const close = () => {
		selected = null;
		openCls = null;
	};
</script>

<figure class="cc">
	<svg viewBox="0 0 {W} {H}" role="img" aria-label="Contracts per CPV division">
		<text class="axis-name" transform={`translate(12 ${PAD.t}) rotate(90)`}>contracts declaring a code of the division</text>
		{#if chosen}
			<!-- svelte-ignore a11y_no_static_element_interactions a11y_no_noninteractive_tabindex -->
			<text class="close" x={W - PAD.r} y={14} text-anchor="end" role="button" tabindex="0" onclick={close} onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && close()}>✕ close</text>
			<text class="axis-name" x={W - PAD.r} y={H - 6} text-anchor="end">{layout.hidden ? `CPV divisions — the ${grInt(layout.hidden)} smallest step aside while CPV ${chosen.code.slice(0, 2)} is open` : 'CPV divisions'}</text>
		{:else}
			<text class="axis-name" x={W - PAD.r} y={H - 6} text-anchor="end">CPV divisions — click one to split it into its classes</text>
		{/if}
		{#each ticks as t (t)}
			<line x1={PAD.l} y1={y(t)} x2={W - PAD.r} y2={y(t)} class="grid" />
			<text x={PAD.l - 6} y={y(t) + 3} class="ylab">{t}</text>
		{/each}
		{#each layout.slots as s, si (s.d.code)}
			{@const on = chosen?.code === s.d.code}
			{@const rows = labels[si]?.rows ?? []}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<g
				class="col"
				class:on
				class:dim={!!chosen && !on}
				role="button"
				tabindex="0"
				onclick={() => pick(s.d.code)}
				onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && pick(s.d.code)}
				aria-label={`CPV ${s.d.code.slice(0, 2)} ${s.d.name_en}: ${grInt(s.d.n)} contracts`}
			>
				<rect x={s.x0} y={PAD.t} width={s.w} height={PLOT_H} class="hit" />
				{#if on}
					<!-- the split: one thinner column per class, the division's own
					     number and count on the number line, its whole name under -->
					{@const k = s.d.classes.length}
					{@const cw = Math.min(28, (s.w / k) * 0.7)}
					{@const gap = (s.w - cw * k) / (k + 1)}
					{#each s.d.classes as c, j (c.code)}
						{@const cx = s.x0 + gap + j * (cw + gap)}
						<!-- a class bar opens its codes in the key below -->
						<!-- svelte-ignore a11y_no_static_element_interactions -->
						<g
							role="button"
							tabindex="0"
							aria-label={`${c.name_en}: ${grInt(c.n)} contracts`}
							onclick={(e) => {
								e.stopPropagation();
								openCls = openCls === c.code ? null : c.code;
							}}
							onkeydown={(e) => {
								if (e.key === 'Enter' || e.key === ' ') {
									e.stopPropagation();
									openCls = openCls === c.code ? null : c.code;
								}
							}}
						>
							<rect x={cx} y={y(c.n)} width={cw} height={Math.max(1, y(0) - y(c.n))} class="bar cls" class:lit={openCls === c.code}>
								<title>{c.name_en}: {grInt(c.n)} contracts</title>
							</rect>
						</g>
						{#if inside(c.n, cw)}
							<text x={cx + cw / 2} y={y(c.n) + 12} class="ctotal in">{grInt(c.n)}</text>
						{:else}
							<text x={cx + cw / 2} y={y(c.n) - 4} class="ctotal">{grInt(c.n)}</text>
						{/if}
						<text x={cx + cw / 2} y={y(0) + 13} class="cnum">{c.code.slice(0, 4)}</text>
					{/each}
					<text x={s.x0 + s.w / 2} y={y(0) + 30} class="num"><tspan class="pre">CPV </tspan>{s.d.code.slice(0, 2)} · {grInt(s.d.n)} contracts</text>
					{#each rows as ln, k (k)}
						<text x={s.x0 + s.w / 2} y={y(0) + 46 + k * ROW} class="lab on">{ln}</text>
					{/each}
				{:else}
					{@const cw = colW(s.w)}
					{@const cx = s.x0 + (s.w - cw) / 2}
					<rect x={cx} y={y(s.d.n)} width={cw} height={Math.max(1, y(0) - y(s.d.n))} class="bar" />
					{#if inside(s.d.n)}
						<text x={cx + cw / 2} y={y(s.d.n) + 14} class="total in">{grInt(s.d.n)}</text>
					{:else}
						<text x={cx + cw / 2} y={y(s.d.n) - 5} class="total">{grInt(s.d.n)}</text>
					{/if}
					<text x={cx + cw / 2} y={y(0) + 15} class="num"><tspan class="pre">CPV </tspan>{s.d.code.slice(0, 2)}</text>
					{#each rows as ln, k (k)}
						<text x={cx + cw / 2} y={y(0) + 31 + k * ROW} class="lab">{ln}</text>
					{/each}
				{/if}
			</g>
		{/each}
	</svg>

	{#if chosen}
		<!-- the key: the chosen division's classes, English names, each
		     opening into its codes -->
		<div class="key">
			<ul class="classes">
				{#each chosen.classes as c (c.code)}
					<li class:open={openCls === c.code}>
						<button class="crow" onclick={() => (openCls = openCls === c.code ? null : c.code)} aria-expanded={openCls === c.code}>
							<span class="caret" aria-hidden="true">{openCls === c.code ? '−' : '+'}</span>
							<span class="kcode">{c.code.slice(0, 4)}</span>
							<span class="kname">{c.name_en}</span>
							<span class="kn">{grInt(c.n)}</span>
						</button>
						{#if openCls === c.code}
							<ul class="codes">
								{#each c.codes as cd (cd.code)}
									<li>
										<span class="kcode">{cd.code}</span>
										<span class="kname">{cd.name_en}</span>
										<span class="kn">{grInt(cd.n)}</span>
									</li>
								{/each}
							</ul>
						{/if}
					</li>
				{/each}
			</ul>
		</div>
	{/if}
</figure>

<style>
	.cc {
		margin: 0;
	}
	svg {
		width: 100%;
		height: auto;
		display: block;
	}
	.grid {
		stroke: var(--line);
		stroke-width: 0.6;
	}
	.ylab {
		font-size: 10px;
		fill: var(--ink-faint);
		text-anchor: end;
	}
	.axis-name {
		font-size: 10.5px;
		fill: var(--ink-soft);
	}
	.col {
		cursor: pointer;
		outline: none;
	}
	.hit {
		fill: transparent;
	}
	/* the bars take the hosting page's ink (— the ΔΑΣΕ page passes its
	   green via --cpv-ink, 2026-08-24); the hover/dim states are the same
	   ink mixed toward the paper, so every page gets its own colour's
	   «transparencies» — on Anti-nero the mixes land on the exact greys
	   these rules used to hardcode (#3a3a3a / #bdbdbd / #9b9b9b) */
	.bar {
		fill: var(--cpv-ink, var(--c-antinero));
	}
	.col:hover .bar {
		fill: color-mix(in srgb, var(--cpv-ink, var(--c-antinero)) 77%, #fff);
	}
	/* the other divisions, faded while one is split open */
	.col.dim .bar {
		fill: color-mix(in srgb, var(--cpv-ink, var(--c-antinero)) 26%, #fff);
	}
	.col.dim:hover .bar {
		fill: color-mix(in srgb, var(--cpv-ink, var(--c-antinero)) 39%, #fff);
	}
	.bar.cls {
		fill: var(--cpv-ink, var(--c-antinero));
		cursor: pointer;
	}
	.col.on:hover .bar.cls {
		fill: var(--cpv-ink, var(--c-antinero));
	}
	.bar.cls:hover {
		fill: color-mix(in srgb, var(--cpv-ink, var(--c-antinero)) 77%, #fff);
	}
	.bar.cls.lit {
		fill: var(--accent);
	}
	.total,
	.ctotal {
		font-weight: 700;
		fill: var(--ink);
		text-anchor: middle;
		pointer-events: none;
	}
	.total {
		font-size: var(--fs-13);
	}
	.ctotal {
		font-size: var(--fs-13);
	}
	.total.in,
	.ctotal.in {
		fill: var(--paper);
	}
	.col.dim .total {
		fill: var(--ink-soft);
	}
	.col.dim .total.in {
		fill: var(--paper);
	}
	/* the code NUMBERS wear a muted dress and a «CPV» prefix, so they never
	   read as counts */
	.num,
	.cnum {
		font-size: 11px;
		fill: var(--ink-faint);
		text-anchor: middle;
		font-variant-numeric: tabular-nums;
		letter-spacing: 0.04em;
		pointer-events: none;
	}
	.cnum {
		font-size: 10.5px;
	}
	.num .pre {
		font-size: 8px;
		letter-spacing: 0.08em;
	}
	.lab {
		font-size: var(--fs-13);
		fill: var(--ink-soft);
		text-anchor: middle;
		pointer-events: none;
	}
	.lab.on {
		fill: var(--ink);
		font-weight: 700;
	}
	.close {
		font-size: 11px;
		fill: var(--ink-soft);
		cursor: pointer;
	}
	.close:hover {
		fill: var(--ink);
	}
	.key {
		margin-top: var(--sp-3);
		border-top: 1px solid var(--line-strong);
		padding-top: var(--sp-3);
	}
	.crow,
	.codes li {
		display: grid;
		grid-template-columns: 1.2rem 6.5rem 1fr 3.5rem;
		gap: var(--sp-3);
		align-items: baseline;
	}
	.kcode {
		color: var(--ink-faint);
		font-variant-numeric: tabular-nums;
		font-size: var(--fs-12);
		letter-spacing: 0.04em;
	}
	.kname {
		font-size: var(--fs-13);
	}
	.kn {
		text-align: right;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
		font-size: var(--fs-13);
	}
	.classes,
	.codes {
		list-style: none;
		margin: 0;
		padding: 0;
	}
	.classes {
		columns: 2 26rem;
		column-gap: var(--sp-6);
	}
	.classes > li {
		break-inside: avoid;
		padding: 2px 0;
	}
	.crow {
		width: 100%;
		border: 0;
		background: none;
		font: inherit;
		text-align: left;
		cursor: pointer;
		color: var(--ink);
		padding: 2px 0;
	}
	.crow:hover .kname {
		text-decoration: underline;
	}
	.caret {
		color: var(--ink-faint);
		text-align: center;
	}
	.codes {
		margin: 2px 0 6px 1.2rem;
		padding-left: var(--sp-3);
		border-left: 1px solid var(--line);
	}
	.codes li {
		grid-template-columns: 6.5rem 1fr 3.5rem;
		color: var(--ink-soft);
	}
</style>
