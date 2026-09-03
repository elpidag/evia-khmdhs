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
	 * ("a firm's reach"): solid arcs arrive here (work won by firms based
	 * elsewhere), dashed arcs leave (local firms winning work elsewhere), a
	 * ringed white dot is money that stays local.
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
	// that never leaves. Round two (user, 2026-08-21): THIN lines — the
	// widest is ~4 units, not 8 — the dash and its gap grow WITH the stroke
	// (a wide dashed line with a fixed gap read as a misprint), and the
	// arrowhead is an OPEN chevron, never a solid triangle.
	const ARC = 'color-mix(in srgb, var(--ink) 53.3%, black)';
	const LOCAL = 'var(--paper)';

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

	/** stroke width in map units: 0.7 … 4 by √€, divided by the zoom */
	const width = (f: Flow) => (0.7 + 3.3 * Math.sqrt(f.total_eur / maxEur)) / ctx.k;
	/** dash and gap scale with the stroke — a proportion, not a fixed pattern */
	const dashes = (w: number) => `${Math.max(3 / ctx.k, 3.2 * w)} ${Math.max(2 / ctx.k, 2.2 * w)}`;

	function tip(f: Flow): string {
		const inbound = f.target_pe === focusPe;
		return inbound
			? `<strong>${peEn(f.source_pe)} firms → works in ${peEn(focusPe)}</strong>` +
					`<br>${eurShort(f.total_eur)} · ${grInt(f.n_contracts)} contracts`
			: `<strong>${peEn(focusPe)} firms → works in ${peEn(f.target_pe)}</strong>` +
					`<br>${eurShort(f.total_eur)} · ${grInt(f.n_contracts)} contracts`;
	}
	// hover SHOWS the arc's card, click HOLDS it (✕ or Esc release it) — the
	// same gesture as the allocation maps' dots (user, 2026-08-21)
	let pinned = $state<string | null>(null);
	const key = (f: Flow) => f.source_pe + '→' + f.target_pe;
	function enter(f: Flow) {
		if (!pinned) ctx.showTip(tip(f));
	}
	function leave() {
		if (!pinned) ctx.hideTip();
	}
	function hold(f: Flow) {
		pinned = key(f);
		ctx.showTip(tip(f), {
			pinned: true,
			onClose: () => {
				pinned = null;
				ctx.hideTip();
			}
		});
	}
</script>

<defs>
	<!-- fixed-size OPEN arrowhead (userSpaceOnUse, ÷k against the zoom): the
	     stroke width alone carries the €, the chevron only the direction -->
	<marker
		id="fa-head"
		viewBox="0 0 10 10"
		refX="8"
		refY="5"
		markerWidth={9 / ctx.k}
		markerHeight={9 / ctx.k}
		orient="auto-start-reverse"
		markerUnits="userSpaceOnUse"
	>
		<path d="M 1.5 1.5 L 8 5 L 1.5 8.5" fill="none" stroke={ARC} stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" />
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
			stroke="color-mix(in srgb, var(--ink) 53.3%, black)"
			stroke-width={1.2 / ctx.k}
			opacity="0.9"
			onmouseenter={() =>
				ctx.showTip(
					`<strong>stays local</strong><br>${eurShort(localEur)} won by firms based in ${peEn(focusPe)}`
				)}
			onmouseleave={() => ctx.hideTip()}
		/>
	{/if}
{/if}

{#each shown as f (key(f))}
	{@const d = arc(f)}
	{@const w = width(f)}
	{#if d}
		<!-- svelte-ignore a11y_no_static_element_interactions, a11y_click_events_have_key_events -->
		<path
			class="flow"
			class:held={pinned === key(f)}
			{d}
			stroke={ARC}
			stroke-dasharray={f.target_pe === focusPe ? undefined : dashes(w)}
			stroke-width={w}
			marker-end="url(#fa-head)"
			onmouseenter={() => enter(f)}
			onmouseleave={leave}
			onclick={() => hold(f)}
		/>
	{/if}
{/each}

<style>
	.flow {
		fill: none;
		opacity: 0.62;
		stroke-linecap: butt;
		cursor: pointer;
	}
	.flow:hover,
	.flow.held {
		opacity: 1;
	}
	circle {
		cursor: default;
	}
</style>
