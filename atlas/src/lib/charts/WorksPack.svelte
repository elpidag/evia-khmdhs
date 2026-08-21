<script lang="ts">
	/**
	 * TYPES OF WORK as packed circles (trial, user 2026-08-22): every
	 * in-scope contract is a circle, area ∝ stated net €, packed into one
	 * bubble per main category; the bubbles packed together, biggest first.
	 * The programme chart's pack arrangement, regrouped by type of work —
	 * two levels of `packSiblings` (never `d3.pack`, which would re-sort).
	 * Grayscale: bubbles are a light grey with a thin rim, contracts a dark
	 * grey; a bubble's label and € sit on its rim.
	 */
	import { packSiblings, packEnclose } from 'd3-hierarchy';
	import { eurShort, grInt } from '$lib/transforms/format';

	interface Row {
		ref: string;
		eur: number;
		category?: string | null;
		t?: string;
	}
	interface Cat {
		key: string;
		label: string;
		n: number;
		eur: number;
	}
	interface Props {
		rows: Row[];
		cats: Cat[];
		/** drawing box, square (the blob is round) */
		size?: number;
		linkBase?: string;
	}
	let { rows, cats, size = 560, linkBase = '/antinero/contract/' }: Props = $props();

	// area ∝ € on one scale: r = K·√€; K chosen so the whole blob fits
	interface Dot {
		ref: string;
		eur: number;
		t?: string;
		r: number;
		x: number;
		y: number;
	}
	interface Bubble {
		key: string;
		label: string;
		n: number;
		eur: number;
		r: number;
		x: number;
		y: number;
		dots: Dot[];
	}
	const scene = $derived.by(() => {
		const maxEur = Math.max(1, ...rows.map((d) => d.eur || 0));
		const K = 22 / Math.sqrt(maxEur); // the biggest contract ≈ 22 units
		const order = [...cats].sort((a, b) => b.eur - a.eur);
		const bubbles: Bubble[] = [];
		for (const c of order) {
			const dots: Dot[] = rows
				.filter((d) => d.category === c.key && (d.eur || 0) > 0)
				.sort((a, b) => b.eur - a.eur)
				.map((d) => ({ ref: d.ref, eur: d.eur, t: d.t, r: Math.max(1.6, K * Math.sqrt(d.eur)), x: 0, y: 0 }));
			if (!dots.length) continue;
			packSiblings(dots);
			const enc = packEnclose(dots);
			// re-centre the dots on the bubble's own origin
			for (const d of dots) {
				d.x -= enc.x;
				d.y -= enc.y;
			}
			bubbles.push({ key: c.key, label: c.label, n: c.n, eur: c.eur, r: enc.r + 6, x: 0, y: 0, dots });
		}
		if (!bubbles.length) return { bubbles, enc: { x: 0, y: 0, r: 1 } };
		packSiblings(bubbles);
		const all = packEnclose(bubbles) ?? { x: 0, y: 0, r: 1 };
		return { bubbles, enc: all };
	});
	// the swarm rows carry the category only since 2026-08-22 — an API that
	// predates it sends none, and the drawing must say so, not stay blank
	const noCategories = $derived(rows.length > 0 && rows.every((d) => !d.category));
	// the viewBox crops to the round blob with room for the rim labels
	const pad = 28;
	const vb = $derived(
		`${scene.enc.x - scene.enc.r - pad} ${scene.enc.y - scene.enc.r - pad} ${2 * (scene.enc.r + pad)} ${2 * (scene.enc.r + pad)}`
	);
	let hot = $state<string | null>(null);
</script>

{#if noCategories}
	<p class="empty">The contract rows carry no category yet — restart the API (the swarm payload gained it on 2026-08-22).</p>
{/if}
<svg viewBox={vb} width={size} height={size} class="pack" role="img" aria-label="Contracts packed by type of work">
	{#each scene.bubbles as b (b.key)}
		<g class="bubble" class:dim={hot !== null && hot !== b.key} onmouseenter={() => (hot = b.key)} onmouseleave={() => (hot = null)} role="presentation">
			<circle cx={b.x} cy={b.y} r={b.r} class="rim" />
			{#each b.dots as d (d.ref)}
				<a href={`${linkBase}${d.ref}`}>
					<circle cx={b.x + d.x} cy={b.y + d.y} r={d.r} class="dot">
						<title>{d.ref} · {eurShort(d.eur)}{d.t ? ` · ${d.t}` : ''}</title>
					</circle>
				</a>
			{/each}
			<!-- the label on the bubble's upper rim; big bubbles carry name + €,
			     small ones only the €, the smallest nothing (hover instead) -->
			{#if b.r > 34}
				<text class="lbl" x={b.x} y={b.y - b.r + 11} text-anchor="middle">{b.label.length > Math.floor(b.r / 3) ? b.label.split(' — ')[0].slice(0, Math.max(10, Math.floor(b.r / 3))) + '…' : b.label}</text>
				<text class="val" x={b.x} y={b.y - b.r + 22} text-anchor="middle">{eurShort(b.eur)} · {grInt(b.n)}</text>
			{:else if b.r > 16}
				<text class="val" x={b.x} y={b.y - b.r - 3} text-anchor="middle">{eurShort(b.eur)}</text>
			{/if}
			<title>{b.label} — {grInt(b.n)} contracts, {eurShort(b.eur)}</title>
		</g>
	{/each}
</svg>

<style>
	.empty {
		font-size: var(--fs-13);
		color: var(--ink-soft);
	}
	.pack {
		display: block;
		margin: 0 auto;
		max-width: 100%;
		height: auto;
	}
	.rim {
		fill: #f0f0f0;
		stroke: #8a8a8a;
		stroke-width: 0.8;
	}
	.dot {
		fill: #3a3a3a;
		stroke: none;
	}
	.dot:hover {
		fill: #000;
	}
	.bubble.dim {
		opacity: 0.35;
	}
	.lbl {
		font-size: 9px;
		font-weight: 700;
		fill: var(--ink);
	}
	.val {
		font-size: 8.5px;
		fill: var(--ink-soft);
	}
</style>
