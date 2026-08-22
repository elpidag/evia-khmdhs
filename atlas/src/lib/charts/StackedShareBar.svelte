<script lang="ts">
	import { grInt } from '$lib/transforms/format';

	/**
	 * ONE horizontal bar whose segments share a total — the SCOPE charts
	 * (Anti-nero CONTRACT SCOPE, sponsored PROJECT SCOPE), which is all
	 * this component draws since PROJECT TYPE became a BarH (2026-08-22).
	 *
	 * Redesigned per the user the same day: the counts print as PLAIN
	 * NUMBERS always visible above each segment (the hover pills are
	 * gone), and EVERY label sits on one line under the bar at its
	 * segment's position — «study only», «study & works» and «works only»
	 * read together. Edge labels pin to the frame so nothing overflows.
	 */
	export interface ShareSeg {
		label: string;
		value: number;
		color: string;
		/** label ink where the segment colour is too pale to read;
		 *  defaults to the segment colour */
		labelColor?: string;
		/** kept for call-site compatibility; the numbers are always shown */
		badge?: 'above' | 'outleft' | 'outright';
	}
	interface Props {
		segments: ShareSeg[];
		/** bar height in px */
		height?: number;
		/** number formatter (default: Greek-formatted integer) */
		fmt?: (v: number) => string;
		/** kept for call-site compatibility; labels always show below */
		outside?: boolean;
	}
	let { segments, height = 34, fmt = grInt }: Props = $props();

	const segs = $derived(segments.filter((s) => s.value > 0));
	const total = $derived(Math.max(1, segs.reduce((s, x) => s + x.value, 0)));
	const placed = $derived.by(() => {
		let acc = 0;
		return segs.map((s) => {
			const w = (100 * s.value) / total;
			const out = { s, w, start: acc, center: acc + w / 2 };
			acc += w;
			return out;
		});
	});
</script>

<div class="row">
	<div class="ssbwrap">
		<!-- the numbers: plain, always on, above their segments -->
		<div class="nums" aria-hidden="true">
			{#each placed as p (p.s.label)}
				{#if p.center < 3}
					<span class="edge-l">{fmt(p.s.value)}</span>
				{:else if p.center > 97}
					<span class="edge-r">{fmt(p.s.value)}</span>
				{:else}
					<span class="mid" style:left={`${p.center}%`}>{fmt(p.s.value)}</span>
				{/if}
			{/each}
		</div>
		<div class="ssb" style:height={`${height}px`}>
			{#each placed as p (p.s.label)}
				<div
					class="seg"
					style:width={`${p.w}%`}
					style:background={p.s.color}
					title={`${p.s.label}: ${fmt(p.s.value)}`}
				></div>
			{/each}
		</div>
		<!-- every label on ONE line under the bar, at its segment -->
		<div class="out">
			{#each placed as p (p.s.label)}
				{#if p.center > 92}
					<span class="edge-r" style:color={p.s.labelColor ?? p.s.color}>{p.s.label}</span>
				{:else if p.center < 8}
					<span class="edge-l" style:color={p.s.labelColor ?? p.s.color}>{p.s.label}</span>
				{:else}
					<span class="mid" style:left={`${p.center}%`} style:color={p.s.labelColor ?? p.s.color}
						>{p.s.label}</span
					>
				{/if}
			{/each}
		</div>
	</div>
</div>

<style>
	.row {
		display: flex;
		align-items: center;
		gap: var(--sp-3);
	}
	.ssbwrap {
		position: relative;
		flex: 1;
		min-width: 0;
	}
	/* the number line above the bar; pages may give it extra height to
	   align the bar with a neighbouring chart's rows */
	.nums {
		position: relative;
		height: 20px;
	}
	.nums span {
		position: absolute;
		bottom: 3px;
		font-size: var(--fs-13);
		color: var(--ink-soft);
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
	.ssb {
		display: flex;
		border-radius: 2px; /* matches BarH — the pair charts share corners */
		overflow: hidden;
	}
	.seg {
		display: block;
		height: 100%;
	}
	.out {
		position: relative;
		height: 1.5em;
		margin-top: var(--sp-1);
	}
	.out span {
		position: absolute;
		font-weight: 400;
		font-size: var(--fs-13);
		line-height: 1.12;
		white-space: nowrap;
	}
	.nums span.mid,
	.out span.mid {
		transform: translateX(-50%);
	}
	.nums span.edge-r,
	.out span.edge-r {
		right: 0;
	}
	.nums span.edge-l,
	.out span.edge-l {
		left: 0;
	}
</style>
