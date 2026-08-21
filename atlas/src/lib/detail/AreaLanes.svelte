<script lang="ts">
	/**
	 * The per-area STRIPS of a contract's timeline bar — SVG fragments drawn
	 * inside ChainTimeline's <svg>, on its axis (user, 2026-08-21, second
	 * round: «instead of duplicating the bar, split the grey part»).
	 *
	 * The solid bar is the contract's promise, once. After the announced
	 * deadline its lighter (extended) part is split into one thin strip per
	 * forest service: the strip runs to the last date that service's own
	 * partial extensions granted, cut into SEGMENTS — one piece per extension,
	 * from the deadline it found in force to the one it granted, consecutive
	 * pieces in two alternating tones of the same grey, no lines (the day the
	 * approval was signed is in the piece's hover card and its trail row) —
	 * the service's name at the right end of its own grey bar («Kalampaka
	 * F.S.O.», on hover), and shows a ✔ ONLY where ΥΠΕΝ accepted that part on its own —
	 * an area without a part-acceptance has no ✔ of its own (the contract's
	 * single acceptance stays on the bar). Acts that name no area sit on a
	 * last strip, said so. Same lettering, no-outline symbols, two-way hover
	 * with the document trail.
	 */
	import { dmy } from '$lib/transforms/format';
	import type { Lane, LaneStepLike } from '$lib/transforms/lanes';

	interface Props {
		lanes: Lane<LaneStepLike>[];
		x: (d: string | null) => number | null;
		/** signature x */
		xs: number;
		/** the announced deadline's x, null when none was announced */
		xd: number | null;
		/** y of the bar's top — the first strip starts here */
		top: number;
		/** one strip's row height (the strip itself is 1 unit shorter) */
		stripH: number;
		/** chart width — the names are right-aligned at the timeline's end */
		w: number;
		highlightRef?: string | null;
		onActHover?: (ref: string | null) => void;
	}
	let { lanes, x, xs, xd, top, stripH, w, highlightRef = null, onActHover }: Props = $props();

	const ORDINAL = (n: number): string =>
		n === 1 ? '1st' : n === 2 ? '2nd' : n === 3 ? '3rd' : `${n}th`;
	// the strips start where the bar's grey part would — at the announced
	// deadline; without one, right after the signature stub
	const x0 = $derived(xd !== null && xd > xs ? xd : xs + 7);

	/** where a strip's ink ends: the latest deadline its acts granted */
	function lastX(lane: Lane<LaneStepLike>): number {
		let m = x0;
		for (const s of lane.steps) {
			const sx = x(s.deadline);
			if (sx !== null && sx > m) m = sx;
		}
		return m;
	}
	/** one piece per extension: from the deadline in force to the one it granted */
	function segments(lane: Lane<LaneStepLike>) {
		const out: { s: LaneStepLike; x0: number; x1: number; alt: boolean }[] = [];
		let cur = x0;
		let alt = false;
		const ordered = [...lane.steps].sort((a, b) => (a.deadline ?? '').localeCompare(b.deadline ?? ''));
		for (const s of ordered) {
			const dx = x(s.deadline);
			if (dx === null || dx <= cur) continue; // a re-statement adds no piece
			out.push({ s, x0: cur, x1: dx, alt });
			alt = !alt;
			cur = dx;
		}
		return out;
	}
	const rows = $derived(
		lanes.map((lane, i) => {
			const xl = lastX(lane);
			const own = lane.end && !lane.end.shared ? x(lane.end.d) : null;
			const y = top + i * stripH;
			const mid = y + (stripH - 1) / 2;
			const label = lane.label + (lane.extra ? ' *' : '');
			// the name sits at the right end of ITS OWN grey bar (user,
			// 2026-08-21, final form); when there is no room before the chart's
			// edge it sits just ABOVE the bar's end instead — never on the grey;
			// ~4.4 units per character at 8px
			const fits = xl + 5 + label.length * 4.4 < w - 2;
			return { lane, y, mid, xl, own, label, fits, segs: segments(lane) };
		})
	);
	const hot = (ref: string | null | undefined) => highlightRef !== null && ref === highlightRef;
	// the service's name shows only while the reader is over its strip — or
	// while one of its acts is lit from the document trail (user, 2026-08-21)
	let hoverKey = $state<string | null>(null);
	const named = (r: (typeof rows)[number]) =>
		hoverKey === r.lane.key ||
		(highlightRef !== null &&
			(r.lane.steps.some((s) => s.ref === highlightRef) || r.lane.end?.ref === highlightRef));
</script>

{#each rows as r (r.lane.key)}
	<!-- the strip: one piece per extension, alternating tones, no lines -->
	{#each r.segs as g (g.s.ref)}
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<rect
			x={g.x0}
			y={r.y}
			width={g.x1 - g.x0}
			height={stripH - 1}
			class="strip"
			class:alt={g.alt}
			class:hot={hot(g.s.ref)}
			onmouseenter={() => ((hoverKey = r.lane.key), onActHover?.(g.s.ref))}
			onmouseleave={() => ((hoverKey = null), onActHover?.(null))}
		>
			<title
				>{ORDINAL(g.s.n)} partial extension — approved {dmy(g.s.d)} · {r.lane.unplaced
					? 'area not stated in the act'
					: r.lane.label} → {dmy(g.s.deadline)}</title
			>
		</rect>
	{/each}
	{#if r.own !== null && r.lane.end}
		<!-- this area's OWN acceptance — a shared one draws nothing here -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<text
			x={r.own}
			y={r.mid + 3}
			class="stripmark"
			class:hot={hot(r.lane.end.ref)}
			text-anchor="middle"
			onmouseenter={() => onActHover?.(r.lane.end?.ref ?? null)}
			onmouseleave={() => onActHover?.(null)}
		>
			✔<title>{dmy(r.lane.end.d)} — this area’s own acceptance</title>
		</text>
	{/if}
	<!-- the service's name, right-aligned at the timeline's end, only while
	     its strip is hovered (user, 2026-08-21) -->
	{#if named(r)}
		<text
			x={r.fits ? r.xl + 5 : r.xl}
			y={r.fits ? r.mid + 3 : r.y - 2.5}
			class="striplbl"
			class:unplaced={r.lane.unplaced}
			text-anchor={r.fits ? 'start' : 'end'}>{r.label}</text
		>
	{/if}
{/each}

<style>
	/* consecutive pieces alternate two tones of the bar's own ink */
	.strip {
		fill: var(--c-antinero);
		opacity: 0.28;
		cursor: default;
	}
	.strip.alt {
		opacity: 0.42;
	}
	.strip:hover,
	.strip.hot {
		opacity: 0.6;
	}
	.stripmark {
		font-size: 8px;
		font-weight: 900;
		fill: var(--ink);
		stroke: none;
		cursor: pointer;
	}
	.stripmark.hot {
		fill: var(--c-antinero);
		font-size: 9.5px;
	}
	/* plain letters, NO outline (user, 2026-08-21) */
	.striplbl {
		font-size: 8px;
		fill: var(--ink);
		font-weight: 600;
		stroke: none;
		pointer-events: none;
	}
	.striplbl.unplaced {
		fill: var(--ink-faint);
		font-style: italic;
	}
</style>
