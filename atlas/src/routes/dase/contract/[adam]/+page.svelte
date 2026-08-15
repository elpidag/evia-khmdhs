<script lang="ts">
	import FamilyTree from '$lib/charts/FamilyTree.svelte';
	import KpiRow from '$lib/ui/KpiRow.svelte';
	import StatPair from '$lib/ui/StatPair.svelte';
	import { eur, eurShort } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const c = $derived(data.c);
	const live = $derived(c.payments.filter((p) => !p.cancelled));

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
		if (!c.timeline?.length) return [];
		const rows = c.timeline.map((t) => ({ ...t, self: false }));
		rows.push({
			adam: c.reference_number,
			kind: 'contract' as const,
			title: c.title,
			d: (c.contract_signed_date ?? '').slice(0, 10) || null,
			cancelled: c.cancelled ?? 0,
			in_db: true,
			who: c.contractors[0]?.name ?? null,
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

<hgroup>
	<h1>{c.title ?? c.reference_number}</h1>
	<p class="muted tabular">
		ADAM {c.reference_number} · signed {(c.contract_signed_date ?? '—').slice(0, 10)} ·
		forest-cooperative dataset
		{#if c.cancelled}<span class="chip bad">cancelled</span>{/if}
		{#if c.bids_submitted === 1}<span class="chip warn">single bidder</span>{/if}
	</p>
</hgroup>

{#if c.duplicate_of}
	<div class="dupbanner">
		<strong>Registry double-posting.</strong> This ΑΔΑΜ is a second upload of the same signed
		document and is excluded from every calculation — the counted posting is
		<a href={`/dase/contract/${c.duplicate_of}`} class="tabular">{c.duplicate_of}</a>.
	</div>
{/if}
{#if c.duplicates?.length}
	<p class="muted dupnote">
		Also posted in the registry as
		{#each c.duplicates as dref, i (dref)}{i ? ', ' : ''}<a
				href={`/dase/contract/${dref}`}
				class="tabular">{dref}</a>{/each}
		— duplicate upload{c.duplicates.length > 1 ? 's' : ''}, excluded from the calculations.
	</p>
{/if}

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
		color="var(--c-dase)"
	/>
	<StatPair
		value={live.length ? String(live.length) : '—'}
		label="payment orders"
		compare={c.paid_without_vat !== null
			? `${eurShort(c.paid_without_vat)} paid net`
			: 'none in the registry chain'}
	/>
	<StatPair
		value={c.contract_duration ? `${c.contract_duration} ${c.contract_duration_unit ?? ''}` : '—'}
		label="duration"
		compare="{(c.start_date ?? '—').slice(0, 10)} → {(c.end_date ?? 'open').slice(0, 10)}"
	/>
	<StatPair value={c.procedure_type ?? '—'} label="procedure" />
</KpiRow>

{#if live.length}
	<section id="payments">
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
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</section>
{/if}

<section>
	<h2>Contractors ({c.contractors.length})</h2>
	<table>
		<tbody>
			{#each c.contractors as ct (ct.vat_number)}
				<tr>
					<td><a href={`/dase/coop/${ct.vat_number}`}>{ct.name}</a></td>
					<td class="tabular muted">{ct.vat_number}</td>
				</tr>
			{/each}
		</tbody>
	</table>
</section>

<section>
	<h2>Procurement record</h2>
	<dl class="facts">
		<div><dt>Authority</dt><dd>{c.organization_name ?? '—'}</dd></div>
		<div><dt>Operating unit</dt><dd>{c.units_operator_name ?? '—'}</dd></div>
		<div><dt>Signer</dt><dd>{c.signer_name ?? '—'}</dd></div>
		<div><dt>Type</dt><dd>{c.contract_type ?? '—'}</dd></div>
		<div><dt>Legal framework</dt><dd>{c.legal_context ?? '—'}</dd></div>
		<div><dt>Funding</dt><dd>{c.public_funding_ref ?? '—'}</dd></div>
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
					{#if cpv.cpv_code === '66519300-4'}<span class="chip warn">registry keying noise</span
						>{/if}
				</li>
			{/each}
		</ul>
	{/if}
</section>

<section>
	{#if timeline.length}
		<h2>Procurement timeline ({timeline.length} acts)</h2>
		<p class="muted">
			The contract's full ΚΗΜΔΗΣ family — αίτημα → πρόσκληση → κατακύρωση → συμβάσεις. This
			contract's trail is drawn in green; grey boxes are the sibling acts of the same
			procedure. An award connects to a contract only when it names that contract's co-op;
			payment orders are listed above. Every box opens its act.
		</p>
		<FamilyTree
			acts={timeline}
			kindLabel={TIMELINE_KIND}
			payments={live.length
				? { n: live.length, eur: eurShort(c.paid_without_vat ?? 0) }
				: null}
		/>
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
									<a href={`/dase/contract/${t.adam}`}>{t.title ?? t.adam}</a>
								{:else}
									{t.title ?? '—'}
									{#if t.kind === 'contract'}<span class="muted">(εκτός dataset)</span>{/if}
								{/if}
								{#if t.cancelled === 1}<span class="chip bad">cancelled</span>{/if}
								{#if t.kind === 'completion' && t.end_excerpt}
									<blockquote class="excerpt">«{t.end_excerpt}»</blockquote>
								{/if}
							</small>
						</td>
						<td class="nowrap">
							{#if t.kind === 'completion'}
								<a href={`/pdf/diavgeia/${t.adam}`} target="_blank" rel="noopener">📄 PDF</a>
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
			registry's chain returns none.
		</p>
	{/if}
</section>

{#if c.notice_reference_number || c.prev_reference_no || c.next_reference_no}
	<section>
		<h2>Related acts</h2>
		<ul>
			{#if c.notice_reference_number}
				<li>Tender notice: <span class="tabular">{c.notice_reference_number}</span></li>
			{/if}
			{#if c.prev_reference_no}
				<li>
					Previous version:
					<a class="tabular" href={`/dase/contract/${c.prev_reference_no}`}>{c.prev_reference_no}</a>
				</li>
			{/if}
			{#if c.next_reference_no}
				<li>
					Next version:
					<a class="tabular" href={`/dase/contract/${c.next_reference_no}`}>{c.next_reference_no}</a>
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
	.dupbanner {
		background: color-mix(in srgb, var(--c-dase) 12%, #fff);
		border: 1.5px solid var(--c-dase);
		border-radius: 8px;
		padding: var(--sp-3) var(--sp-4);
		margin: var(--sp-3) 0;
		max-width: var(--prose-w);
	}
	.dupnote {
		margin: var(--sp-2) 0;
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
	.muted {
		color: var(--ink-soft);
	}
	td a {
		text-decoration: none;
	}
	td a:hover {
		text-decoration: underline;
	}
	tr.dead {
		opacity: 0.55;
	}
	.chip.hl {
		background: var(--c-dase);
		color: #fff;
		border-color: var(--c-dase);
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
		background: color-mix(in srgb, var(--c-dase) 7%, transparent);
	}
	tr.cancelled {
		opacity: 0.55;
	}
	.nowrap {
		white-space: nowrap;
	}
</style>
