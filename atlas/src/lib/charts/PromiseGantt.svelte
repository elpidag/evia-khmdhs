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
	import ProjectCard from './ProjectCard.svelte';
	import { cardFor, displayName, type CardData } from './projectCard';

	interface Props {
		projects: GanttProject[];
		/** current date (ISO) — the dashed "today" rule */
		today: string;
		/** legend style: compact chip line (default) or the bordered panel
		 *  with the "how to read a row" schematic */
		legend?: 'compact' | 'panel';
		/** «card» is the dataset card's form (user, 2026-08-27): EVERY
		 *  project, bars of ONE height, one-line labels and rows squeezed
		 *  to the height given — the money encoding and the legend live on
		 *  the full frame. */
		variant?: 'full' | 'card';
		/** card variant: draw at the tile's own pixel width, so the
		 *  lettering is the size it says it is */
		width?: number;
		/** card variant: the height the rows must fit into */
		height?: number;
		/** card variant: told how many rows actually fitted */
		onFit?: (info: { shown: number; total: number }) => void;
	}
	let {
		projects,
		today,
		legend = 'compact',
		variant = 'full',
		width = 920,
		height = 0,
		onFit
	}: Props = $props();
	const card = $derived(variant === 'card');

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
	const W = $derived(card ? width || 700 : 920);
	const LABEL_W = $derived(card ? Math.min(168, W * 0.26) : 210);
	/** the readable floor for a row of the card (an 8,5 px name needs it) */
	const ROW_MIN = 9.6;
	/** top band: year labels + the today label live above the rows */
	const TOP_H = $derived(card ? 20 : 30);
	/** how many rows fit, and how tall each is: every project if the height
	 *  allows it at the readable floor, otherwise the EARLIEST ones (user,
	 *  2026-08-27) — and the card says how many it is showing */
	const fit = $derived.by(() => {
		if (!card) return { rows: projects.length, h: 20 };
		const room = Math.max(40, (height || 700) - TOP_H - 6);
		const n = projects.length;
		if (n * ROW_MIN <= room) return { rows: n, h: Math.min(16, room / n) };
		return { rows: Math.max(1, Math.floor(room / ROW_MIN)), h: ROW_MIN };
	});
	const ROW_H = $derived(card ? fit.h : 20);
	/** bars sit on a shared baseline; on the full frame the height encodes
	 *  the row's own €, on the card every bar is the same */
	const BASE = $derived(card ? Math.min(11, ROW_H - 1.5) : 16);
	const BAR_MAX = $derived(card ? 5 : 10);
	const BAR_MIN = $derived(card ? 5 : 4);
	const LINE_H = $derived(card ? 5 : 3);


	let rowTip = $state<{ x: number; y: number; card: CardData } | null>(null);

	/** the row's hover card: fixed width, height per content; its RIGHT
	 *  edge midpoint sits on the LEFT edge midpoint of the highlighted
	 *  row's outline, so it hangs in the page margin beside the row. */
	function showRow(e: MouseEvent, p: GanttProject) {
		const box = (e.currentTarget as SVGGElement)
			.querySelector('.rowbox')
			?.getBoundingClientRect();
		if (!box) return;
		rowTip = {
			// clamped so the card can never leave the viewport on the left
			x: Math.max(290, box.left),
			y: box.top + box.height / 2,
			card: cardFor(p)
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
		if (order === 'category' && !card) sorted.sort((a, b) => catRank(a) - catRank(b));
		// the card takes them from the earliest act forward
		const kept = card ? sorted.slice(0, fit.rows) : sorted;
		const rows: Row[] = kept.map((p, i) => ({ p, y: TOP_H + i * ROW_H }));
		return { rows, height: TOP_H + rows.length * ROW_H + (card ? 4 : 8) };
	});
	$effect(() => {
		if (card) onFit?.({ shown: layout.rows.length, total: projects.length });
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
	/** the card's lettering: small, but never below what can be read */
	const LABEL_FS = $derived(card ? Math.max(8, Math.min(9.5, ROW_H - 1.6)) : 9.5);




	/** full company name over at most two lines (the doubled rows fit two);
	 *  breaks at a word boundary, never silently truncates short of ~76 chars */
	function nameLines(name: string): string[] {
		if (card) {
			// one line, cut to the label column's own width
			const max = Math.max(8, Math.floor((LABEL_W - 8) / (LABEL_FS * 0.52)));
			return [name.length > max ? name.slice(0, max - 1).trimEnd() + '…' : name];
		}
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

{#if !card}<GanttLegend {projects} variant={legend} />{/if}

<div class="gwrap" style:--mark-fs={card ? '8px' : null}>
<!-- ordering control, sitting on the years band left of the first label -->
{#if !card}
	<div class="orderctl">
		<select bind:value={order} aria-label="Row ordering">
			<option value="time">by time</option>
			<option value="category">by category</option>
		</select>
	</div>
{/if}
{#if rowTip}
	<ProjectCard x={rowTip.x} y={rowTip.y} anchor="left" card={rowTip.card} />
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
		{@const h1 = card
			? BAR_MAX
			: isLine
				? LINE_H
				: Math.max(BAR_MIN, (BAR_MAX * (b1 ?? maxB)) / maxB)}
		{@const h0 = card
			? BAR_MAX
			: b0 !== null && maxB > 0
				? Math.max(BAR_MIN, (BAR_MAX * b0) / maxB)
				: null}
		{@const lines = nameLines(displayName(p.company))}
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<g
			class="row"
			onmouseenter={(e) => !card && showRow(e, p)}
			onmouseleave={() => (rowTip = null)}
		>
			{#if card}<title>{displayName(p.company)}</title>{/if}
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
			<!-- the card's rows are not links (user, 2026-08-27): the clicking
			     belongs to the full chart -->
			<svelte:element this={card ? 'g' : 'a'} href={card ? undefined : `/anadohoi/project/${p.ada}`}>
				{#each lines as ln, li (li)}
					<text
						x={LABEL_W - 6}
						y={y + (lines.length === 1 ? (card ? BASE : 13) : 8.5 + li * 9)}
						class="label"
						style:font-size="{LABEL_FS}px"
					>
						{ln}
					</text>
				{/each}
			</svelte:element>
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
				{#if !card}
					<text x={xs + 2} y={y + BASE - Math.max(h0, h1) - 2} class="step">
						{eurShort(b0 ?? 0)} → {eurShort(b1 ?? 0)}
					</text>
				{/if}
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
		font-size: var(--mark-fs, 10px);
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
