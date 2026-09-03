<script lang="ts">
	/**
	 * TYPES OF WORKS as a CHORD diagram (user, 2026-08-23, many rounds):
	 * two flaggings of the same 245 contracts, one per half of the circle,
	 * a ribbon per pair as wide as the number of contracts carrying both.
	 * The halves come in as DATA (`$lib/transforms/chordSides`): the right
	 * half is the coloured, one-per-contract flagging (main category, or
	 * the contract scope), the left half the works named (grey arcs — the
	 * light grey the ribbons fade to) or the scope; the matrix counts
	 * contracts. A bipartite chord — the square matrix is symmetric, so
	 * every ribbon runs from a right arc to a left arc.
	 *
	 * The circle is divided top to bottom: wide seams at the two poles,
	 * the headings at the SIDES level with the centre (each heading carries
	 * the half's toggle), short dashed stubs marking the seam. Labels are
	 * RADIAL at 11.5 px, wrapping to up to three rows where the room at
	 * their angle runs out; adaptive spacer groups between neighbouring
	 * arcs keep every label ON its arc; the frame's height hugs the labels'
	 * measured reach. The hover card, top-right, says only «N contracts».
	 */
	import type { Snippet } from 'svelte';
	import { chord, ribbon } from 'd3-chord';
	import { arc } from 'd3-shape';
	import type { ChordData } from '$lib/transforms/chordSides';
	import { grInt } from '$lib/transforms/format';

	interface Props {
		data: ChordData;
		/** the toggles rendered under each heading */
		leftControl?: Snippet;
		rightControl?: Snippet;
	}
	let { data, leftControl, rightControl }: Props = $props();

	const W = 1120;
	const R = 200;
	const PAD = 0.022;
	/** zero-value spacer groups: d3-chord pads every group, so spacers
	 *  between two arcs open their gap; three at each seam open the seam */
	const SEAM_SPACERS = 3;
	const CX = W / 2;
	const LABEL_R = R + 26;
	const CHAR_PX = 4.9; // the display face at 11.5px, MEASURED (4.84 regular / 4.73 bold)
	/** the vertical budget a label may reach beyond LABEL_R — more at the
	 *  top, where the small arcs of both halves fan out, than at the bottom */
	const V_TOP = 125;
	const V_BOT = 105;
	const ROW_PX = 13.5; // one row of 11.5px text, perpendicular to the radius
	const HEAD_ROOM = 6;
	const SEAM_STUB = 34;
	const RIB_END = 'color-mix(in srgb, var(--ink) 23.9%, var(--paper))';
	const MAX_ROWS = 3;

	/** greedy word wrap into at most MAX_ROWS rows; a name that still
	 *  overflows is cut with «…» (full text on hover) */
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
			return [...lines.slice(0, MAX_ROWS - 1), rest.slice(0, Math.max(4, perLine - 1)).trimEnd() + '…'];
		}
		return lines;
	};

	const polar = (a: number, r: number) => ({ x: r * Math.sin(a), y: -r * Math.cos(a) });
	const arcPath = (r: number, a0: number, a1: number) => {
		const p0 = polar(a0, r);
		const p1 = polar(a1, r);
		const large = Math.abs(a1 - a0) > Math.PI ? 1 : 0;
		return `M${p0.x.toFixed(2)} ${p0.y.toFixed(2)}A${r} ${r} 0 ${large} 1 ${p1.x.toFixed(2)} ${p1.y.toFixed(2)}`;
	};

	type Ent = { id: string; label: string; side: 'right' | 'left' | 'gap'; key: string; n: number; color: string };

	const sc = $derived.by(() => {
		const rightEnts: Ent[] = data.right.items.map((it) => ({
			id: `r:${it.key}`,
			label: it.label,
			side: 'right',
			key: it.key,
			n: it.n,
			color: it.color ?? 'color-mix(in srgb, var(--ink) 44.5%, var(--paper))'
		}));
		const leftEnts: Ent[] = data.left.items.map((it) => ({
			id: `l:${it.key}`,
			label: it.label,
			side: 'left',
			key: it.key,
			n: it.n,
			color: it.color ?? RIB_END
		}));
		/** the layout for a given number of spacer groups between each pair of
		 *  neighbouring arcs (keyed `a|b`); one spacer is the floor */
		const build = (extra: Record<string, number>) => {
			let gi = 0;
			const gap = (): Ent => ({ id: `g:${gi++}`, label: '', side: 'gap', key: '', n: 0, color: '' });
			const spaced = (es: Ent[]) =>
				es.flatMap((e, k) =>
					k ? [...Array.from({ length: 1 + (extra[`${es[k - 1].id}|${e.id}`] ?? 0) }, gap), e] : [e]
				);
			const names: Ent[] = [
				...spaced(rightEnts),
				...Array.from({ length: SEAM_SPACERS }, gap),
				...spaced(leftEnts),
				...Array.from({ length: SEAM_SPACERS }, gap)
			];
			const n = names.length;
			const idx = new Map(names.map((e, i) => [e.id, i]));
			const M: number[][] = Array.from({ length: n }, () => new Array(n).fill(0));
			for (const r of rightEnts)
				for (const l of leftEnts) {
					const v = data.matrix[`${r.key}|${l.key}`] ?? 0;
					if (!v) continue;
					const i = idx.get(r.id)!;
					const j = idx.get(l.id)!;
					M[i][j] = v;
					M[j][i] = v;
				}
			return { names, lay: chord().padAngle(PAD)(M) };
		};
		const ringArc = arc<{ startAngle: number; endAngle: number }>().innerRadius(R).outerRadius(R + 14);
		const rib = ribbon().radius(R - 1);

		// the rows a label needs at a given pointing angle: the room is the
		// frame's side horizontally and the vertical budget towards top or
		// bottom; a name longer than one row wraps
		const linesAt = (label: string, a: number) => {
			const sin = Math.abs(Math.sin(a));
			const cos = Math.abs(Math.cos(a));
			const vb = Math.cos(a) > 0 ? V_TOP : V_BOT;
			const room =
				Math.min(
					sin > 1e-6 ? (CX - 10 - LABEL_R) / sin : Infinity,
					cos > 1e-6 ? vb / cos : Infinity
				) - 8;
			const chars = Math.max(10, Math.floor(room / CHAR_PX));
			return label.length <= chars ? [label] : wrapRows(label, chars);
		};
		const groupsOf = (names: Ent[], lay: ReturnType<ReturnType<typeof chord>>) =>
			lay.groups
				.filter((g) => names[g.index].side !== 'gap')
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
						angle: mid,
						/** where the label points — slides off `angle` only when a
						 *  neighbour's label is still too close (then a tick leads back) */
						la: mid,
						lines: linesAt(e.label, mid),
						flip: mid > Math.PI
					};
				});
		// ADAPTIVE SPACERS: a first layout tells how many rows each label needs
		// at its arc; where two neighbouring arcs sit closer than their
		// labels' rows need, spacer groups are inserted between them so the
		// arcs themselves move apart and the labels can stay ON their arcs
		const first = build({});
		const probe = groupsOf(first.names, first.lay);
		const extra: Record<string, number> = {};
		for (const side of ['right', 'left'] as const) {
			const col = probe.filter((g) => g.side === side).sort((a, b) => a.angle - b.angle);
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
		// the safety net: de-collide the label ANGLES within each half
		const decollide = () => {
			for (const side of ['right', 'left'] as const) {
				const col = groups.filter((g) => g.side === side).sort((a, b) => a.la - b.la);
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
				g.lines = linesAt(g.label, g.la);
				g.flip = g.la > Math.PI;
			}
		};
		decollide();
		decollide();
		// the frame hugs the labels' ACTUAL reach above and below the centre
		const reachOf = (g: (typeof groups)[number]) => {
			const len = Math.max(...g.lines.map((l) => l.length)) * CHAR_PX + 8;
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
			const rEnd = s.side === 'right' ? c.source : c.target;
			const lEnd = s.side === 'right' ? c.target : c.source;
			const rightEnt = s.side === 'right' ? s : t;
			const p0 = polar((rEnd.startAngle + rEnd.endAngle) / 2, R);
			const p1 = polar((lEnd.startAngle + lEnd.endAngle) / 2, R);
			return {
				key: `${c.source.index}-${c.target.index}`,
				d: rib(c as never) as unknown as string,
				color: rightEnt.color,
				si: c.source.index,
				ti: c.target.index,
				n: c.source.value,
				grad: { x1: p0.x, y1: p0.y, x2: p1.x, y2: p1.y }
			};
		});
		const half = (side: 'right' | 'left') => {
			const gs = groups.filter((g) => g.side === side);
			return arcPath(R + 19, Math.min(...gs.map((g) => g.a0)), Math.max(...gs.map((g) => g.a1)));
		};
		return { groups, chords, rightBracket: half('right'), leftBracket: half('left'), CY, H };
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
	const hotCount = $derived.by(() => {
		if (hotChord) return hotChord.n;
		if (hotGroup == null) return null;
		const g = sc.groups.find((x) => x.i === hotGroup);
		return g ? g.n : null;
	});
</script>

<figure class="cw">
	<svg viewBox="0 0 {W} {sc.H}" role="img" aria-label="{data.right.heading} and {data.left.heading}, as a chord diagram">
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
					<stop offset="0.15" stop-color={c.color} />
					<stop offset="0.85" stop-color={RIB_END} />
				</linearGradient>
			{/each}
		</defs>
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
					fill={g.color}
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
					class:strong={g.side === 'right'}
					transform={`rotate(${deg(g.la)}) translate(${LABEL_R} 0) ${g.flip ? 'rotate(180)' : ''}`}
					text-anchor={g.flip ? 'end' : 'start'}
					opacity={groupLit(g) ? 1 : 0.3}
					><title>{g.label} — {grInt(g.n)} contracts</title>{#each g.lines as ln, k (k)}<tspan
							x="0"
							dy={k === 0 ? `${(0.35 - 0.55 * (g.lines.length - 1)).toFixed(2)}em` : '1.1em'}>{ln}</tspan
						>{/each}</text
				>
			{/each}
			<path d={sc.rightBracket} class="bracket" />
			<path d={sc.leftBracket} class="bracket" />
		</g>
	</svg>

	<!-- the headings, at the sides level with the centre, each with the
	     half's toggle under it -->
	<div class="head left" style:top={`${(sc.CY / sc.H) * 100}%`}>
		<strong>{data.left.heading}</strong>
		<span>{data.left.sub}</span>
		{#if leftControl}{@render leftControl()}{/if}
	</div>
	<div class="head right" style:top={`${(sc.CY / sc.H) * 100}%`}>
		<strong>{data.right.heading}</strong>
		<span>{data.right.sub}</span>
		{#if rightControl}{@render rightControl()}{/if}
	</div>

	{#if hotCount != null}
		<div class="card"><strong>{grInt(hotCount)} contracts</strong></div>
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
	.lbl.strong {
		fill: var(--ink);
		font-weight: 700;
	}
	.head {
		position: absolute;
		transform: translateY(-50%);
		display: grid;
		gap: 2px;
		font-size: 11px;
		line-height: 1.25;
		pointer-events: none;
	}
	.head.left {
		left: 8px;
		text-align: left;
		justify-items: start;
	}
	.head.right {
		right: 8px;
		text-align: right;
		justify-items: end;
	}
	.head strong {
		font-weight: 700;
		letter-spacing: 0.08em;
		color: var(--ink);
	}
	.head span {
		color: var(--ink-soft);
	}
	.head :global(.toggle) {
		margin-top: 6px;
		pointer-events: auto;
	}
	.card {
		position: absolute;
		right: 0;
		top: 0;
		background: var(--ink);
		color: var(--paper);
		padding: 8px 10px;
		font-size: var(--fs-12);
		pointer-events: none;
	}
</style>
