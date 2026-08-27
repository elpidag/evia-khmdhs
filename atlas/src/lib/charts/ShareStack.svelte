<script lang="ts">
	/**
	 * ONE stacked share bar of the sponsor groups (user, 2026-08-27, the
	 * card tile of WHO THE SPONSORS ARE): every kind of business is a
	 * segment of one bar, width = its share of the committed €, in a ramp
	 * of the section hue from full strength (the biggest) to pale; the
	 * share prints above a segment wide enough to carry it. A KEY under
	 * the bar names every group with its € and share in two columns —
	 * hovering a row lights its segment — and the groups that committed
	 * no stated sum are listed there too, since a share of zero cannot be
	 * drawn. Everything printed is computed from the payload.
	 */
	import { eurShort, pct } from '$lib/transforms/format';

	export interface ShareGroup {
		key?: string;
		label: string;
		eur: number;
		n: number;
	}
	let {
		groups,
		color = 'var(--c-anadohoi)',
		height = 30
	}: { groups: ShareGroup[]; color?: string; height?: number } = $props();

	const funded = $derived(groups.filter((g) => g.eur > 0));
	const unfunded = $derived(groups.filter((g) => !(g.eur > 0)));
	const total = $derived(funded.reduce((s, g) => s + g.eur, 0));
	/** the ramp: 100% of the hue for the first segment down to 22% for the last */
	function tone(i: number, k: number) {
		const p = k <= 1 ? 100 : 100 - (i * 78) / (k - 1);
		return `color-mix(in srgb, ${color} ${p.toFixed(0)}%, white)`;
	}
	const segs = $derived.by(() => {
		let acc = 0;
		return funded.map((g, i) => {
			const w = total ? (100 * g.eur) / total : 0;
			const s = { g, w, start: acc, fill: tone(i, funded.length), i };
			acc += w;
			return s;
		});
	});
	let hot = $state<number | null>(null);
	const keyOf = (g: ShareGroup) => g.key ?? g.label;
</script>

<div class="stack">
	<div class="nums" aria-hidden="true">
		{#each segs as s (keyOf(s.g))}
			{#if s.w >= 7}
				<span class="num" class:hot={hot === s.i} style:left="{s.start}%" style:width="{s.w}%"
					>{pct(s.w, 0)}</span
				>
			{/if}
		{/each}
	</div>
	<div class="bar" style:height="{height}px" role="img" aria-label="Committed € by kind of sponsor">
		{#each segs as s (keyOf(s.g))}
			<span
				class="seg"
				class:hot={hot === s.i}
				class:dim={hot !== null && hot !== s.i}
				style:width="{s.w}%"
				style:background={s.fill}
				title="{s.g.label} · {eurShort(s.g.eur)} · {pct(s.w, 1)}"
			></span>
		{/each}
	</div>
	<ul class="key">
		{#each segs as s (keyOf(s.g))}
			<li
				class:hot={hot === s.i}
				onmouseenter={() => (hot = s.i)}
				onmouseleave={() => (hot = null)}
			>
				<i class="sw" style:background={s.fill}></i>
				<span class="lab">{s.g.label}</span>
				<span class="val">{eurShort(s.g.eur)}</span>
				<span class="share">{pct(s.w, 1)}</span>
			</li>
		{/each}
		{#each unfunded as g (keyOf(g))}
			<li class="none">
				<i class="sw"></i>
				<span class="lab">{g.label}</span>
				<span class="val">no stated sum</span>
				<span class="share">{g.n} {g.n === 1 ? 'project' : 'projects'}</span>
			</li>
		{/each}
	</ul>
</div>

<style>
	.stack {
		display: flex;
		flex-direction: column;
		gap: 4px;
		min-width: 0;
	}
	.nums {
		position: relative;
		height: 14px;
		font-family: var(--font-ui);
		font-size: var(--fs-12);
		color: var(--ink-soft);
	}
	.num {
		position: absolute;
		top: 0;
		text-align: center;
		white-space: nowrap;
		overflow: hidden;
	}
	.num.hot {
		color: var(--ink);
		font-weight: 700;
	}
	.bar {
		display: flex;
		width: 100%;
		overflow: hidden;
	}
	.seg {
		display: block;
		height: 100%;
		transition: opacity 0.12s ease;
	}
	.seg.dim {
		opacity: 0.45;
	}
	.key {
		list-style: none;
		margin: 6px 0 0;
		padding: 0;
		display: grid;
		grid-template-columns: 1fr 1fr;
		column-gap: 18px;
		row-gap: 2px;
	}
	.key li {
		display: grid;
		grid-template-columns: 10px minmax(0, 1fr) auto auto;
		align-items: center;
		gap: 6px;
		font-family: var(--font-ui);
		font-size: var(--fs-12);
		line-height: 1.25;
		color: var(--ink-soft);
		cursor: default;
	}
	.key li.hot {
		color: var(--ink);
	}
	.key li.none {
		color: var(--ink-faint);
	}
	.sw {
		width: 10px;
		height: 10px;
		display: inline-block;
		border: 1px solid transparent;
		box-sizing: border-box;
	}
	.none .sw {
		border-color: var(--line);
		background: transparent;
	}
	.lab {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.val,
	.share {
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
	.share {
		min-width: 3.2em;
		text-align: right;
	}
</style>
