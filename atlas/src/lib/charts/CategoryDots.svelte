<script lang="ts">
	/**
	 * One EQUAL dot per contract, clustered by its curated main category —
	 * the Flourish «Company ownership» form the user asked for (2026-08-22).
	 * Each cluster is a phyllotaxis disc (deterministic, no simulation),
	 * discs bottom-aligned on one baseline, count + name under each. The
	 * dots are equal on purpose: this face counts contracts; the € lives
	 * in the CONTRACT TYPE bars above.
	 */
	import { CAT_COLORS } from './catColors';
	import { eur } from '$lib/transforms/format';

	interface Dot {
		ref: string;
		eur?: number | null;
		cat?: string | null;
	}
	interface Props {
		nodes: Dot[];
		/** category key → short English label */
		labels: Record<string, string>;
	}
	let { nodes, labels }: Props = $props();

	const W = 1120;
	const GOLD = Math.PI * (3 - Math.sqrt(5));

	const wrap = (s: string, max = 18): string[] => {
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

	const sceneOf = (dotR: number, c: number, gap: number, minC2C: number) => {
		const by = new Map<string, Dot[]>();
		for (const n of nodes) {
			const k = n.cat ?? 'unknown';
			(by.get(k) ?? by.set(k, []).get(k)!).push(n);
		}
		const clusters = [...by.entries()]
			.map(([key, ds]) => ({
				key,
				ds: [...ds].sort((a, b) => (b.eur ?? 0) - (a.eur ?? 0) || a.ref.localeCompare(b.ref)),
				R: (ds.length > 1 ? c * Math.sqrt(ds.length - 1) : 0) + dotR + 2
			}))
			.sort((a, b) => b.ds.length - a.ds.length);
		// a small cluster's LABEL is wider than its disc — reserve half a
		// label at both row ends or the last name clips at the frame edge
		const LABEL_HALF = 62;
		let x = 0;
		let prevR = 0;
		const xs: number[] = [];
		for (const cl of clusters) {
			x = xs.length === 0 ? Math.max(cl.R, LABEL_HALF) : x + Math.max(prevR + cl.R + gap, minC2C);
			xs.push(x);
			prevR = cl.R;
		}
		return { clusters, xs, total: x + Math.max(prevR, LABEL_HALF) };
	};

	const sc = $derived.by(() => {
		let dotR = 4.4;
		let c = 9.8;
		let s = sceneOf(dotR, c, 28, 118);
		if (s.total > W) {
			const f = W / s.total;
			dotR *= f;
			c *= f;
			s = sceneOf(dotR, c, 28 * f, 118 * f);
		}
		const maxR = Math.max(...s.clusters.map((cl) => cl.R));
		const base = 8 + 2 * maxR; // discs bottom-aligned on this line
		const off = (W - s.total) / 2;
		const groups = s.clusters.map((cl, i) => ({
			key: cl.key,
			cx: off + s.xs[i],
			cy: base - cl.R,
			n: cl.ds.length,
			lines: wrap(labels[cl.key] ?? cl.key),
			dots: cl.ds.map((d, k) => ({
				ref: d.ref,
				eur: d.eur,
				cat: cl.key,
				x: off + s.xs[i] + c * Math.sqrt(k) * Math.cos(k * GOLD),
				y: base - cl.R + c * Math.sqrt(k) * Math.sin(k * GOLD)
			}))
		}));
		const maxLines = Math.max(...groups.map((g) => g.lines.length));
		return { groups, dotR, base, height: base + 36 + maxLines * 14 + 6 };
	});

	let hover = $state<{ ref: string; eur?: number | null; cat: string } | null>(null);
</script>

<figure class="cd">
	<svg viewBox="0 0 {W} {sc.height}" role="img" aria-label="One dot per contract, grouped by main category">
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
						r={sc.dotR}
						fill={CAT_COLORS[g.key] ?? '#9b9b9b'}
						class="dot"
						opacity={hover && hover.ref !== d.ref ? 0.45 : 1}
					/>
				</a>
			{/each}
			<text class="count" x={g.cx} y={sc.base + 22}>{g.n}</text>
			{#each g.lines as ln, li (li)}
				<text class="name" x={g.cx} y={sc.base + 38 + li * 14}>{ln}</text>
			{/each}
		{/each}
	</svg>
	{#if hover}
		<div class="card">
			<strong class="tabular">{hover.ref}</strong>
			<span>{labels[hover.cat] ?? hover.cat}</span>
			<span class="v">{eur(hover.eur ?? 0)}</span>
		</div>
	{/if}
</figure>

<style>
	.cd {
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
		font-size: 11.5px;
		fill: var(--ink-soft);
		text-anchor: middle;
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
