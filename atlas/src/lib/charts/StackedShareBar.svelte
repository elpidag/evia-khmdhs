<script lang="ts">
	/** One 100%-stacked horizontal bar. Category labels sit inside their
	 *  segments (white, Futura 100 GRK Book); each count pops out as a
	 *  black circular badge straddling the bar's top edge over its
	 *  segment's centre. A segment too narrow for its label lists it
	 *  after the bar in the segment's colour. */
	import { grInt } from '$lib/transforms/format';

	export interface ShareSeg {
		label: string;
		value: number;
		color: string;
		/** hover-badge spot: floating slightly above the bar (default), or
		 *  outside the bar at its vertical middle, left or right of it */
		badge?: 'above' | 'outleft' | 'outright';
	}
	interface Props {
		segments: ShareSeg[];
		/** bar height in px */
		height?: number;
	}
	let { segments, height = 50 }: Props = $props();

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

	// fit rule: the label goes inside when the segment can hold its
	// longest word (multi-word labels may wrap onto two lines)
	let barW = $state(0);
	let wordW = $state<number[]>([]);
	const longestWord = (s: string) =>
		s.split(' ').reduce((a, b) => (b.length > a.length ? b : a), '');
	const fits = $derived(
		segs.map((s, i) => {
			const px = (barW * s.value) / total;
			return (wordW[i] ?? Infinity) + 12 <= px;
		})
	);
	const outside = $derived(placed.filter((_, i) => !fits[i]));
	// count badges show on hover only, at their fixed spots
	let hot = $state<number | null>(null);
</script>

<div class="row">
	<div class="ssbwrap">
		<div class="ssb" bind:clientWidth={barW} style:height={`${height}px`}>
			<div class="measure" aria-hidden="true">
				{#each segs as s, i (s.label)}
					<span bind:clientWidth={wordW[i]}>{longestWord(s.label)}</span>
				{/each}
			</div>
			{#each placed as p, i (p.s.label)}
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<div
					class="seg"
					style:width={`${p.w}%`}
					style:background={p.s.color}
					title={`${p.s.label}: ${grInt(p.s.value)}`}
					onmouseenter={() => (hot = i)}
					onmouseleave={() => (hot = null)}
				>
					{#if fits[i]}<span class="lab">{p.s.label}</span>{/if}
				</div>
			{/each}
		</div>
		<div class="badges" aria-hidden="true">
			{#each placed as p, i (p.s.label)}
				{#if p.s.badge === 'outleft'}
					<span
						class="badge"
						class:show={hot === i}
						style:left={`-19px`}
						style:top={`${2 + height / 2 - 13}px`}>{grInt(p.s.value)}</span
					>
				{:else if p.s.badge === 'outright'}
					<span
						class="badge"
						class:show={hot === i}
						style:left={`calc(100% + 19px)`}
						style:top={`${2 + height / 2 - 13}px`}>{grInt(p.s.value)}</span
					>
				{:else}
					<span
						class="badge"
						class:show={hot === i}
						style:left={`${p.center}%`}
						style:top={`-25px`}>{grInt(p.s.value)}</span
					>
				{/if}
			{/each}
		</div>
		{#if outside.length}
			<div class="out">
				{#each outside as p (p.s.label)}
					{#if p.center > 92}
						<span class="edge-r" style:color={p.s.color}>{p.s.label}</span>
					{:else}
						<span
							style:left={`${p.center}%`}
							style:color={p.s.color}
							class="mid">{p.s.label}</span
						>
					{/if}
				{/each}
			</div>
		{/if}
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
		/* headroom for the badges straddling the top edge */
		padding-top: 15px;
	}
	.ssb {
		display: flex;
		border-radius: 10px;
		overflow: hidden;
	}
	.measure {
		position: absolute;
		visibility: hidden;
		height: 0;
		overflow: hidden;
		white-space: nowrap;
		font-family: 'futura-100-greek-book', 'futura-100-greek', 'Sofia Sans', sans-serif;
		font-size: var(--fs-16);
	}
	.measure span {
		display: inline-block;
	}
	.seg {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0 9px;
		overflow: hidden;
		text-align: center;
	}
	.lab,
	.out span {
		font-family: 'futura-100-greek-book', 'futura-100-greek', 'Sofia Sans', sans-serif;
		font-weight: 400;
		font-size: var(--fs-16);
		line-height: 1.12;
	}
	.lab {
		color: #fff;
	}
	.badges {
		position: absolute;
		inset: 0;
		pointer-events: none;
	}
	.badge {
		position: absolute;
		transform: translateX(-50%);
		width: 26px;
		height: 26px;
		border-radius: 50%;
		background: #000;
		color: #fff;
		display: flex;
		align-items: center;
		justify-content: center;
		font-family: 'futura-100-greek', 'futura-100-greek-book', 'Sofia Sans', sans-serif;
		font-size: var(--fs-13);
		box-shadow: 0 1px 4px rgba(0, 0, 0, 0.35);
		opacity: 0;
		transition: opacity 0.12s;
	}
	.badge.show {
		opacity: 1;
	}
	/* labels that don't fit sit BELOW the bar, near their segment */
	.out {
		position: relative;
		height: 1.5em;
		margin-top: var(--sp-1);
	}
	.out span {
		position: absolute;
		top: 0;
		white-space: nowrap;
	}
	.out span.mid {
		transform: translateX(-50%);
	}
	.out span.edge-r {
		right: 0;
	}
</style>
