<script lang="ts">
	/**
	 * Promise-vs-delivery Gantt: one row per sponsor project — bar from
	 * designation act to the initial deadline, a lighter segment for
	 * amendment extensions, ✓ where a completion act exists, ✕ where
	 * revoked, and a "today" rule. One flat chronology ordered by the
	 * first designation act; the legend lives in GanttLegend.
	 */
	import { dmy, eurShort } from '$lib/transforms/format';
	import { COLOR, EXT_COLOR, NODATE_COLOR, noDate, type GanttProject } from './ganttTheme';
	import GanttLegend from './GanttLegend.svelte';

	interface Props {
		projects: GanttProject[];
		/** current date (ISO) — the dashed "today" rule */
		today: string;
		/** legend style: compact chip line (default) or the bordered panel
		 *  with the "how to read a row" schematic */
		legend?: 'compact' | 'panel';
	}
	let { projects, today, legend = 'compact' }: Props = $props();

	const T0 = new Date('2021-07-01').getTime();
	/** axis end = the latest date anywhere in the data (or today) plus a
	 *  5-day margin — computed, so no deadline can run off the chart edge */
	const T1 = $derived.by(() => {
		let m = new Date(today).getTime();
		for (const p of projects)
			for (const d of [p.start, p.start0, p.deadline0, p.deadline, p.completed, p.revoked])
				if (d) {
					const t = new Date(d).getTime();
					if (!Number.isNaN(t)) m = Math.max(m, t);
				}
		return m + 5 * 86_400_000;
	});
	const W = 920;
	const LABEL_W = 210;
	const ROW_H = 20;
	/** top band: year labels + the today label live above the rows */
	const TOP_H = 30;
	/** bars sit on a shared baseline; height encodes the row's own € */
	const BASE = 16; // baseline offset inside the row
	const BAR_MAX = 10; // tallest bar (the row's largest stated €)
	const BAR_MIN = 4;
	const LINE_H = 3; // acts with no stated budget render as a thick line

	/** English renderings of the duration-based deadlines (shown on hover;
	 *  the act's own Greek wording stays printed on the row) */
	const DTEXT_EN: Record<string, string> = {
		'15 ημέρες από την έκδοση': '15 days from issue of the act',
		'2 έτη από την υπογραφή': '2 years from signing',
		'3 έτη από την υπογραφή': '3 years from signing',
		'4 μήνες από την έκδοση': '4 months from issue of the act',
		'4 μήνες από την έναρξη εργασιών (μέγ. 6)': '4 months from start of works (max 6)',
		'5 έτη από την έκδοση': '5 years from issue of the act',
		'5 μήνες από την έναρξη εργασιών': '5 months from start of works',
		'μελέτες: 30 ημέρες από επιλογή μελετητή · έργο: 4 μήνες από έναρξη (μέγ. 6)':
			'studies: 30 days from selecting the engineer · works: 4 months from start (max 6)',
		'μελέτη: 2 μήνες · έργο: 12 μήνες από την έναρξη':
			'study: 2 months · works: 12 months from start'
	};

	let rowTip = $state<{
		x: number;
		y: number;
		name: string;
		color: string;
		/** text colour — dark ink on the pale no-date background */
		ink: string;
		lines: string[];
	} | null>(null);

	/** the row's hover card: fixed width, height per content; its RIGHT
	 *  edge midpoint sits on the LEFT edge midpoint of the highlighted
	 *  row's outline, so it hangs in the page margin beside the row. */
	function showRow(e: MouseEvent, p: GanttProject) {
		const b1 = p.budget_stated ?? null;
		const b0 = p.start0 ? (p.budget0 ?? null) : null;
		const lines: string[] = [];
		lines.push(
			`designation act: ${dmy(p.start0 ?? p.start) || '—'}${p.start0 ? ` (restated ${dmy(p.start) || '—'})` : ''}`
		);
		lines.push(
			b0 !== null && b1 !== null
				? `budget announced: ${eurShort(b0)} → ${eurShort(b1)}`
				: b1 !== null
					? `budget announced: ${eurShort(b1)}`
					: 'budget announced: none stated'
		);
		if (p.deadline) {
			lines.push(
				p.deadline0 && p.deadline0 !== p.deadline
					? `deadline: ${dmy(p.deadline0)} → ${dmy(p.deadline)}`
					: `deadline: ${dmy(p.deadline)}`
			);
		} else if (p.dtext) {
			lines.push(`deadline: ${DTEXT_EN[p.dtext] ?? p.dtext}`);
		} else {
			lines.push('deadline: —');
		}
		const box = (e.currentTarget as SVGGElement)
			.querySelector('.rowbox')
			?.getBoundingClientRect();
		if (!box) return;
		rowTip = {
			// clamped so the card can never leave the viewport on the left
			x: Math.max(290, box.left),
			y: box.top + box.height / 2,
			name: displayName(p.company),
			color: noDate(p) ? NODATE_COLOR : (COLOR[p.status] ?? 'var(--ink)'),
			ink: noDate(p) ? 'var(--ink)' : '#fff',
			lines
		};
	}

	function x(d: string | null): number | null {
		if (!d) return null;
		const t = new Date(d).getTime();
		if (Number.isNaN(t)) return null;
		return LABEL_W + ((W - LABEL_W - 8) * (t - T0)) / (T1 - T0);
	}

	interface Row {
		p: GanttProject;
		y: number;
	}
	/** row ordering, user-switchable: "time" = one flat chronology by the
	 *  FIRST designation act (the restated pair sorts by start0);
	 *  "category" = grouped in the legend's category order, chronological
	 *  within each group */
	let order = $state<'time' | 'category'>('time');
	const CAT_ORDER: Record<string, number> = {
		completed: 0,
		active: 1,
		no_completion_recorded: 3,
		revoked: 4
	};
	function catRank(p: GanttProject): number {
		if (noDate(p)) return 2;
		return CAT_ORDER[p.status] ?? 5;
	}
	const layout = $derived.by(() => {
		const sorted = [...projects].sort((a, b) =>
			(a.start0 ?? a.start ?? '').localeCompare(b.start0 ?? b.start ?? '')
		);
		// stable sort → chronological order survives inside each category
		if (order === 'category') sorted.sort((a, b) => catRank(a) - catRank(b));
		const rows: Row[] = sorted.map((p, i) => ({ p, y: TOP_H + i * ROW_H }));
		return { rows, height: TOP_H + rows.length * ROW_H + 8 };
	});

	// every full year inside the axis range, skipping a label that would
	// clip at the right edge
	const years = $derived.by(() => {
		const out: string[] = [];
		for (let yr = new Date(T0).getFullYear() + 1; yr <= new Date(T1).getFullYear(); yr++) {
			const gx = x(`${yr}-01-01`);
			if (gx !== null && gx <= W - 18) out.push(String(yr));
		}
		return out;
	});
	const todayX = $derived(x(today) ?? LABEL_W);


	/** display form of a company name: uppercase per the Greek all-caps
	 *  convention — the τόνος is dropped but the dialytika is KEPT (ϊ → Ϊ,
	 *  so TATOΪ stays TATOΪ, not TATOI) */
	function displayName(name: string): string {
		return name
			.toUpperCase()
			.normalize('NFD')
			.replace(/[\u0300-\u0307\u0309-\u036f]/g, '')
			.normalize('NFC');
	}

	/** full company name over at most two lines (the doubled rows fit two);
	 *  breaks at a word boundary, never silently truncates short of ~76 chars */
	function nameLines(name: string): string[] {
		const MAX = 38;
		if (name.length <= MAX) return [name];
		let cut = name.lastIndexOf(' ', MAX);
		if (cut < MAX - 16) cut = MAX; // no usable space — hard break
		const l1 = name.slice(0, cut).trimEnd();
		let l2 = name.slice(cut).trimStart();
		if (l2.length > MAX) l2 = l2.slice(0, MAX - 1) + '…';
		return [l1, l2];
	}

</script>

<GanttLegend {projects} variant={legend} />

<div class="gwrap">
<!-- ordering control, sitting on the years band left of the first label -->
<div class="orderctl">
	<select bind:value={order} aria-label="Row ordering">
		<option value="time">by time</option>
		<option value="category">by category</option>
	</select>
</div>
{#if rowTip}
	<div
		class="row-tip"
		style:left={`${rowTip.x}px`}
		style:top={`${rowTip.y}px`}
		style:background={rowTip.color}
		style:color={rowTip.ink}
	>
		<div class="tip-name">{rowTip.name}</div>
		{#each rowTip.lines as ln, i (i)}
			<div>{ln}</div>
		{/each}
	</div>
{/if}
<svg viewBox="0 0 {W} {layout.height}" role="img" aria-label="Timeline of every sponsor project">
	<!-- year grid: labels on TOP, right under the legend -->
	{#each years as yr (yr)}
		{@const gx = x(`${yr}-01-01`)}
		{#if gx}
			<text x={gx} y="12" class="axis">{yr}</text>
			<line x1={gx} y1="16" x2={gx} y2={layout.height - 4} class="grid" />
		{/if}
	{/each}

	<!-- today rule -->
	<line x1={todayX} y1="16" x2={todayX} y2={layout.height - 4} class="today" />
	<text x={todayX + 4} y="26" class="today-label">today ({dmy(today)})</text>

	{#each layout.rows as { p, y } (p.ada)}
		{@const xs = x(p.start)}
		{@const xs0 = x(p.start0 ?? null)}
		{@const xd0 = x(p.deadline0 ?? p.deadline)}
		{@const xd = x(p.deadline)}
		{@const xc = x(p.completed)}
		{@const xr = x(p.revoked)}
		{@const c = noDate(p) ? NODATE_COLOR : COLOR[p.status]}
		{@const b1 = p.budget_stated ?? null}
		{@const b0 = p.start0 ? (p.budget0 ?? null) : null}
		{@const maxB = Math.max(b0 ?? 0, b1 ?? 0)}
		{@const isLine = maxB <= 0}
		{@const h1 = isLine
			? LINE_H
			: Math.max(BAR_MIN, (BAR_MAX * (b1 ?? maxB)) / maxB)}
		{@const h0 = b0 !== null && maxB > 0 ? Math.max(BAR_MIN, (BAR_MAX * b0) / maxB) : null}
		{@const lines = nameLines(displayName(p.company))}
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<g
			class="row"
			onmouseenter={(e) => showRow(e, p)}
			onmouseleave={() => (rowTip = null)}
		>
			<!-- hover highlight: discreet rounded outline around the whole
			     line (transparent fill also makes the full row hoverable) -->
			<rect
				class="rowbox"
				x="0.5"
				y={y + 0.5}
				width={W - 1}
				height={ROW_H - 1}
				rx="4"
			/>
			<a href={`/anadohoi/project/${p.ada}`}>
				{#each lines as ln, li (li)}
					<text x={LABEL_W - 6} y={y + (lines.length === 1 ? 13 : 8.5 + li * 9)} class="label">
						{ln}
					</text>
				{/each}
			</a>
			<!-- restated predecessor: its money at its own height until the
			     restatement date (the step IS the story: €1M → €800k) -->
			{#if xs0 !== null && xs !== null && h0 !== null && xs > xs0}
				<rect
					x={xs0}
					y={y + BASE - h0}
					width={xs - xs0}
					height={h0}
					fill={c}
					opacity="0.55"
					rx="1"
				/>
				<text x={xs + 2} y={y + BASE - Math.max(h0, h1) - 2} class="step">
					{eurShort(b0 ?? 0)} → {eurShort(b1 ?? 0)}
				</text>
			{/if}
			{#if xs !== null && xd0 !== null && xd0 > xs}
				<rect x={xs} y={y + BASE - h1} width={xd0 - xs} height={h1} fill={c} opacity="0.85" rx="1" />
			{:else if xs !== null}
				<!-- no deadline to draw to — a short stub wide enough to read -->
				<rect x={xs} y={y + BASE - h1} width="7" height={h1} fill={c} opacity="0.85" />
			{/if}
			{#if xd0 !== null && xd !== null && xd > xd0}
				{@const ext = EXT_COLOR[p.status]}
				<rect
					x={xd0}
					y={y + BASE - h1}
					width={xd - xd0}
					height={h1}
					fill={ext ?? c}
					opacity={ext ? 0.9 : 0.35}
					rx="1"
				/>
			{/if}
			{#if xd !== null}
				<line x1={xd} y1={y + 2} x2={xd} y2={y + BASE + 2} stroke={c} stroke-width="1.3" />
			{/if}
			{#if xc !== null}
				<text x={xc + 2} y={y + BASE - 1} class="mark ok">✔</text>
			{/if}
			{#if xr !== null}
				<text x={xr + 2} y={y + BASE - 1} class="mark bad">✖</text>
			{/if}
		</g>
	{/each}
</svg>
</div>

<style>
	.gwrap {
		position: relative;
	}
	.orderctl {
		position: absolute;
		top: 0;
		left: 0;
		z-index: 10;
	}
	.orderctl select {
		font-family: var(--font-ui);
		font-size: var(--fs-13);
		color: var(--ink);
		background: var(--paper);
		border: 1px solid var(--line);
		border-radius: 4px;
		padding: 1px 4px;
	}
	.row-tip {
		/* fixed width, content-driven height; right-edge midpoint anchored
		   on the highlighted row's left-edge midpoint */
		position: fixed;
		transform: translate(-100%, -50%);
		width: 270px;
		color: #fff;
		font-size: 12px;
		line-height: 1.5;
		padding: 8px 12px;
		border-radius: 5px;
		pointer-events: none;
		z-index: 120;
		box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
	}
	.tip-name {
		font-weight: 700;
		margin-bottom: 2px;
	}
	svg {
		width: 100%;
		height: auto;
		display: block;
	}
	.grid {
		stroke: var(--line);
		stroke-width: 0.5;
	}
	.axis {
		font-size: 10px;
		fill: var(--ink-faint);
		text-anchor: middle;
	}
	.today {
		stroke: var(--ink);
		stroke-width: 1;
		stroke-dasharray: 3 3;
	}
	.today-label {
		font-size: 10px;
		fill: var(--ink);
		font-weight: 600;
	}
	.label {
		font-size: 9.5px;
		fill: var(--ink-soft);
		text-anchor: end;
	}
	.rowbox {
		fill: transparent;
		stroke: #000;
		stroke-width: 1;
		opacity: 0;
	}
	.row:hover .rowbox {
		opacity: 1;
	}
	.row:hover .label {
		fill: var(--ink);
	}
	.mark {
		font-size: 10px;
		font-weight: 900;
	}
	.mark.ok {
		fill: var(--c-anadohoi);
	}
	.mark.bad {
		fill: #000000;
	}
	.step {
		font-size: 8.5px;
		font-weight: 700;
		fill: var(--ink);
		paint-order: stroke;
		stroke: var(--paper);
		stroke-width: 2.5px;
	}
</style>
