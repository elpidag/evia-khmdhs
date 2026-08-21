<script lang="ts">
	/**
	 * One Anti-nero contract's life on the programme axis: the bar from
	 * signature to the day it was accepted, a dot for every later act on the
	 * same contract (τροποποίηση όρων, παράταση προθεσμίας, έγκριση
	 * συμπληρωματικών εργασιών), a tick for every payment order, and the ✔ of
	 * its completion act.
	 *
	 * Before the bar, the procurement that produced it: the primary request,
 * the commitment approval, the call and the award, wherever the document
 * trail has them dated (217 of 246 in-scope contracts have at least one;
 * 6 more carry an act the registry never dated).
 * They sit on a dotted run-up to the signature, because they are acts of the
 * procurement, not of the contract — which did not exist yet.
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
	import AreaLanes from './AreaLanes.svelte';
	import type { Lane, LaneStepLike } from '$lib/transforms/lanes';

	export interface ChainAct {
		ref: string;
		/** ISO date, already normalised */
		d: string | null;
		/** document_kind — what this record IS */
		kind: string | null;
		eur: number | null;
		self?: boolean;
	}
	/** what the call that produced this contract also produced — the one
	 *  fact from the procurement diagram that belongs on a time axis */
	export interface CallInfo {
		/** the call's ΑΔΑΜ, matched against the run-up act */
		ref: string;
		/** how many contracts answered it, this one included */
		lots: number;
		/** their Σ stated net € */
		total: number;
	}
	/** an act of the procurement that PRECEDES the contract */
	export interface RunUpAct {
		ref: string;
		/** ISO date, already normalised */
		d: string | null;
		kind: 'request' | 'approved_request' | 'notice' | 'auction';
	}
	export interface PayTick {
		ref: string;
		/** ISO date, already normalised */
		d: string | null;
		eur: number | null;
	}
	/** a later act that moved the announced deadline */
	export interface ExtStep {
		ref: string;
		/** what the act IS — an extension of the deadline, or a supplementary
		 *  approval that carried a later end date with it */
		kind?: string | null;
		/** the act's own date (ISO) — where its dot sits */
		d: string | null;
		/** the new deadline it set (ISO) */
		deadline: string | null;
		/** 1-based, chronological */
		n: number;
		/** 'khmdhs' (a ΣΥΜΒ record) or 'diavgeia' (an extension approval act) */
		source?: string | null;
		/** the act granted different dates per area; the step carries the latest */
		per_area?: boolean;
		/** whether this step moved the deadline in force forward */
		later?: boolean;
		/** what the act extends: 'study' | 'stage' | 'area' | 'whole' | null */
		scope?: string | null;
	}
	interface Props {
		/** the contract's signature date (ISO) */
		signed: string | null;
		/** the ΑΔΑΜ the BAR stands for — the σύμβαση itself, so its trail row
		 *  has a mark to light like every other row does */
		signedRef?: string | null;
		/** the day the works were accepted (completion act), ISO or null */
		end: string | null;
		/** the ΑΔΑ of that acceptance act — pairs the ✔ with its trail row */
		endRef?: string | null;
		/** the deadline the contract announced (ISO), null when it announced
		 *  none — 155 of 246 in-scope contracts */
		deadline?: string | null;
		/** where that deadline came from: the contract's own sentence, its
		 *  fire season, or — only when no reading exists — the registry's
		 *  end date, stated duration, or a later act of the chain */
		deadlineBasis?:
			| 'document'
			| 'document_season'
			| 'end_date'
			| 'duration'
			| 'act'
			| null;
		/** deadline extensions that belong on the CONTRACT bar, oldest first —
		 *  with lanes, the area-scoped ones move to their lanes */
		extensions?: ExtStep[];
		/** one strip per forest service where the acts name areas (user,
		 *  2026-08-21) — built by `transforms/lanes.buildLanes`; the bar's
		 *  grey part is split into them instead of being drawn once */
		lanes?: Lane<LaneStepLike>[];
		/** current date (ISO) — the dashed «today» rule */
		today: string;
		/** the version chain, oldest first; [] when posted once */
		chain?: ChainAct[];
		/** live payment orders */
		payments?: PayTick[];
		/** the procurement's own acts, before the signature */
		runUp?: RunUpAct[];
		/** the call's other lots — badges the call mark and makes it clickable */
		callInfo?: CallInfo | null;
		/** clicking the call mark (the page swaps the header to the diagram) */
		onCallClick?: () => void;
		/** ΑΔΑΜ whose act dot is enlarged (trail-row hover) */
		highlightRef?: string | null;
		/** act-dot hover in/out — the page highlights the trail row */
		onActHover?: (ref: string | null) => void;
	}
	let {
		signed,
		signedRef = null,
		end,
		endRef = null,
		deadline = null,
		deadlineBasis = null,
		extensions = [],
		lanes = [],
		today,
		chain = [],
		payments = [],
		runUp = [],
		callInfo = null,
		onCallClick,
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

	// the extension fill the sponsor Gantt uses for a running project's
	// extended stretch — the same convention, so the two read alike
	// the extension is the SAME ink as the bar, thinned (user, 2026-08-19) —
	// the sponsor pages' green said «other dataset» on an Anti-nero page
	const EXT_FILL = 'var(--c-antinero)';
	const EXT_OPACITY = 0.3;
	const ORDINAL = (n: number): string =>
		n === 1 ? '1st' : n === 2 ? '2nd' : n === 3 ? '3rd' : `${n}th`;

	// the same four words the document trail prints, shortened to fit
	const RUNUP: Record<string, string> = {
		request: 'request',
		approved_request: 'approval',
		notice: 'call',
		auction: 'award'
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
	const BAR_TOP = 34; // the bar's upper edge, fixed under the year band
	// the per-area strips: the bar's grey (extended) part split into one
	// strip per forest service, stacked from the bar's top — and the solid
	// bar is as tall as all the strips together (user, 2026-08-21)
	const STRIP_H = $derived(lanes.length ? Math.max(7, 12 / lanes.length) : 12);
	const BAR_H = $derived(lanes.length ? lanes.length * STRIP_H : 12);
	const BASE = $derived(BAR_TOP + BAR_H); // bar baseline
	// the extension arcs and their ordinal row sit under the bar
	const arcY = $derived(BASE);
	const H = $derived(arcY + 20); // year band, the bar line, the arcs and their label row
	const gridBottom = $derived(arcY + 4);

	// with per-area strips the axis stops short of the right edge, so a
	// service's name always has room at the end of its own grey bar — a name
	// above the bar collided with the € row, a name inside it sat on the grey
	// (user, 2026-08-21)
	const NAME_PAD = $derived(lanes.length ? 96 : 0);
	function x(d: string | null): number | null {
		if (!d) return null;
		const t = new Date(d).getTime();
		if (Number.isNaN(t)) return null;
		return 4 + ((W - 12 - NAME_PAD) * (t - T0)) / (T1 - T0);
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
	const xe = $derived(x(end));               // acceptance ✔, not a bar edge
	const xd = $derived(x(deadline));          // the announced deadline
	// the last deadline in force, after every extension
	// the latest date any step granted — a per-area act may come AFTER one
	// that already granted a later date for another area
	const lastDeadline = $derived(
		extensions.reduce<string | null>(
			(m, e) => (e.deadline && (!m || e.deadline > m) ? e.deadline : m),
			deadline
		)
	);
	const xdLast = $derived(x(lastDeadline));
	// the extension labels print the ordinal only («1st», «2nd»…, the word
	// is the legend's), and a label closer than 14 units to the previous
	// printed one is dropped — the arc and its hover title stay (user, 2026-08-21)
	const extLabels = $derived.by(() => {
		let last = -Infinity;
		return extensions.map((e) => {
			const ex = x(e.d);
			const label = ex !== null && ex - last >= 14;
			if (label) last = ex as number;
			return { ...e, label };
		});
	});
	const todayX = $derived(x(today) ?? 4);
	const todayFlip = $derived(todayX > W - 110);
	// nothing was announced: the Gantt's stub, never an invented span
	const stub = $derived(xd === null || xs === null || xd <= xs);

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
		let lastLabel = -99;
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
			// «supplementary» is 60 units wide at 8.5px: two acts a fortnight
			// apart printed both labels on top of each other
			const label = stack === 0 && ax - lastLabel >= 62;
			if (label) lastLabel = ax;
			out.push({ a, x: ax + stack * 7, label });
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
	/**
	 * Payment marks, nudged clear of each other and of the act dots they share
	 * the line with — a € printed under a dot reads as neither.
	 */
	/** Where the bar's ink is: a mark inside it must print white to be seen,
	 *  and a mark outside it must print dark for the same reason. */
	const barSpan = $derived.by(() => {
		if (xs === null) return null;
		// only the SOLID stretch: the extension is the same ink thinned to
		// 30%, and white on that is nearly invisible — a dark mark reads
		const end = stub ? xs + 7 : (xd ?? xs);
		return [xs, Math.max(end, xs)] as [number, number];
	});
	const onBar = (v: number): boolean =>
		barSpan !== null && v >= barSpan[0] - 0.5 && v <= barSpan[1] + 0.5;

	/** the bar stands for the σύμβαση, so it lights when that row is hovered */
	const barHot = $derived(highlightRef !== null && signedRef === highlightRef);

	const ticks = $derived.by(() => {
		const taken = [...acts.map((m) => m.x), ...pre.map((m) => m.x)];
		const out: { p: PayTick; x: number }[] = [];
		for (const p of payments) {
			let px = x(p.d);
			if (px === null) continue;
			for (let guard = 0; guard < 12; guard++) {
				const clash = [...taken, ...out.map((o) => o.x)].some((t) => Math.abs(t - px!) < 5.5);
				if (!clash) break;
				px += 6;
			}
			out.push({ p, x: px });
		}
		return out;
	});

	/**
	 * The procurement's acts, oldest first, placed on the run-up.
	 *
	 * A request and its commitment approval are routinely posted the same
	 * day, so the marks nudge apart like the act dots do, and a label is
	 * printed only where it would not overprint the previous one — the
	 * hover card and the trail row below carry the rest.
	 */
	const pre = $derived.by(() => {
		const out: { a: RunUpAct; x: number; label: boolean }[] = [];
		const dated = runUp
			.filter((a) => a.d !== null)
			.slice()
			.sort((a, b) => (a.d ?? '').localeCompare(b.d ?? ''));
		let lastX = -99;
		for (const a of dated) {
			let ax = x(a.d);
			if (ax === null) continue;
			if (ax - lastX < 5) ax = lastX + 6;
			lastX = ax;
			out.push({ a, x: ax, label: false });
		}
		// Which labels get printed: a request and its call are days apart on a
		// four-year axis, and both printed «rcall·1 of 5» over each other. The
		// call label claims its box FIRST — it is the one that says something —
		// and the rest are taken in time order only where they still fit.
		const boxes: [number, number][] = [];
		const width = (m: (typeof out)[number]) =>
			((RUNUP[m.a.kind] ?? '').length + (m.a.ref === callInfo?.ref ? 9 : 0)) * 4.6;
		const claim = (m: (typeof out)[number]) => {
			const w = width(m);
			const box: [number, number] = [m.x - w / 2 - 3, m.x + w / 2 + 3];
			if (boxes.some(([l, r]) => box[0] < r && l < box[1])) return;
			boxes.push(box);
			m.label = true;
		};
		const call = out.find((m) => callInfo !== null && m.a.ref === callInfo.ref);
		if (call) claim(call);
		for (const m of out) if (m !== call) claim(m);
		return out;
	});
	const preStart = $derived(pre.length ? pre[0].x : null);
</script>

{#if xs !== null}
	<svg viewBox="0 0 {W} {H}" class="chainbar" role="img" aria-label="Timeline of this contract">
		{#each years as yr (yr)}
			{@const gx = x(`${yr}-01-01`)}
			{#if gx}
				<text x={gx} y="10" class="axis">{yr}</text>
				<line x1={gx} y1={TOP - 2} x2={gx} y2={gridBottom} class="grid" />
			{/if}
		{/each}

		<!-- the procurement that produced the contract -->
		{#if preStart !== null && xs !== null}
			<line x1={preStart} y1={BASE - BAR_H / 2} x2={xs} y2={BASE - BAR_H / 2} class="runup" />
		{/if}
		{#each pre as m (m.a.ref)}
			{@const isCall = callInfo !== null && m.a.ref === callInfo.ref}
			<!-- the call mark is a SHORTCUT to the header's DIAGRAM button, which
			     is a real <button> and carries the keyboard route -->
			<!-- svelte-ignore a11y_no_static_element_interactions, a11y_click_events_have_key_events -->
			<circle
				cx={m.x}
				cy={BASE - BAR_H / 2}
				r={(highlightRef !== null && m.a.ref === highlightRef) || isCall ? 4.5 : 3}
				class="pre"
				class:hot={highlightRef !== null && m.a.ref === highlightRef}
				class:callmark={isCall}
				onmouseenter={() => onActHover?.(m.a.ref)}
				onmouseleave={() => onActHover?.(null)}
				onclick={isCall ? () => onCallClick?.() : undefined}
			>
				<title
					>{dmy(m.a.d)} — {RUNUP[m.a.kind] ?? 'act'} ({m.a.ref}){isCall
						? ` · ${callInfo!.lots} contracts under this call, ${eurShort(callInfo!.total)} in total — click for the diagram`
						: ''}</title
				>
			</circle>
			{#if m.label}
				<!-- svelte-ignore a11y_no_static_element_interactions, a11y_click_events_have_key_events -->
				<text
					x={m.x}
					y={BASE - BAR_H - 4}
					class="actlbl runlbl"
					class:calllbl={isCall}
					onclick={isCall ? () => onCallClick?.() : undefined}
					>{RUNUP[m.a.kind]}{isCall ? ` · 1 of ${callInfo!.lots}` : ''}</text
				>
			{/if}
		{/each}

		<!-- what the contract promised: signature → announced deadline -->
		{#if stub}
			<rect
				x={xs}
				y={BASE - BAR_H}
				width="7"
				height={BAR_H}
				fill="var(--c-antinero)"
				opacity={barHot ? 1 : 0.85}
				class:barhot={barHot}
			>
				<title>{dmy(signed)} — no deadline announced in the registry record</title>
			</rect>
		{:else}
			<rect
				x={xs}
				y={BASE - BAR_H}
				width={(xd ?? 0) - xs}
				height={BAR_H}
				fill="var(--c-antinero)"
				opacity={barHot ? 1 : 0.85}
				class:barhot={barHot}
			>
				<title
					>{dmy(signed)} → {dmy(deadline)} — the deadline the contract announced{deadlineBasis ===
					'duration'
						? ' (ΚΗΜΔΗΣ duration)'
						: deadlineBasis === 'document'
							? ' (as the contract states it)'
							: deadlineBasis === 'document_season'
								? ' (the fire season, 1 May – 31 October)'
								: deadlineBasis === 'act'
							? ' (announced by a later act; the σύμβαση announced none)'
							: ''}</title
				>
			</rect>
		{/if}
		<!-- every extension, in the sponsor pages' lighter fill -->
		{#if xd !== null && xdLast !== null && xdLast > xd}
			<rect
				x={xd}
				y={BASE - BAR_H}
				width={xdLast - xd}
				height={BAR_H}
				fill={EXT_FILL}
				opacity={EXT_OPACITY}
				rx="1"
			/>
		{/if}
		{#if xd !== null && !stub}
			<line x1={xd} y1={BASE - BAR_H - 4} x2={xd} y2={BASE + 2} class="dline" />
		{/if}

		<!-- payment orders, on the same line as the rest: the money's rhythm -->
		{#each ticks as t (t.p.ref)}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<!-- with per-area strips the bar is tall and striped: the € marks
			     move up to the label line, where «call» is written (user, 2026-08-21) -->
			<text
				x={t.x}
				y={lanes.length ? BAR_TOP - 4 : BASE - BAR_H / 2 + 3.5}
				class="pay"
				class:onbar={!lanes.length && onBar(t.x)}
				class:hot={highlightRef !== null && t.p.ref === highlightRef}
				text-anchor="middle"
				onmouseenter={() => onActHover?.(t.p.ref)}
				onmouseleave={() => onActHover?.(null)}
			>
				€<title>{dmy(t.p.d)} — {eurShort(t.p.eur ?? 0)}</title>
			</text>
		{/each}

		<!-- every later act on the same contract -->
		{#each acts as m (m.a.ref)}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<circle
				cx={m.x}
				cy={BASE - BAR_H / 2}
				r={highlightRef !== null && m.a.ref === highlightRef ? 4.5 : 3}
				class="act"
				class:onbar={onBar(m.x)}
				class:hot={highlightRef !== null && m.a.ref === highlightRef}
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

		<!-- deadline extensions: the act's dot, an arrow dipping under the bar
		     to the NEW deadline it set — the promised-vs-executed record -->
		<defs>
			<marker
				id="chainextarrow"
				viewBox="0 0 6 6"
				refX="5"
				refY="3"
				markerWidth="6"
				markerHeight="6"
				orient="auto-start-reverse"
			>
				<path d="M0,0 L6,3 L0,6 Z" class="extarrowfill" />
			</marker>
		</defs>
		{#each extLabels as e (e.n)}
			{@const ex = x(e.d)}
			{@const en = x(e.deadline)}
			{#if ex !== null}
				{#if en !== null && Math.abs(en - ex) > 8}
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<path
						d={`M ${ex} ${arcY + 1} Q ${(ex + en) / 2} ${arcY + 12}, ${en} ${arcY + 2}`}
						class="extarrow"
						class:hot={highlightRef !== null && e.ref === highlightRef}
						marker-end="url(#chainextarrow)"
						onmouseenter={() => onActHover?.(e.ref)}
						onmouseleave={() => onActHover?.(null)}
					>
						<title
							>{ORDINAL(e.n)} {e.kind === 'approval_schedule_extension' || e.kind === 'extension_act'
								? 'extension'
								: e.kind === 'extension_partial_act'
									? 'partial extension'
									: 'new deadline'}{e.per_area ? ' (per area — latest date shown)' : ''} — {e.source === 'diavgeia' ? 'approved' : 'signed'} {dmy(e.d)} · deadline {e.later ? 'moved to' : 'set at'} {dmy(e.deadline)}</title
						>
					</path>
				{/if}
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<text
					x={ex}
					y={arcY + 18}
					class="actlbl extlbl"
					class:hot={highlightRef !== null && e.ref === highlightRef}
					text-anchor="middle"
					onmouseenter={() => onActHover?.(e.ref)}
					onmouseleave={() => onActHover?.(null)}
					>{e.label ? (e.scope === 'study' ? 'studies' : ORDINAL(e.n)) : ''}</text
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

		<!-- the per-area strips: the grey part split by forest service, where
		     the acts name areas (user, 2026-08-21) -->
		{#if lanes.length}
			<AreaLanes {lanes} {x} {xs} {xd} top={BAR_TOP} stripH={STRIP_H} w={W} {highlightRef} {onActHover} />
		{/if}

		<!-- today rule LAST so it stays visible over the bar; its lettering
		     sits on the year line, where the axis is read (user, 2026-08-19) -->
		<line x1={todayX} y1={TOP - 2} x2={todayX} y2={gridBottom} class="today" />
		<text
			x={todayFlip ? todayX - 4 : todayX + 4}
			y="10"
			class="today-label"
			text-anchor={todayFlip ? 'end' : 'start'}>today</text
		>

		{#if xe !== null}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<text
				x={xe}
				y={BASE - 2}
				class="mark"
				class:hot={highlightRef !== null && endRef === highlightRef}
				text-anchor="middle"
				onmouseenter={() => onActHover?.(endRef ?? null)}
				onmouseleave={() => onActHover?.(null)}
			>
				✔<title>{dmy(end)} — works accepted</title>
			</text>
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
	/* symbols carry NO outline — no halo on ✔ or €, no stroke on a dot, no
	   outline on the bar (user, 2026-08-21) */
	.mark {
		font-size: 11px;
		font-weight: 900;
		fill: var(--ink);
		stroke: none;
	}
	/* a dot ON the bar prints white with no outline; off the bar it prints
	   in ink, or it would be a white dot on white paper (user, 2026-08-19) */
	.act {
		fill: var(--ink);
		stroke: none;
		cursor: pointer;
	}
	.act.onbar,
	.act.selfact.onbar {
		fill: #fff;
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
	.runup {
		stroke: var(--ink-faint);
		stroke-width: 1;
		stroke-dasharray: 2 3;
	}
	.pre {
		fill: #9b9b9b;
		stroke: none;
		cursor: pointer;
	}
	.runlbl {
		fill: var(--ink-soft);
		font-weight: 600;
	}
	/* the call is the one run-up act that leads somewhere: to the other lots
	   it produced, which the header's diagram draws (user, 2026-08-19) */
	.pre.callmark {
		fill: var(--ink);
		cursor: pointer;
	}
	/* no underline: the halo behind these labels turns one into a strike
	   through the words — the filled mark is the affordance */
	.calllbl {
		fill: var(--ink);
		cursor: pointer;
		font-weight: 700;
	}
	.calllbl:hover {
		fill: var(--c-antinero);
	}
	.pay,
	.mark,
	.extlbl,
	.extarrow {
		cursor: pointer;
	}
	.pay.hot,
	.mark.hot {
		font-size: 12px;
		fill: var(--c-antinero);
	}
	.extlbl.hot {
		fill: var(--c-antinero);
	}
	.extarrow.hot {
		stroke: var(--c-antinero);
		stroke-width: 1.6;
	}
	.act.hot,
	.pre.hot {
		fill: var(--c-antinero);
	}
	.pay {
		font-size: 9px;
		font-weight: 700;
		fill: var(--ink);
		stroke: none;
	}
	.pay.onbar {
		fill: #fff;
		stroke: none;
	}
	.barhot {
		stroke: none;
	}
	.dline {
		stroke: var(--c-antinero);
		stroke-width: 1.3;
	}
	.extarrow {
		fill: none;
		stroke: var(--ink-soft);
		stroke-width: 1;
	}
	.extarrowfill {
		fill: var(--ink-soft);
	}
	.extlbl {
		fill: var(--ink-soft);
	}
</style>
