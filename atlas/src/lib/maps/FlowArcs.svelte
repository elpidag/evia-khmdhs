<script lang="ts">
	import { peEn } from '$lib/transforms/regions';
	import type { MapCtx } from './PaperMap.svelte';
	import { eurShort, grInt } from '$lib/transforms/format';

	export interface Flow {
		source_pe: string; // where the winning firm is based
		target_pe: string; // where the work happens
		n_contracts: number;
		total_eur: number;
	}

	/**
	 * Directed flows for ONE selected region. Arrows always point home→work
	 * ("a firm's reach"): red arcs arrive here (work won by firms based
	 * elsewhere), blue arcs leave (local firms winning work elsewhere),
	 * a green dot is money that stays local.
	 */
	interface Props {
		ctx: MapCtx;
		flows: Flow[];
		centroids: Record<string, [number, number]>;
		focusPe: string;
	}
	let { ctx, flows, centroids, focusPe }: Props = $props();

	// black-white-grayscale only, all arcs BLACK, direction by line STYLE
	// (user, 2026-08-20, third pass — grey read poorly, all-solid explained
	// poorly): solid black reaches IN to the focused region, dashed black
	// reaches OUT of it, arrowheads point home → work at a fixed size so the
	// stroke width alone carries the €; the ringed white dot is the money
	// that never leaves
	const ARC = '#111111';
	const LOCAL = '#ffffff';

	const shown = $derived(
		flows
			.filter(
				(f) =>
					(f.source_pe === focusPe || f.target_pe === focusPe) &&
					f.source_pe !== f.target_pe
			)
			.sort((a, b) => b.total_eur - a.total_eur)
	);
	const localEur = $derived(
		flows.find((f) => f.source_pe === focusPe && f.target_pe === focusPe)?.total_eur ?? 0
	);
	const maxEur = $derived(Math.max(...shown.map((f) => f.total_eur), localEur, 1));

	function pt(pe: string): [number, number] | null {
		const c = centroids[pe];
		return c ? ctx.projection([c[1], c[0]]) : null;
	}

	function arc(f: Flow): string | null {
		const p1 = pt(f.source_pe);
		const p2 = pt(f.target_pe);
		if (!p1 || !p2) return null;
		const mx = (p1[0] + p2[0]) / 2;
		const my = (p1[1] + p2[1]) / 2;
		const dx = p2[0] - p1[0];
		const dy = p2[1] - p1[1];
		const bend = 0.22;
		return `M ${p1[0]} ${p1[1]} Q ${mx - dy * bend} ${my + dx * bend} ${p2[0]} ${p2[1]}`;
	}

	function tip(f: Flow): string {
		const inbound = f.target_pe === focusPe;
		return inbound
			? `<strong>${peEn(f.source_pe)} firms → works in ${peEn(focusPe)}</strong>` +
					`<br>${eurShort(f.total_eur)} · ${grInt(f.n_contracts)} contracts`
			: `<strong>${peEn(focusPe)} firms → works in ${peEn(f.target_pe)}</strong>` +
					`<br>${eurShort(f.total_eur)} · ${grInt(f.n_contracts)} contracts`;
	}
</script>

<defs>
	<!-- fixed-size arrowhead (userSpaceOnUse, ÷k against the zoom): the
	     stroke width alone carries the €, the head only the direction -->
	<marker
		id="fa-head"
		viewBox="0 0 10 10"
		refX="8"
		refY="5"
		markerWidth={11 / ctx.k}
		markerHeight={11 / ctx.k}
		orient="auto-start-reverse"
		markerUnits="userSpaceOnUse"
	>
		<path d="M 0 0 L 10 5 L 0 10 z" fill={ARC} />
	</marker>
</defs>

{#if localEur > 0}
	{@const p = pt(focusPe)}
	{#if p}
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<circle
			cx={p[0]}
			cy={p[1]}
			r={(4 + 9 * Math.sqrt(localEur / maxEur)) / ctx.k}
			fill={LOCAL}
			stroke="#111111"
			stroke-width={1.6 / ctx.k}
			opacity="0.9"
			onmouseenter={() =>
				ctx.showTip(
					`<strong>stays local</strong><br>${eurShort(localEur)} won by firms based in ${peEn(focusPe)}`
				)}
			onmouseleave={() => ctx.hideTip()}
		/>
	{/if}
{/if}

{#each shown as f (f.source_pe + '→' + f.target_pe)}
	{@const d = arc(f)}
	{#if d}
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<path
			class="flow"
			{d}
			stroke={ARC}
			stroke-dasharray={f.target_pe === focusPe ? undefined : `${8 / ctx.k} ${5 / ctx.k}`}
			stroke-width={(1 + 7 * Math.sqrt(f.total_eur / maxEur)) / ctx.k}
			marker-end="url(#fa-head)"
			onmouseenter={() => ctx.showTip(tip(f))}
			onmouseleave={() => ctx.hideTip()}
		/>
	{/if}
{/each}

<style>
	.flow {
		fill: none;
		opacity: 0.55;
		stroke-linecap: round;
	}
	.flow:hover {
		opacity: 1;
	}
	circle {
		cursor: default;
	}
</style>
