<script lang="ts">
	/**
	 * One Anti-nero contract's life on the programme axis: the bar from
	 * signature to the day it was accepted, a dot for every later act on the
	 * same contract (τροποποίηση όρων, παράταση προθεσμίας, έγκριση
	 * συμπληρωματικών εργασιών), a tick for every payment order, and the ✔ of
	 * its completion act.
	 *
	 * It is the sponsor pages' ActTimelineBar one level down — same programme
	 * axis, same lettering, same dashed «today» rule drawn last, same
	 * two-way hover with the document trail — with two differences the data
	 * makes possible: payments, which no other view puts on a time axis, and
	 * the printed € step where a supplementary approval moved the price
	 * («€3,78M → €5,00M»), exactly as PromiseGantt prints a restatement.
	 *
	 * The axis is FIXED across contract pages (user decision, 2026-08-19), so
	 * two contracts can be compared by eye; a short 2026 contract is a short
	 * bar at the right, and that is the reading.
	 */
	import { dmy, eurShort } from '$lib/transforms/format';

	export interface ChainAct {
		ref: string;
		/** ISO date, already normalised */
		d: string | null;
		/** document_kind — what this record IS */
		kind: string | null;
		eur: number | null;
		self?: boolean;
	}
	export interface PayTick {
		ref: string;
		/** ISO date, already normalised */
		d: string | null;
		eur: number | null;
	}
	interface Props {
		/** the contract's signature date (ISO) */
		signed: string | null;
		/** the day the work was accepted — a completion act, else the
		 *  registry's contractual end; null when neither is on record */
		end: string | null;
		/** what `end` came from, for the printed label */
		endBasis?: 'completion' | 'contract' | null;
		/** current date (ISO) — the dashed «today» rule */
		today: string;
		/** the version chain, oldest first; [] when posted once */
		chain?: ChainAct[];
		/** live payment orders */
		payments?: PayTick[];
		/** ΑΔΑΜ whose act dot is enlarged (trail-row hover) */
		highlightRef?: string | null;
		/** act-dot hover in/out — the page highlights the trail row */
		onActHover?: (ref: string | null) => void;
	}
	let {
		signed,
		end,
		endBasis = null,
		today,
		chain = [],
		payments = [],
		highlightRef = null,
		onActHover
	}: Props = $props();

	// what each later record is, in the words the site settled on 2026-08-18
	const KIND: Record<string, string> = {
		amendment: 'revision',
		supplementary_contract: 'supplementary',
		approval_ape_supplementary: 'supplementary',
		approval_supplementary: 'supplementary',
		approval_ape: 'revised quantities',
		approval_schedule_extension: 'extension'
	};

	// Anti-nero's own programme axis: the first in-scope signature is
	// 2022-04-13 and the ΥΠΕΝ↔ΤΑΙΠΕΔ framework 07.02.2022, so the year opens it
	const T0 = new Date('2022-01-01').getTime();
	const T1 = $derived.by(() => {
		let m = new Date(today).getTime();
		for (const d of [signed, end, ...chain.map((a) => a.d), ...payments.map((p) => p.d)])
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
	const H = 76; // room for the payment ticks and the printed dates below

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

	const xs = $derived(x(signed));
	const xe = $derived(x(end));
	const todayX = $derived(x(today) ?? 4);
	const todayFlip = $derived(todayX > W - 110);
	// no acceptance on record: the bar runs to today, drawn faint and
	// uncapped, so «we do not know when it ended» never reads as «it ended»
	const xStop = $derived(xe ?? todayX);
	const open = $derived(end === null);

	/**
	 * Later records of the chain, with an x each.
	 *
	 * The registry stamps most later acts with the CONTRACT's date, not their
	 * own — 42 of the 50 chains carry two or more records on one day — so
	 * their dots would land exactly on top of each other. Overlapping dots are
	 * nudged apart by 7 units, and only the first of a stack keeps its label.
	 */
	const acts = $derived.by(() => {
		const out: { a: ChainAct; x: number; label: boolean }[] = [];
		let lastX = -99;
		let stack = 0;
		for (const a of chain.length > 1 ? chain.slice(1) : []) {
			const ax = x(a.d);
			if (ax === null) continue;
			if (Math.abs(ax - lastX) < 6) {
				stack += 1;
			} else {
				stack = 0;
				lastX = ax;
			}
			out.push({ a, x: ax + stack * 7, label: stack === 0 });
		}
		return out;
	});
	/** where a later act moved the price — the step IS the story */
	const steps = $derived.by(() => {
		const out: { ref: string; d: string; from: number; to: number }[] = [];
		for (let i = 1; i < chain.length; i++) {
			const a = chain[i];
			const b = chain[i - 1];
			if (a.d && a.eur !== null && b.eur !== null && Math.abs(a.eur - b.eur) > 0.01)
				out.push({ ref: a.ref, d: a.d, from: b.eur, to: a.eur });
		}
		return out;
	});
	const ticks = $derived(payments.filter((p) => p.d !== null));
</script>

{#if xs !== null}
	<svg viewBox="0 0 {W} {H}" class="chainbar" role="img" aria-label="Timeline of this contract">
		{#each years as yr (yr)}
			{@const gx = x(`${yr}-01-01`)}
			{#if gx}
				<text x={gx} y="10" class="axis">{yr}</text>
				<line x1={gx} y1={TOP - 2} x2={gx} y2={BASE + 4} class="grid" />
			{/if}
		{/each}

		<!-- the contract's own span -->
		<rect
			x={xs}
			y={BASE - BAR_H}
			width={Math.max(2, xStop - xs)}
			height={BAR_H}
			fill="var(--c-antinero)"
			opacity={open ? 0.28 : 0.85}
			rx="1"
		/>

		<!-- payment orders, under the baseline: the money's own rhythm -->
		{#each ticks as p (p.ref)}
			{@const px = x(p.d)}
			{#if px !== null}
				<line x1={px} y1={BASE + 2} x2={px} y2={BASE + 7} class="pay">
					<title>{dmy(p.d)} — {eurShort(p.eur ?? 0)} (net)</title>
				</line>
			{/if}
		{/each}

		<!-- every later act on the same contract -->
		{#each acts as m (m.a.ref)}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<circle
				cx={m.x}
				cy={BASE - BAR_H / 2}
				r={highlightRef !== null && m.a.ref === highlightRef ? 4.5 : 3}
				class="act"
				class:selfact={m.a.self}
				onmouseenter={() => onActHover?.(m.a.ref)}
				onmouseleave={() => onActHover?.(null)}
			>
				<title>{dmy(m.a.d)} — {KIND[m.a.kind ?? ''] ?? 'later act'} ({m.a.ref})</title>
			</circle>
			{#if m.label}
				<text x={m.x} y={BASE - BAR_H - 4} class="actlbl"
					>{KIND[m.a.kind ?? ''] ?? 'act'}</text
				>
			{/if}
		{/each}

		<!-- the price the later act set, where it changed -->
		{#each steps as s (s.ref)}
			{@const sx = x(s.d)}
			{#if sx !== null}
				<text x={sx} y={BASE - BAR_H - 16} class="step" text-anchor="middle">
					{eurShort(s.from)} → {eurShort(s.to)}
				</text>
			{/if}
		{/each}

		<!-- today rule LAST so it stays visible over the bar -->
		<line x1={todayX} y1={TOP - 2} x2={todayX} y2={BASE + 4} class="today" />
		<text
			x={todayFlip ? todayX - 4 : todayX + 4}
			y="24"
			class="today-label"
			text-anchor={todayFlip ? 'end' : 'start'}>today ({dmy(today)})</text
		>

		{#if xe !== null}
			<text x={xe + 2} y={BASE - 2} class="mark">✔</text>
		{/if}

		<text x={xs} y={BASE + 22} class="dlabel">{dmy(signed)}</text>
		{#if xe !== null && xe - xs > 90}
			<text x={xe} y={BASE + 22} class="dlabel" text-anchor={xe > W - 60 ? 'end' : 'middle'}>
				{dmy(end)}{endBasis === 'completion' ? ' accepted' : ''}
			</text>
		{:else if open && todayX - xs > 90}
			<text x={todayX - 6} y={BASE + 22} class="dlabel" text-anchor="end">no acceptance on record</text>
		{/if}
	</svg>
{/if}

<style>
	.chainbar {
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
		fill: var(--ink);
	}
	.dlabel {
		font-size: 10px;
		fill: var(--ink-soft);
	}
	.act {
		fill: var(--paper);
		stroke: var(--ink);
		stroke-width: 1.4;
		cursor: pointer;
	}
	.act.selfact {
		fill: var(--ink);
	}
	.actlbl {
		font-size: 8.5px;
		fill: var(--ink);
		text-anchor: middle;
		font-weight: 700;
		paint-order: stroke;
		stroke: var(--paper);
		stroke-width: 2.5px;
	}
	.step {
		font-size: 8.5px;
		font-weight: 700;
		fill: var(--ink);
		paint-order: stroke;
		stroke: var(--paper);
		stroke-width: 2.5px;
	}
	.pay {
		stroke: var(--ink-soft);
		stroke-width: 1;
		opacity: 0.65;
	}
</style>
