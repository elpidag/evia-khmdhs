<script lang="ts">
	import { authEn, bodyEn, devGreek, orgEn } from '$lib/transforms/names';
	import { ruLabel } from '$lib/transforms/regions';
	import FactsHeader from '$lib/detail/FactsHeader.svelte';
	import DocTrail, { type TrailRow } from '$lib/detail/DocTrail.svelte';
	import { trailChip } from '$lib/transforms/exclusion';
	import QuoteList, { type Quote } from '$lib/detail/QuoteList.svelte';
	import ChainTimeline from '$lib/detail/ChainTimeline.svelte';
	import Fold from '$lib/ui/Fold.svelte';
	import ProcurementFamily from '$lib/charts/ProcurementFamily.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import { dmy, eur, eurShort, grInt } from '$lib/transforms/format';
	import { scopeLabel } from '$lib/transforms/scopes';
	import { loadMunicipalities, type MuniProps } from '$lib/maps/useGeo';
	import type { FeatureCollection } from 'geojson';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const c = $derived(data.c);
	const live = $derived(c.payments.filter((p) => !p.cancelled));

	/** the registry's date formats ('03/11/2023', '2026-07-24T00:00:00') —
	 *  the API normalises the trail's, but payment dates arrive raw */
	const iso = (v: string | null | undefined): string | null => {
		if (!v) return null;
		const s = v.trim();
		if (s.length >= 10 && s[2] === '/' && s[5] === '/')
			return `${s.slice(6, 10)}-${s.slice(3, 5)}-${s.slice(0, 2)}`;
		if (s.length >= 10 && s[4] === '-' && s[7] === '-') return s.slice(0, 10);
		return null;
	};
	const todayIso = new Date().toLocaleDateString('en-CA');
	// the header slot shows one of two things; the map is the default
	const hasFamily = $derived(!!c.family && c.family.contracts.length > 1);
	let view = $state<'map' | 'family'>('map');
	let cpvAll = $state(false);
	// hover binds the timeline's act dots to the trail's rows, both ways
	let hoverAct = $state<string | null>(null);
	let hoverRow = $state<string | null>(null);
	const chain = $derived(c.chain ?? []);
	const payTicks = $derived(
		live.map((p) => ({
			ref: p.payment_ref,
			// `d` is resolved server-side (signed_date, else the submission
			// stamp — 182 of 886 orders carry only the latter)
			d: p.d ?? iso(p.signed_date),
			eur: p.amount_without_vat
		}))
	);
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
		const rows = c.timeline.map((t) => ({ ...t, self: false }));
		// the contract's own later records — τροποποιήσεις, παρατάσεις,
		// εγκρίσεις συμπληρωματικών. The registry's adamChain rarely links
		// them, so without this the trail shows a contract whose amendments
		// exist on the site but nowhere on its own page
		const seen = new Set(rows.map((t) => t.adam));
		for (const a of chain) {
			if (a.self || seen.has(a.ref)) continue;
			seen.add(a.ref);
			rows.push({
				adam: a.ref,
				kind: 'contract' as const,
				title: a.title,
				d: a.d,
				cancelled: 0,
				doc_kind: a.kind,
				duplicate_of: null,
				related_to: null,
				in_db: true,
				self: false
			});
		}
		if (!rows.length) return [];
		rows.push({
			adam: c.reference_number,
			kind: 'contract' as const,
			title: c.title,
			// the viewed document's OWN date, not the contract's, which ΚΗΜΔΗΣ
			// copies onto every act posted against it
			d: c.own_date ?? ((c.contract_signed_date ?? '').slice(0, 10) || null),
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
	/** the acts that produced the contract — request, commitment approval,
	 *  call, award — wherever the trail has them dated (user, 2026-08-19) */
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
		if (t.kind === 'completion') return `/pdf/diavgeia/${t.adam}`;
		if (t.kind !== 'contract')
			return `/pdf/${t.kind === 'approved_request' ? 'request' : t.kind}/${t.adam}`;
		return t.in_db ? `/pdf/contract/${t.adam}` : null;
	};
	/**
	 * The payment orders belong in the trail (user, 2026-08-19): they are
	 * documents of this contract with a date, a code and a PDF, and reading
	 * them in a separate table meant reading the contract's story twice. The
	 * amount rides in the title cell, where the other rows carry their title,
	 * and the Διαύγεια act keeps its own link.
	 */
	const payRows = $derived<TrailRow[]>(
		c.payments.map((p) => ({
			d: p.d ?? iso(p.signed_date),
			type: 'Payment order',
			code: p.payment_ref,
			title: eur(p.amount_without_vat ?? p.amount_with_vat),
			pdf: `/pdf/payment/${p.payment_ref}`,
			alt: p.ada
				? { href: `https://diavgeia.gov.gr/decision/view/${p.ada}`, label: 'Διαύγεια' }
				: null,
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
		].sort((a, b) => `${a.d ?? '9999'}`.localeCompare(`${b.d ?? '9999'}`))
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

	// the record the deadline was read from, and what a later act did to it
	const dlFields = $derived(
		c.deadlines?.fields ?? {
			ref: c.reference_number,
			duration: c.contract_duration,
			unit: c.contract_duration_unit,
			start_date: iso(c.start_date),
			end_date: iso(c.end_date)
		}
	);
	const extNote = $derived(
		c.deadlines?.extensions?.length
			? `, extended to ${dmy(c.deadlines.extensions[c.deadlines.extensions.length - 1].deadline)} by ${c.deadlines.extensions.map((e) => e.ref).join(', ')}`
			: ''
	);

	/** the δήμοι the documents place the works in, one level finer than the
	 *  Π.Ε. layer; `outside_region` marks a δήμος whose Π.Ε. we never curated
	 *  for this contract — recorded as the document states it (2026-08-19) */
	const munis = $derived(c.municipalities ?? []);
	let muniLayer = $state.raw<FeatureCollection<
		GeoJSON.MultiPolygon | GeoJSON.Polygon,
		MuniProps
	> | null>(null);
	$effect(() => {
		if (munis.length && !muniLayer) loadMunicipalities(fetch).then((fc) => (muniLayer = fc));
	});
	const muniShapes = $derived.by(() => {
		if (!muniLayer) return [];
		const want = new Set(munis.map((m) => m.code));
		return muniLayer.features.filter((f) => want.has(f.properties.code));
	});
	const regionLine = $derived(
		c.regions.length ? c.regions.map((r) => ruLabel(r.region_pe)).join(', ') : ''
	);
	/** which document named them — the contract itself, or the call it cites */
	const muniSource = $derived.by(() => {
		if (!munis.length) return '';
		const calls = [...new Set(munis.map((m) => m.from_call).filter(Boolean))];
		if (calls.length && munis.every((m) => m.from_call))
			return `as named in the call ${calls.join(', ')}`;
		return calls.length ? 'as named in the contract and its call' : 'as named in the contract';
	});

	const themes = $derived(c.work_themes?.themes ?? []);
	const cpvNotes = $derived(c.work_themes?.cpv_notes ?? []);

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
		// WHERE the δήμοι come from — one quote per distinct sentence, since
		// one sentence usually names several («εντός των Δήμων Χαϊδαρίου και
		// Ασπροπύργου, αρμοδιότητας Δασαρχείου Αιγάλεω»)
		...[...new Map(munis.map((m) => [m.excerpt, m])).values()].map((m) => ({
			label: `Areas of intervention — ${munis
				.filter((x) => x.excerpt === m.excerpt)
				.map((x) => `Δήμος ${x.name}`)
				.join(', ')}`,
			text: m.excerpt,
			code: m.source_ref,
			href: `/pdf/${m.from_call ? 'notice' : 'contract'}/${m.source_ref}`,
			note:
				(m.from_call ? 'Named in the call this contract was awarded under. ' : '') +
				(munis.some((x) => x.excerpt === m.excerpt && x.outside_region)
					? 'A municipality here lies outside the regional units curated for this contract and no forest-service jurisdiction accounts for it; the document is recorded as it stands and the region layer is unchanged.'
					: '')
		})),
		// WHERE the jurisdiction row got its services. Most contracts name them
		// in their own title or object list; some are named only by the
		// Diavgeia act that accepted the works — and one of those acts accepts
		// a single PART of the works, which is not a whole jurisdiction
		// (26SYMV018978343; DATA_DECISIONS 2026-08-19)
		...(c.authorities ?? [])
			.filter((a) => a.excerpt && (a.source ?? '').startsWith('completion_act'))
			.map((a) => {
				const ada = (a.source ?? '').slice('completion_act:'.length).replace('|part', '');
				const part = (a.source ?? '').endsWith('|part');
				return {
					label: `Area within the jurisdiction of — ${authEn(a.name)}`,
					text: a.excerpt as string,
					code: ada,
					href: `/pdf/diavgeia/${ada}`,
					note:
						'The contract itself names no forest service. This is the acceptance act that names one' +
						(part
							? ' — and it accepts only the part of the works quoted here, so it does not describe the whole contract.'
							: '.')
				};
			}),
		// WHERE the type chips come from: the contract's own project title,
		// one quoted clause per theme (user, 2026-08-19)
		...themes.map((t) => ({
			label: `Type of work — ${t.en}`,
			text: t.excerpt,
			code: c.work_themes?.source?.startsWith('inherited:')
				? c.work_themes.source.slice(10)
				: c.reference_number,
			href: `/pdf/contract/${
				c.work_themes?.source?.startsWith('inherited:')
					? c.work_themes.source.slice(10)
					: c.reference_number
			}`,
			note: null
		})),
		// WHERE the duration comes from: the contract's own sentence, with
		// the ΚΗΜΔΗΣ field named beside it where it disagrees
		...(c.stated_duration?.excerpt
			? [
					{
						label: 'Duration — as the contract states it',
						text: c.stated_duration.excerpt,
						code: c.stated_duration.source_ref,
						href: `/pdf/contract/${c.stated_duration.source_ref}`,
						note:
							(c.stated_duration.registry_n
								? `ΚΗΜΔΗΣ records ${c.stated_duration.registry_n}${c.stated_duration.registry_unit ? ` ${c.stated_duration.registry_unit}` : ' with no unit'}; the figure shown above is the one the signed text states. `
								: 'The ΚΗΜΔΗΣ record states no duration for this contract. ') +
							(c.stated_duration.source_ref !== c.reference_number
								? `Read from ${c.stated_duration.source_ref}, the σύμβαση this record amends.`
								: '')
					}
				]
			: []),
		...(c.stated_duration?.fire_season
			? [
					{
						label: 'Duration — a season, not a number of months',
						text: `Αντιπυρική Περίοδος: Είναι η αντιπυρική περίοδος του έτους ${c.stated_duration.fire_season}, όπως αυτή εκάστοτε καθορίζεται`,
						code: c.stated_duration.source_ref,
						href: `/pdf/contract/${c.stated_duration.source_ref}`,
						note: 'Greece’s fire season runs 1 May to 31 October, so the works had until 31.10 of that year.'
					}
				]
			: []),
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

	/**
	 * DURATION — the contract's own sentence, with the ΚΗΜΔΗΣ field beside
	 * it (user decision, 2026-08-19). The documents state a deadline for 243
	 * of 246 in-scope contracts and the start basis for all 243; the registry
	 * has a number for 83, never says what it counts from, and agrees with
	 * the signed text in 3 of the 65 cases where both exist. Three contracts
	 * answer with a season instead — Greece's fire season is 1 May to 31
	 * October, so «the fire season of 2024» IS a deadline.
	 */
	const BASIS_EN: Record<string, string> = {
		signature: 'from signature',
		works_start: 'from the start of works',
		publication: 'from publication',
		protocol: 'from the installation protocol'
	};
	const UNIT_EN: Record<string, string> = { months: 'month', days: 'day', years: 'year' };
	const duration = $derived.by(() => {
		const d = c.stated_duration;
		if (d?.fire_season)
			return {
				text: `the fire season of ${d.fire_season}`,
				note: 'The contract sets no number of months: its works run within the fire season, 1 May – 31 October.'
			};
		if (d?.n) {
			const unit = UNIT_EN[d.unit ?? ''] ?? d.unit ?? '';
			const reg = d.registry_n
				? ` ΚΗΜΔΗΣ records ${d.registry_n}${d.registry_unit ? ` ${d.registry_unit}` : ' (no unit)'}.`
				: '';
			return {
				text: `${d.n} ${unit}${d.n === 1 ? '' : 's'} ${BASIS_EN[d.basis ?? ''] ?? ''}`.trim(),
				note: `As stated in the signed contract${d.source_ref !== c.reference_number ? ` ${d.source_ref}` : ''}.${reg}`
			};
		}
		// nothing curated for this record (a contract added since the last run)
		const n = c.contract_duration;
		if (!n) return { text: '—', note: null };
		const u = (c.contract_duration_unit ?? '').toUpperCase();
		const m = u.startsWith('ΗΜΕΡ') ? Math.round((n / 30.44) * 10) / 10 : n;
		return {
			text: `${m} month${m === 1 ? '' : 's'}`,
			note: 'From the ΚΗΜΔΗΣ record; the signed text was not read for this contract.'
		};
	});

	/**
	 * What the bar means, said on the page it is drawn on (user, 2026-08-19).
	 * The wording follows THIS contract's own deadline source — never a
	 * generic sentence that would be wrong for most of them.
	 */
	const barNote = $derived.by(() => {
		const dl = c.deadlines;
		const head =
			'The bar is the time the contract was given: from signature to the deadline it announced' +
			(dl?.extensions?.length
				? ', with the lighter stretch added by ' +
					(dl.extensions.length === 1 ? 'its extension' : `its ${dl.extensions.length} extensions`)
				: '') +
			'. ✔ marks the day the works were accepted, which may fall after that deadline; € marks a payment order, and the grey dots before the signature are the procurement that produced the contract.';
		const src =
			dl?.basis === 'document'
				? ` The deadline is the one the contract itself states — ${duration.text} — which falls on ${dmy(dl.deadline)}.`
				: dl?.basis === 'document_season'
					? ` The contract sets no number of months: its works run within the fire season, 1 May – 31 October, so the deadline is ${dmy(dl.deadline)}.`
					: dl?.basis === 'end_date'
						? ` The deadline is the end date stated in the ΚΗΜΔΗΣ record (${dmy(dl.deadline)}).`
						: dl?.basis === 'duration'
							? ` The deadline is the ΚΗΜΔΗΣ duration of ${dl.duration}${dl.unit ? ` ${dl.unit}` : ''} counted from the start date (${dmy(dl.deadline)}).`
							: dl?.basis === 'act'
								? ` The σύμβαση announced no deadline; ${dmy(dl.deadline)} is the one ${dl.source_ref} set.`
								: ' No deadline is on record for this contract, so the bar is a stub and no span is drawn.';
		return head + src;
	});

	const regionSet = $derived(new Set(c.regions.map((r) => r.region_pe)));
	const seatDots = $derived((c.authorities ?? []).filter((a) => a.lat != null && a.lon != null));
	/**
	 * Frame the map on the contract's own ground rather than on Greece (user,
	 * 2026-08-19): the WHOLE of every region it highlights, plus the whole of
	 * every region an awarding authority sits in — a frame built from centres
	 * cut Εύβοια in half on 26SYMV018978343, whose Attica works are accepted
	 * by a service in Χαλκίδα. The seat points ride along so a seat outside
	 * both stays in view.
	 */
	const worksPes = $derived([
		...new Set([
			...c.regions.map((r) => r.region_pe),
			...(c.authorities ?? []).map((a) => a.region_pe).filter((v): v is string => !!v)
		])
	]);
	const worksPoints = $derived(
		seatDots.length ? (seatDots.map((a) => [a.lon!, a.lat!]) as [number, number][]) : null
	);

	const CAVEAT = $derived(
		"Areas of intervention are read from the contract's own signed documents or from the call " +
			'it cites, and quoted below. The map highlights the contract’s regional units, outlines ' +
			'the municipalities its documents name and marks the seats of the awarding forest ' +
			'authorities' +
			(munis.some((m) => m.outside_region)
				? '; one municipality here lies outside the highlighted units and no forest-service jurisdiction accounts for it — the document is recorded as it stands and the region layer is left as curated.'
				: '.')
	);
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
		<dt class="id">Contract</dt>
		<dd class="id">
			{c.reference_number}
			{#if c.scope && !c.scope.in_scope}<span class="chip bad">out of scope</span>{/if}
			{#if c.scope?.scope === 'antinero_probable'}<span class="chip warn"
					>{scopeLabel(c.scope.scope)}</span
				>{/if}
		</dd>
		<dt>Date</dt>
		<dd>
			{dmy(c.own_date ?? c.contract_signed_date) || '—'}
			{#if c.own_date_basis === 'published'}<small class="muted"
					>· posted to ΚΗΜΔΗΣ; the document states no date</small
				>{:else if c.own_date_basis === 'inherited'}<small class="muted"
					>· ΚΗΜΔΗΣ repeats the contract's own date on this act</small
				>{/if}
		</dd>
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
		<dt>Type</dt>
		<dd>
			{#if c.category}<span class="chip cat" title={c.category.note ?? ''}
					>{c.category.label}</span
				>{:else}—{/if}
			<!-- what the contract's OWN title says the works are: 101 of 246
			     name more than one kind, which one category cannot carry
			     (user, 2026-08-19) -->
			{#if themes.length}
				<div class="themes">
					{#each themes as t (t.key)}<span class="theme" title={devGreek(t.el)}
							>{t.en}</span
						>{/each}
				</div>
			{:else}
				<div class="themes muted"><small>the contract states no further detail</small></div>
			{/if}
			{#if cpvNotes.length}
				<div class="themes muted">
					<small
						>the procurement's CPV codes also cover {cpvNotes
							.map((n) => n.en.toLowerCase())
							.join(', ')}</small
					>
				</div>
			{/if}
		</dd>
		<dt>Scope</dt>
		<dd>{c.category?.key === 'meletes' ? 'study' : 'works'}</dd>
		<dt>Budget <small class="muted">(excl. VAT)</small></dt>
		<dd>
			{eurShort(c.total_cost_without_vat ?? 0)}
		</dd>
		<dt>Awarding procedure</dt>
		<dd>
			{c.procedure_type ?? '—'}
			{#if c.bids_submitted === 1}<span class="chip warn">single bidder</span>{/if}
		</dd>
		<dt>Contracting authority</dt>
		<dd><span title={devGreek(c.organization_name)}>{orgEn(c.organization_name) || '—'}</span></dd>
		<!-- the user's header, revised 2026-08-19: WHERE the works were is its
		     own row and the service responsible for them follows it -->
		<dt>Areas of intervention</dt>
		<dd>
			{#if munis.length}
				{#each munis as m, i (m.code)}
					{#if i}{', '}{/if}<span
						class:flagged={m.outside_region}
						title={m.outside_region
							? `${m.region_pe} — not among this contract's curated work regions, and nothing accounts for it`
							: m.outside_pe_explained === 'covers_pe'
								? `${m.region_pe} — outside the curated regions, but the service that names it administers that regional unit`
								: m.outside_pe_explained === 'seat'
									? `${m.region_pe} — outside the curated regions; it is the seat region of the service that names it`
									: m.outside_pe_explained === 'curated verdict'
										? `${m.region_pe} — outside the curated regions; reviewed and kept as the document states it`
										: (m.note ?? m.region_pe ?? '')}>Δήμος {m.name}</span
					>
				{/each}
				<br /><small class="muted"
					>{regionLine}{muniSource ? ` · ${muniSource}` : ''}</small
				>
			{:else}
				{regionLine || '—'}
				<br /><small class="muted">the documents name no municipality</small>
			{/if}
		</dd>
		<dt>Responsible forest service body</dt>
		<dd>
			{#if c.authorities?.length}
				{#each c.authorities as a, i (a.name)}
					{#if i}{', '}{/if}<span title={devGreek(a.name)}>{authEn(a.name)}</span>
				{/each}
				{#if c.authorities.every((a) => a.source?.startsWith('completion_act'))}
					<!-- a region-scoped «άμεσης διαχείρισης» contract names no forest
					     service at all; the only ones on record are those an
					     acceptance act happened to name, and one of those acts covers
					     a single part of the works -->
					<br /><small class="muted"
						>named by {c.authorities.some((a) => a.source?.endsWith('|part'))
							? 'an acceptance act covering one part of the works'
							: 'the acceptance acts'}; the contract itself names none</small
					>
				{/if}
			{:else}
				<span title={devGreek(c.units_operator_name)}>{bodyEn(c.units_operator_name) || '—'}</span>
			{/if}
		</dd>
		<dt>Duration</dt>
		<dd>
			{duration.text}
			{#if duration.note}<br /><small class="muted">{duration.note}</small>{/if}
		</dd>
		<dt>Amendments to original contract</dt>
		<dd>{chain.length > 1 || c.prev_reference_no || c.next_reference_no ? 'yes' : 'no'}</dd>
		<dt>Status</dt>
		<dd>
			{#if c.cancelled}
				cancelled
			{:else}
				{completion ? 'completion act found' : 'completion act not found'}
			{/if}
		</dd>
	{/snippet}
	{#snippet map()}
		{#if hasFamily}
			<!-- the header's square slot carries either view; the switch sits ON
			     the frame so it costs no vertical space (user, 2026-08-19) -->
			<div class="viewsw" role="group" aria-label="Map or procurement diagram">
				<button class="sw" class:on={view === 'map'} onclick={() => (view = 'map')}>Map</button>
				<button class="sw" class:on={view === 'family'} onclick={() => (view = 'family')}
					>Diagram</button
				>
			</div>
		{/if}
		{#if hasFamily && view === 'family'}
			<div class="famslot">
				<ProcurementFamily
					call={c.family!.call}
					contracts={c.family!.contracts}
					total={c.family!.total_eur}
					self={c.reference_number}
					amendments={c.family!.amendments}
				/>
				<p class="muted">
					<small
						>One of {c.family!.contracts.length} contracts awarded under call {c.family!.call}{c
							.family!.source.startsWith('inherited')
							? ` (cited by the version it amends, ${c.family!.source.slice(10)})`
							: ''}. Circle area ∝ stated net €.</small
					>
				</p>
			</div>
		{:else}
		<div class="detailmap">
			<PaperMap
				interactive={false}
				fitPoints={worksPoints}
				fitPes={worksPes}
				fitPad={0.26}
				colorOf={(pe) => (regionSet.has(pe) ? 'color-mix(in srgb, var(--c-antinero) 22%, #fff)' : '#fff')}
				tipOf={(pe) => `<strong>${ruLabel(pe)}</strong>`}
			>
				{#snippet overlay(ctx)}
					<!-- the δήμοι the documents name, outlined inside their region
					     (user, 2026-08-19). The layer is fetched only here, and only
					     when a contract actually names one. -->
					{#each muniShapes as f (f.properties.code)}
						<path
							d={ctx.path(f) ?? ''}
							class="munishape"
							role="img"
							aria-label={`Δήμος ${f.properties.name}`}
							onmouseenter={() => ctx.showTip(`<strong>Δήμος ${f.properties.name}</strong>`)}
							onmouseleave={() => ctx.hideTip()}
						/>
					{/each}
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
		{/if}
	{/snippet}
</FactsHeader>

<section class="plain">
	<h2>Timeline</h2>
	<ChainTimeline
		signed={chain[0]?.d ?? iso(c.own_date ?? c.contract_signed_date)}
		signedRef={chain[0]?.ref ?? c.reference_number}
		end={completion?.d ?? null}
		endRef={completion?.adam ?? null}
		deadline={c.deadlines?.deadline ?? null}
		deadlineBasis={c.deadlines?.basis ?? null}
		extensions={c.deadlines?.extensions ?? []}
		today={todayIso}
		{chain}
		payments={payTicks}
		runUp={runUpActs}
		callInfo={hasFamily
			? { ref: c.family!.call, lots: c.family!.contracts.length, total: c.family!.total_eur }
			: null}
		onCallClick={() => {
			view = 'family';
			document.querySelector('.detailmap, .famslot')?.scrollIntoView({ block: 'center' });
		}}
		highlightRef={hoverRow}
		onActHover={(ref) => (hoverAct = ref)}
	/>
	<p class="tlnote">{barNote} <a href="/methodology#contract-timeline">Methodology</a>.</p>
</section>

<section class="plain">
	<h2>Document trail</h2>
	<DocTrail
		heading={null}
		rows={trailRows}
		highlight={hoverAct ?? hoverRow}
		onRowHover={(code) => (hoverRow = code)}
	/>
	{#if live.length}
		<p class="muted">
			<small
				>{grInt(live.length)} live payment orders{c.paid_without_vat !== null
					? ` · ${eurShort(c.paid_without_vat)} paid`
					: ''}</small
			>
		</p>
	{/if}
</section>

{#if !timeline.length}
	<p class="muted">
		ΚΗΜΔΗΣ links no upstream acts (αίτημα, διακήρυξη, κατακύρωση) to this contract — the
		registry's chain returns none, a linkage gap common across the programme's direct awards.
	</p>
{/if}

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
		<div><dt>Award basis</dt><dd>{c.award_procedure ?? '—'}</dd></div>
		<div><dt>Registry type</dt><dd>{c.contract_type ?? '—'}</dd></div>
		<div><dt>Legal framework</dt><dd>{c.legal_context ?? '—'}</dd></div>
		<div><dt>Bids</dt><dd>{c.bids_submitted ?? '—'}</dd></div>
	</dl>
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
	</div>
</Fold>

<!-- the evidence and the codes side by side: both are reference material the
     reader opens when they want it (user, 2026-08-19) -->
<div class="refcols">
	<Fold title="Extracted quotes from documents">
		<QuoteList heading={null} {quotes} />
	</Fold>
	{#if c.cpvs.length}
		<Fold title="CPV codes">
			<ul class="cpvlist">
				{#each c.cpvs.slice(0, cpvAll ? c.cpvs.length : 12) as cpv, i (i)}
					<li><span class="tabular">{cpv.cpv_code}</span> {cpv.cpv_description ?? ''}</li>
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

<style>
	/* the header's square slot shows the map or the call's other contracts;
	   the trail runs full width beneath, so its timeline has the same span as
	   the sponsored-works bar (user, 2026-08-19) */
	/* the page's two spine sections carry no fold: the timeline and the trail
	   are what the page IS (user, 2026-08-19) */
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
	/* the named δήμοι: a wash and a firm edge inside the highlighted region */
	.detailmap :global(.munishape) {
		fill: color-mix(in srgb, var(--c-antinero) 26%, transparent);
		stroke: var(--c-antinero);
		stroke-width: 0.6;
		vector-effect: non-scaling-stroke;
		cursor: pointer;
	}
	.flagged {
		border-bottom: 1px dotted var(--ink-faint);
	}
	.themes {
		margin-top: 3px;
		display: flex;
		gap: 4px 10px;
		flex-wrap: wrap;
	}
	.theme {
		font-size: var(--fs-12);
		color: var(--ink-soft);
	}
	.theme + .theme::before {
		content: '· ';
		color: var(--ink-faint);
	}
	.tlnote {
		margin: 0 0 var(--sp-4);
		color: var(--ink-soft);
		font-size: var(--fs-12);
		max-width: 78ch;
	}
	/* the switch rides ON the frame's top-right corner, so choosing a view
	   costs no vertical space and the two views stay the same size */
	.viewsw {
		position: absolute;
		top: 4px;
		right: 4px;
		z-index: 2;
		display: flex;
		gap: 3px;
	}
	.sw {
		font: inherit;
		font-size: 10px;
		font-family: var(--font-display);
		text-transform: uppercase;
		letter-spacing: 0.02em;
		padding: 2px 7px;
		border: 1px solid var(--line-strong);
		border-radius: 999px;
		background: var(--paper);
		color: var(--ink-soft);
		cursor: pointer;
	}
	.sw.on {
		background: var(--c-antinero);
		border-color: var(--c-antinero);
		color: var(--paper);
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
	.famslot {
		display: flex;
		flex-direction: column;
		justify-content: center;
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
	.nowrap {
		white-space: nowrap;
	}
	.chip.cat {
		background: color-mix(in srgb, var(--c-antinero) 12%, #fff);
	}
	.muted {
		color: var(--ink-soft);
	}
</style>
