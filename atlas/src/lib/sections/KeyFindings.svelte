<script lang="ts">
	/**
	 * KEY FINDINGS — Anti-nero beside the forest co-op contracts. Until
	 * 2026-08-27 this was the /compare page; it is now a chapter of the
	 * story (user), frames, anchors and dress unchanged, the hero's four
	 * cards on the shared KpiCards.
	 */
	import { peEn } from '$lib/transforms/regions';
	import BarH from '$lib/charts/BarH.svelte';
	import CompareHist from '$lib/charts/CompareHist.svelte';
	import PairedBars from '$lib/charts/PairedBars.svelte';
	import StateFunded from '$lib/charts/StateFunded.svelte';
	import SignedTimeline from '$lib/charts/SignedTimeline.svelte';
	import ScatterLogLog from '$lib/charts/ScatterLogLog.svelte';
	import ChartFrame from '$lib/ui/ChartFrame.svelte';
	import KpiCards from '$lib/ui/KpiCards.svelte';
	import { eur, eurShort, grInt, grNumber } from '$lib/transforms/format';
	import type { ComparePayload } from '$lib/api';

	let { c }: { c: ComparePayload } = $props();

	// finding inputs — computed, never hardcoded
	const topShared = $derived.by(() => {
		let best = null as null | { pe: string; v: number };
		for (const r of c.by_pe) {
			const v = Math.min(r.antinero_eur, r.dase_eur);
			if (!best || v > best.v) best = { pe: r.pe, v };
		}
		return peEn(best?.pe) || '';
	});
	const topDase = $derived.by(() => {
		let best = null as null | { pe: string; v: number };
		for (const r of c.by_pe)
			if (!best || r.dase_eur > best.v) best = { pe: r.pe, v: r.dase_eur };
		return peEn(best?.pe) || '';
	});
	/** a year with no contracts prints «—», not «0,00 €» */
	const dash = (v: number) => (v ? eurShort(v) : '—');
	const yearRows = (vals: number[]) =>
		c.years.map((y, i) => ({ label: String(y), value: vals[i] || 0 }));
	const peakYear = (vals: number[]) => {
		let bi = 0;
		vals.forEach((v, i) => {
			if (v > vals[bi]) bi = i;
		});
		return { year: c.years[bi], eur: vals[bi] || 0 };
	};
	const cards = $derived([
		{
			num: eurShort(c.antinero.total_eur).toLowerCase(),
			label: `Anti-nero — ${grInt(c.antinero.n_contracts)} contracts, median ${eurShort(c.antinero.median_eur).toLowerCase()}`,
			color: 'var(--c-antinero)'
		},
		{
			num: eurShort(c.dase.total_eur).toLowerCase(),
			label: `forest co-ops — ${grInt(c.dase.n_contracts)} contracts, median ${eur(c.dase.median_eur)}`,
			color: 'var(--c-dase)'
		},
		{
			num: `${grNumber(c.ratio, 1)}×`,
			label: `the size of the gap, stated to stated — ≈${grInt(Math.round(c.antinero.median_eur / c.dase.median_eur))}× at the median`,
			color: '#6c6c6c'
		},
		{
			num: grInt(c.pipelines.vat_overlap.length),
			label: `companies in both datasets — ${grInt(c.pipelines.antinero.n_vats + c.pipelines.dase.n_vats)} entities, no shared ΑΦΜ`,
			color: '#6c6c6c'
		}
	]);
	/** EVERY CONTRACT BY THE DAY IT WAS SIGNED — the frame's own facts,
	 *  computed from the dots (2026-08-29): how much of each programme is
	 *  signed inside Greece's fire season (1 May – 31 October) */
	let signedShift = $state(0);
	const signed = $derived.by(() => {
		const inSeason = (d: string | null) => {
			if (!d) return false;
			const m = Number(d.slice(5, 7));
			return m >= 5 && m <= 10;
		};
		const side = (s: { d: (string | null)[]; eur: number[] }) => {
			const n = s.d.filter(Boolean).length;
			const k = s.d.filter(inSeason).length;
			const e = s.eur.reduce((t, v, i) => t + (inSeason(s.d[i]) ? v : 0), 0);
			return { n, k, share: n ? (100 * k) / n : 0, eur: e };
		};
		const a = side(c.dots.antinero);
		const d = side(c.dots.dase);
		const byYear = (s: { d: (string | null)[] }) => {
			const m = new Map<string, number>();
			for (const x of s.d) if (x) m.set(x.slice(0, 4), (m.get(x.slice(0, 4)) ?? 0) + 1);
			return [...m.entries()].sort((p, q) => q[1] - p[1])[0] ?? ['—', 0];
		};
		return { a, d, aYear: byYear(c.dots.antinero), dYear: byYear(c.dots.dase),
			fallback: c.dots.antinero.n_date_fallback + c.dots.dase.n_date_fallback };
	});
</script>

<div class="cmpp">
	<section class="hero">
		<div class="cards"><KpiCards {cards} /></div>
		<div class="about">
			<p>
				The Anti-nero programme pays construction and technical companies. Forest labour
				co-operatives (ΔΑΣΕ) do woodland work for a living. The two flows run through the same
				ministry, into the same regions — and never touch. This chapter sets them side by side.
			</p>
			<p class="basis">
				Both sides are stated contract values excl. VAT (the co-op side deduplicated across
				amendment versions); payments are a separate layer on each dataset's own page. Anti-nero
				is one programme; the co-op dataset is every public contract won by a forest co-operative
				anywhere in the state since September 2021 —
				<a href="/methodology#stated-basis">basis</a>.
			</p>
		</div>
	</section>

	<ChartFrame
		title="STATE-FUNDED, TWO WORLDS"
		insight={`Zero shared companies: ${grInt(c.pipelines.antinero.n_vats)} Anti-nero contractors and ${grInt(c.pipelines.dase.n_vats)} co-op-side entities (${grInt(c.pipelines.dase_n_coops)} of them curated co-operatives), and not one ΑΦΜ appears on both sides.`}
		caveat="The € scale carries a radius floor: the smallest contracts print larger than true scale, or they would vanish beside the €11M dots."
		anchor="pipelines"
		methodology={null}
	>
		<StateFunded
			dots={c.dots}
			nCompanies={c.pipelines.antinero.n_vats}
			nCoops={c.pipelines.dase.n_vats}
		/>
	</ChartFrame>

	<ChartFrame
		title="EVERY CONTRACT, BY THE DAY IT WAS SIGNED"
		insight={`Two rhythms on one calendar: ${grInt(signed.a.k)} of the ${grInt(signed.a.n)} Anti-nero contracts (${grNumber(signed.a.share, 0)}%, ${eurShort(signed.a.eur)}) were signed inside the fire season, against ${grNumber(signed.d.share, 0)}% of the co-operatives' ${grInt(signed.d.n)}; the programme's busiest year was ${signed.aYear[0]} with ${grInt(signed.aYear[1])} signatures, the co-ops' ${signed.dYear[0]} with ${grInt(signed.dYear[1])}.`}
		caveat={`One dot per contract at its signature date as recorded in ΚΗΜΔΗΣ — the colour is the programme, the Anti-nero dot drawn a little larger; the shaded bands are the fire season, 1 May – 31 October. The dots stack in columns of one week and never leave the frame, so in the busiest weeks a dot sits up to ${grInt(signedShift)} days from its date.${signed.fallback ? ` ${grInt(signed.fallback)} record${signed.fallback === 1 ? '' : 's'} state no signature date and sit at their registry posting date.` : ''}`}
		anchor="signed-timeline"
		methodology="stated-basis"
	>
		<SignedTimeline dots={c.dots} bind:maxShiftDays={signedShift} />
	</ChartFrame>

	<ChartFrame
		title="CONTRACT SIZES"
		insight={`Different universes: the median Anti-nero contract is ${eurShort(c.hist.antinero_median)}, the median co-op contract ${eur(c.hist.dase_median)} — the two distributions barely overlap.`}
		caveat="Contract-size distribution on shared log₂ brackets, each programme as % of its own contracts; both on stated values excl. VAT."
		anchor="distributions"
		methodology="stated-basis"
	>
		<CompareHist hist={c.hist} />
	</ChartFrame>

	<ChartFrame
		title="WHERE BOTH FLOWS LAND"
		insight={`${topShared} gets millions from each programme; ${topDase} is co-op country. Each regional unit sits by its € from both programmes, log–log; the coloured gutters hold the units that see only one of them.`}
		caveat="Anti-nero regions curated per contract from its signed text, the co-op side derived from the awarding forest unit; a contract covering several units or signed by several firms is split equally."
		anchor="pe-scatter"
		methodology="even-split"
	>
		<ScatterLogLog rows={c.by_pe} />
	</ChartFrame>

	<ChartFrame
		title="REGION BY REGION"
		insight={`The programmes weight the regions differently — the top ${grInt(Math.min(15, c.by_pe.length))} regional units, each programme's own share of its total beside the other's, absolute € printed.`}
		caveat={`The co-op side omits ${grInt(c.dase_unresolved.n)} multi-unit contracts (${eurShort(c.dase_unresolved.eur)}), honestly unresolved.`}
		anchor="pe-paired"
		methodology="dase-regions"
	>
		<PairedBars rows={c.by_pe} antineroTotal={c.antinero.total_eur} daseTotal={c.dase.total_eur} />
	</ChartFrame>

	<ChartFrame
		title="MONEY PER YEAR"
		insight={`Anti-nero ramps up while the co-op money drifts down: Anti-nero peaked in ${peakYear(c.yearly.antinero).year} (${eurShort(peakYear(c.yearly.antinero).eur)}), the co-ops in ${peakYear(c.yearly.dase).year} (${eurShort(peakYear(c.yearly.dase).eur)}). Each programme on its own scale — a shared axis would erase the co-op bars entirely.`}
		caveat="Stated € excl. VAT by signature year, each side on its own scale."
		anchor="yearly"
		methodology="stated-basis"
	>
		<div class="years">
			<div>
				<div class="sublabel antinero">ANTI-NERO</div>
				<BarH
					rows={yearRows(c.yearly.antinero)}
					color="var(--c-antinero)"
					inside
					barHeight={35}
					fmt={dash}
				/>
			</div>
			<div>
				<div class="sublabel dase">FOREST CO-OPS</div>
				<BarH rows={yearRows(c.yearly.dase)} color="var(--c-dase)" inside barHeight={35} fmt={dash} />
			</div>
		</div>
	</ChartFrame>
</div>

<style>
	/* the frame titles and bulbs in the dataset pages' dress; no dataset
	   hue here, so they wear the ink */
	.cmpp {
		--frame-accent: var(--ink);
	}
	.cmpp :global(.frame .finding) {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		line-height: 1.3;
		color: var(--ink);
	}
	.hero {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: var(--sp-6) var(--sp-12);
		margin: var(--sp-6) 0 var(--sp-12);
	}
	.cards {
		width: 552px;
		max-width: 100%;
	}
	/* the four cards as two by two, the old hero's geometry */
	.cards :global(.cards) {
		grid-auto-flow: row;
		grid-template-columns: 1fr 1fr;
	}
	.about p {
		margin: 0;
		max-width: var(--prose-w);
	}
	.about p.basis {
		margin-top: var(--sp-3);
		font-size: var(--fs-13);
		color: var(--ink-soft);
		line-height: 1.5;
	}
	.about p.basis a {
		color: var(--ink-soft);
	}
	.years {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--sp-8);
	}
	.sublabel {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		margin-bottom: var(--sp-2);
	}
	.sublabel.antinero {
		color: var(--c-antinero);
	}
	.sublabel.dase {
		color: var(--c-dase);
	}
	@media (max-width: 900px) {
		.hero,
		.years {
			grid-template-columns: 1fr;
		}
	}
</style>
