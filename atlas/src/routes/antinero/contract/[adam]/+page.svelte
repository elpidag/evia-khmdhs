<script lang="ts">
	import { authEn, bodyEn, devGreek, orgEn } from '$lib/transforms/names';
	import { ruLabel } from '$lib/transforms/regions';
	import FactsHeader from '$lib/detail/FactsHeader.svelte';
	import DocTrail, { type TrailRow } from '$lib/detail/DocTrail.svelte';
	import { trailChip } from '$lib/transforms/exclusion';
	import QuoteList, { type Quote } from '$lib/detail/QuoteList.svelte';
	import ProcurementFamily from '$lib/charts/ProcurementFamily.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import { dmy, eur, eurShort, grInt } from '$lib/transforms/format';
	import { scopeLabel } from '$lib/transforms/scopes';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const c = $derived(data.c);
	const live = $derived(c.payments.filter((p) => !p.cancelled));
	const catSrcRef = $derived(
		c.category?.source.startsWith('inherited:') ? c.category.source.slice(10) : null
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
	// a ΣΥΜΒ ΑΔΑΜ is not always a contract: ΥΠΕΝ posts amendments,
	// supplementary contracts and ministry approvals under one too, and the
	// trail has to say which (DATA_DECISIONS 2026-08-18)
	// Every ΣΥΜΒ record IS a σύμβαση — the label says which kind, so the plain
	// contract is «αρχική» (user, 2026-08-18). Kept in step with
	// khmdhs/document_kinds.py:KINDS.
	const DOCKIND: Record<string, string> = {
		contract: 'Original contract',
		amendment: 'Revision of terms',
		supplementary_contract: 'Supplementary contract',
		approval_ape_supplementary: 'Approval of supplementary works',
		approval_supplementary: 'Approval of supplementary works',
		approval_ape: 'Approval of revised quantities',
		approval_schedule_extension: 'Deadline extension'
	};
	const CKIND: Record<string, string> = {
		oristiki_paralavi: 'Completion — final acceptance',
		paralavi: 'Completion — acceptance protocol',
		peraiosi: 'Completion — certificate',
		oloklirosi: 'Completion — statement'
	};
	const ORDER: Record<string, number> = {
		request: 0, approved_request: 1, notice: 2, auction: 3, contract: 4, completion: 5
	};

	const timeline = $derived.by(() => {
		if (!c.timeline.length) return [];
		const rows = c.timeline.map((t) => ({ ...t, self: false }));
		rows.push({
			adam: c.reference_number,
			kind: 'contract' as const,
			title: c.title,
			d: (c.contract_signed_date ?? '').slice(0, 10) || null,
			cancelled: c.cancelled ?? 0,
			doc_kind: c.document_kind?.kind ?? null,
			duplicate_of: c.duplicate_of ?? null,
			related_to: c.related_to ?? null,
			in_db: true,
			self: true
		});
		rows.sort((a, b) =>
			`${a.d ?? '9999'}${ORDER[a.kind]}`.localeCompare(`${b.d ?? '9999'}${ORDER[b.kind]}`)
		);
		return rows;
	});
	const completion = $derived(timeline.find((t) => t.kind === 'completion'));

	const pdfHref = (t: (typeof timeline)[number]): string | null => {
		if (t.kind === 'completion') return `/pdf/diavgeia/${t.adam}`;
		if (t.kind !== 'contract')
			return `/pdf/${t.kind === 'approved_request' ? 'request' : t.kind}/${t.adam}`;
		return t.in_db ? `/pdf/contract/${t.adam}` : null;
	};
	const trailRows = $derived<TrailRow[]>(
		timeline.map((t) => ({
			d: t.d,
			type:
				t.kind === 'completion'
					? (CKIND[t.ckind ?? ''] ?? KIND.completion)
					: (t.kind === 'contract'
							? (DOCKIND[t.doc_kind ?? ''] ?? KIND.contract)
							: (KIND[t.kind] ?? t.kind)) + (t.self ? ' — this document' : ''),
			code: t.adam,
			title: t.title ?? null,
			pdf: pdfHref(t),
			self: t.self,
			// rows the registry never published: they are in the trail because
			// this contract's text cites them, and the chip says so
			...(t.cited ? { chip: 'cited in this contract', chipBad: false } : {}),
			// the registry title stays verbatim — it IS the document's title and
			// the evidence of the error; the chip points at the explanation below
			...(t.self && overrideNote
				? { chip: 'unit corrected from the PDF', chipBad: false }
				: trailChip(t))
		}))
	);

	// 6 contracts are linked to their forest units by curated OVERRIDE, and 3
	// of those registry titles contradict the units shown (25SYMV016491944 is
	// titled «ΔΔ ΛΕΣΒΟΥ» over works its PDF places in Ρόδος). The evidence
	// exists; without it the page reads as our error, not the registry's.
	// One sentence per contract — it is stored on every one of its links.
	const overrideNote = $derived(
		(c.authorities ?? []).find((a) => (a.source ?? '').startsWith('override') && a.excerpt)
			?.excerpt ?? null
	);

	const quotes = $derived<Quote[]>([
		// a curated stated-value correction must be visible on the page it
		// changes: 5 Anti-nero contracts carry one (DATA_DECISIONS 2026-08-14,
		// 2026-08-18), and without this the page shows a figure that differs
		// from the registry with no explanation
		...(c.correction_note
			? [
					{
						label: 'Stated value — curated correction',
						text: c.correction_note,
						code: c.reference_number,
						href: `/pdf/contract/${c.reference_number}`,
						note: 'The value shown above is the one the signed contract states, not the registry figure.'
					}
				]
			: []),
		...(overrideNote
			? [
					{
						label: 'Awarding unit — curated correction',
						text: overrideNote,
						code: c.reference_number,
						href: `/pdf/contract/${c.reference_number}`,
						note: 'The units above follow the signed PDF, not the registry title.'
					}
				]
			: []),
		...(c.category
			? [
					{
						label: 'Type of work — descriptive project title',
						text: c.category.title,
						code: catSrcRef ?? c.reference_number,
						href: `/pdf/contract/${catSrcRef ?? c.reference_number}`,
						note: catSrcRef
							? `Stated in the signed PDF of the previous version ${catSrcRef}; this record's own document quotes only the parties or the amendment object.`
							: "Stated verbatim in this contract's signed PDF — the classification evidence."
					}
				]
			: []),
		...c.sites
			.filter((s) => s.excerpt)
			.map((s) => ({
				label: `Work site — ${s.site_name}`,
				text: s.excerpt as string,
				code: c.reference_number,
				href: `/pdf/contract/${c.reference_number}`,
				note: s.page ? `PDF p.${s.page}` : null
			})),
		...(completion?.end_excerpt
			? [
					{
						label: 'Completion',
						text: completion.end_excerpt,
						code: completion.adam,
						href: `/pdf/diavgeia/${completion.adam}`
					}
				]
			: [])
	]);

	const regionSet = $derived(new Set(c.regions.map((r) => r.region_pe)));
	const seatDots = $derived(
		(c.authorities ?? []).filter((a) => a.lat != null && a.lon != null)
	);

	const CAVEAT =
		"Work regions and named sites are curated from the contract's signed documents. The map " +
		"highlights the contract's regional units and marks the seats of the awarding forest " +
		'authorities; site positions below regional-unit level are not mapped.';
</script>

<svelte:head>
	<title>{c.title ?? c.reference_number} — Anti-nero</title>
	<meta property="og:title" content={c.title ?? c.reference_number} />
	<meta
		property="og:description"
		content="Anti-nero contract {c.reference_number}: {eurShort(
			c.total_cost_without_vat ?? 0
		)} stated (excl. VAT) · {c.contractors.map((x) => x.name).join(', ')}"
	/>
</svelte:head>

<p class="crumb"><a href="/antinero/contracts">← Anti-nero contracts</a></p>

<FactsHeader caveat={CAVEAT}>
	{#snippet facts()}
		<dt class="id">Contract (ΑΔΑΜ)</dt>
		<dd class="id">
			{c.reference_number}
			{#if c.scope && !c.scope.in_scope}<span class="chip bad">out of scope</span>{/if}
			{#if c.scope?.scope === 'antinero_probable'}<span class="chip warn"
					>{scopeLabel(c.scope.scope)}</span
				>{/if}
		</dd>
		<dt>Date</dt>
		<dd>{dmy(c.contract_signed_date) || '—'}</dd>
		{#if c.document_kind}
			<!-- ΚΗΜΔΗΣ files contracts, amendments, supplementary contracts AND
			     ministry approvals under one ΣΥΜΒ ΑΔΑΜ, and types all of them
			     «Έργα»/«Υπηρεσίες»; this says what the document itself is -->
			<dt>Document</dt>
			<dd>
				{c.document_kind.label_en}
				<br /><small class="muted">{c.document_kind.label_el}</small>
			</dd>
		{/if}
		<dt>Contractor</dt>
		<dd>
			{#each c.contractors as ct, i (ct.vat_number)}
				{#if i}{', '}{/if}<a href={`/antinero/contractor/${ct.vat_number}`}>{ct.name}</a>
			{/each}
			{#if c.contractors.length > 1}
				<br /><small class="muted"
					>consortium — each partner is credited the full value in per-contractor views</small
				>
			{/if}
		</dd>
		<dt>Procedure</dt>
		<dd>
			{c.procedure_type ?? '—'}
			{#if c.bids_submitted === 1}<span class="chip warn">single bidder</span>{/if}
		</dd>
		<dt>Budget <small class="muted">(excl. VAT)</small></dt>
		<dd>
			{eurShort(c.total_cost_without_vat ?? 0)}
			{#if c.gross?.stated_gross}<small class="muted"
					>· {eurShort(c.gross.stated_gross)} incl. ΦΠΑ</small
				>{/if}
		</dd>
		<dt>Type</dt>
		<dd>
			{#if c.category}<span class="chip cat" title={c.category.note ?? ''}
					>{c.category.label}</span
				>{:else}—{/if}
		</dd>
		<dt>Scope</dt>
		<dd>{c.category?.key === 'meletes' ? 'study' : 'works'}</dd>
		<dt>Awarding unit</dt>
		<dd>
			{#if c.authorities?.length}
				{#each c.authorities as a, i (a.name)}
					{#if i}{', '}{/if}<span title={devGreek(a.name)}>{authEn(a.name)}</span>
				{/each}
			{:else}
				<span title={devGreek(c.units_operator_name)}>{bodyEn(c.units_operator_name) || '—'}</span>
			{/if}
		</dd>
		<dt class="gap"></dt>
		<dd class="gap"></dd>
		<dt>Work regions</dt>
		<dd>
			{#if c.regions.length}
				{#each c.regions as r, i (i)}{#if i}{', '}{/if}{ruLabel(r.region_pe)}{/each}
				{#if c.sites.length}
					<small class="muted"> · {grInt(c.sites.length)} named site(s) below</small>
				{/if}
			{:else}
				—
			{/if}
		</dd>
		<dt>Duration</dt>
		<dd>
			{c.contract_duration ? `${c.contract_duration} ${c.contract_duration_unit ?? ''}` : '—'}
			<small class="muted">{dmy(c.start_date) || '—'} → {c.end_date ? dmy(c.end_date) : 'open'}</small
			>
		</dd>
		<dt>Amendments to initial contract</dt>
		<dd>
			{#if c.prev_reference_no || c.next_reference_no}
				yes
				{#if c.prev_reference_no}
					<small class="muted"
						>· previous <a class="tabular" href={`/antinero/contract/${c.prev_reference_no}`}
							>{c.prev_reference_no}</a
						></small
					>
				{/if}
				{#if c.next_reference_no}
					<small class="muted"
						>· next <a class="tabular" href={`/antinero/contract/${c.next_reference_no}`}
							>{c.next_reference_no}</a
						></small
					>
				{/if}
			{:else}
				no
			{/if}
		</dd>
		<dt>Status</dt>
		<dd>
			{#if c.cancelled}
				cancelled
			{:else if completion}
				completed <small class="muted">{dmy(completion.d)}</small>
			{:else}
				no completion recorded
			{/if}
		</dd>
	{/snippet}
	{#snippet map()}
		<div class="detailmap">
			<PaperMap
				interactive={false}
				colorOf={(pe) => (regionSet.has(pe) ? 'color-mix(in srgb, var(--c-antinero) 22%, #fff)' : '#fff')}
				tipOf={(pe) => `<strong>${ruLabel(pe)}</strong>`}
			>
				{#snippet overlay(ctx)}
					<DotLayer
						{ctx}
						points={seatDots.map((a) => ({ ...a, lat: a.lat!, lon: a.lon! }))}
						r={4}
						fillOf={() => 'var(--c-antinero)'}
						tipOf={(a) => `<strong>${authEn(String(a.name))}</strong><br>awarding forest authority seat`}
					/>
				{/snippet}
			</PaperMap>
		</div>
	{/snippet}
</FactsHeader>

<p>
	<a class="pdf" href={`/pdf/contract/${c.reference_number}`} target="_blank" rel="noopener">
		📄 View the signed contract PDF
	</a>
	<small class="muted">fetched from KHMDHS once, then served from the local cache</small>
</p>

<div class="trailrow">
	<DocTrail rows={trailRows} />
	{#if c.family && c.family.contracts.length > 1}
		<section class="famsec">
			<h2>CONTRACTS UNDER THE SAME CALL</h2>
			<p class="muted">
				<small
					>This contract is one of {c.family.contracts.length} awarded under call
					{c.family.call}{c.family.source.startsWith('inherited')
						? ` (cited by the version it amends, ${c.family.source.slice(10)})`
						: ''}.</small
				>
			</p>
			<ProcurementFamily
				call={c.family.call}
				contracts={c.family.contracts}
				total={c.family.total_eur}
				self={c.reference_number}
				amendments={c.family.amendments}
			/>
		</section>
	{/if}
</div>

{#if !timeline.length}
	<p class="muted">
		ΚΗΜΔΗΣ links no upstream acts (αίτημα, διακήρυξη, κατακύρωση) to this contract — the
		registry's chain returns none, a linkage gap common across the programme's direct awards.
	</p>
{/if}

<section class="tplsec">
	<h2>Procurement details of {c.reference_number}</h2>
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
		<div><dt>Award basis</dt><dd>{c.award_procedure ?? '—'}</dd></div>
		<div><dt>Registry type</dt><dd>{c.contract_type ?? '—'}</dd></div>
		<div><dt>Legal framework</dt><dd>{c.legal_context ?? '—'}</dd></div>
		<div><dt>Bids</dt><dd>{c.bids_submitted ?? '—'}</dd></div>
	</dl>
	{#if c.cpvs.length}
		<h3>CPV</h3>
		<ul>
			{#each c.cpvs.slice(0, 12) as cpv, i (i)}
				<li><span class="tabular">{cpv.cpv_code}</span> {cpv.cpv_description ?? ''}</li>
			{/each}
			{#if c.cpvs.length > 12}<li class="muted">… {grInt(c.cpvs.length - 12)} more</li>{/if}
		</ul>
	{/if}
	{#if c.sites.length}
		<h3>Named work sites</h3>
		<table>
			<thead><tr><th>site</th><th>regional unit</th></tr></thead>
			<tbody>
				{#each c.sites as s, i (i)}
					<tr>
						<td>{s.site_name}</td>
						<td>{ruLabel(s.region_pe)}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	{/if}
</section>

{#if live.length}
	<section class="tplsec">
		<h2>Payment orders</h2>
		<table>
			<thead>
				<tr
					><th>date</th><th>order</th><th class="num">amount (net)</th><th class="num"
						>incl. ΦΠΑ</th
					><th></th></tr
				>
			</thead>
			<tbody>
				{#each c.payments as p (p.payment_ref)}
					<tr class:dead={p.cancelled === 1}>
						<td class="tabular muted">{dmy(p.signed_date) || '—'}</td>
						<td>
							<span class="tabular">{p.payment_ref}</span>
							{#if p.credit}<span class="chip">credit</span>{/if}
							{#if p.cancelled}<span class="chip bad">cancelled</span>{/if}
							{#if p.correction_note}<span class="chip warn" title={p.correction_note}
									>corrected</span
								>{/if}
						</td>
						<td class="num">{eur(p.amount_without_vat ?? p.amount_with_vat)}</td>
						<td class="num muted"
							><small
								>{c.gross?.payments?.[p.payment_ref] != null
									? eur(c.gross.payments[p.payment_ref])
									: '—'}</small
							></td
						>
						<td>
							<a href={`/pdf/payment/${p.payment_ref}`} target="_blank" rel="noopener">PDF</a>
							{#if p.ada}
								· <a
									href={`https://diavgeia.gov.gr/decision/view/${p.ada}`}
									target="_blank"
									rel="noopener">Διαύγεια</a
								>
							{/if}
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
		<p class="muted">
			<small
				>{grInt(live.length)} live orders · {c.paid_without_vat !== null
					? `${eurShort(c.paid_without_vat)} paid net`
					: ''}{c.gross?.paid_gross ? ` · ${eurShort(c.gross.paid_gross)} incl. ΦΠΑ` : ''}</small
			>
		</p>
	</section>
{/if}

<QuoteList {quotes} />

<style>
	/* the family sits under the map, on the same column width, with the
	   trail compressed beside it — one procurement read top to bottom */
	.trailrow {
		display: grid;
		grid-template-columns: minmax(0, 1fr) minmax(300px, 460px);
		gap: var(--sp-8);
		align-items: start;
		margin-bottom: var(--sp-6);
	}
	@media (max-width: 900px) {
		.trailrow { grid-template-columns: minmax(0, 1fr); }
	}
	.crumb a {
		text-decoration: none;
		color: var(--ink-soft);
	}
	/* template map look — same as the sponsored-works maps:
	   grey sea, no border, no paper shadow */
	.detailmap :global(.map) {
		background: #f2f2f2;
		border: none;
		box-shadow: none;
		border-radius: 4px;
	}
	.detailmap :global(.map .region) {
		stroke: #8f8f8f;
	}
	.tplsec h2 {
		font-family: var(--font-display);
		font-weight: 900;
		text-transform: uppercase;
		font-size: var(--fs-18);
	}
	.tplsec {
		margin-top: var(--sp-8);
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
	.dead td {
		color: var(--ink-faint);
	}
	.chip.cat {
		background: color-mix(in srgb, var(--c-antinero) 12%, #fff);
	}
	.muted {
		color: var(--ink-soft);
	}
	.pdf {
		font-weight: 700;
	}
</style>
