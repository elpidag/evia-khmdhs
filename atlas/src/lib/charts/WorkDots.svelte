<script lang="ts">
	/**
	 * TYPES OF WORKS as the Flourish «Company ownership» form the user
	 * picked (2026-08-22, second round): one dot per CONTRACT-NAMING-A-WORK,
	 * clustered by the work named, COLOURED by the contract's main
	 * category — the interactive bridge between the 8 categories and the
	 * works. A contract appears in every cluster its title names (the
	 * counts say so honestly); hovering any of its dots lights all of
	 * them, and hovering a category chip lights that category everywhere.
	 * Phyllotaxis discs, greedy-wrapped rows, no simulation.
	 */
	import { CAT_COLORS } from './catColors';
	import { eur } from '$lib/transforms/format';

	interface Dot {
		ref: string;
		eur?: number | null;
		cat?: string | null;
		wk?: string[];
	}
	interface Props {
		nodes: Dot[];
		/** theme key → label, display order = descending count */
		themes: { theme: string; label: string }[];
		/** category key → short label, for the chips and the card */
		catLabels: Record<string, string>;
		/** label of the cluster for contracts naming no work */
		noneLabel: string;
	}
	let { nodes, themes, catLabels, noneLabel }: Props = $props();

	const W = 1120;
	const GOLD = Math.PI * (3 - Math.sqrt(5));
	const DOT_R = 4.4;
	const C = 9.8;
	const GAP = 30;
	const MIN_C2C = 112;
	const LABEL_HALF = 56;

	const wrap = (s: string, max = 17): string[] => {
		const out: string[] = [];
		let line = '';
		for (const w of s.split(/\s+/)) {
			if (line && (line + ' ' + w).length > max) {
				out.push(line);
				line = w;
			} else line = line ? line + ' ' + w : w;
		}
		if (line) out.push(line);
		return out;
	};

	const sc = $derived.by(() => {
		const groups = [
			...themes.map((t) => ({
				key: t.theme,
				label: t.label,
				ds: nodes.filter((n) => (n.wk ?? []).includes(t.theme))
			})),
			{ key: 'none', label: noneLabel, ds: nodes.filter((n) => !(n.wk ?? []).length) }
		]
			.filter((g) => g.ds.length)
			.map((g) => ({
				...g,
				ds: [...g.ds].sort((a, b) => (b.eur ?? 0) - (a.eur ?? 0) || a.ref.localeCompare(b.ref)),
				R: (g.ds.length > 1 ? C * Math.sqrt(g.ds.length - 1) : 0) + DOT_R + 2
			}));
		// biggest first, the naming-nothing cluster always LAST (the same
		// convention as the works × category rows)
		groups.sort((a, b) =>
			a.key === 'none' ? 1 : b.key === 'none' ? -1 : b.ds.length - a.ds.length
		);
		// greedy row wrap: discs bottom-aligned per row, labels under
		type G = (typeof groups)[number] & { cx: number; cy: number; lines: string[] };
		const rows: G[][] = [];
		let row: G[] = [];
		let x = 0;
		let prevR = 0;
		for (const g of groups) {
			const cx = row.length === 0 ? Math.max(g.R, LABEL_HALF) : x + Math.max(prevR + g.R + GAP, MIN_C2C);
			if (row.length && cx + Math.max(g.R, LABEL_HALF) > W) {
				rows.push(row);
				row = [];
				x = Math.max(g.R, LABEL_HALF);
			} else x = cx;
			row.push({ ...g, cx: x, cy: 0, lines: wrap(g.label) });
			prevR = g.R;
		}
		if (row.length) rows.push(row);

		let yTop = 4;
		const placed: {
			key: string;
			cx: number;
			base: number;
			n: number;
			lines: string[];
			dots: { ref: string; eur?: number | null; cat?: string | null; x: number; y: number }[];
		}[] = [];
		for (const r of rows) {
			const maxR = Math.max(...r.map((g) => g.R));
			const base = yTop + 2 * maxR;
			const maxLines = Math.max(...r.map((g) => g.lines.length));
			for (const g of r) {
				const cy = base - g.R;
				placed.push({
					key: g.key,
					cx: g.cx,
					base,
					n: g.ds.length,
					lines: g.lines,
					dots: g.ds.map((d, k) => ({
						ref: d.ref,
						eur: d.eur,
						cat: d.cat,
						x: g.cx + C * Math.sqrt(k) * Math.cos(k * GOLD),
						y: cy + C * Math.sqrt(k) * Math.sin(k * GOLD)
					}))
				});
			}
			yTop = base + 40 + maxLines * 13 + 14;
		}
		return { groups: placed, height: yTop - 8 };
	});

	let hover = $state<{ ref: string; eur?: number | null; cat?: string | null } | null>(null);
	let hoverCat = $state<string | null>(null);
	const lit = (d: { ref: string; cat?: string | null }) =>
		hover ? hover.ref === d.ref : hoverCat ? d.cat === hoverCat : true;
	const worksOf = (ref: string) => nodes.find((n) => n.ref === ref)?.wk?.length ?? 0;
</script>

<figure class="wd">
	<ul class="key">
		{#each Object.keys(CAT_COLORS).filter((k) => nodes.some((n) => n.cat === k)) as k (k)}
			<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
			<li onmouseenter={() => (hoverCat = k)} onmouseleave={() => (hoverCat = null)}>
				<i style:background={CAT_COLORS[k]}></i>{catLabels[k] ?? k}
			</li>
		{/each}
	</ul>

	<svg viewBox="0 0 {W} {sc.height}" role="img" aria-label="One dot per contract under every work it names, coloured by main category">
		{#each sc.groups as g (g.key)}
			{#each g.dots as d (d.ref)}
				<a
					href={`/antinero/contract/${d.ref}`}
					aria-label={d.ref}
					onmouseenter={() => (hover = d)}
					onmouseleave={() => (hover = null)}
				>
					<circle
						cx={d.x}
						cy={d.y}
						r={DOT_R}
						fill={CAT_COLORS[d.cat ?? ''] ?? '#9b9b9b'}
						class="dot"
						class:hot={hover?.ref === d.ref}
						opacity={lit(d) ? 1 : 0.22}
					/>
				</a>
			{/each}
			<text class="count" x={g.cx} y={g.base + 24}>{g.n}</text>
			{#each g.lines as ln, li (li)}
				<text class="name" x={g.cx} y={g.base + 40 + li * 13}>{ln}</text>
			{/each}
		{/each}
	</svg>

	{#if hover}
		<div class="card">
			<strong class="tabular">{hover.ref}</strong>
			<span>{catLabels[hover.cat ?? ''] ?? hover.cat}{worksOf(hover.ref) > 1 ? ` · names ${worksOf(hover.ref)} works` : ''}</span>
			<span class="v">{eur(hover.eur ?? 0)}</span>
		</div>
	{/if}
</figure>

<style>
	.wd {
		margin: 0;
		position: relative;
	}
	svg {
		width: 100%;
		height: auto;
		display: block;
	}
	.dot {
		stroke: var(--paper);
		stroke-width: 0.6;
		transition: opacity 0.12s;
	}
	.dot.hot,
	a:hover .dot {
		stroke: #000;
		stroke-width: 1.4;
	}
	.count {
		font-size: 15px;
		font-weight: 700;
		fill: var(--ink);
		text-anchor: middle;
	}
	.name {
		font-size: 11px;
		fill: var(--ink-soft);
		text-anchor: middle;
	}
	/* the MAP legend's dress, as on the PROCUREMENT TIMELINE key */
	.key {
		list-style: none;
		margin: 0 0 var(--sp-3);
		box-sizing: border-box;
		padding: var(--sp-2) var(--sp-3);
		background: #f2f2f2;
		border-radius: 6px;
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 4px var(--sp-6, 1.5rem);
		font-size: var(--fs-14);
		color: var(--ink-soft);
	}
	.key li {
		display: flex;
		align-items: center;
		gap: 8px;
		cursor: default;
	}
	.key li i {
		width: 12px;
		height: 12px;
		border-radius: 3px;
		flex: none;
	}
	.card {
		position: absolute;
		left: 0;
		bottom: 0;
		background: #000;
		color: #fff;
		padding: 8px 10px;
		display: grid;
		gap: 2px;
		font-size: var(--fs-12);
		pointer-events: none;
	}
	.card .v {
		font-weight: 700;
	}
</style>
