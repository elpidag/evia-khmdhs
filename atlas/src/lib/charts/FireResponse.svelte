<script lang="ts">
	/**
	 * FROM FIRE TO SPONSOR — one lane per fire, the burn on the left, the
	 * designation acts that followed it on the right (DATA_DECISIONS
	 * 2026-08-24, replacing the monthly bar strip).
	 *
	 * The strip it replaces could only say «acts happen in autumn». This
	 * says what the page is actually about: how long a burnt forest waits
	 * for a sponsor, and that the wait tracks the fire's size — Έβρος
	 * (96.610 ha) was sponsored in 26 days, Κερατέα (546 ha) in 574.
	 *
	 * Conventions kept from the rest of the site: the fire season (1 May –
	 * 31 Oct) shaded as the PROCUREMENT TIMELINE shades it, the burn scars
	 * in the EFFIS maroon the maps use, area ∝ hectares.
	 */
	import { dmy } from '$lib/transforms/format';

	export interface FireLane {
		fire: string;
		n: number;
		burn_date: string | null;
		burn_ha: number;
		lag_days: number | null;
		first_start: string | null;
		acts: { d: string; ada: string }[];
	}
	interface Props {
		fires: FireLane[];
		/** today, so the axis ends where the data does */
		today: string;
	}
	let { fires, today }: Props = $props();

	const W = 920;
	// the right margin is the LAG column: printed at the row's end, the
	// labels used to sit beside the first act dot and collide with the
	// ones that followed it (user, 2026-08-24)
	const PAD = { l: 200, r: 52, t: 26, b: 22 };
	const LANE = 14;

	const lanes = $derived(
		fires
			.filter((f) => f.burn_date && f.acts.length)
			.sort((a, b) => (a.burn_date! < b.burn_date! ? -1 : 1))
	);
	const H = $derived(PAD.t + lanes.length * LANE + PAD.b);

	const t0 = $derived(
		Math.min(...lanes.map((l) => Date.parse(l.burn_date!)), Date.parse('2021-05-01'))
	);
	const t1 = $derived(Date.parse(today) + 20 * 864e5);
	const x = (iso: string | number) =>
		PAD.l + ((typeof iso === 'string' ? Date.parse(iso) : iso) - t0) / (t1 - t0) * (W - PAD.l - PAD.r);
	const y = (i: number) => PAD.t + i * LANE + LANE / 2;

	/** area ∝ hectares, floored so a small fire is still visible */
	const haMax = $derived(Math.max(1, ...lanes.map((l) => l.burn_ha)));
	const rOf = (ha: number) => 2.2 + 5.6 * Math.sqrt(Math.max(ha, 0) / haMax);

	const years = $derived.by(() => {
		const out: { y: number; x0: number; x1: number; seasonX0: number; seasonX1: number }[] = [];
		const y0 = new Date(t0).getUTCFullYear();
		const y1 = new Date(t1).getUTCFullYear();
		for (let yr = y0; yr <= y1; yr++)
			out.push({
				y: yr,
				x0: x(`${yr}-01-01`),
				x1: x(`${yr + 1}-01-01`),
				// Greece's fire season, the same 1 May – 31 Oct the
				// Anti-nero procurement timeline shades
				seasonX0: x(`${yr}-05-01`),
				seasonX1: x(`${yr}-11-01`)
			});
		return out;
	});

	const clip = (v: number) => Math.max(PAD.l, Math.min(W - PAD.r, v));
	const short = (s: string) => (s.length > 32 ? s.slice(0, 31) + '…' : s);
	const grHa = (ha: number) =>
		ha >= 1000 ? `${Math.round(ha / 1000).toLocaleString('el-GR')}.000 ha` : `${Math.round(ha)} ha`;
</script>

<figure class="fr">
	<svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Fire to first designation act, per fire">
		<!-- the fire season, shaded per year, behind everything -->
		{#each years as yr (yr.y)}
			{#if yr.seasonX1 > PAD.l && yr.seasonX0 < W - PAD.r}
				<rect
					x={clip(yr.seasonX0)}
					y={PAD.t - 6}
					width={Math.max(0, clip(yr.seasonX1) - clip(yr.seasonX0))}
					height={lanes.length * LANE + 8}
					class="season"
				/>
			{/if}
			{#if yr.x0 > PAD.l && yr.x0 < W - PAD.r}
				<line x1={yr.x0} y1={PAD.t - 6} x2={yr.x0} y2={PAD.t + lanes.length * LANE + 2} class="yr" />
				<text x={yr.x0 + 3} y={PAD.t - 11} class="yrlab">{yr.y}</text>
			{/if}
		{/each}

		{#each lanes as l, i (l.fire)}
			{@const xb = x(l.burn_date!)}
			{@const xa = x(l.first_start!)}
			<g class="lane">
				<text x={PAD.l - 8} y={y(i) + 3.4} class="name"
					>{short(l.fire)}<title>{l.fire}</title></text
				>
				<!-- the wait: burn → first act -->
				<line x1={xb} y1={y(i)} x2={xa} y2={y(i)} class="wait" />
				{#each l.acts as a (a.ada)}
					<a href={`/anadohoi/project/${a.ada}`}>
						<circle cx={x(a.d)} cy={y(i)} r="3" class="act">
							<title>{l.fire} — designation act {dmy(a.d)}</title>
						</circle>
					</a>
				{/each}
				<circle cx={xb} cy={y(i)} r={rOf(l.burn_ha)} class="burn">
					<title
						>{l.fire} — burnt {dmy(l.burn_date!)}, {grHa(l.burn_ha)} (EFFIS); first sponsor
						appointed after {l.lag_days} days, {l.n} project{l.n === 1 ? '' : 's'} in all</title
					>
				</circle>
				<text x={W - 6} y={y(i) + 3.4} class="lag">{l.lag_days} d</text>
			</g>
		{/each}
	</svg>

	<ul class="key">
		<li><i class="sw burn"></i>the fire, area ∝ hectares burnt (EFFIS)</li>
		<li><i class="sw act"></i>a designation act</li>
		<li><i class="sw wait"></i>the wait between them</li>
		<li><i class="sw season"></i>fire season, 1 May – 31 Oct</li>
		<li class="lagkey">right column: days from the fire to its first designation act</li>
	</ul>
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
	.season {
		fill: #b4553f;
		opacity: 0.07;
	}
	.yr {
		stroke: var(--line);
		stroke-width: 0.8;
	}
	.yrlab {
		font-size: 11px;
		fill: var(--ink-faint);
		font-variant-numeric: tabular-nums;
	}
	.name {
		font-size: 11.5px;
		fill: var(--ink-soft);
		text-anchor: end;
	}
	.wait {
		stroke: var(--ink-faint);
		stroke-width: 1;
		stroke-dasharray: 2 2;
	}
	.burn {
		fill: #6b2d35;
		opacity: 0.85;
	}
	.act {
		fill: var(--c-anadohoi);
		stroke: var(--paper);
		stroke-width: 0.8;
		cursor: pointer;
	}
	.act:hover {
		fill: var(--ink);
	}
	.lag {
		text-anchor: end;
		font-size: 10px;
		fill: var(--ink-faint);
		font-variant-numeric: tabular-nums;
	}
	.key {
		list-style: none;
		margin: var(--sp-2) 0 0;
		padding: 0;
		display: flex;
		flex-wrap: wrap;
		gap: 4px var(--sp-6);
		font-size: var(--fs-12);
		color: var(--ink-soft);
	}
	.key li.lagkey {
		color: var(--ink-faint);
	}
	.key li {
		display: flex;
		align-items: center;
		gap: 7px;
	}
	.sw {
		width: 11px;
		height: 11px;
		flex: none;
		border-radius: 50%;
		display: inline-block;
	}
	.sw.burn {
		background: #6b2d35;
	}
	.sw.act {
		background: var(--c-anadohoi);
	}
	.sw.wait {
		border-radius: 0;
		height: 0;
		border-top: 1px dashed var(--ink-faint);
	}
	.sw.season {
		border-radius: 2px;
		background: #b4553f;
		opacity: 0.18;
	}
</style>
