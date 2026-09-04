<script lang="ts">
	/**
	 * KEY FINDINGS — Anti-nero beside the forest co-op contracts. Until
	 * 2026-08-27 this was the /compare page, then the story's full-width
	 * coda; since 2026-09-02 (the author) it renders ONE item at a time in
	 * the story's FIGURE COLUMN, at that column's width, advancing with the
	 * paragraphs of KEY FINDINGS AND OPEN QUESTIONS — `i` picks the item.
	 * The old hero text and the WHERE BOTH FLOWS LAND scatter were removed
	 * the same day (the author); the four KPI cards ride with the first item.
	 */
	import BarH from '$lib/charts/BarH.svelte';
	import CompareHist from '$lib/charts/CompareHist.svelte';
	import PairedBars from '$lib/charts/PairedBars.svelte';
		import SignedTimeline from '$lib/charts/SignedTimeline.svelte';
	import KpiCards from '$lib/ui/KpiCards.svelte';
	import { eur, eurShort, grInt, grNumber } from '$lib/transforms/format';
	import type { ComparePayload } from '$lib/api';

	let { c, i = 0 }: { c: ComparePayload; i?: number } = $props();

	/** a year with no contracts prints «—», not «0,00 €» */
	const dash = (v: number) => (v ? eurShort(v) : '—');
	const yearRows = (vals: number[]) =>
		c.years.map((y, idx) => ({ label: String(y), value: vals[idx] || 0 }));
	const peakYear = (vals: number[]) => {
		let bi = 0;
		vals.forEach((v, idx) => {
			if (v > vals[bi]) bi = idx;
		});
		return { year: c.years[bi], eur: vals[bi] || 0 };
	};
	/** the KPI cards as the author set them (2026-09-04): TWO COLUMNS — the
	 *  Anti-nero programme and the forest workers' co-operatives — each with
	 *  its stated money and its number of contracts */
	const A = 'var(--c-antinero)';
	const D = 'var(--c-dase)';
	/** by ROW, so the two columns' rectangles align whatever their headers'
	 *  line count: the money row, then the contracts row */
	const kpiMoney = $derived([
		{ num: eurShort(c.antinero.total_eur).toLowerCase(), label: 'stated value, excl. VAT', color: A },
		{ num: eurShort(c.dase.total_eur).toLowerCase(), label: 'stated value, excl. VAT', color: D }
	]);
	const kpiCount = $derived([
		{ num: grInt(c.antinero.n_contracts), label: 'contracts', color: A },
		{ num: grInt(c.dase.n_contracts), label: 'contracts', color: D }
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
			const e = s.eur.reduce((t, v, idx) => t + (inSeason(s.d[idx]) ? v : 0), 0);
			return { n, k, share: n ? (100 * k) / n : 0, eur: e };
		};
		const a = side(c.dots.antinero);
		const d = side(c.dots.dase);
		const byYear = (s: { d: (string | null)[] }) => {
			const m = new Map<string, number>();
			for (const x of s.d) if (x) m.set(x.slice(0, 4), (m.get(x.slice(0, 4)) ?? 0) + 1);
			return [...m.entries()].sort((p, q) => q[1] - p[1])[0] ?? ['—', 0];
		};
		return {
			a,
			d,
			aYear: byYear(c.dots.antinero),
			dYear: byYear(c.dots.dase),
			fallback: c.dots.antinero.n_date_fallback + c.dots.dase.n_date_fallback
		};
	});
</script>

<div class="cmpp">
	{#if i <= 0}
		<!-- the STATE-FUNDED chart left this card for the full-width band in
		     the narrative (ChartBand.svelte, the author, 2026-09-04) -->
		<div class="item" id="pipelines">
			<!-- headers on one row (bottom-aligned, so a two-line name never
			     pushes its column's cards down), then the cards ROW by ROW —
			     a little below the section title, a little smaller (the author,
			     2026-09-04) -->
			<div class="kgrid">
				<div class="kheads">
					<h3 class="tt">ANTI-NERO PROGRAMME</h3>
					<h3 class="tt">FOREST WORKERS' CO-OPERATIVES</h3>
				</div>
				<KpiCards cards={kpiMoney} />
				<KpiCards cards={kpiCount} />
			</div>
		</div>
	{:else if i === 1}
		<div class="item" id="signed-timeline">
			<h3 class="tt">EVERY CONTRACT, BY THE DAY IT WAS SIGNED</h3>
			<SignedTimeline dots={c.dots} bind:maxShiftDays={signedShift} />
			<p class="note">
				Two rhythms on one calendar: {grInt(signed.a.k)} of the {grInt(signed.a.n)} Anti-nero
				contracts ({grNumber(signed.a.share, 0)}%, {eurShort(signed.a.eur)}) were signed inside the
				fire season, against {grNumber(signed.d.share, 0)}% of the co-operatives' {grInt(
					signed.d.n
				)}; the programme's busiest year was {signed.aYear[0]} with {grInt(signed.aYear[1])}
				signatures, the co-ops' {signed.dYear[0]} with {grInt(signed.dYear[1])}.
			</p>
			<p class="caveat">
				One dot per contract at its ΚΗΜΔΗΣ signature date; the shaded bands are the fire season,
				1 May – 31 October. Dots stack in week columns, up to {grInt(signedShift)} days from their
				date in the busiest weeks.
			</p>
		</div>
	{:else if i === 2}
		<div class="item" id="distributions">
			<h3 class="tt">CONTRACT SIZES</h3>
			<CompareHist hist={c.hist} />
			<p class="note">
				Different universes: the median Anti-nero contract is {eurShort(c.hist.antinero_median)},
				the median co-op contract {eur(c.hist.dase_median)} — the two distributions barely overlap.
			</p>
			<p class="caveat">
				Shared log₂ brackets, each programme as % of its own contracts; stated values excl. VAT.
			</p>
		</div>
	{:else if i === 3}
		<div class="item" id="pe-paired">
			<h3 class="tt">REGION BY REGION</h3>
			<PairedBars rows={c.by_pe} antineroTotal={c.antinero.total_eur} daseTotal={c.dase.total_eur} />
			<p class="note">
				The programmes weight the regions differently — the top {grInt(
					Math.min(15, c.by_pe.length)
				)} regional units, each programme's own share of its total beside the other's.
			</p>
			<p class="caveat">
				The co-op side omits {grInt(c.dase_unresolved.n)} multi-unit contracts ({eurShort(
					c.dase_unresolved.eur
				)}), honestly unresolved.
			</p>
		</div>
	{:else}
		<div class="item" id="yearly">
			<h3 class="tt">MONEY PER YEAR</h3>
			<div class="years">
				<div>
					<div class="sublabel antinero">ANTI-NERO</div>
					<BarH
						rows={yearRows(c.yearly.antinero)}
						color="var(--c-antinero)"
						inside
						barHeight={26}
						fmt={dash}
					/>
				</div>
				<div>
					<div class="sublabel dase">FOREST CO-OPS</div>
					<BarH
						rows={yearRows(c.yearly.dase)}
						color="var(--c-dase)"
						inside
						barHeight={26}
						fmt={dash}
					/>
				</div>
			</div>
			<p class="note">
				Anti-nero ramps up while the co-op money drifts down: Anti-nero peaked in {peakYear(
					c.yearly.antinero
				).year} ({eurShort(peakYear(c.yearly.antinero).eur)}), the co-ops in {peakYear(
					c.yearly.dase
				).year} ({eurShort(peakYear(c.yearly.dase).eur)}). Each side on its own scale.
			</p>
		</div>
	{/if}
</div>

<style>
	.cmpp {
		--frame-accent: var(--ink);
		width: 100%;
	}
	.item {
		display: flex;
		flex-direction: column;
		gap: var(--sp-3);
	}
	.kgrid {
		display: flex;
		flex-direction: column;
		gap: var(--sp-3);
		/* below the docked section title's line, not level with it */
		margin-top: 44px;
	}
	.kheads {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--sp-4);
		align-items: end;
	}
	/* the rectangles a little smaller than the site's KPI cards */
	.kgrid :global(.card) {
		min-height: 5.75rem;
		padding: var(--sp-3) var(--sp-4);
		gap: var(--sp-3);
	}
	.kgrid :global(.num) {
		font-size: var(--fs-34);
	}
	.tt {
		margin: 0;
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-13);
		letter-spacing: 0.08em;
		line-height: 1.3;
		color: var(--ink);
		text-transform: uppercase;
	}
	.note {
		margin: 0;
		font-size: var(--fs-12);
		line-height: 1.4;
		color: var(--ink-soft);
	}
	.caveat {
		margin: 0;
		font-size: 11px;
		line-height: 1.35;
		color: var(--ink-faint);
	}
	.years {
		display: flex;
		flex-direction: column;
		gap: var(--sp-4);
	}
	.sublabel {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-13);
		letter-spacing: 0.08em;
		margin-bottom: var(--sp-1);
	}
	.sublabel.antinero {
		color: var(--c-antinero);
	}
	.sublabel.dase {
		color: var(--c-dase);
	}
</style>
