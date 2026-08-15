<script lang="ts">
	import { peEn, ruLabel } from '$lib/transforms/regions';
	import KpiRow from '$lib/ui/KpiRow.svelte';
	import StatPair from '$lib/ui/StatPair.svelte';
	import { eur, eurShort, grInt } from '$lib/transforms/format';
	import { scopeLabel } from '$lib/transforms/scopes';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const c = $derived(data.c);
	const live = $derived(c.payments.filter((p) => !p.cancelled));
	// category evidence provenance: the parent ADAM when the title was
	// inherited from a previous version's PDF
	const catSrcRef = $derived(
		c.category?.source.startsWith('inherited:') ? c.category.source.slice(10) : null
	);

	const TIMELINE_KIND: Record<string, string> = {
		request: 'Πρωτογενές αίτημα',
		approved_request: 'Ανάληψη υποχρέωσης',
		notice: 'Διακήρυξη / πρόσκληση',
		auction: 'Κατακύρωση / ανάθεση',
		contract: 'Σύμβαση',
		completion: 'Ολοκλήρωση'
	};
	const CKIND_LABEL: Record<string, string> = {
		oristiki_paralavi: 'Οριστική παραλαβή',
		paralavi: 'Πρωτόκολλο παραλαβής',
		peraiosi: 'Βεβαίωση περαίωσης',
		oloklirosi: 'Διαπιστωτική ολοκλήρωσης'
	};
	const TIMELINE_ORDER: Record<string, number> = {
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
			in_db: true,
			self: true
		});
		rows.sort((a, b) =>
			`${a.d ?? '9999'}${TIMELINE_ORDER[a.kind]}`.localeCompare(
				`${b.d ?? '9999'}${TIMELINE_ORDER[b.kind]}`
			)
		);
		return rows;
	});
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

<hgroup>
	<h1>{c.title ?? c.reference_number}</h1>
	<p class="muted tabular">
		ADAM {c.reference_number} · signed {(c.contract_signed_date ?? '—').slice(0, 10)}
		{#if c.scope}· <span class="chip">{scopeLabel(c.scope.scope)}</span>
			{#if !c.scope.in_scope}<span class="chip bad">out of scope</span>{/if}
		{/if}
		{#if c.category}<span class="chip cat" title={c.category.note ?? ''}>{c.category.label}</span>{/if}
		{#if c.cancelled}<span class="chip bad">cancelled</span>{/if}
		{#if c.bids_submitted === 1}<span class="chip warn">single bidder</span>{/if}
	</p>
</hgroup>

<p>
	<a class="pdf" href={`/pdf/contract/${c.reference_number}`} target="_blank" rel="noopener">
		📄 View the signed contract PDF
	</a>
	<small class="muted">fetched from KHMDHS once, then served from the local cache</small>
</p>

<KpiRow>
	<StatPair
		value={eurShort(c.total_cost_without_vat ?? 0)}
		label="stated value (excl. VAT)"
		compare={c.gross?.stated_gross ? `${eurShort(c.gross.stated_gross)} incl. ΦΠΑ` : ''}
		basis="the analytic basis across the site"
		color="var(--c-antinero)"
	/>
	<StatPair
		value={String(live.length)}
		label="payment orders"
		compare={c.paid_without_vat !== null
			? `${eurShort(c.paid_without_vat)} paid net${
					c.gross?.paid_gross ? ` · ${eurShort(c.gross.paid_gross)} incl. ΦΠΑ` : ''
				}`
			: 'none recorded'}
	/>
	<StatPair
		value={c.contract_duration ? `${c.contract_duration} ${c.contract_duration_unit ?? ''}` : '—'}
		label="duration"
		compare="{(c.start_date ?? '—').slice(0, 10)} → {(c.end_date ?? 'open').slice(0, 10)}"
	/>
</KpiRow>

{#if c.category}
	<section>
		<h2>Type of work</h2>
		<p>
			<span class="chip cat">{c.category.label}</span>
			{#if c.category.note}<small class="muted">{c.category.note}</small>{/if}
		</p>
		<blockquote class="excerpt">«{c.category.title}»</blockquote>
		<p class="muted">
			<small>
				The project title above is the classification evidence —
				{#if catSrcRef}
					stated in the signed PDF of the contract's previous version
					<a class="tabular" href={`/antinero/contract/${catSrcRef}`}>{catSrcRef}</a>
					(<a href={`/pdf/contract/${catSrcRef}`} target="_blank" rel="noopener">PDF</a>);
					this record's own document quotes only the parties or the amendment object.
				{:else}
					stated verbatim in this contract's signed PDF.
				{/if}
				One curated category per contract; see the
				<a href="/methodology#categories">methodology</a>.
			</small>
		</p>
	</section>
{/if}

<section>
	<h2>Contractors ({c.contractors.length})</h2>
	<table>
		<tbody>
			{#each c.contractors as ct (ct.vat_number)}
				<tr>
					<td><a href={`/antinero/contractor/${ct.vat_number}`}>{ct.name}</a></td>
					<td class="tabular muted">{ct.vat_number}</td>
					<td class="muted">{ct.country ?? ''}</td>
				</tr>
			{/each}
		</tbody>
	</table>
	{#if c.contractors.length > 1}
		<p class="muted"><small>Consortium — each partner is credited the full value in per-contractor views.</small></p>
	{/if}
</section>

{#if live.length}
	<section>
		<h2>Payment orders</h2>
		<table>
			<thead>
				<tr
					><th>Date</th><th>Order</th><th class="num">Amount (net)</th><th class="num"
						>incl. ΦΠΑ</th
					><th></th></tr
				>
			</thead>
			<tbody>
				{#each c.payments as p (p.payment_ref)}
					<tr class:dead={p.cancelled === 1}>
						<td class="tabular muted">{(p.signed_date ?? '—').slice(0, 10)}</td>
						<td>
							<span class="tabular">{p.payment_ref}</span>
							{#if p.credit}<span class="chip">credit</span>{/if}
							{#if p.cancelled}<span class="chip bad">cancelled</span>{/if}
							{#if p.correction_note}<span class="chip warn" title={p.correction_note}>corrected</span>{/if}
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
								· <a href={`https://diavgeia.gov.gr/decision/view/${p.ada}`} target="_blank" rel="noopener">Διαύγεια</a>
							{/if}
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</section>
{/if}

<section>
	<h2>Where the work is</h2>
	{#if c.regions.length}
		<p>
			{#each c.regions as r, i (i)}{#if i}, {/if}{ruLabel(r.region_pe)}{/each}
		</p>
	{:else}
		<p class="muted">No curated project regions.</p>
	{/if}
	{#if c.sites.length}
		<table>
			<thead><tr><th>Named site</th><th>R.U.</th><th>Evidence</th></tr></thead>
			<tbody>
				{#each c.sites as s, i (i)}
					<tr>
						<td>{s.site_name}</td>
						<td>{peEn(s.region_pe)}</td>
						<td class="muted"><small>PDF p.{s.page}{s.excerpt ? ` — «${s.excerpt}»` : ''}</small></td>
					</tr>
				{/each}
			</tbody>
		</table>
	{/if}
</section>

<section>
	<h2>Procurement record</h2>
	<dl class="facts">
		<div><dt>Authority</dt><dd>{c.organization_name ?? '—'}</dd></div>
		<div><dt>Operating unit</dt><dd>{c.units_operator_name ?? '—'}</dd></div>
		<div><dt>Signer</dt><dd>{c.signer_name ?? '—'}</dd></div>
		<div><dt>Procedure</dt><dd>{c.procedure_type ?? '—'}</dd></div>
		<div><dt>Award basis</dt><dd>{c.award_procedure ?? '—'}</dd></div>
		<div><dt>Type</dt><dd>{c.contract_type ?? '—'}</dd></div>
		<div><dt>Legal framework</dt><dd>{c.legal_context ?? '—'}</dd></div>
		<div><dt>Funding</dt><dd>{c.public_funding_ref ?? '—'}</dd></div>
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
</section>

<section>
	{#if timeline.length}
		<h2>Procurement timeline ({timeline.length} acts)</h2>
		<p class="muted">
			The contract's full ΚΗΜΔΗΣ family — αίτημα → πρόσκληση → κατακύρωση → συμβάσεις,
			chronological. Payment orders are listed above.
		</p>
		<table class="listing">
			<thead>
				<tr><th>Date</th><th>Act</th><th>Title</th><th>PDF</th></tr>
			</thead>
			<tbody>
				{#each timeline as t (t.adam)}
					<tr class:cancelled={t.cancelled === 1} class:self={t.self}>
						<td class="tabular muted">{t.d ?? '—'}</td>
						<td>
							<span
								class="chip"
								class:hl={t.kind === 'auction' || t.self}
								class:ok={t.kind === 'completion'}
								>{t.kind === 'completion'
									? (CKIND_LABEL[t.ckind ?? ''] ?? TIMELINE_KIND.completion)
									: (TIMELINE_KIND[t.kind] ?? t.kind)}</span
							>
							<br /><small class="tabular muted">{t.adam}</small>
						</td>
						<td>
							<small>
								{#if t.self}
									<strong>this contract</strong>
								{:else if t.kind === 'contract' && t.in_db}
									<a href={`/antinero/contract/${t.adam}`}>{t.title ?? t.adam}</a>
								{:else}
									{t.title ?? '—'}
									{#if t.kind === 'contract'}<span class="muted">(εκτός dataset)</span>{/if}
								{/if}
								{#if t.cancelled === 1}<span class="chip bad">cancelled</span>{/if}
								{#if t.kind === 'completion' && t.end_excerpt}
									<blockquote class="excerpt">«{t.end_excerpt}»</blockquote>
								{:else if t.kind === 'completion' && t.end_basis === 'act_date'}
									<br /><span class="muted">(ημερομηνία πράξης — το πρωτόκολλο δεν χρονολογείται στο κείμενο)</span>
								{/if}
							</small>
						</td>
						<td class="nowrap">
							{#if t.kind === 'completion'}
								<a href={`/pdf/diavgeia/${t.adam}`} target="_blank" rel="noopener">📄 PDF</a>
								<br /><a
									class="ext"
									href={`https://diavgeia.gov.gr/decision/view/${t.adam}`}
									target="_blank"
									rel="noopener"><small>Diavgeia ↗</small></a
								>
							{:else if t.kind !== 'contract'}
								<a
									href={`/pdf/${t.kind === 'approved_request' ? 'request' : t.kind}/${t.adam}`}
									target="_blank"
									rel="noopener">📄 PDF</a
								>
							{:else if t.in_db}
								<a href={`/pdf/contract/${t.adam}`} target="_blank" rel="noopener">📄 PDF</a>
							{/if}
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	{:else}
		<h2>Procurement timeline</h2>
		<p class="muted">
			ΚΗΜΔΗΣ links no upstream acts (αίτημα, διακήρυξη, κατακύρωση) to this contract — the
			registry's chain returns none, a linkage gap common across the programme's direct
			awards.
		</p>
	{/if}
</section>

{#if c.prev_reference_no || c.next_reference_no || c.scope?.superseded_by || c.notice_reference_number}
	<section>
		<h2>Amendment chain</h2>
		<ul>
			{#if c.notice_reference_number}
				<li>Tender notice: <span class="tabular">{c.notice_reference_number}</span></li>
			{/if}
			{#if c.prev_reference_no}
				<li>
					Previous version:
					<a class="tabular" href={`/antinero/contract/${c.prev_reference_no}`}>{c.prev_reference_no}</a>
				</li>
			{/if}
			{#if c.next_reference_no}
				<li>
					Next version:
					<a class="tabular" href={`/antinero/contract/${c.next_reference_no}`}>{c.next_reference_no}</a>
				</li>
			{/if}
			{#if c.scope?.superseded_by && c.scope.superseded_by !== c.next_reference_no}
				<li>
					Superseded by:
					<a class="tabular" href={`/antinero/contract/${c.scope.superseded_by}`}>{c.scope.superseded_by}</a>
				</li>
			{/if}
		</ul>
	</section>
{/if}

<style>
	.crumb a {
		text-decoration: none;
		color: var(--ink-soft);
	}
	section {
		margin-bottom: var(--sp-8);
	}
	.pdf {
		font-weight: 600;
	}
	.facts {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
		gap: var(--sp-2) var(--sp-6);
		margin: 0;
	}
	.facts dt {
		font-size: var(--fs-12);
		color: var(--ink-faint);
	}
	.facts dd {
		margin: 0 0 var(--sp-2);
		font-size: var(--fs-14);
	}
	tr.dead {
		opacity: 0.55;
	}
	.muted {
		color: var(--ink-soft);
	}
	td a {
		text-decoration: none;
	}
	td a:hover {
		text-decoration: underline;
	}
	.chip.hl {
		background: var(--c-antinero);
		color: #fff;
		border-color: var(--c-antinero);
	}
	.chip.cat {
		background: var(--paper-2);
		border-color: var(--ink);
		color: var(--ink);
		font-weight: 600;
	}
	.chip.ok {
		background: var(--c-anadohoi);
		color: #fff;
		border-color: var(--c-anadohoi);
	}
	.excerpt {
		margin: var(--sp-1) 0 0;
		padding-left: var(--sp-2);
		border-left: 2px solid var(--line-strong);
		color: var(--ink-soft);
		font-style: italic;
	}
	tr.self {
		background: color-mix(in srgb, var(--c-antinero) 7%, transparent);
	}
	tr.cancelled {
		opacity: 0.55;
	}
	.nowrap {
		white-space: nowrap;
	}
</style>
