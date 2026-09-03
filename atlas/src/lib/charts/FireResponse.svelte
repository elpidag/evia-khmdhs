<script lang="ts">
	/**
	 * FROM FIRE TO SPONSOR — one lane per PHYSICAL fire, the burn on the
	 * left, the designation acts that followed on its row (DATA_DECISIONS
	 * 2026-08-24; decomposed 2026-08-25: an act answering several fires
	 * attaches to EACH, its dots joined by a vertical tie).
	 *
	 * HONESTY RULES (user, 2026-08-25):
	 * - dots sit at their true date; the ONLY exception is acts signed the
	 *   SAME DAY on the same row, drawn a hair apart so both stay visible
	 *   (a tie member keeps the true date, the loose dot gives way) — the
	 *   legend says so;
	 * - to separate near dots properly the reader FRAMES A PERIOD on the
	 *   context strip below the chart (a brush, not free zoom): the chart
	 *   rescales and positions stay true;
	 * - hover never recolours a dot (black means revoked): it grows the
	 *   act's dots and inks its tie.
	 */
	import { dmy } from '$lib/transforms/format';
	import { fireEn } from '$lib/transforms/names';
	import { COLOR, NODATE_COLOR } from '$lib/charts/ganttTheme';

	export interface FireLane {
		fire: string;
		n: number;
		burn_date: string | null;
		burn_ha: number;
		lag_days: number | null;
		first_start: string | null;
		/** `st` = the CURRENT STATUS OF PROJECTS bucket of the act's project */
		acts: { d: string; ada: string; st?: string }[];
	}
	interface Props {
		fires: FireLane[];
		/** today, so the axis ends where the data does */
		today: string;
	}
	let { fires, today }: Props = $props();

	// 1120 units = the frame's full width at 1 unit ≈ 1 CSS px
	const W = 1120;
	const PAD = { l: 185, r: 62, t: 30, b: 10 };
	const LANE = 16;

	const lanes = $derived(
		fires
			.filter((f) => f.burn_date && f.acts.length)
			.sort((a, b) => (a.burn_date! < b.burn_date! ? -1 : 1))
	);
	const H = $derived(PAD.t + lanes.length * LANE + PAD.b);

	// the FULL period (the context strip's fixed domain)
	const T0 = $derived(
		Math.min(...lanes.map((l) => Date.parse(l.burn_date!)), Date.parse('2021-05-01'))
	);
	const T1 = $derived(Date.parse(today) + 20 * 864e5);

	// the framed window (null = the whole period)
	let win = $state<[number, number] | null>(null);
	const d0 = $derived(win ? win[0] : T0);
	const d1 = $derived(win ? win[1] : T1);

	const plotW = W - PAD.l - PAD.r;
	const x = (iso: string | number) =>
		PAD.l + (((typeof iso === 'string' ? Date.parse(iso) : iso) - d0) / (d1 - d0)) * plotW;
	/** the strip's own scale — always the full period */
	const xs = (iso: string | number) =>
		PAD.l + (((typeof iso === 'string' ? Date.parse(iso) : iso) - T0) / (T1 - T0)) * plotW;
	const y = (i: number) => PAD.t + i * LANE + LANE / 2;

	/** area ∝ hectares, floored so a small fire is still visible */
	const haMax = $derived(Math.max(1, ...lanes.map((l) => l.burn_ha)));
	const rOf = (ha: number) => 2.2 + 5.6 * Math.sqrt(Math.max(ha, 0) / haMax);

	/** year (and, in a narrow window, month) rules for a [a,b] domain */
	const rules = (a: number, b: number, forStrip: boolean) => {
		const out: { t: number; lab: string; minor: boolean }[] = [];
		const y0 = new Date(a).getUTCFullYear();
		const y1 = new Date(b).getUTCFullYear();
		for (let yr = y0; yr <= y1; yr++) {
			const t = Date.parse(`${yr}-01-01`);
			if (t > a && t < b) out.push({ t, lab: String(yr), minor: false });
		}
		// months once the window is short enough to give them room
		const span = (b - a) / 864e5;
		if (!forStrip && span < 550) {
			const step = span < 200 ? 1 : 3;
			const d = new Date(a);
			d.setUTCDate(1);
			d.setUTCHours(0, 0, 0, 0);
			for (;;) {
				d.setUTCMonth(d.getUTCMonth() + 1);
				const t = d.getTime();
				if (t >= b) break;
				const m = d.getUTCMonth();
				if (m === 0 || m % step) continue;
				out.push({
					t,
					lab: `${String(m + 1).padStart(2, '0')}-${d.getUTCFullYear()}`,
					minor: true
				});
			}
		}
		return out;
	};
	const chartRules = $derived(rules(d0, d1, false));
	const stripRules = $derived(rules(T0, T1, true));
	/** the fire seasons (1 May – 31 Oct) inside a domain */
	const seasons = (a: number, b: number) => {
		const out: { x0: number; x1: number }[] = [];
		const y0 = new Date(a).getUTCFullYear();
		const y1 = new Date(b).getUTCFullYear();
		for (let yr = y0; yr <= y1; yr++)
			out.push({ x0: Date.parse(`${yr}-05-01`), x1: Date.parse(`${yr}-11-01`) });
		return out.filter((s) => s.x1 > a && s.x0 < b);
	};
	const chartSeasons = $derived(seasons(d0, d1));
	const stripSeasons = $derived(seasons(T0, T1));

	const clampX = (v: number) => Math.max(PAD.l, Math.min(W - PAD.r, v));
	const short = (s: string) => (s.length > 26 ? s.slice(0, 25) + '…' : s);
	/** the lane prints the fire's NAME alone — its date is where its flame
	 *  sits; the full label stays in the hover title */
	const laneName = (s: string) => fireEn(s).replace(/,\s*\d{2}-\d{4}.*$/, '');
	const grHa = (ha: number) =>
		ha >= 1000 ? `${Math.round(ha / 1000).toLocaleString('el-GR')}.000 ha` : `${Math.round(ha)} ha`;

	/* each act dot wears the CURRENT STATUS OF PROJECTS palette — same
	   source (ganttTheme) as the waffle and the map, so the vocabularies
	   cannot drift */
	const dotFill = (st?: string) =>
		st === 'nodate' ? NODATE_COLOR : (COLOR[st ?? ''] ?? 'var(--c-anadohoi)');
	const STATUS_WORD: Record<string, string> = {
		completed: 'completion act identified',
		active: 'within deadline — no completion act identified',
		nodate: 'no specific dates for implementation',
		no_completion_recorded: 'past deadline — no completion act identified',
		revoked: 'revoked'
	};

	/* ONE ACT, ONE COLUMN OF JOINED DOTS: an act answering several fires
	   draws a dot on each of their rows — all at the SAME date — joined by
	   a thin vertical tie (the UpSet convention); hovering any of its dots
	   lights the whole act. */
	const ties = $derived.by(() => {
		const rows = new Map<string, { d: string; ys: number[] }>();
		lanes.forEach((l, i) =>
			l.acts.forEach((a) => {
				const e = rows.get(a.ada) ?? { d: a.d, ys: [] };
				e.ys.push(y(i));
				rows.set(a.ada, e);
			})
		);
		return [...rows.entries()]
			.filter(([, e]) => e.ys.length > 1)
			.map(([ada, e]) => ({
				ada,
				x: x(e.d),
				y0: Math.min(...e.ys),
				y1: Math.max(...e.ys),
				n: e.ys.length
			}));
	});
	const multi = $derived(new Map(ties.map((t) => [t.ada, t.n])));
	let hovAda = $state<string | null>(null);

	/* the ONLY departure from true position: acts signed the SAME DAY on
	   the same row cannot overprint — they sit a hair apart (6.5 px), the
	   tie member keeping the true date so its tie passes through its own
	   dot alone (user, 2026-08-25: ΤΕΡΝΑ's and ΔΕΔΔΗΕ's acts are both of
	   06.09.2023). Near-but-different days are NOT moved — framing a
	   period on the strip separates them truthfully. */
	const GAP = 6.5;
	const dodged = $derived.by(() => {
		const out = new Map<string, number>();
		lanes.forEach((l, i) => {
			const byDay = new Map<string, { ada: string; pin: boolean }[]>();
			for (const a of l.acts) {
				const g = byDay.get(a.d) ?? [];
				g.push({ ada: a.ada, pin: multi.has(a.ada) });
				byDay.set(a.d, g);
			}
			for (const [d, g] of byDay) {
				if (g.length < 2) continue;
				g.sort((a, b) => Number(b.pin) - Number(a.pin) || a.ada.localeCompare(b.ada));
				const base = x(d);
				const pinned = g[0].pin;
				g.forEach((it, k) => {
					// a pinned member holds the true date and the rest step
					// right; with no member the pair sits symmetrically on it
					const off = pinned ? k * GAP : (k - (g.length - 1) / 2) * GAP;
					out.set(`${i}|${it.ada}`, base + off);
				});
			}
		});
		return out;
	});
	const dotX = (i: number, ada: string, d: string) => dodged.get(`${i}|${ada}`) ?? x(d);

	/* ---- the context strip (frame a period; the chart rescales) ---- */
	const STRIP_H = 30;
	let stripEl = $state<SVGSVGElement | null>(null);
	let drag: { mode: 'move' | 'l' | 'r' | 'new'; at: number; w: [number, number] } | null = null;
	const MIN_WIN = 5 * 864e5;

	const toVb = (e: PointerEvent) => {
		const r = stripEl!.getBoundingClientRect();
		return ((e.clientX - r.left) / r.width) * W;
	};
	const toT = (vb: number) => Math.max(T0, Math.min(T1, T0 + ((vb - PAD.l) / plotW) * (T1 - T0)));

	function stripDown(e: PointerEvent) {
		if (!stripEl) return;
		stripEl.setPointerCapture(e.pointerId);
		const vb = toVb(e);
		const t = toT(vb);
		if (win) {
			const e0 = xs(win[0]);
			const e1 = xs(win[1]);
			if (Math.abs(vb - e0) < 7) drag = { mode: 'l', at: t, w: [...win] };
			else if (Math.abs(vb - e1) < 7) drag = { mode: 'r', at: t, w: [...win] };
			else if (vb > e0 && vb < e1) drag = { mode: 'move', at: t, w: [...win] };
			else drag = { mode: 'new', at: t, w: [t, t] };
		} else drag = { mode: 'new', at: t, w: [t, t] };
	}
	function stripMove(e: PointerEvent) {
		if (!drag || !stripEl) return;
		const t = toT(toVb(e));
		if (drag.mode === 'new') {
			const a = Math.min(drag.at, t);
			const b = Math.max(drag.at, t);
			if (b - a >= MIN_WIN) win = [a, b];
		} else if (drag.mode === 'move') {
			const dt = t - drag.at;
			let a = drag.w[0] + dt;
			let b = drag.w[1] + dt;
			if (a < T0) {
				b += T0 - a;
				a = T0;
			}
			if (b > T1) {
				a -= b - T1;
				b = T1;
			}
			win = [a, b];
		} else if (drag.mode === 'l') {
			win = [Math.min(t, drag.w[1] - MIN_WIN), drag.w[1]];
		} else {
			win = [drag.w[0], Math.max(t, drag.w[0] + MIN_WIN)];
		}
	}
	function stripUp() {
		drag = null;
	}
</script>

<figure class="fr">
	<!-- the legend in the TIMELINE panel's own organisation (user,
	     2026-08-25): a HOW-TO-READ-A-ROW schematic on the left, the dot
	     colour key as a column, the marks beside it — one tinted strip -->
	<div class="legendbox">
		<div class="how" role="img" aria-label="How to read a row of this chart">
			<div class="mrow">
				<span class="m mfire">fire event<br /><small>area ∝ ha burnt (EFFIS)</small></span>
				<span class="m macts">the acts connected to it</span>
			</div>
			<div class="lanedemo">
				<i class="dburn"></i>
				<i class="dwait"></i>
				<i class="ddot" style:background={COLOR.completed}></i>
				<i class="ddot g2" style:background={COLOR.active}></i>
				<i class="ddot g3" style:background={COLOR.no_completion_recorded}></i>
			</div>
			<div class="tiedemo">
				<span class="tglyph">
					<i class="tline"></i>
					<i class="tdot t1" style:background={COLOR.completed}></i>
					<i class="tdot t2" style:background={COLOR.completed}></i>
				</span>
				<span class="tcap">one act for more than one fire events</span>
			</div>
		</div>

		<ul class="pkey">
			<li class="phead">each dot is one designation act, coloured by the project's status</li>
			<li><i style:background={COLOR.completed}></i>completion act identified</li>
			<li><i style:background={COLOR.active}></i>within deadline — no completion act identified</li>
			<li><i style:background={NODATE_COLOR}></i>no specific dates for implementation</li>
			<li>
				<i style:background={COLOR.no_completion_recorded}></i>past deadline — no completion act
				identified
			</li>
			<li><i style:background={COLOR.revoked}></i>revoked</li>
		</ul>

		<ul class="mkey">
			<li><i class="season"></i>fire season, 1 May – 31 Oct</li>
		</ul>
	</div>

	<svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Fire to first designation act, per fire">
		<defs>
			<clipPath id="fr-plot"><rect x={PAD.l} y="0" width={plotW} height={H} /></clipPath>
		</defs>
		<!-- what the two text columns hold -->
		<text x={PAD.l - 8} y={PAD.t - 11} class="colhead">FIRE</text>
		<text x={W - 6} y={PAD.t - 11} class="colhead">DAYS TO FIRST ACT</text>

		<g clip-path="url(#fr-plot)">
			<!-- the fire seasons, behind everything -->
			{#each chartSeasons as s (s.x0)}
				<rect
					x={clampX(x(s.x0))}
					y={PAD.t - 6}
					width={Math.max(0, clampX(x(s.x1)) - clampX(x(s.x0)))}
					height={lanes.length * LANE + 8}
					class="season"
				/>
			{/each}
			{#each chartRules as r (r.t)}
				<line
					x1={x(r.t)}
					y1={PAD.t - 6}
					x2={x(r.t)}
					y2={PAD.t + lanes.length * LANE + 2}
					class="yr"
					class:minor={r.minor}
				/>
				{#if x(r.t) < W - PAD.r - 40}
					<text x={x(r.t)} y={PAD.t - 11} class="yrlab" class:minor={r.minor}>{r.lab}</text>
				{/if}
			{/each}

			<!-- the one-act ties, under the dots -->
			{#each ties as tie (tie.ada)}
				<line
					x1={tie.x}
					y1={tie.y0}
					x2={tie.x}
					y2={tie.y1}
					class="tie"
					class:hot={hovAda === tie.ada}
				/>
			{/each}
		</g>

		{#each lanes as l, i (l.fire)}
			{@const xb = x(l.burn_date!)}
			{@const xa = x(l.first_start!)}
			<g class="lane">
				<text x={PAD.l - 8} y={y(i) + 3.8} class="name"
					>{short(laneName(l.fire))}<title>{fireEn(l.fire)}</title></text
				>
				<g clip-path="url(#fr-plot)">
					<!-- the wait: burn → first act -->
					<line x1={xb} y1={y(i)} x2={xa} y2={y(i)} class="wait" />
					{#each l.acts as a (a.ada)}
						{@const nFires = multi.get(a.ada)}
						<a
							href={`/anadohoi/project/${a.ada}`}
							onmouseenter={() => (hovAda = a.ada)}
							onmouseleave={() => (hovAda = null)}
						>
							<circle
								cx={dotX(i, a.ada, a.d)}
								cy={y(i)}
								r={hovAda === a.ada ? 4.4 : 3}
								class="act"
								style:fill={dotFill(a.st)}
							>
								<title
									>{fireEn(l.fire)} — designation act {dmy(a.d)}{nFires
										? ` · ONE act answering ${nFires} fires (the joined dots)`
										: ''}{a.st ? ` · ${STATUS_WORD[a.st] ?? a.st}` : ''}</title
								>
							</circle>
						</a>
					{/each}
					<circle cx={xb} cy={y(i)} r={rOf(l.burn_ha)} class="burn">
						<title
							>{fireEn(l.fire)} — burnt {dmy(l.burn_date!)}, {grHa(l.burn_ha)} (EFFIS); first
							sponsor appointed after {l.lag_days} days, {l.n} project{l.n === 1 ? '' : 's'} in all</title
						>
					</circle>
				</g>
				<text x={W - 6} y={y(i) + 3.8} class="lag">{l.lag_days} d</text>
			</g>
		{/each}
	</svg>

	<!-- the context strip: frame a period, the chart above rescales — the
	     disciplined kin of zoom (user, 2026-08-25) -->
	<svg
		bind:this={stripEl}
		viewBox={`0 0 ${W} ${STRIP_H}`}
		class="strip"
		role="slider"
		aria-label="Frame a period"
		aria-valuemin={T0}
		aria-valuemax={T1}
		aria-valuenow={d0}
		tabindex="-1"
		onpointerdown={stripDown}
		onpointermove={stripMove}
		onpointerup={stripUp}
		ondblclick={() => (win = null)}
	>
		<rect x={PAD.l} y="4" width={plotW} height={STRIP_H - 10} class="stripbg" />
		{#each stripSeasons as s (s.x0)}
			<rect
				x={xs(s.x0)}
				y="4"
				width={Math.max(0, Math.min(W - PAD.r, xs(s.x1)) - xs(s.x0))}
				height={STRIP_H - 10}
				class="season"
			/>
		{/each}
		{#each stripRules as r (r.t)}
			<line x1={xs(r.t)} y1="4" x2={xs(r.t)} y2={STRIP_H - 6} class="yr" />
			<text x={xs(r.t) + 3} y={STRIP_H - 9} class="striplab">{r.lab}</text>
		{/each}
		{#each lanes as l, i (l.fire)}
			{#each l.acts as a (a.ada + i)}
				<line x1={xs(a.d)} y1={STRIP_H - 12} x2={xs(a.d)} y2={STRIP_H - 6} class="acttick" />
			{/each}
		{/each}
		{#if win}
			<rect
				x={xs(win[0])}
				y="2"
				width={Math.max(2, xs(win[1]) - xs(win[0]))}
				height={STRIP_H - 6}
				class="window"
			/>
			<line x1={xs(win[0])} y1="2" x2={xs(win[0])} y2={STRIP_H - 4} class="edge" />
			<line x1={xs(win[1])} y1="2" x2={xs(win[1])} y2={STRIP_H - 4} class="edge" />
		{/if}
	</svg>
	<p class="striphint">
		{#if win}
			showing {dmy(new Date(d0).toISOString().slice(0, 10))} – {dmy(
				new Date(d1).toISOString().slice(0, 10)
			)} · drag the frame to move it, its edges to resize — double-click to see the whole period
		{:else}
			drag on the strip to frame a period — the chart rescales and close-together acts separate
		{/if}
	</p>
</figure>

<style>
	.fr {
		margin: 0;
	}
	svg {
		width: 100%;
		height: auto;
		display: block;
	}

	/* ---------- the legend, on the TIMELINE panel's model ---------- */
	.legendbox {
		display: grid;
		grid-template-columns: auto minmax(0, 1fr) max-content;
		gap: var(--sp-1) var(--sp-6);
		/* the three columns' FIRST lines share one line (user, 2026-08-25):
		   «fire event» · «the acts connected to it» · «each dot is …» ·
		   «fire season …» all start level */
		align-items: start;
		background: color-mix(in srgb, var(--ink) 5.8%, var(--paper));
		border-radius: 6px;
		padding: var(--sp-2) var(--sp-3);
		margin: 0 0 var(--sp-3);
		font-size: var(--fs-14);
		color: var(--ink-soft);
	}
	@media (max-width: 900px) {
		.legendbox {
			grid-template-columns: 1fr;
		}
	}
	/* the schematic: labels over one demo lane, then the tie demo */
	.how {
		width: 340px;
		max-width: 100%;
		line-height: 1.2;
	}
	.mrow {
		position: relative;
		height: 2.4em;
	}
	.m {
		position: absolute;
		bottom: 0;
		white-space: nowrap;
	}
	.m small {
		color: var(--ink-faint);
		font-size: var(--fs-12);
	}
	/* both labels share the TOP line (user, 2026-08-25); the fire's
	   sub-caption flows beneath its own */
	.m.mfire {
		left: 0;
		top: 0;
		bottom: auto;
	}
	.m.macts {
		left: 188px;
		transform: translateX(-50%);
		top: 0;
		bottom: auto;
	}
	.lanedemo {
		position: relative;
		height: 20px;
		margin-top: 4px;
	}
	.dburn {
		position: absolute;
		left: 2px;
		top: 3px;
		width: 13px;
		height: 13px;
		border-radius: 50%;
		background: var(--c-fire);
		opacity: 0.85;
	}
	.dwait {
		position: absolute;
		left: 20px;
		top: 9px;
		width: 132px;
		border-top: 1.5px dashed var(--ink-faint);
	}
	.ddot {
		position: absolute;
		top: 6px;
		width: 7px;
		height: 7px;
		border-radius: 50%;
		left: 155px;
	}
	.ddot.g2 {
		left: 190px;
	}
	.ddot.g3 {
		left: 214px;
	}
	.tiedemo {
		display: flex;
		align-items: center;
		gap: 10px;
		margin-top: var(--sp-2);
	}
	.tglyph {
		position: relative;
		width: 14px;
		height: 26px;
		flex: none;
	}
	.tline {
		position: absolute;
		left: 6px;
		top: 3px;
		bottom: 3px;
		width: 1.4px;
		background: var(--ink-faint);
	}
	.tdot {
		position: absolute;
		left: 3px;
		width: 7px;
		height: 7px;
		border-radius: 50%;
	}
	.tdot.t1 {
		top: 0;
	}
	.tdot.t2 {
		bottom: 0;
	}
	.tcap {
		min-width: 0;
	}
	/* the dot colour key, one column like the Gantt panel's */
	.pkey {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.pkey li {
		display: flex;
		align-items: center;
		gap: 8px;
		line-height: 1.25;
	}
	.pkey li.phead {
		color: var(--ink);
		margin-bottom: 2px;
	}
	.pkey i {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		flex: none;
	}
	.mkey {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: var(--sp-2);
	}
	.mkey li {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.mkey .season {
		width: 12px;
		height: 12px;
		border-radius: 2px;
		/* the season: the red's light shade (user, 2026-08-28) */
		background: var(--c-fire-season);
		flex: none;
	}

	/* ---------- the chart ---------- */
	.season {
		fill: var(--c-fire-season);
	}
	.yr {
		stroke: var(--line);
		stroke-width: 0.8;
	}
	.yr.minor {
		stroke-dasharray: 2 3;
	}
	.yrlab {
		font-size: 12px;
		fill: var(--ink-faint);
		font-variant-numeric: tabular-nums;
		/* centred on the rule it belongs to */
		text-anchor: middle;
	}
	.yrlab.minor {
		font-size: 10px;
	}
	.colhead {
		font-size: 11px;
		fill: var(--ink-faint);
		letter-spacing: 0.07em;
		text-anchor: end;
	}
	.name {
		font-size: 12.5px;
		fill: var(--ink-soft);
		text-anchor: end;
	}
	.wait {
		stroke: var(--ink-faint);
		stroke-width: 1;
		stroke-dasharray: 2 3;
	}
	.burn {
		fill: var(--c-fire);
		opacity: 0.85;
	}
	.act {
		/* fallback only — the status fill rides inline; no outline, and
		   hover NEVER recolours (black means revoked): it grows instead */
		fill: var(--c-anadohoi);
		cursor: pointer;
	}
	.tie {
		stroke: var(--ink-faint);
		stroke-width: 1.2;
	}
	.tie.hot {
		stroke: var(--ink-soft);
		stroke-width: 2;
	}
	.lag {
		text-anchor: end;
		font-size: 11.5px;
		fill: var(--ink-faint);
		font-variant-numeric: tabular-nums;
	}

	/* ---------- the context strip ---------- */
	.strip {
		margin-top: var(--sp-1);
		cursor: crosshair;
		touch-action: none;
	}
	.strip:focus {
		outline: none;
	}
	.stripbg {
		fill: color-mix(in srgb, var(--ink) 3.6%, var(--paper));
		stroke: var(--line);
		stroke-width: 0.6;
	}
	.striplab {
		font-size: 9.5px;
		fill: var(--ink-faint);
		font-variant-numeric: tabular-nums;
	}
	.acttick {
		stroke: var(--ink-faint);
		stroke-width: 1;
		opacity: 0.55;
	}
	.window {
		fill: rgba(45, 106, 79, 0.14);
		stroke: var(--c-anadohoi);
		stroke-width: 1;
		cursor: grab;
	}
	.edge {
		stroke: var(--c-anadohoi);
		stroke-width: 3;
		cursor: ew-resize;
	}
	.striphint {
		margin: 2px 0 0;
		font-size: var(--fs-12);
		color: var(--ink-faint);
		text-align: right;
	}
</style>
