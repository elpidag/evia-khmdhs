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

	interface Member { ref: string; title: string | null; d: string | null; eur: number | null }
	interface Props {
		call: string;
		contracts: Member[];
		total: number;
		self: string;
		amendments?: string[];
	}
	let { call, contracts, total, self, amendments = [] }: Props = $props();

	// The ΑΔΑΜ labels sit OUTSIDE the orbit, so the viewBox has to be sized
	// from their width — underestimating it clips them against the column.
	// 6.6 is measured from the rendered futura digits at 9 units, not guessed.
	const CHAR = 6.6;

	const layout = $derived.by(() => {
		const vals = contracts.map((c) => c.eur ?? 0);
		const max = Math.max(...vals, 1);
		// area ∝ €; the centre is the sum, so it dwarfs its lots naturally
		const rOf = (v: number) => Math.max(7, Math.sqrt(v / max) * 30);
		const rMax = Math.max(...vals.map(rOf), 7);
		const rCall = Math.min(88, Math.sqrt(total / max) * 30);
		const orbit = rCall + rMax + 34;

		const n = contracts.length;
		// start at the left so the first lot sits where the eye lands
		const nodes = contracts.map((c, i) => {
			const a = Math.PI + (i / n) * Math.PI * 2;
			const r = rOf(c.eur ?? 0);
			const x = Math.cos(a) * orbit;
			const y = Math.sin(a) * orbit;
			const left = Math.cos(a) < -0.15;
			const lw = c.ref.length * CHAR + 4;
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
			<a href={`/antinero/contract/${n.ref}`}>
				<title>{n.ref} · {eur(n.eur)} · {n.title ?? ''}</title>
				<circle cx={n.x} cy={n.y} r={n.r} class="node" class:self={n.ref === self} />
				<text x={n.lx} y={n.y - 1} class="id" class:selfid={n.ref === self}
					text-anchor={n.left ? 'end' : 'start'}>{n.ref}</text>
				<text x={n.lx} y={n.y + 11} class="val" text-anchor={n.left ? 'end' : 'start'}
					>{eurShort(n.eur ?? 0)}</text>
			</a>
		{/each}
	</svg>
	<figcaption>
		Circle area is the stated value excl. VAT — the centre is the call and the sum of its
		contracts; this contract is filled. Read from this contract's own signed text: the
		registry declares no upstream act for it.
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
	.callid { text-anchor: middle; font-size: 11px; fill: var(--ink); }
	.callsum { text-anchor: middle; font-size: 11px; fill: var(--ink); font-weight: 700; }
	.id { font-size: 9px; fill: var(--ink-soft); }
	.id.selfid { fill: var(--ink); font-weight: 700; }
	.val { font-size: 9px; fill: var(--ink-soft); }
	.link { stroke: #9a9a9a; stroke-width: 1; stroke-dasharray: 4 3; }
	figcaption { font-size: var(--fs-12); color: var(--ink-soft); margin-top: var(--sp-2); }
</style>
