<script lang="ts">
	/**
	 * CONTRACTS UNDER THE SAME CALL — the πρόσκληση at the centre, the
	 * contracts it produced orbiting it, each circle's AREA proportional to
	 * its stated net €. The centre carries the call's own ΑΔΑΜ and the sum,
	 * so an out-of-scale lot is obvious against both its siblings and the
	 * call — the reading that exposed a €31M project-budget error.
	 *
	 * The graph comes from the contracts' own signed texts: the ΚΗΜΔΗΣ
	 * adamChain returns empty lists for most of these contracts (verified
	 * live, DATA_DECISIONS 2026-08-18).
	 */
	import { eur, eurShort } from '$lib/transforms/format';

	interface Member { ref: string; title: string | null; d: string | null; eur: number | null; in_db?: boolean }
	interface Props {
		call: string;
		contracts: Member[];
		total: number;
		self: string;
		amendments?: string[];
		/** where a lot's circle links to — the ΔΑΣΕ pages pass their own (2026-08-29) */
		linkBase?: string;
		/** the filled circle's colour — the page's own accent */
		selfColor?: string;
		/** the caption; the Anti-nero one by default */
		caption?: string;
	}
	let {
		call, contracts, total, self, amendments = [],
		linkBase = '/antinero/contract/', selfColor = 'var(--c-antinero, #000)', caption
	}: Props = $props();

	// The ΑΔΑΜ labels sit OUTSIDE the orbit, so the viewBox has to be sized
	// from their width — underestimating it clips them against the column.
	// 6.6 is measured from the rendered futura digits at 9 units, not guessed.
	const CHAR = 6.6;
	/** past a dozen lots the ΑΔΑΜ labels collide: the multi-lot ΔΑΣΕ
	 *  procurements (33 firewood lots under one award, 41 lots of which one
	 *  is a co-op's) print only THIS contract's label, the rest stay in
	 *  their hover titles (2026-08-29) */
	const dense = $derived(contracts.length > 12);

	const layout = $derived.by(() => {
		const vals = contracts.map((c) => c.eur ?? 0);
		const max = Math.max(...vals, 1);
		// area ∝ €; the centre is the sum, so it dwarfs its lots naturally
		const rOf = (v: number) => Math.max(7, Math.sqrt(v / max) * 30);
		// a lot the dataset does not hold has no €: a small outlined dot
		const rAt = (c: Member) => (c.in_db === false ? (dense ? 4 : 7) : rOf(c.eur ?? 0));
		const rs = contracts.map(rAt);
		const rMax = Math.max(...rs, 7);
		const rCall = Math.min(88, Math.sqrt(total / max) * 30);
		const n = contracts.length;
		// the lots sit at angles proportional to the room they need — each
		// step is the two neighbours' radii plus a gap — so a big lot beside
		// small ones never overlaps them (2026-08-29); the orbit grows when
		// the ring's own circumference asks for more than the centre does
		const GAP = 3;
		const segs = rs.map((r, i) => r + rs[(i + 1) % n] + GAP);
		const ring = segs.reduce((a, b) => a + b, 0);
		const orbit = Math.max(rCall + rMax + 34, ring / (2 * Math.PI));
		let cum = 0;
		// start at the left so the first lot sits where the eye lands
		const nodes = contracts.map((c, i) => {
			const a = Math.PI + (n > 1 ? (cum / ring) * Math.PI * 2 : 0);
			cum += segs[i];
			const r = rs[i];
			const x = Math.cos(a) * orbit;
			const y = Math.sin(a) * orbit;
			const left = Math.cos(a) < -0.15;
			const lw = dense && c.ref !== self ? 0 : c.ref.length * CHAR + 4;
			return {
				...c, r, x, y, a, left,
				lx: x + (left ? -(r + 6) : r + 6),
				reach: Math.abs(x) + r + 8 + lw
			};
		});
		const halfW = Math.max(...nodes.map((n) => n.reach), orbit + rMax) + 8;
		const halfH = Math.max(...nodes.map((n) => Math.abs(n.y) + n.r + 16), rCall + 20) + 8;
		return { nodes, rCall, halfW, halfH, w: halfW * 2, h: halfH * 2 };
	});
</script>

<figure class="fam">
	<svg viewBox={`${-layout.halfW} ${-layout.halfH} ${layout.w} ${layout.h}`} role="img"
		aria-label={`Call ${call}: ${contracts.length} contracts`}>
		{#each layout.nodes as n (n.ref)}
			<line x1={Math.cos(n.a) * layout.rCall} y1={Math.sin(n.a) * layout.rCall}
				x2={n.x - Math.cos(n.a) * n.r} y2={n.y - Math.sin(n.a) * n.r} class="link" />
		{/each}
		<circle cx="0" cy="0" r={layout.rCall} class="call" />
		<text x="0" y="-2" class="callid">{call}</text>
		<text x="0" y="14" class="callsum">{eurShort(total)}</text>
		{#each layout.nodes as n (n.ref)}
			<a href={n.in_db === false ? undefined : `${linkBase}${n.ref}`}>
				<title>{n.ref} · {n.in_db === false ? 'outside the dataset' : eur(n.eur)} · {n.title ?? ''}</title>
				<circle cx={n.x} cy={n.y} r={n.r} class="node" class:self={n.ref === self}
					class:outside={n.in_db === false} style:fill={n.ref === self ? selfColor : undefined} />
				{#if !dense || n.ref === self}
					<text x={n.lx} y={n.y - 1} class="id" class:selfid={n.ref === self}
						text-anchor={n.left ? 'end' : 'start'}>{n.ref}</text>
					<text x={n.lx} y={n.y + 11} class="val" text-anchor={n.left ? 'end' : 'start'}
						>{n.in_db === false ? 'outside the dataset' : eurShort(n.eur ?? 0)}</text>
				{/if}
			</a>
		{/each}
	</svg>
	<figcaption>
		{#if caption}{caption}{:else}Circle area is the stated value excl. VAT — the centre is the call and the sum of its
		contracts; this contract is filled. Read from this contract's own signed text: the
		registry declares no upstream act for it.{/if}
		{#if amendments.length}The call was later amended ({amendments.join(', ')}).{/if}
	</figcaption>
</figure>

<style>
	.fam { margin: 0; }
	svg { width: 100%; height: auto; display: block; overflow: visible; }
	.call { fill: #e4e4e4; }
	.node { fill: #d8d8d8; transition: fill 0.15s; }
	a:hover .node { fill: #b0b0b0; }
	.node.self { fill: var(--c-antinero, #000); }
	/* a lot of the same procurement the dataset does not hold: outlined */
	.node.outside { fill: #fff; stroke: #9a9a9a; stroke-width: 1; stroke-dasharray: 3 2; }
	.callid { text-anchor: middle; font-size: 11px; fill: var(--ink); }
	.callsum { text-anchor: middle; font-size: 11px; fill: var(--ink); font-weight: 700; }
	.id { font-size: 9px; fill: var(--ink-soft); }
	.id.selfid { fill: var(--ink); font-weight: 700; }
	.val { font-size: 9px; fill: var(--ink-soft); }
	.link { stroke: #9a9a9a; stroke-width: 1; stroke-dasharray: 4 3; }
	figcaption { font-size: var(--fs-12); color: var(--ink-soft); margin-top: var(--sp-2); }
</style>
