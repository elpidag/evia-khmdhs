<script lang="ts">
	/**
	 * The ΔΑΣΕ contract page on the Anti-nero skeleton (user, DATA_DECISIONS
	 * 2026-08-23): the facts list where the data exists, the map with the
	 * procurement DIAGRAM behind a switch, the TIMELINE (signature, run-up
	 * acts and € payment marks — NO deadline bar), the DOCUMENT TRAIL with
	 * the payment orders in it, and the three folds — procurement details,
	 * extracted quotes, CPV. The curated TYPE / FIRE CONTEXT / document
	 * DURATION layers are loaded in the DB and shipped in the payload but
	 * NOT presented (user, same day): their certainty is below the site's
	 * bar until independently verified — DATA_DECISIONS 2026-08-23.
	 */
	import { bodyEn, devGreek, orgEn } from '$lib/transforms/names';
	import { peEn, ruLabel } from '$lib/transforms/regions';
	import FactsHeader from '$lib/detail/FactsHeader.svelte';
	import DocTrail, { type TrailRow } from '$lib/detail/DocTrail.svelte';
	import { isOutOfScope, trailChip } from '$lib/transforms/exclusion';
	import QuoteList, { type Quote } from '$lib/detail/QuoteList.svelte';
	import ChainTimeline from '$lib/detail/ChainTimeline.svelte';
	import FamilyTree from '$lib/charts/FamilyTree.svelte';
	import ProcurementFamily from '$lib/charts/ProcurementFamily.svelte';
	import Fold from '$lib/ui/Fold.svelte';
	import Hint from '$lib/ui/Hint.svelte';
	import { procedureEn } from '$lib/transforms/procedures';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import { dmy, eur, eurShort, grInt } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const c = $derived(data.c);
	const live = $derived(c.payments.filter((p) => !p.cancelled));
	// excluded because no co-op is a party to it — the registry cancelled
	// nothing, so the page must not say «cancelled» (related_to is set by
	// the curated correction, '' when no in-scope sibling exists)
	const outOfScope = $derived(isOutOfScope(c));

	/** the registry's date formats ('03/11/2023', '2026-07-24T00:00:00') */
	const iso = (v: string | null | undefined): string | null => {
		if (!v) return null;
		const s = v.trim();
		if (s.length >= 10 && s[2] === '/' && s[5] === '/')
			return `${s.slice(6, 10)}-${s.slice(3, 5)}-${s.slice(0, 2)}`;
		if (s.length >= 10 && s[4] === '-' && s[7] === '-') return s.slice(0, 10);
		return null;
	};
	const todayIso = new Date().toLocaleDateString('en-CA');
	let cpvAll = $state(false);
	// hover binds the timeline's act dots to the trail's rows, both ways
	let hoverAct = $state<string | null>(null);
	let hoverRow = $state<string | null>(null);
	const chain = $derived(c.chain ?? []);
	const payTicks = $derived(
		live.map((p) => ({ ref: p.payment_ref, d: p.d ?? iso(p.signed_date), eur: p.amount_without_vat }))
	);

	// English document-type labels (user template, 2026-08-17)
	const KIND: Record<string, string> = {
		request: 'Primary request',
		approved_request: 'Commitment approval',
		notice: 'Call / notice',
		auction: 'Award',
		contract: 'Contract',
		completion: 'Completion'
	};
	const ORDER: Record<string, number> = {
		request: 0, approved_request: 1, notice: 2, auction: 3, contract: 4, completion: 5
	};

	// the registry's chain returns the awards of EVERY lot of a multi-lot
	// procurement; the trail keeps only the award that names THIS co-op (the
	// FamilyTree's own name-verified pairing), the diagram keeps them all
	const fold = (s: string | null | undefined): string =>
		(s ?? '').toUpperCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^\p{L}\p{N}]/gu, '');
	const whoCore = (s: string | null | undefined): string =>
		fold(s).replace(/^(ΕΔΑΣΕ|ΑΔΣΕ|ΔΑΣΕ|ΔΑΣΙΚΟΣΣΥΝΕΤΑΙΡΙΣΜΟΣ(ΕΡΓΑΣΙΑΣ)?)/u, '');
	const ownAward = (title: string | null, awards: number): boolean => {
		if (awards <= 1) return true;
		const f = fold(title);
		return c.contractors.some((ct) =>
			[fold(ct.name), whoCore(ct.name)].some((w) => w.length >= 5 && f.includes(w))
		);
	};
	/** the trail table: this contract's own records; the other lots of the
	 *  same procurement — and their awards — live in the family diagram
	 *  (user, 2026-08-19) */
	const timeline = $derived.by(() => {
		const src = c.timeline ?? [];
		const nAwards = src.filter((t) => t.kind === 'auction').length;
		const rows = rowsOf(src.filter((t) => t.kind !== 'auction' || ownAward(t.title, nAwards)));
		// the contract's own later versions — the registry's prev/next links
		const seen = new Set(rows.map((t) => t.adam));
		for (const a of chain) {
			if (a.self || seen.has(a.ref)) continue;
			seen.add(a.ref);
			rows.push({
				adam: a.ref, kind: 'contract' as const, title: a.title, d: a.d,
				cancelled: 0, duplicate_of: null, related_to: null, in_db: true,
				who: null, self: false, version: true
			});
		}
		rows.sort((a, b) =>
			`${a.d ?? '9999'}${ORDER[a.kind]}`.localeCompare(`${b.d ?? '9999'}${ORDER[b.kind]}`)
		);
		return rows;
	});
	/** the diagram: the whole family the registry's chain returns */
	const familyActs = $derived(rowsOf(c.family_acts ?? c.timeline ?? []));
	/** the Anti-nero-style radial (user, 2026-08-29): the call — or the award,
	 *  where the procedure published no call — at the centre, the family's
	 *  contracts around it; the FamilyTree stays in the repo, off the page */
	const family = $derived(c.family ?? null);
	const hasFamily = $derived(!!family);
	const familyCaption = $derived.by(() => {
		if (!family) return '';
		const n = family.contracts.length;
		const inDb = n - (family.n_outside ?? 0);
		const centre = family.centre_kind === 'notice' ? `call ${family.call}` : `award ${family.call} (the procedure published no call)`;
		const outside = family.n_outside
			? ` ${grInt(family.n_outside)} other lot${family.n_outside === 1 ? '' : 's'} of the same procurement went to contractors that are not forest co-operatives and ${family.n_outside === 1 ? 'is' : 'are'} outside the dataset (outlined).`
			: '';
		return `${n === 1 ? 'The one contract' : `One of ${grInt(inDb)} contracts in the dataset`} awarded under ${centre}. Circle area ∝ stated net €; the centre is the sum of the lots the dataset holds.${outside}`;
	});
	const siblingContracts = $derived(familyActs.filter((a) => a.kind === 'contract').length);
	let view = $state<'map' | 'family'>('map');
	const showDiagram = () => {
		view = 'family';
		document.querySelector('.detailmap, .famslot')?.scrollIntoView({ block: 'center' });
	};

	function rowsOf(src: NonNullable<typeof c.timeline>) {
		const rows = src.map((t) => ({ ...t, self: false, version: false }));
		rows.push({
			adam: c.reference_number,
			kind: 'contract' as const,
			title: c.title,
			d: (c.contract_signed_date ?? '').slice(0, 10) || null,
			cancelled: c.cancelled ?? 0,
			duplicate_of: c.duplicate_of ?? null,
			related_to: c.related_to ?? null,
			in_db: true,
			who: c.contractors[0]?.name ?? null,
			self: true,
			version: false
		});
		rows.sort((a, b) =>
			`${a.d ?? '9999'}${ORDER[a.kind]}`.localeCompare(`${b.d ?? '9999'}${ORDER[b.kind]}`)
		);
		return rows;
	}
	/** the acts that produced the contract — request, commitment approval,
	 *  call, award — wherever the trail has them dated */
	const RUNUP_KINDS = ['request', 'approved_request', 'notice', 'auction'] as const;
	const runUpActs = $derived(
		timeline
			.filter(
				(t): t is (typeof timeline)[number] & { kind: (typeof RUNUP_KINDS)[number] } =>
					(RUNUP_KINDS as readonly string[]).includes(t.kind) && !t.cancelled
			)
			.map((t) => ({ ref: t.adam, d: t.d, kind: t.kind }))
	);

	const pdfHref = (t: (typeof timeline)[number]): string | null => {
		if (t.kind !== 'contract')
			return `/pdf/${t.kind === 'approved_request' ? 'request' : t.kind}/${t.adam}`;
		return t.in_db ? `/pdf/contract/${t.adam}` : null;
	};
	/** the payment orders belong in the trail (user, 2026-08-19): documents
	 *  of this contract with a date, a code and a PDF */
	const payRows = $derived<TrailRow[]>(
		c.payments.map((p) => ({
			d: p.d ?? iso(p.signed_date),
			type: 'Payment order',
			code: p.payment_ref,
			title: eur(p.amount_without_vat ?? p.amount_with_vat),
			pdf: `/pdf/payment/${p.payment_ref}`,
			...(p.cancelled
				? { chip: 'cancelled', chipBad: true }
				: p.credit
					? { chip: 'credit', chipBad: false }
					: p.correction_note
						? { chip: 'corrected', chipBad: false }
						: {})
		}))
	);
	const trailRows = $derived<TrailRow[]>(
		[
			...payRows,
			...timeline.map((t) => ({
				d: t.d,
				type:
					(t.kind === 'contract' ? (t.version ? 'Later version' : KIND.contract) : (KIND[t.kind] ?? t.kind)) +
					(t.self ? ' — this document' : ''),
				code: t.adam,
				title: t.title ?? null,
				pdf: pdfHref(t),
				self: t.self,
				...trailChip(t)
			}))
		].sort((a, b) => `${a.d ?? '9999'}`.localeCompare(`${b.d ?? '9999'}`))
	);

	/** the chart's legend — the symbols and nothing else */
	const barNote = $derived.by(() =>
		[
			'●  the contract, at its signature date — no deadline bar is drawn: the deadlines the signed texts state are not yet verified to the site’s bar',
			'€  a payment order',
			'•  the grey dots before the signature — the procurement that produced the contract',
			'no ✔ is ever drawn: the awarding bodies publish no completion act that cites the contract'
		].join(String.fromCharCode(10))
	);

	const quotes = $derived<Quote[]>([
		...(c.correction_note
			? [{
					label: 'Stated value — curated correction',
					text: c.correction_note,
					code: c.reference_number,
					href: `/pdf/contract/${c.reference_number}`,
					note: 'The value shown above is the one the signed contract states, not the registry figure.'
				}]
			: []),
	]);

	const pe = $derived(c.geo?.pe ?? null);
	const seat = $derived(c.geo?.unit_seat ?? null);
	let leftH = $state(0);
	let mapW = $state(0);
	const mapH = $derived(Math.max(420, Math.round(leftH)));
	const CAVEAT =
		'On the map: the regional unit derived from the awarding unit is shaded and the dot is the ' +
		"unit's seat where the registry knows it. Named work sites are not recorded for forest co-op contracts.";
</script>

<svelte:head>
	<title>{c.title ?? c.reference_number} — forest co-ops</title>
	<meta property="og:title" content={c.title ?? c.reference_number} />
	<meta
		property="og:description"
		content="Forest co-op contract {c.reference_number}: {eurShort(c.total_cost_without_vat ?? 0)} stated (excl. VAT)"
	/>
</svelte:head>

<div class="dasep">
<p class="crumb"><a href="/dase/contracts">← Forest co-op contracts</a></p>

{#if c.duplicate_of}
	<div class="dupbanner">
		<strong>Registry double-posting.</strong> This ΑΔΑΜ is a second upload of the same signed
		document and is excluded from every calculation — the counted posting is
		<a href={`/dase/contract/${c.duplicate_of}`} class="tabular">{c.duplicate_of}</a>.
	</div>
{:else if outOfScope}
	<div class="dupbanner">
		<strong>Related contract, outside this dataset.</strong> The signed contract names no forest
		co-operative as a party, so it is shown for reference and excluded from every calculation.
		{#if c.related_to}
			The co-operative's own contract in the same procurement is
			<a href={`/dase/contract/${c.related_to}`} class="tabular">{c.related_to}</a>.
		{/if}
	</div>
{/if}
{#if c.duplicates?.length}
	<p class="muted dupnote">
		Also posted in the registry as
		{#each c.duplicates as dref, i (dref)}{i ? ', ' : ''}<a href={`/dase/contract/${dref}`} class="tabular">{dref}</a>{/each}
		— duplicate upload{c.duplicates.length > 1 ? 's' : ''}, excluded from the calculations.
	</p>
{/if}

<FactsHeader caveat={CAVEAT} bind:leftHeight={leftH}>
	{#snippet facts()}
		<dt class="id">Contract</dt>
		<dd class="id">
			{c.reference_number}
			{#if outOfScope}<span class="chip">outside the dataset</span>
			{:else if c.cancelled}<span class="chip bad">cancelled</span>{/if}
		</dd>
		<dt>Date</dt>
		<dd>{dmy(c.contract_signed_date) || '—'}</dd>
		<dt>Contractor</dt>
		<dd>
			{#each c.contractors as ct, i (ct.vat_number)}
				{#if i}{', '}{/if}<a href={`/dase/coop/${ct.vat_number}`}>{ct.display_el ?? ct.name}</a>
			{/each}
			{#if c.contractors.some((x) => x.display_el && x.display_el !== x.name)}<Hint
					text={`in the registry as ${c.contractors.map((x) => x.name).join(', ')}`}
				/>{/if}
			{#if c.contractors.length > 1}<Hint
					text="signed by more than one co-operative; each co-op's own page counts its even share, so no euro is counted twice"
				/>{/if}
		</dd>
		<dt>Budget <small class="muted">(excl. VAT)</small></dt>
		<dd>{eurShort(c.total_cost_without_vat ?? 0)}</dd>
		<dt>Awarding procedure</dt>
		<dd>
			<span title={devGreek(c.procedure_type ?? '')}>{procedureEn(c.procedure_type)}</span>
		</dd>
		<dt>Contracting authority</dt>
		<dd><span title={devGreek(c.organization_name)}>{orgEn(c.organization_name) || '—'}</span></dd>
		<dt>Awarding unit</dt>
		<dd><span title={devGreek(c.units_operator_name)}>{bodyEn(c.units_operator_name) || '—'}</span></dd>
		<dt>Areas of intervention</dt>
		<dd>
			{#if pe}<span class="lead">Regional Unit:</span> {peEn(pe)}<Hint
					text="derived from the awarding unit's seat — forest co-op contracts name no municipality in a curated layer"
				/>{:else}—<Hint text="the awarding unit spans several regional units (e.g. a power-line operator); no single unit is assigned" />{/if}
		</dd>
		<dt>Amendments to original contract</dt>
		<dd>{chain.length > 1 || c.prev_reference_no || c.next_reference_no ? 'yes' : 'no'}</dd>
		<dt>Status</dt>
		<dd>
			{#if outOfScope}
				outside the dataset
			{:else if c.cancelled}
				cancelled
			{:else}
				completion unknown: no record of the works’ completion was found in ΚΗΜΔΗΣ or Διαύγεια
			{/if}
		</dd>
	{/snippet}
	{#snippet map()}
		{#if hasFamily}
			<div class="viewsw" role="group" aria-label="Map or procurement diagram">
				<button class="sw" class:on={view === 'map'} onclick={() => (view = 'map')}>Map</button>
				<button class="sw" class:on={view === 'family'} onclick={() => (view = 'family')}>Diagram</button>
			</div>
		{/if}
		{#if hasFamily && view === 'family'}
			<div class="famslot" style:min-height="{mapH}px">
				<ProcurementFamily
					call={family!.call}
					contracts={family!.contracts}
					total={family!.total_eur}
					self={c.reference_number}
					linkBase="/dase/contract/"
					selfColor="var(--c-dase)"
					caption={familyCaption}
				/>
			</div>
		{:else}
			<div class="detailmap" bind:clientWidth={mapW}>
				<PaperMap
					width={mapW || 460}
					height={mapH}
					fitPes={pe ? [pe] : undefined}
					fitPoints={seat ? [[seat.lon, seat.lat]] : null}
					fitPad={0.15}
					colorOf={(p) => (p === pe ? 'color-mix(in srgb, var(--c-dase) 30%, var(--paper))' : 'var(--paper)')}
					tipOf={(p) => `<strong>${ruLabel(p)}</strong>`}
				>
					{#snippet overlay(ctx)}
						{#if seat}
							<DotLayer
								{ctx}
								points={[{ lat: seat.lat, lon: seat.lon, name: seat.name }]}
								r={4.5}
								fillOf={() => 'var(--c-dase)'}
								tipOf={() => `<strong>${bodyEn(seat.name)}</strong><br>awarding unit seat`}
								tipCorner="top-left"
							/>
						{/if}
					{/snippet}
				</PaperMap>
			</div>
		{/if}
	{/snippet}
</FactsHeader>

<section class="plain">
	<h2 class="withhint">
		Timeline<Hint text={barNote} width="21rem" up heading />
		<a class="mth" href="/methodology#validation">Methodology</a>
	</h2>
	<div class="tlrow">
		<ChainTimeline
			signed={chain[0]?.d ?? iso(c.contract_signed_date)}
			signedRef={chain[0]?.ref ?? c.reference_number}
			end={null}
			deadline={null}
			deadlineBasis={null}
			today={todayIso}
			{chain}
			payments={payTicks}
			runUp={runUpActs}
			highlightRef={hoverRow}
			onActHover={(ref) => (hoverAct = ref)}
			ink="var(--c-dase)"
			axisStart="2021-09-01"
			stubDot
		/>
	</div>
</section>

<section class="plain">
	<h2>Document trail</h2>
	<DocTrail
		heading={null}
		rows={trailRows}
		highlight={hoverAct ?? hoverRow}
		onRowHover={(code) => (hoverRow = code)}
	/>
	{#if hasFamily && siblingContracts > 1}
		<p class="muted">
			<small
				>One of {grInt(siblingContracts)} contracts the registry files under the same procurement —
				<button class="linkish" onclick={showDiagram}>see the diagram</button></small
			>
		</p>
	{/if}
	{#if live.length}
		<p class="muted">
			<small
				>{grInt(live.length)} live payment orders{c.paid_without_vat !== null
					? ` · ${eurShort(c.paid_without_vat)} paid`
					: ''}</small
			>
		</p>
	{/if}
	{#if !timeline.some((t) => t.kind !== 'contract')}
		<p class="muted">
			<small>ΚΗΜΔΗΣ links no upstream acts (αίτημα, διακήρυξη, κατακύρωση) to this contract — the registry's chain returns none.</small>
		</p>
	{/if}
</section>

<Fold title="Procurement details of {c.reference_number}">
	<div class="tplsec">
		<div class="scrollx">
			<table class="listing">
				<thead>
					<tr>
						<th>date</th>
						<th>type of document</th>
						<th>document code (ΑΔΑΜ)</th>
						<th>title</th>
						<th>contracting authority</th>
						<th>operating unit</th>
						<th>signer</th>
						<th>funding</th>
					</tr>
				</thead>
				<tbody>
					<tr>
						<td class="tabular nowrap">{dmy(c.contract_signed_date) || '—'}</td>
						<td>Contract</td>
						<td class="tabular nowrap">{c.reference_number}</td>
						<td>{c.title ?? '—'}</td>
						<td title={devGreek(c.organization_name)}>{orgEn(c.organization_name) || '—'}</td>
						<td title={devGreek(c.units_operator_name)}>{bodyEn(c.units_operator_name) || '—'}</td>
						<td>{c.signer_name ?? '—'}</td>
						<td class="tabular">{c.public_funding_ref ?? '—'}</td>
					</tr>
				</tbody>
			</table>
		</div>
		<dl class="facts more">
			<div><dt>Registry type</dt><dd>{c.contract_type ?? '—'}</dd></div>
			<div><dt>Legal framework</dt><dd>{c.legal_context ?? '—'}</dd></div>
			<div><dt>Registry duration</dt><dd>{c.contract_duration ? `${c.contract_duration} ${c.contract_duration_unit ?? ''}` : '—'} <small class="muted">{dmy(c.start_date) || '—'} → {c.end_date ? dmy(c.end_date) : 'open'}</small></dd></div>
		</dl>
		{#if c.objects.length}
			<h3>Items</h3>
			<table>
				<thead><tr><th>item</th><th class="num">quantity</th><th class="num">net €</th></tr></thead>
				<tbody>
					{#each c.objects as o, i (i)}
						<tr>
							<td>{o.short_description ?? ''}</td>
							<td class="num">{o.quantity ? `${o.quantity} ${o.unit_type ?? ''}` : '—'}</td>
							<td class="num">{o.cost_without_vat ? eurShort(o.cost_without_vat) : '—'}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		{/if}
	</div>
</Fold>

<div class="refcols">
	<Fold title="Extracted quotes from documents">
		<QuoteList heading={null} {quotes} />
	</Fold>
	{#if c.cpvs.length}
		<Fold title="CPV codes">
			<ul class="cpvlist">
				{#each c.cpvs.slice(0, cpvAll ? c.cpvs.length : 12) as cpv, i (i)}
					<li>
						<span class="tabular">{cpv.cpv_code}</span>
						{cpv.cpv_description ?? ''}
						{#if cpv.cpv_code === '66519300-4'}<span
								class="chip"
								title="The insurance CPV tags the ΕΦΚΑ employer contributions for the δασεργάτες that the award funds on top of the works — not procured insurance services."
								>ΕΦΚΑ contributions, not insurance</span
							>{/if}
					</li>
				{/each}
			</ul>
			{#if c.cpvs.length > 12}
				<button class="linkish" onclick={() => (cpvAll = !cpvAll)}
					>{cpvAll ? 'show fewer' : `… ${grInt(c.cpvs.length - 12)} more`}</button
				>
			{/if}
		</Fold>
	{/if}
</div>
</div>

<style>
	/* the page wears the dataset's hue: folds, the timeline's ink, the map's
	   zoom buttons — the Anti-nero page's skeleton in green */
	.dasep {
		--fold-accent: var(--c-dase);
	}
	.crumb a {
		text-decoration: none;
		color: var(--ink-soft);
	}
	/* the page's two spine sections carry no fold: the timeline and the
	   trail are what the page IS (user, 2026-08-19) */
	.plain {
		margin-top: var(--sp-8);
	}
	.plain h2 {
		font-family: var(--font-display);
		font-weight: 900;
		text-transform: uppercase;
		font-size: var(--fs-18);
		letter-spacing: 0.01em;
		margin: 0 0 var(--sp-3);
	}
	.lead {
		font-weight: 600;
	}
	.withhint {
		display: flex;
		align-items: center;
		gap: 4px;
	}
	.tlrow {
		position: relative;
	}
	.mth {
		margin-left: auto;
		font-family: var(--font-ui);
		font-weight: 400;
		text-transform: none;
		letter-spacing: normal;
		font-size: var(--fs-12);
		color: var(--ink-soft);
	}
	/* the switch rides ON the frame's top-right corner */
	/* the site's segmented toggle (user, 2026-08-26), left of the map's
	   own +/−/⌂ stack, which keeps its usual corner */
	.viewsw {
		position: absolute;
		top: var(--sp-2);
		right: calc(var(--sp-2) + 1.45rem + 8px);
		z-index: 2;
		display: inline-flex;
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		overflow: hidden;
		background: var(--paper);
	}
	.sw {
		font: inherit;
		font-size: var(--fs-13);
		padding: 2px var(--sp-3);
		border: 0;
		background: var(--paper);
		color: var(--ink-soft);
		cursor: pointer;
	}
	.sw.on {
		background: var(--c-dase);
		color: var(--paper);
	}
	.famslot {
		position: relative;
		display: flex;
		flex-direction: column;
		justify-content: center;
		padding-bottom: 3.2rem;
		box-sizing: border-box;
	}
	/* evidence left, codes right — two reference blocks, one row */
	.refcols {
		display: grid;
		grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
		gap: var(--sp-6);
		align-items: start;
	}
	@media (max-width: 900px) {
		.refcols {
			grid-template-columns: 1fr;
		}
	}
	.cpvlist {
		margin: 0;
		padding-left: 1.1em;
		font-size: var(--fs-14);
	}
	.cpvlist li {
		margin-bottom: 2px;
	}
	.linkish {
		font: inherit;
		font-size: var(--fs-12);
		background: none;
		border: none;
		padding: 0;
		color: var(--ink-soft);
		text-decoration: underline;
		cursor: pointer;
	}
	/* template map look — same as the sponsored-works maps */
	.detailmap :global(.map) {
		background: color-mix(in srgb, var(--ink) 5.8%, var(--paper));
		border: 1px solid var(--line);
		--map-accent: var(--c-dase);
		box-shadow: none;
		border-radius: 4px;
	}
	.detailmap :global(.map .region) {
		stroke: var(--line);
	}
	.tplsec {
		margin-top: var(--sp-2);
	}
	.tplsec h3 {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: var(--fs-13);
		text-transform: uppercase;
		letter-spacing: 0.04em;
		margin: var(--sp-4) 0 var(--sp-2);
	}
	.scrollx {
		overflow-x: auto;
	}
	.facts.more {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: var(--sp-2) var(--sp-4);
		margin-top: var(--sp-3);
	}
	.facts.more dt {
		color: var(--ink-soft);
		font-size: var(--fs-12);
	}
	.facts.more dd {
		margin: 0;
		font-size: var(--fs-13);
	}
	table {
		width: 100%;
		border-collapse: collapse;
		font-size: var(--fs-13);
	}
	th {
		text-align: left;
		font-weight: 400;
		color: var(--ink-soft);
		padding: 6px 10px 6px 0;
		border-bottom: 1px solid var(--line-strong, var(--line));
	}
	td {
		padding: 8px 10px 8px 0;
		border-bottom: 1px solid var(--line);
		vertical-align: top;
	}
	.num {
		text-align: right;
		font-variant-numeric: tabular-nums;
	}
	.nowrap {
		white-space: nowrap;
	}
	.dupbanner {
		border: 1.5px solid var(--c-dase);
		border-radius: 8px;
		padding: var(--sp-2) var(--sp-3);
		margin-bottom: var(--sp-4);
		font-size: var(--fs-14);
	}
	.dupnote {
		font-size: var(--fs-13);
	}
	.muted {
		color: var(--ink-soft);
	}
</style>
