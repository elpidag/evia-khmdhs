<script lang="ts">
	import { bodyEn, devGreek, orgEn } from '$lib/transforms/names';
	import { ruLabel } from '$lib/transforms/regions';
	import FactsHeader from '$lib/detail/FactsHeader.svelte';
	import DocTrail, { type TrailRow } from '$lib/detail/DocTrail.svelte';
	import { isOutOfScope, trailChip } from '$lib/transforms/exclusion';
	import QuoteList, { type Quote } from '$lib/detail/QuoteList.svelte';
	import FamilyTree from '$lib/charts/FamilyTree.svelte';
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
	// the FamilyTree keeps the Greek registry vocabulary — it matches acts
	// against registry names; the trail table below is the English view
	const TREE_KIND: Record<string, string> = {
		request: 'Πρωτογενές αίτημα',
		approved_request: 'Ανάληψη υποχρέωσης',
		notice: 'Διακήρυξη / πρόσκληση',
		auction: 'Κατακύρωση / ανάθεση',
		contract: 'Σύμβαση',
		completion: 'Ολοκλήρωση'
	};

	const timeline = $derived.by(() => {
		if (!c.timeline?.length) return [];
		const rows = c.timeline.map((t) => ({ ...t, self: false }));
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
			self: true
		});
		rows.sort((a, b) =>
			`${a.d ?? '9999'}${ORDER[a.kind]}`.localeCompare(`${b.d ?? '9999'}${ORDER[b.kind]}`)
		);
		return rows;
	});

	const pdfHref = (t: (typeof timeline)[number]): string | null => {
		if (t.kind !== 'contract')
			return `/pdf/${t.kind === 'approved_request' ? 'request' : t.kind}/${t.adam}`;
		return t.in_db ? `/pdf/contract/${t.adam}` : null;
	};
	const trailRows = $derived<TrailRow[]>(
		timeline.map((t) => ({
			d: t.d,
			type: (KIND[t.kind] ?? t.kind) + (t.self ? ' — this document' : ''),
			code: t.adam,
			title: t.title ?? null,
			pdf: pdfHref(t),
			self: t.self,
			...trailChip(t)
		}))
	);

	const quotes = $derived<Quote[]>([
		...(c.correction_note
			? [
					{
						label: 'Curated correction',
						text: c.correction_note,
						code: c.reference_number,
						href: `/pdf/contract/${c.reference_number}`
					}
				]
			: [])
	]);

	const pe = $derived(c.geo?.pe ?? null);
	const seat = $derived(c.geo?.unit_seat ?? null);
	const CAVEAT =
		'The regional unit is derived from the awarding operator unit; the map marks the ' +
		"unit's seat where the registry knows it. Named work sites are not recorded for " +
		'forest co-op contracts.';
</script>

<svelte:head>
	<title>{c.title ?? c.reference_number} — ΔΑΣΕ</title>
	<meta property="og:title" content={c.title ?? c.reference_number} />
	<meta
		property="og:description"
		content="ΔΑΣΕ contract {c.reference_number}: {eurShort(
			c.total_cost_without_vat ?? 0
		)} stated (excl. VAT)"
	/>
</svelte:head>

<p class="crumb"><a href="/dase/contracts">← ΔΑΣΕ contracts</a></p>

{#if c.duplicate_of}
	<div class="dupbanner">
		<strong>Registry double-posting.</strong> This ΑΔΑΜ is a second upload of the same signed
		document and is excluded from every calculation — the counted posting is
		<a href={`/dase/contract/${c.duplicate_of}`} class="tabular">{c.duplicate_of}</a>.
	</div>
{:else if outOfScope}
	<!-- a valid, uncancelled contract that simply is not a co-op contract:
	     the registry listed a co-op among its contractors, the signed PDF
	     names someone else. Saying «cancelled» here would be a lie. -->
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
		{#each c.duplicates as dref, i (dref)}{i ? ', ' : ''}<a
				href={`/dase/contract/${dref}`}
				class="tabular">{dref}</a
			>{/each}
		— duplicate upload{c.duplicates.length > 1 ? 's' : ''}, excluded from the calculations.
	</p>
{/if}

<FactsHeader caveat={CAVEAT}>
	{#snippet facts()}
		<dt class="id">Contract (ΑΔΑΜ)</dt>
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
			{#if c.contractors.some((x) => x.display_el)}
				<br /><small class="muted"
					>in the registry: {c.contractors.map((x) => x.name).join(', ')}</small
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

		</dd>
		<dt>Type</dt>
		<dd>{c.contract_type ?? '—'}</dd>
		<dt>Awarding unit</dt>
		<dd>
			<span title={devGreek(c.units_operator_name)}>{bodyEn(c.units_operator_name) || '—'}</span>
			<br /><small class="muted" title={devGreek(c.organization_name)}
				>{orgEn(c.organization_name)}</small
			>
		</dd>
		<dt class="gap"></dt>
		<dd class="gap"></dd>
		<dt>Work region</dt>
		<dd>{pe ? ruLabel(pe) : '—'}</dd>
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
						>· previous <a class="tabular" href={`/dase/contract/${c.prev_reference_no}`}
							>{c.prev_reference_no}</a
						></small
					>
				{/if}
				{#if c.next_reference_no}
					<small class="muted"
						>· next <a class="tabular" href={`/dase/contract/${c.next_reference_no}`}
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
			{#if outOfScope}
				outside the dataset
				<small class="muted">— no forest co-operative is a party to this contract</small>
			{:else if c.cancelled}
				cancelled
			{:else}
				no completion record trackable
				<small class="muted"
					>— municipal awarders publish no citable completion acts (methodology)</small
				>
			{/if}
		</dd>
	{/snippet}
	{#snippet map()}
		<div class="detailmap">
			<PaperMap
				interactive={false}
				colorOf={(p) => (p === pe ? 'color-mix(in srgb, var(--c-dase) 30%, #fff)' : '#fff')}
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
						/>
					{/if}
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

<DocTrail rows={trailRows} />
{#if !timeline.length}
	<p class="muted">
		ΚΗΜΔΗΣ links no upstream acts to this contract — the registry's chain returns none.
	</p>
{/if}

{#if timeline.length > 1}
	<section class="tplsec">
		<h2>Procurement family</h2>
		<p class="muted">
			The full ΚΗΜΔΗΣ family — αίτημα → πρόσκληση → κατακύρωση → συμβάσεις. This contract's
			trail is drawn in green; grey boxes are sibling acts of the same procedure. An award
			connects to a contract only when it names that contract's co-op.
		</p>
		<FamilyTree
			acts={timeline}
			kindLabel={TREE_KIND}
			payments={live.length ? { n: live.length, eur: eurShort(c.paid_without_vat ?? 0) } : null}
		/>
	</section>
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
		<div><dt>Registry type</dt><dd>{c.contract_type ?? '—'}</dd></div>
		<div><dt>Legal framework</dt><dd>{c.legal_context ?? '—'}</dd></div>
		<div><dt>Bids</dt><dd>{c.bids_submitted ?? '—'}</dd></div>
	</dl>
	{#if c.objects.length}
		<h3>Items</h3>
		{#each c.objects as o, i (i)}
			<p class="muted">
				<small>
					{#if o.quantity}{o.quantity} {o.unit_type ?? ''} ·{/if}
					{#if o.cost_without_vat}{eurShort(o.cost_without_vat)} net ·{/if}
					{o.short_description ?? ''}
				</small>
			</p>
		{/each}
	{/if}
	{#if c.cpvs.length}
		<h3>CPV</h3>
		<ul>
			{#each c.cpvs as cpv, i (i)}
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
	{/if}
</section>

{#if c.payments.length}
	<section class="tplsec" id="payments">
		<h2>Payment orders</h2>
		<table>
			<thead>
				<tr
					><th>date</th><th>order</th><th class="num">amount (net)</th><th></th></tr
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
						<td>
							<a href={`/pdf/payment/${p.payment_ref}`} target="_blank" rel="noopener">PDF</a>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
		<p class="muted">
			<small
				>{grInt(live.length)} live orders{c.paid_without_vat !== null
					? ` · ${eurShort(c.paid_without_vat)} paid net`
					: ''}</small
			>
		</p>
	</section>
{/if}

<QuoteList {quotes} />

<style>
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
	.pdf {
		font-weight: 700;
	}
</style>
