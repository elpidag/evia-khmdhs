<script lang="ts">
	/**
	 * One project's row from the overview TIMELINE (PromiseGantt), standing
	 * alone on the detail page: the same programme axis (Jul 2021 → today),
	 * the same status palette, bar from designation act to initial deadline,
	 * lighter extension segment, deadline tick, ✓/✕ marks and the dashed
	 * "today" rule — plus printed start/deadline dates, since there is no
	 * hover card here.
	 */
	import { dmy, grInt } from '$lib/transforms/format';
	import { COLOR, EXT_COLOR, NODATE_COLOR } from '$lib/charts/ganttTheme';

	export interface FireMark {
		/** EFFIS feature id — hover linking with the map's scars */
		id?: number;
		/** fire start date, ISO */
		d: string;
		ha: number;
		name: string;
		/** per-fire tone, shared with the map's scar fill */
		color?: string;
	}

	interface Props {
		/** designation act date */
		start: string | null;
		/** initial deadline (pre-amendment) */
		deadline0: string | null;
		/** current deadline (post-amendment) */
		deadline: string | null;
		completed: string | null;
		revoked: string | null;
		status: string;
		/** current date (ISO) — the dashed "today" rule */
		today: string;
		/** restated predecessor's designation date (folded, like the Gantt) */
		start0?: string | null;
		/** the project's linked EFFIS fires — maroon dots at their start date */
		fires?: FireMark[];
		/** fire-dot hover in/out — the page mirrors it onto the map */
		onFireHover?: (id: number | null) => void;
	}
	let {
		start,
		deadline0,
		deadline,
		completed,
		revoked,
		status,
		today,
		start0 = null,
		fires = [],
		onFireHover
	}: Props = $props();

	// identical axis convention to PromiseGantt: programme start → the
	// latest date in the row (or today) plus a small margin
	const T0 = new Date('2021-07-01').getTime();
	const T1 = $derived.by(() => {
		let m = new Date(today).getTime();
		for (const d of [start, start0, deadline0, deadline, completed, revoked, ...fires.map((f) => f.d)])
			if (d) {
				const t = new Date(d).getTime();
				if (!Number.isNaN(t)) m = Math.max(m, t);
			}
		return m + 5 * 86_400_000;
	});

	const W = 920;
	const TOP = 16; // year-label band
	const BASE = 46; // bar baseline
	const BAR_H = 12;
	const H = 62; // leaves room for the date labels under the bar

	function x(d: string | null): number | null {
		if (!d) return null;
		const t = new Date(d).getTime();
		if (Number.isNaN(t)) return null;
		return 4 + ((W - 12) * (t - T0)) / (T1 - T0);
	}

	const years = $derived.by(() => {
		const out: string[] = [];
		for (let yr = new Date(T0).getFullYear() + 1; yr <= new Date(T1).getFullYear(); yr++) {
			const gx = x(`${yr}-01-01`);
			if (gx !== null && gx <= W - 18) out.push(String(yr));
		}
		return out;
	});

	const noDate = $derived(status === 'active' && !deadline);
	const c = $derived(noDate ? NODATE_COLOR : (COLOR[status] ?? NODATE_COLOR));
	const xs = $derived(x(start));
	const xs0 = $derived(x(start0));
	const xd0 = $derived(x(deadline0 ?? deadline));
	const xd = $derived(x(deadline));
	const xc = $derived(x(completed));
	const xr = $derived(x(revoked));
	const todayX = $derived(x(today) ?? 4);
	// today's label flips to the left of its rule near the right edge
	const todayFlip = $derived(todayX > W - 110);
</script>

{#if xs !== null}
	<svg viewBox="0 0 {W} {H}" class="actbar" role="img" aria-label="Timeline of this act">
		{#each years as yr (yr)}
			{@const gx = x(`${yr}-01-01`)}
			{#if gx}
				<text x={gx} y="10" class="axis">{yr}</text>
				<line x1={gx} y1={TOP - 2} x2={gx} y2={BASE + 4} class="grid" />
			{/if}
		{/each}

		<line x1={todayX} y1={TOP - 2} x2={todayX} y2={BASE + 4} class="today" />
		<!-- sits a line below the year labels, as on the overview Gantt -->
		<text
			x={todayFlip ? todayX - 4 : todayX + 4}
			y="24"
			class="today-label"
			text-anchor={todayFlip ? 'end' : 'start'}>today ({dmy(today)})</text
		>

		<!-- the fire(s) that triggered the project, at their start dates -->
		{#each fires as f, i (f.d + i)}
			{@const fx = x(f.d)}
			{#if fx !== null && fx >= 4}
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<circle
					cx={fx}
					cy={BASE - BAR_H / 2}
					r="3.5"
					class="fire"
					style:fill={f.color}
					onmouseenter={() => onFireHover?.(f.id ?? null)}
					onmouseleave={() => onFireHover?.(null)}
				>
					<title>πυρκαγιά {dmy(f.d)} — {grInt(f.ha)} εκτάρια ({f.name})</title>
				</circle>
			{/if}
		{/each}

		<!-- restated predecessor: its own designation until the re-issue -->
		{#if xs0 !== null && xs > xs0}
			<rect x={xs0} y={BASE - BAR_H} width={xs - xs0} height={BAR_H} fill={c} opacity="0.55" rx="1" />
		{/if}
		{#if xd0 !== null && xd0 > xs}
			<rect x={xs} y={BASE - BAR_H} width={xd0 - xs} height={BAR_H} fill={c} opacity="0.85" rx="1" />
		{:else}
			<!-- no calendar deadline to draw to — the Gantt's short stub -->
			<rect x={xs} y={BASE - BAR_H} width="7" height={BAR_H} fill={c} opacity="0.85" />
		{/if}
		{#if xd0 !== null && xd !== null && xd > xd0}
			{@const ext = EXT_COLOR[status]}
			<rect
				x={xd0}
				y={BASE - BAR_H}
				width={xd - xd0}
				height={BAR_H}
				fill={ext ?? c}
				opacity={ext ? 0.9 : 0.35}
				rx="1"
			/>
		{/if}
		{#if xd !== null}
			<line x1={xd} y1={BASE - BAR_H - 4} x2={xd} y2={BASE + 2} stroke={c} stroke-width="1.3" />
		{/if}
		{#if xc !== null}
			<text x={xc + 2} y={BASE - 2} class="mark ok">✔</text>
		{/if}
		{#if xr !== null}
			<text x={xr + 2} y={BASE - 2} class="mark bad">✖</text>
		{/if}

		<!-- printed dates: designation under the bar start, deadline under its tick -->
		<text x={xs} y={BASE + 14} class="dlabel" text-anchor={xs < 60 ? 'start' : 'middle'}>
			{dmy(start)}
		</text>
		{#if xd !== null && xd - xs > 70}
			<text x={xd} y={BASE + 14} class="dlabel" text-anchor={xd > W - 60 ? 'end' : 'middle'}>
				{dmy(deadline)}
			</text>
		{/if}
	</svg>
{/if}

<style>
	.actbar {
		width: 100%;
		height: auto;
		display: block;
		margin: var(--sp-2) 0 var(--sp-3);
	}
	.grid {
		stroke: var(--line);
		stroke-width: 0.5;
	}
	.axis {
		font-size: 10px;
		fill: var(--ink-faint);
		text-anchor: middle;
	}
	.today {
		stroke: var(--ink);
		stroke-width: 1;
		stroke-dasharray: 3 3;
	}
	.today-label {
		font-size: 10px;
		fill: var(--ink);
		font-weight: 600;
	}
	.mark {
		font-size: 11px;
		font-weight: 900;
	}
	.mark.ok {
		fill: var(--c-anadohoi);
	}
	.mark.bad {
		fill: #000;
	}
	.dlabel {
		font-size: 10px;
		fill: var(--ink-soft);
	}
	/* per-fire tones arrive inline, matching the site map's scar fills */
	.fire {
		fill: color-mix(in srgb, #6b2d35 85%, #fff);
		stroke: #6b2d35;
		stroke-width: 0.8;
		cursor: pointer;
	}
	.fire:hover {
		filter: brightness(0.82);
	}
</style>
