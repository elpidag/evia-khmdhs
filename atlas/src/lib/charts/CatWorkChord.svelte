<script lang="ts">
	/**
	 * The category ↔ works connection as a CHORD diagram (user trial,
	 * 2026-08-23, several rounds): the 8 main categories hold the RIGHT
	 * half of the circle, the works named the LEFT half, a ribbon per
	 * (category, work) pair as wide as the number of contracts of that
	 * category naming that work. A bipartite chord — the square matrix is
	 * symmetric, so every ribbon runs from a category arc to a work arc.
	 *
	 * The two halves must READ as two different flaggings of one contract:
	 * the category half is FILLED in the category colours under the
	 * heading «MAIN CATEGORY · one per contract», the works half is the
	 * LIGHT GREY the ribbons fade to (user, 2026-08-23 — the hollow white
	 * arcs read oddly) under «WORKS NAMED IN THE TITLE · several per
	 * contract», the seams between them are wide (at the two poles —
	 * the circle is divided top to bottom), and every ribbon fades from
	 * its category's colour to a neutral grey at the work end.
	 *
	 * Labels are RADIAL (the user rejected a horizontal column) at the
	 * sizes the user approved; a name longer than the room at its angle
	 * wraps to TWO rows (user, 2026-08-23), so the circle stays big and the
	 * frame fits a screen without scrolling.
	 */
	import { chord, ribbon } from 'd3-chord';
	import { arc } from 'd3-shape';
	import { CAT_COLORS, CAT_ORDER } from './catColors';
	import { grInt } from '$lib/transforms/format';

	export interface CWRow {
		theme: string;
		label: string;
		n: number;
		by: { key: string; label: string; n: number }[];
	}
	interface Props {
		rows: CWRow[];
		/** the categories with their CONTRACT counts — the card prints
		 *  contracts, never the arc's mentions (user, 2026-08-23) */
		cats: { key: string; label: string; n: number }[];
	}
	let { rows, cats }: Props = $props();

	const W = 1120;
	const R = 200;
	const PAD = 0.022;
	/** zero-value spacer groups: d3-chord pads every group, so a spacer
	 *  between two arcs doubles their gap (room for two-row labels) and
	 *  three at each seam open the seam wide */
	const SEAM_SPACERS = 3;
	const CX = W / 2;
	const LABEL_R = R + 26;
	const CHAR_PX = 4.9; // the display face at 11.5px, MEASURED (4.84 regular / 4.73 bold)
	/** the vertical budget a label may reach beyond LABEL_R — more at the
	 *  top, where the small arcs of both halves fan out, than at the bottom
	 *  — what fixes the frame's height */
	const V_TOP = 125;
	const V_BOT = 105;
	const ROW_PX = 13.5; // one row of 11.5px text, perpendicular to the radius
	/** the headings sit at the SIDES, level with the centre (user,
	 *  2026-08-23), so nothing but the labels' own reach sits above the
	 *  circle — the whole graph fits a screen */
	const HEAD_ROOM = 6;
	const SEAM_STUB = 34; // the dashed seam marks are short stubs
	const RIB_END = '#c9c9c9';

	/** greedy word wrap into at most MAX_ROWS rows (three, for the one
	 *  sentence-long category name — user, 2026-08-23); a name that still
	 *  overflows is cut with «…» (full text on hover) */
	const MAX_ROWS = 3;
	const wrapRows = (s: string, perLine: number): string[] => {
		const lines: string[] = [];
		let cur = '';
		for (const w of s.split(/\s+/)) {
			if (cur && (cur + ' ' + w).length > perLine) {
				lines.push(cur);
				cur = w;
			} else cur = cur ? cur + ' ' + w : w;
		}
		if (cur) lines.push(cur);
		if (lines.length > MAX_ROWS) {
			const rest = lines.slice(MAX_ROWS - 1).join(' ');
			return [
				...lines.slice(0, MAX_ROWS - 1),
				rest.slice(0, Math.max(4, perLine - 1)).trimEnd() + '…'
			];
		}
		return lines;
	};
	/** no caps in the names (user): only the opening letter is dropped,
	 *  so a proper noun inside a name would stay */
	const lower = (s: string) => s.charAt(0).toLowerCase() + s.slice(1);
	/** the works in READING order up the left half (user, 2026-08-23):
	 *  the two big clearing/road works run on from the bottom seam, the four
	 *  firebreak works sit side by side, then the rest by count, «no
	 *  specific work named» last at the top seam */
	const WORK_ORDER = [
		'katharismoi',
		'odiko_diktyo',
		'syntirisi_zonon',
		'miktes_zones',
		'estegasmenes_zones',
		'psiles_zones'
	];

	const polar = (a: number, r: number) => ({ x: r * Math.sin(a), y: -r * Math.cos(a) });
	const arcPath = (r: number, a0: number, a1: number) => {
		const p0 = polar(a0, r);
		const p1 = polar(a1, r);
		const large = Math.abs(a1 - a0) > Math.PI ? 1 : 0;
		return `M${p0.x.toFixed(2)} ${p0.y.toFixed(2)}A${r} ${r} 0 ${large} 1 ${p1.x.toFixed(2)} ${p1.y.toFixed(2)}`;
	};

	const sc = $derived.by(() => {
		const rankW = (k: string) => {
			const i = WORK_ORDER.indexOf(k);
			return i >= 0 ? i : k === '_none' ? 1e6 : 1e3;
		};
		const rankC = (k: string) => {
			const i = CAT_ORDER.indexOf(k);
			return i >= 0 ? i : 1e3;
		};
		const orderedW = [...rows].sort((a, b) => rankW(a.theme) - rankW(b.theme) || b.n - a.n);
		const orderedC = cats
			.filter((c) => rows.some((r) => r.by.some((b) => b.key === c.key && b.n > 0)))
			.sort((a, b) => rankC(a.key) - rankC(b.key));
		type Ent = { id: string; label: string; kind: 'cat' | 'work' | 'gap'; key: string };
		const catEnts: Ent[] = orderedC.map((c) => ({ id: `c:${c.key}`, label: c.label, kind: 'cat', key: c.key }));
		const workEnts: Ent[] = orderedW.map((r) => ({
			id: `w:${r.theme}`,
			label: lower(r.label),
			kind: 'work',
			key: r.theme
		}));
		/** the layout for a given number of spacer groups between each pair of
		 *  neighbouring arcs (keyed `a|b`); one spacer is the floor */
		const build = (extra: Record<string, number>) => {
			let gi = 0;
			const gap = (): Ent => ({ id: `g:${gi++}`, label: '', kind: 'gap', key: '' });
			const spaced = (es: Ent[]) =>
				es.flatMap((e, k) =>
					k ? [...Array.from({ length: 1 + (extra[`${es[k - 1].id}|${e.id}`] ?? 0) }, gap), e] : [e]
				);
			const names: Ent[] = [
				...spaced(catEnts),
				...Array.from({ length: SEAM_SPACERS }, gap),
				...spaced(workEnts),
				...Array.from({ length: SEAM_SPACERS }, gap)
			];
			const n = names.length;
			const idx = new Map(names.map((e, i) => [e.id, i]));
			const M: number[][] = Array.from({ length: n }, () => new Array(n).fill(0));
			for (const r of rows)
				for (const b of r.by) {
					const i = idx.get(`c:${b.key}`);
					const j = idx.get(`w:${r.theme}`);
					if (i == null || j == null) continue;
					M[i][j] = b.n;
					M[j][i] = b.n;
				}
			return { names, lay: chord().padAngle(PAD)(M) };
		};
		const ringArc = arc<{ startAngle: number; endAngle: number }>().innerRadius(R).outerRadius(R + 14);
		const rib = ribbon().radius(R - 1);

		// the rows a label needs at a given pointing angle: the room is the
		// frame's side horizontally and the vertical budget towards top or
		// bottom; a name longer than one row wraps
		const linesAt = (label: string, kind: string, a: number) => {
			const sin = Math.abs(Math.sin(a));
			const cos = Math.abs(Math.cos(a));
			const vb = Math.cos(a) > 0 ? V_TOP : V_BOT;
			const room =
				Math.min(
					sin > 1e-6 ? (CX - 10 - LABEL_R) / sin : Infinity,
					cos > 1e-6 ? vb / cos : Infinity
				) - 8;
			const px = kind === 'cat' ? CHAR_PX : CHAR_PX; // bold is wider
			const chars = Math.max(10, Math.floor(room / px));
			return label.length <= chars ? [label] : wrapRows(label, chars);
		};
		const groupsOf = (names: Ent[], lay: ReturnType<ReturnType<typeof chord>>) =>
			lay.groups
				.filter((g) => names[g.index].kind !== 'gap')
				.map((g) => {
					const e = names[g.index];
					const mid = (g.startAngle + g.endAngle) / 2;
					return {
						...e,
						i: g.index,
						a0: g.startAngle,
						a1: g.endAngle,
						d: ringArc({ startAngle: g.startAngle, endAngle: g.endAngle }) ?? '',
						value: g.value,
						/** the arc's own middle */
						angle: mid,
						/** where the label points — slides off `angle` only when a
						 *  neighbour's label is still too close (then a tick leads back) */
						la: mid,
						lines: linesAt(e.label, e.kind, mid),
						flip: mid > Math.PI
					};
				});
		// ADAPTIVE SPACERS (user, 2026-08-23: as few connector ticks as
		// possible): a first layout tells how many rows each label needs at
		// its arc; where two neighbouring arcs sit closer than their labels'
		// rows need, spacer groups are inserted between them so the arcs
		// themselves move apart and the labels can stay ON their arcs
		const first = build({});
		const probe = groupsOf(first.names, first.lay);
		const extra: Record<string, number> = {};
		for (const kind of ['cat', 'work'] as const) {
			const col = probe.filter((g) => g.kind === kind).sort((a, b) => a.angle - b.angle);
			for (let k = 1; k < col.length; k++) {
				const a = col[k - 1];
				const b = col[k];
				const need = (((a.lines.length + b.lines.length) / 2) * ROW_PX + 5) / LABEL_R;
				const have = b.angle - a.angle;
				if (have < need) extra[`${a.id}|${b.id}`] = Math.min(6, Math.ceil((need - have) / PAD));
			}
		}
		const { names, lay } = build(extra);
		const groups = groupsOf(names, lay);
		// de-collide the label ANGLES within each half: two radial labels need
		// their rows' worth of perpendicular room at LABEL_R; a forward pass
		// pushes clockwise, a backward pass pulls back inside the half — then
		// the rows are recomputed at the new angles and the pass repeats once
		const decollide = () => {
			for (const kind of ['cat', 'work'] as const) {
				const col = groups.filter((g) => g.kind === kind).sort((a, b) => a.la - b.la);
				if (!col.length) continue;
				const need = (a: (typeof col)[number], b: (typeof col)[number]) =>
					(((a.lines.length + b.lines.length) / 2) * ROW_PX + 5) / LABEL_R;
				for (let k = 1; k < col.length; k++)
					col[k].la = Math.max(col[k].la, col[k - 1].la + need(col[k - 1], col[k]));
				const end = Math.max(...col.map((g) => g.a1)) - 0.02;
				for (let k = col.length - 1; k >= 0; k--) {
					const cap = k === col.length - 1 ? end : col[k + 1].la - need(col[k], col[k + 1]);
					if (col[k].la > cap) col[k].la = cap;
				}
			}
			for (const g of groups) {
				g.lines = linesAt(g.label, g.kind, g.la);
				g.flip = g.la > Math.PI;
			}
		};
		decollide();
		decollide();
		// the frame hugs the labels' ACTUAL reach above and below the centre
		// (the budgets are only the cap), so no slack sits over the circle
		const reachOf = (g: (typeof groups)[number]) => {
			const px = g.kind === 'cat' ? CHAR_PX : CHAR_PX;
			const len = Math.max(...g.lines.map((l) => l.length)) * px + 8;
			const along = (LABEL_R + len) * Math.abs(Math.cos(g.la));
			const across = ((g.lines.length * ROW_PX) / 2) * Math.abs(Math.sin(g.la));
			return { up: Math.cos(g.la) > 0 ? along + across : 0, down: Math.cos(g.la) < 0 ? along + across : 0 };
		};
		const floor = R + 24 + SEAM_STUB + 4;
		const topNeed = Math.max(floor, ...groups.map((g) => reachOf(g).up));
		const bottomNeed = Math.max(floor, ...groups.map((g) => reachOf(g).down));
		const CY = HEAD_ROOM + topNeed;
		const H = CY + bottomNeed + 10;

		const chords = lay.map((c) => {
			const s = names[c.source.index];
			const t = names[c.target.index];
			const catEnd = s.kind === 'cat' ? c.source : c.target;
			const workEnd = s.kind === 'cat' ? c.target : c.source;
			const cat = s.kind === 'cat' ? s : t;
			const work = s.kind === 'cat' ? t : s;
			const p0 = polar((catEnd.startAngle + catEnd.endAngle) / 2, R);
			const p1 = polar((workEnd.startAngle + workEnd.endAngle) / 2, R);
			return {
				key: `${c.source.index}-${c.target.index}`,
				d: rib(c as never) as unknown as string,
				catKey: cat.key,
				si: c.source.index,
				ti: c.target.index,
				n: c.source.value,
				catLabel: cat.label,
				workLabel: work.label,
				grad: { x1: p0.x, y1: p0.y, x2: p1.x, y2: p1.y }
			};
		});
		const half = (kind: 'cat' | 'work') => {
			const gs = groups.filter((g) => g.kind === kind);
			return arcPath(R + 19, Math.min(...gs.map((g) => g.a0)), Math.max(...gs.map((g) => g.a1)));
		};
		return { groups, chords, catBracket: half('cat'), workBracket: half('work'), CY, H };
	});

	let hotGroup = $state<number | null>(null);
	let hotChord = $state<(typeof sc.chords)[number] | null>(null);
	const chordLit = (c: (typeof sc.chords)[number]) =>
		hotChord ? hotChord.key === c.key : hotGroup == null ? true : c.si === hotGroup || c.ti === hotGroup;
	const groupLit = (g: (typeof sc.groups)[number]) =>
		hotChord
			? g.i === hotChord.si || g.i === hotChord.ti
			: hotGroup == null
				? true
				: g.i === hotGroup ||
					sc.chords.some((c) => (c.si === hotGroup && c.ti === g.i) || (c.ti === hotGroup && c.si === g.i));
	const deg = (a: number) => (a * 180) / Math.PI - 90;
</script>

<figure class="cw">
	<svg viewBox="0 0 {W} {sc.H}" role="img" aria-label="Main categories and the works their contracts name, as a chord diagram">
		<defs>
			{#each sc.chords as c (c.key)}
				<linearGradient
					id={`cwg-${c.key}`}
					gradientUnits="userSpaceOnUse"
					x1={c.grad.x1}
					y1={c.grad.y1}
					x2={c.grad.x2}
					y2={c.grad.y2}
				>
					<stop offset="0.15" stop-color={CAT_COLORS[c.catKey] ?? '#9b9b9b'} />
					<stop offset="0.85" stop-color={RIB_END} />
				</linearGradient>
			{/each}
		</defs>
		<!-- the headings, at the sides, level with the centre; the seam is
		     marked by short dashed stubs beyond the ring -->
		<text class="head" x="8" y={sc.CY - 4} text-anchor="start">WORKS NAMED IN THE TITLE</text>
		<text class="head sub" x="8" y={sc.CY + 12} text-anchor="start">several per contract</text>
		<text class="head" x={W - 8} y={sc.CY - 4} text-anchor="end">MAIN CATEGORY</text>
		<text class="head sub" x={W - 8} y={sc.CY + 12} text-anchor="end">one per contract</text>
		<line class="seam" x1={CX} y1={sc.CY - R - 24 - SEAM_STUB} x2={CX} y2={sc.CY - R - 24} />
		<line class="seam" x1={CX} y1={sc.CY + R + 24} x2={CX} y2={sc.CY + R + 24 + SEAM_STUB} />
		<g transform="translate({CX} {sc.CY})">
			{#each sc.chords as c (c.key)}
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<path
					d={c.d}
					class="rib"
					fill={`url(#cwg-${c.key})`}
					opacity={chordLit(c) ? 0.8 : 0.08}
					onmouseenter={() => (hotChord = c)}
					onmouseleave={() => (hotChord = null)}
				/>
			{/each}
			{#each sc.groups as g (g.id)}
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<path
					d={g.d}
					class="grp"
					class:work={g.kind === 'work'}
					fill={g.kind === 'cat' ? (CAT_COLORS[g.key] ?? '#9b9b9b') : RIB_END}
					opacity={groupLit(g) ? 1 : 0.25}
					onmouseenter={() => (hotGroup = g.i)}
					onmouseleave={() => (hotGroup = null)}
				/>
				{#if Math.abs(g.la - g.angle) > 0.006}
					{@const a = polar(g.angle, R + 15)}
					{@const b = polar(g.la, LABEL_R - 5)}
					<line class="tick" x1={a.x} y1={a.y} x2={b.x} y2={b.y} opacity={groupLit(g) ? 1 : 0.25} />
				{/if}
				<text
					class="lbl"
					class:cat={g.kind === 'cat'}
					transform={`rotate(${deg(g.la)}) translate(${LABEL_R} 0) ${g.flip ? 'rotate(180)' : ''}`}
					text-anchor={g.flip ? 'end' : 'start'}
					opacity={groupLit(g) ? 1 : 0.3}
					><title>{g.label} — {grInt(g.value)}</title>{#each g.lines as ln, k (k)}<tspan
							x="0"
							dy={k === 0 ? `${(0.35 - 0.55 * (g.lines.length - 1)).toFixed(2)}em` : '1.1em'}>{ln}</tspan
						>{/each}</text
				>
			{/each}
			<path d={sc.catBracket} class="bracket" />
			<path d={sc.workBracket} class="bracket" />
		</g>
	</svg>
	<!-- every card says CONTRACTS and nothing else (user, 2026-08-23): a
	     ribbon = the contracts of that category naming that work; a work
	     arc = the contracts naming it; a category arc = its contracts (the
	     arc itself is drawn to mentions — the bulb says so once) -->
	<!-- …and just the number (user): the names are already lit on the chart -->
	{#if hotChord}
		<div class="card"><strong>{grInt(hotChord.n)} contracts</strong></div>
	{:else if hotGroup != null}
		{@const g = sc.groups.find((x) => x.i === hotGroup)}
		{#if g}
			<div class="card">
				<strong
					>{grInt(g.kind === 'cat' ? (cats.find((c) => c.key === g.key)?.n ?? 0) : g.value)} contracts</strong
				>
			</div>
		{/if}
	{/if}
</figure>

<style>
	.cw {
		margin: 0;
		position: relative;
	}
	svg {
		width: 100%;
		height: auto;
		display: block;
	}
	.rib {
		stroke: none;
		transition: opacity 0.12s;
		cursor: default;
	}
	.grp {
		cursor: default;
		transition: opacity 0.12s;
		/* a paper hairline keeps each arc's edge where a ribbon of the same
		   grey meets it */
		stroke: var(--paper);
		stroke-width: 1;
	}
	.bracket {
		fill: none;
		stroke: var(--line-strong);
		stroke-width: 1;
	}
	.head {
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.08em;
		fill: var(--ink);
		pointer-events: none;
	}
	.head.sub {
		font-weight: 400;
		letter-spacing: 0;
		fill: var(--ink-soft);
	}
	.tick {
		stroke: var(--line-strong);
		stroke-width: 0.8;
	}
	.seam {
		stroke: var(--line-strong);
		stroke-width: 1;
		stroke-dasharray: 2 4;
	}
	.lbl {
		font-size: 11.5px;
		fill: var(--ink-soft);
		pointer-events: none;
	}
	.lbl.cat {
		fill: var(--ink);
		font-weight: 700;
	}
	.card {
		/* the hover card sits at the TOP-RIGHT corner (user, 2026-08-23) */
		position: absolute;
		right: 0;
		top: 0;
		background: #000;
		color: #fff;
		padding: 8px 10px;
		display: grid;
		gap: 2px;
		font-size: var(--fs-12);
		pointer-events: none;
		max-width: 22rem;
	}
</style>
