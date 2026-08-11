<script lang="ts">
	/** Slope chart: initial deadline → current deadline for every amended
	 *  project (the change view that pairs with the Gantt's level view). */
	import { dmy } from '$lib/transforms/format';
	interface SlopeRow {
		ada: string;
		company: string;
		d0: string;
		d1: string;
	}
	interface Props {
		rows: SlopeRow[];
	}
	let { rows }: Props = $props();

	const W = 640;
	const H = 360;
	const PAD = 28;
	const XL = 200;
	const XR = W - 200;

	const T0 = $derived(
		Math.min(...rows.map((r) => new Date(r.d0).getTime()))
	);
	const T1 = $derived(
		Math.max(...rows.map((r) => new Date(r.d1).getTime()))
	);
	function y(d: string): number {
		const t = new Date(d).getTime();
		return PAD + ((H - 2 * PAD) * (t - T0)) / (T1 - T0 || 1);
	}
	// nudge colliding labels apart (several projects share a deadline)
	const placed = $derived.by(() => {
		const s = [...rows].sort((a, b) => a.d0.localeCompare(b.d0));
		const out: { r: SlopeRow; y0: number; ly0: number; y1: number; ly1: number }[] = [];
		let lastL = -Infinity;
		for (const r of s) {
			const y0 = y(r.d0);
			const ly0 = Math.max(y0, lastL + 11);
			lastL = ly0;
			out.push({ r, y0, ly0, y1: y(r.d1), ly1: 0 });
		}
		let lastR = -Infinity;
		for (const o of [...out].sort((a, b) => a.y1 - b.y1)) {
			o.ly1 = Math.max(o.y1, lastR + 11);
			lastR = o.ly1;
		}
		return out;
	});
</script>

<svg viewBox="0 0 {W} {H}" role="img" aria-label="Deadline extensions per project">
	<text x={XL} y="14" class="col">initial deadline</text>
	<text x={XR} y="14" class="col">after amendments</text>
	<line x1={XL} y1={PAD} x2={XL} y2={H - PAD} class="axis" />
	<line x1={XR} y1={PAD} x2={XR} y2={H - PAD} class="axis" />
	{#each placed as { r, y0, ly0, y1, ly1 } (r.ada)}
		<g class="slope">
			<title>{r.company}: {dmy(r.d0)} → {dmy(r.d1)}</title>
			<line x1={XL} y1={y0} x2={XR} y2={y1} class="wire" class:big={y1 - y0 > 40} />
			<circle cx={XL} cy={y0} r="2.5" />
			<circle cx={XR} cy={y1} r="2.5" />
			<a href={`/anadohoi/project/${r.ada}`}>
				<text x={XL - 8} y={ly0 + 3} class="lab left">{r.company.slice(0, 24)} · {dmy(r.d0)}</text>
			</a>
			<text x={XR + 8} y={ly1 + 3} class="lab right">{dmy(r.d1)}</text>
		</g>
	{/each}
</svg>

<style>
	svg {
		width: 100%;
		height: auto;
		display: block;
	}
	.col {
		font-size: 11px;
		font-weight: 700;
		fill: var(--ink);
		text-anchor: middle;
	}
	.axis {
		stroke: var(--line-strong);
	}
	.wire {
		stroke: #9e9e9e;
		stroke-width: 1;
	}
	.wire.big {
		stroke: #000000;
		stroke-width: 1.6;
	}
	circle {
		fill: #8f8f8f;
	}
	.lab {
		font-size: 9.5px;
		fill: var(--ink-soft);
	}
	.lab.left {
		text-anchor: end;
	}
	.slope a:hover .lab {
		fill: var(--ink);
		text-decoration: underline;
	}
</style>
