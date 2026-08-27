<script lang="ts">
	/**
	 * WHAT TYPES OF COMPANIES ARE INVOLVED (user, 2026-08-27) — the kinds
	 * of business by the NUMBER of projects each holds; no money on this
	 * card. Artboard 4's own drawing: one row per kind, all twelve sharing
	 * the tile's height so nothing scrolls, the name inside the bar in
	 * Futura 100 GR 10 px white where it measures to fit and beside it in
	 * ink where it does not, the count at the right in 9,3 px.
	 *
	 * A vertical stacked form was built the same day and PARKED on the
	 * user's decision to keep the bars alone; `mode` still carries it.
	 */
	export interface TypeGroup {
		key?: string;
		label: string;
		n: number;
	}
	let {
		groups,
		mode = 'bars',
		color = 'var(--c-anadohoi)',
		height = 0
	}: { groups: TypeGroup[]; mode?: 'bars' | 'column'; color?: string; height?: number } = $props();

	const rows = $derived([...groups].filter((g) => g.n > 0).sort((a, b) => b.n - a.n));
	const total = $derived(rows.reduce((s, g) => s + g.n, 0));
	const max = $derived(Math.max(1, ...rows.map((g) => g.n)));
	const keyOf = (g: TypeGroup) => g.key ?? g.label;
	const count = (n: number) => `${n} ${n === 1 ? 'project' : 'projects'}`;
	/** the ramp: full strength for the biggest kind, pale for the smallest */
	function tone(i: number, k: number) {
		const p = k <= 1 ? 100 : 100 - (i * 74) / (k - 1);
		return `color-mix(in srgb, ${color} ${p.toFixed(0)}%, white)`;
	}

	// ---- bars: the artboard's longest bar is 65% of the row, the count
	//      right-aligned in the rest; the name goes inside only where it fits
	let boxW = $state(0);
	let labW = $state<number[]>([]);
	const BAR_PAD = 12;
	const barW = (n: number) => Math.max(6, boxW * 0.65 * (n / max));

	// ---- column (parked): segment heights, labels pushed apart on a leader
	let colH = $state(0);
	const COL_W = 78;
	const LAB_X = COL_W + 26;
	const MIN_GAP = 14;
	const seg = $derived.by(() => {
		const H = Math.max(80, height || colH || 300);
		let acc = 0;
		const out = rows.map((g, i) => {
			const h = total ? (H * g.n) / total : 0;
			const s = { g, i, y: acc, h, mid: acc + h / 2, fill: tone(i, rows.length), ly: acc + h / 2 };
			acc += h;
			return s;
		});
		for (let i = 1; i < out.length; i++)
			out[i].ly = Math.max(out[i].ly, out[i - 1].ly + MIN_GAP);
		const over = out.length ? out[out.length - 1].ly - (H - 6) : 0;
		if (over > 0) {
			for (let i = out.length - 1; i >= 0; i--) {
				out[i].ly -= over;
				if (i && out[i].ly - out[i - 1].ly < MIN_GAP) out[i - 1].ly = out[i].ly - MIN_GAP;
			}
		}
		return { items: out, H };
	});
</script>

{#if mode === 'column'}
	<div class="col" bind:clientHeight={colH}>
		<svg
			viewBox="0 0 460 {seg.H}"
			preserveAspectRatio="xMinYMin meet"
			role="img"
			aria-label="Kinds of business by number of projects"
		>
			{#each seg.items as s (keyOf(s.g))}
				<rect x="0" y={s.y} width={COL_W} height={Math.max(0.6, s.h - 0.6)} fill={s.fill} />
				<polyline
					points="{COL_W + 3},{s.mid} {LAB_X - 8},{s.ly} {LAB_X - 4},{s.ly}"
					fill="none"
					stroke="var(--line)"
					stroke-width="0.6"
				/>
				<text x={LAB_X} y={s.ly + 3.2} class="lab">{s.g.label}</text>
				<text x="458" y={s.ly + 3.2} class="val">{count(s.g.n)}</text>
			{/each}
		</svg>
	</div>
{:else}
	<div class="bars" style:grid-template-rows="repeat({rows.length}, minmax(0, 1fr))" bind:clientWidth={boxW}>
		<div class="measure" aria-hidden="true">
			{#each rows as g, i (keyOf(g))}
				<span class="glab" bind:clientWidth={labW[i]}>{g.label}</span>
			{/each}
		</div>
		{#each rows as g, i (keyOf(g))}
			{@const w = barW(g.n)}
			{@const inside = (labW[i] ?? 9999) + BAR_PAD <= w}
			<div class="row">
				<span class="bar" style:width="{w}px" style:background={tone(i, rows.length)}>
					{#if inside}<span class="glab in">{g.label}</span>{/if}
				</span>
				{#if !inside}<span class="glab out">{g.label}</span>{/if}
				<span class="val">{count(g.n)}</span>
			</div>
		{/each}
	</div>
{/if}

<style>
	/* every kind shares the tile's height — the card never scrolls */
	/* the user's edit: 25 px bars 3,3 px apart, twelve rows on the tile */
	.bars {
		display: grid;
		gap: 3.3px;
		height: 100%;
		min-width: 0;
		overflow: hidden;
	}
	.row {
		display: flex;
		align-items: center;
		gap: 8px;
		min-width: 0;
	}
	/* 25 px tall (the user's edit), never taller than the row it sits in */
	.bar {
		flex: none;
		height: min(25px, 100%);
		border-radius: 2px;
		display: flex;
		align-items: center;
		overflow: hidden;
	}
	.glab {
		font-family: var(--font-ui);
		font-weight: 400;
		font-size: 10px;
		line-height: 1.1;
		text-transform: uppercase;
		white-space: nowrap;
		align-self: center;
	}
	.glab.in {
		color: #fff;
		padding-left: 4px;
	}
	.glab.out {
		color: var(--ink);
	}
	.val {
		margin-left: auto;
		flex: none;
		align-self: center;
		padding-right: 14px;
		font-family: var(--font-ui);
		font-size: 9.32px;
		color: var(--ink-soft);
		white-space: nowrap;
		font-variant-numeric: tabular-nums;
	}
	/* measured off-screen; a ResizeObserver reports nothing for an INLINE
	   element, so the measuring spans must be inline-block */
	.measure span {
		display: inline-block;
	}
	.measure {
		position: absolute;
		visibility: hidden;
		height: 0;
		overflow: hidden;
		white-space: nowrap;
		font-family: var(--font-ui);
		font-size: 10px;
		text-transform: uppercase;
	}
	.col {
		height: 100%;
		min-height: 0;
	}
	.col svg {
		width: 100%;
		height: 100%;
		display: block;
	}
	.lab {
		font-family: var(--font-ui);
		font-size: 9.5px;
		fill: var(--ink);
		text-transform: uppercase;
	}
	.col .val {
		font-family: var(--font-ui);
		font-size: 9.5px;
		fill: var(--ink-soft);
		text-anchor: end;
	}
</style>
