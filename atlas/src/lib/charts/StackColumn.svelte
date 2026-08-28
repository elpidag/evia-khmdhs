<script lang="ts">
	/**
	 * ONE stacked column — the Who Owns Britain dashboard's form (user,
	 * 2026-08-28, the Anti-nero card's AWARD PROCEDURES): every row is a
	 * segment of one column, height = its share of the total, the share
	 * printed inside a segment tall enough to carry it.
	 *
	 * Two dressings. `variant="side"` (the first drawing): biggest segment
	 * on top, the name, value and second line beside the column on a short
	 * leader, `highlight` at full strength and the rest at 35 %.
	 * `variant="card"` (the user's own edit of the card page, 2026-08-28):
	 * SMALLEST segment on top and the biggest at the foot, the segments in
	 * the site's grey ramp darkening with size and parted by white seams,
	 * the COUNT at the left of the column, the NAME at its right in lower
	 * case (bold for the highlighted row), no € and no leaders — the
	 * column set ~24 % in from the left so the counts have their room.
	 * Pure SVG, sized to its box; every figure printed is computed.
	 */
	import { eurShort, pct } from '$lib/transforms/format';
	import { RAMP_WORKS } from '$lib/maps/useGeo';
	interface Row {
		label: string;
		value: number;
		sub?: string;
	}
	let {
		rows,
		color = 'var(--ink)',
		width = 0,
		height = 0,
		fmt = eurShort,
		highlight = null,
		variant = 'side',
		inset = 0,
		ramp = RAMP_WORKS,
		ariaLabel = 'Stacked column'
	}: {
		rows: Row[];
		color?: string;
		width?: number;
		height?: number;
		fmt?: (v: number) => string;
		/** the segments drawn at full strength (side) / in bold (card) */
		highlight?: ((r: Row) => boolean) | null;
		variant?: 'side' | 'card';
		/** the card: how far the box extends into the tile's padding on
		 *  each side — the drawing keeps the tile's own left edge as 0 */
		inset?: number;
		/** the card's tones: a ramp whose darker half colours the segments
		 *  (the greys by default, the ΔΑΣΕ greens on that card) */
		ramp?: string[];
		ariaLabel?: string;
	} = $props();
	const COL_W_SIDE = 56;
	const COL_W_CARD = 48; // narrower on the card, so the names have their room (user, 2026-08-28)
	const SEG_GAP = 4; // the card's segments stand a little apart (user, 2026-08-28)
	const GAP = 12; // column → leader → label (side)
	const LEAD = 8;
	const NAME = 12; // a row of the 10 px names
	const LINE = 11; // the 9,3 px value / second lines
	const CHAR = 4.5; // the ui face at 10 px, per character (Futura Book runs narrow)
	const card = $derived(variant === 'card');
	const COL_W = $derived(card ? COL_W_CARD : COL_W_SIDE);
	const ordered = $derived(card ? [...rows].sort((a, b) => a.value - b.value) : rows);
	const total = $derived(rows.reduce((s, r) => s + Math.max(0, r.value), 0));
	/** the tile's own width, without the padding the box bleeds into */
	const innerW = $derived(width - 2 * inset);
	/** the column's left edge: flush in the side form, ~24 % into the
	 *  tile on the card (the user's drawing: 46,6 px of 195) */
	const colX = $derived(card ? inset + Math.round(innerW * 0.239) : 0);
	const labX = $derived(card ? colX + COL_W + 2.5 : COL_W + GAP + LEAD);
	/** the names' room: to the box's right edge */
	const labW = $derived(Math.max(40, width - labX));
	/** real text widths where a canvas is at hand (the browser), the
	 *  per-character estimate on the server */
	let measurer: CanvasRenderingContext2D | null = null;
	$effect(() => {
		const c = document.createElement('canvas').getContext('2d');
		if (!c) return;
		c.font = `10px ${getComputedStyle(document.body).fontFamily}`;
		measurer = c;
		fontReady = true;
	});
	let fontReady = $state(false);
	const textW = (s: string) => (fontReady && measurer ? measurer.measureText(s).width : s.length * CHAR);
	/** the grey ramp's darker half, one tone per segment, the biggest black */
	const tone = (i: number, k: number) =>
		ramp[k <= 1 ? 7 : Math.round(3 + (i * 4) / (k - 1))];
	/** the name beside a segment, WHOLE: wrapped on words to the label's width */
	const wrap = (s: string): string[] => {
		const out: string[] = [];
		let cur = '';
		for (const w of s.split(/\s+/)) {
			if (cur && textW(cur + ' ' + w) > labW) {
				out.push(cur);
				cur = w;
			} else cur = cur ? cur + ' ' + w : w;
		}
		if (cur) out.push(cur);
		// a two-line name breaks where its lines come out most even —
		// «negotiated procedure / without prior publication», the user's
		// own break, not «… without / prior publication»
		if (out.length === 2) {
			const words = s.split(/\s+/);
			let best = out;
			let bestW = Math.max(textW(out[0]), textW(out[1]));
			for (let i = 1; i < words.length; i++) {
				const a = words.slice(0, i).join(' ');
				const b = words.slice(i).join(' ');
				const w = Math.max(textW(a), textW(b));
				if (w <= labW && w < bestW) {
					best = [a, b];
					bestW = w;
				}
			}
			return best;
		}
		return out;
	};
	const segs = $derived.by(() => {
		const H = Math.max(40, height);
		const gap = card ? SEG_GAP : 0;
		const stackH = H - gap * Math.max(0, ordered.length - 1);
		let acc = 0;
		const out = ordered.map((r, i) => {
			const h = total ? (stackH * Math.max(0, r.value)) / total : 0;
			const name = wrap(card ? r.label.toLowerCase() : r.label);
			const bh = card ? name.length * NAME : name.length * NAME + LINE + (r.sub ? LINE : 0);
			const hot = highlight ? highlight(r) : false;
			const s = {
				r,
				i,
				y: acc,
				h,
				share: total ? (100 * r.value) / total : 0,
				mid: acc + h / 2,
				name,
				bh,
				// a two-line name on the card rides 3 px above the middle (user)
				ly: acc + h / 2 - (card && name.length > 1 ? 3 : 0),
				hot,
				dim: highlight && !card ? !hot : false,
				fill: card ? tone(i, ordered.length) : color,
				dark: card ? i >= (ordered.length - 1) / 2 : !highlight || hot
			};
			acc += h + gap;
			return s;
		});
		// labels pushed apart by their own heights, then back inside the box
		// (a label taller than its segment is first kept inside the top)
		for (const s of out) s.ly = Math.max(s.bh / 2, s.ly);
		for (let i = 1; i < out.length; i++)
			out[i].ly = Math.max(out[i].ly, out[i - 1].ly + (out[i - 1].bh + out[i].bh) / 2 + 4);
		const last = out[out.length - 1];
		const over = last ? last.ly + last.bh / 2 - H : 0;
		if (over > 0)
			for (let i = out.length - 1; i >= 0; i--) {
				out[i].ly -= over;
				if (i && out[i].ly - out[i - 1].ly < (out[i - 1].bh + out[i].bh) / 2 + 4)
					out[i - 1].ly = out[i].ly - (out[i - 1].bh + out[i].bh) / 2 - 4;
			}
		for (const s of out) s.ly = Math.max(s.bh / 2, s.ly);
		return out;
	});
</script>

{#if width && height}
	<svg {width} {height} viewBox="0 0 {width} {height}" role="img" aria-label={ariaLabel} class:card>
		{#each segs as s (s.r.label)}
			{@const top = s.ly - s.bh / 2}
			<g class:dim={s.dim}>
				<rect
					x={colX}
					y={s.y}
					width={COL_W}
					height={Math.max(0.6, s.h - (card ? 0 : 1))}
					fill={s.fill}
					class="seg"
					class:seam={card}
				/>
				{#if s.h >= 14}
					<text x={colX + COL_W / 2} y={s.mid + 3.5} class="share" class:onink={s.dark}>{pct(s.share, 0)}</text>
				{/if}
				{#if card}
					{#if s.r.sub}
						<text x={colX - 4} y={s.ly + 3.5} class="sub" text-anchor="end">{s.r.sub}</text>
					{/if}
					{#each s.name as line, j (j)}
						<text x={labX} y={top + 9 + j * NAME} class="lab" class:hot={s.hot}>{line}</text>
					{/each}
				{:else}
					<polyline
						points="{COL_W + 2},{s.mid} {COL_W + GAP},{s.ly} {COL_W + GAP + LEAD - 3},{s.ly}"
						fill="none"
						stroke="var(--ink-faint)"
						stroke-width="0.7"
					/>
					{#each s.name as line, j (j)}
						<text x={labX} y={top + 9 + j * NAME} class="lab">{line}</text>
					{/each}
					<text x={labX} y={top + s.name.length * NAME + 8} class="val">{fmt(s.r.value)}</text>
					{#if s.r.sub}
						<text x={labX} y={top + s.name.length * NAME + LINE + 8} class="sub">{s.r.sub}</text>
					{/if}
				{/if}
			</g>
		{/each}
	</svg>
{/if}

<style>
	svg {
		display: block;
		overflow: visible;
	}
	.dim .seg {
		opacity: 0.35;
	}
	/* the card's segments are parted by a hairline of the paper */
	.seg.seam {
		stroke: #fff;
		stroke-width: 0.4;
	}
	.share {
		font-family: var(--font-ui);
		font-size: 10px;
		font-weight: 700;
		fill: var(--ink);
		text-anchor: middle;
	}
	.share.onink {
		fill: #fff;
	}
	.lab {
		font-family: var(--font-ui);
		font-size: 10px;
		fill: var(--ink);
	}
	.lab.hot {
		font-weight: 700;
	}
	.val {
		font-family: var(--font-ui);
		font-size: 9.32px;
		font-weight: 700;
		fill: var(--ink);
	}
	.sub {
		font-family: var(--font-ui);
		font-size: 9.32px;
		fill: var(--ink-soft);
	}
</style>
