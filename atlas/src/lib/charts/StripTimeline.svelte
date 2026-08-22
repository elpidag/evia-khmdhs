<script lang="ts">
	import type { PaymentsPayload, PaymentEvent } from '$lib/api';
	import { eur, eurShort } from '$lib/transforms/format';
	import { scaleTime } from 'd3-scale';

	/**
	 * One tick per payment order, in LANES BY SIGNATURE COHORT (user,
	 * 2026-08-22, round 2): asking 1.6-px lines to carry five greys was
	 * illegible, so each lane holds the payments of the contracts SIGNED
	 * in one year, all ticks one ink — the payment tail is the lane's
	 * horizontal reach, not a colour to decode. The «signed 2022» lane
	 * visibly runs deep into 2024.
	 */
	let { data }: { data: PaymentsPayload } = $props();

	let width = $state(900);
	const LANE_H = 52;
	const M = { top: 8, right: 12, bottom: 24, left: 92 };

	const dated = $derived(data.events.filter((e): e is PaymentEvent & { d: string } => !!e.d));
	const cohortOf = (e: PaymentEvent) => data.contracts[e.ref]?.y ?? null;
	const lanes = $derived(
		[...new Set(dated.map(cohortOf).filter((y): y is string => !!y))].sort()
	);
	const height = $derived(M.top + lanes.length * LANE_H + M.bottom);
	const laneEur = $derived.by(() => {
		const m = new Map<string, number>();
		for (const e of dated) {
			const y = cohortOf(e);
			if (y) m.set(y, (m.get(y) ?? 0) + (e.eur || 0));
		}
		return m;
	});

	const x = $derived.by(() => {
		const ds = dated.map((e) => new Date(e.d).getTime());
		const min = new Date(Math.min(...ds));
		const max = new Date(Math.max(...ds));
		min.setMonth(min.getMonth() - 1);
		max.setMonth(max.getMonth() + 1);
		return scaleTime([min, max], [M.left, width - M.right]);
	});

	const maxEur = $derived(Math.max(...dated.map((e) => e.eur || 0)));
	const tickH = (e: PaymentEvent) => 5 + (LANE_H - 14) * Math.sqrt((e.eur || 0) / maxEur);

	const years = $derived.by(() => {
		const [min, max] = x.domain();
		const ys: number[] = [];
		for (let y = min.getFullYear(); y <= max.getFullYear(); y++) ys.push(y);
		return ys;
	});

	// the statutory αντιπυρική περίοδος, 1 May – 31 October — the same
	// band every timeline on the site shades
	const seasons = $derived(
		years
			.map((y) => ({ x0: x(new Date(y, 4, 1)), x1: x(new Date(y, 10, 1)) }))
			.filter((s) => s.x1 > M.left && s.x0 < width - M.right)
	);

	let tip = $state<{ html: string } | null>(null);
	function tipFor(e: PaymentEvent): string {
		const c = data.contracts[e.ref];
		return (
			`<strong>${eur(e.eur)}</strong> · ${e.d}` +
			`<br>${c?.t ?? e.ref}` +
			`<br><span style="color:var(--ink-faint)">contract signed ${c?.y ?? '—'} · order ${e.pay}</span>`
		);
	}
</script>

<div class="wrap" bind:clientWidth={width}>
	<svg viewBox="0 0 {width} {height}" style:height="{height}px">
		{#each seasons as s, i (i)}
			<rect
				x={Math.max(s.x0, M.left)}
				y={M.top}
				width={Math.min(s.x1, width - M.right) - Math.max(s.x0, M.left)}
				height={lanes.length * LANE_H}
				fill="var(--accent)"
				opacity="0.06"
			/>
		{/each}
		{#if seasons.length}
			<text class="season-label" x={Math.max(seasons[0].x0, M.left) + 4} y={M.top + 10}>
				fire season (May–Oct)
			</text>
		{/if}

		{#each lanes as lane, li (lane)}
			{@const yBase = M.top + (li + 1) * LANE_H - 6}
			<line class="lane" x1={M.left} x2={width - M.right} y1={yBase} y2={yBase} />
			<text class="lane-label" x={M.left - 8} y={yBase - 16}>signed {lane}</text>
			<text class="lane-eur" x={M.left - 8} y={yBase - 4}>{eurShort(laneEur.get(lane) ?? 0)}</text>
			{#each dated.filter((e) => cohortOf(e) === lane) as e (e.pay)}
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<a href={`/antinero/contract/${e.ref}`} aria-label={`${e.d}: ${eur(e.eur)}`}>
					<line
						class="tick"
						x1={x(new Date(e.d))}
						x2={x(new Date(e.d))}
						y1={yBase}
						y2={yBase - tickH(e)}
						onmouseenter={() => (tip = { html: tipFor(e) })}
						onmouseleave={() => (tip = null)}
					/>
				</a>
			{/each}
		{/each}

		{#each years as y (y)}
			{@const xp = x(new Date(y, 0, 1))}
			{#if xp > M.left && xp < width - M.right}
				<line class="year" x1={xp} x2={xp} y1={M.top} y2={height - M.bottom} />
				<text class="year-label" x={xp + 4} y={height - 8}>{y}</text>
			{/if}
		{/each}
	</svg>

	{#if tip}
		<div class="tip">
			<!-- eslint-disable-next-line svelte/no-at-html-tags -->
			{@html tip.html}
		</div>
	{/if}
</div>

<style>
	.wrap {
		position: relative;
	}
	svg {
		display: block;
		width: 100%;
	}
	.lane {
		stroke: var(--line-strong);
		stroke-width: 1;
	}
	.lane-label {
		font-size: 11px;
		font-weight: 700;
		fill: var(--ink-soft);
		text-anchor: end;
	}
	.lane-eur {
		font-size: 10px;
		fill: var(--ink-faint);
		text-anchor: end;
	}
	.season-label {
		font-size: 10px;
		fill: var(--accent);
		opacity: 0.75;
	}
	.tick {
		stroke: var(--ink);
		stroke-width: 1.4;
		opacity: 0.55;
		cursor: pointer;
	}
	.tick:hover {
		stroke-width: 3;
		opacity: 1;
	}
	.year {
		stroke: var(--line);
		stroke-dasharray: 2 3;
	}
	.year-label {
		font-size: 11px;
		fill: var(--ink-faint);
	}
	.tip {
		position: absolute;
		top: 0;
		right: 0;
		max-width: 26rem;
		background: color-mix(in srgb, var(--paper) 94%, transparent);
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		padding: var(--sp-2) var(--sp-3);
		font-size: var(--fs-13);
		pointer-events: none;
		box-shadow: var(--shadow-paper);
	}
</style>
