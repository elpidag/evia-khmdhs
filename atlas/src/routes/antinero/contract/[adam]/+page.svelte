<script lang="ts">
	import { authEn, authEnShort, bodyEn, devGreek, orgEn } from '$lib/transforms/names';
	import { peEn, ruLabel } from '$lib/transforms/regions';
	import FactsHeader from '$lib/detail/FactsHeader.svelte';
	import DocTrail, { type TrailRow } from '$lib/detail/DocTrail.svelte';
	import { trailChip } from '$lib/transforms/exclusion';
	import QuoteList, { type Quote } from '$lib/detail/QuoteList.svelte';
	import ChainTimeline from '$lib/detail/ChainTimeline.svelte';
	import { buildLanes } from '$lib/transforms/lanes';
	import Fold from '$lib/ui/Fold.svelte';
	import Hint from '$lib/ui/Hint.svelte';
	import { registryStatusNote } from '$lib/transforms/registry';
	import { procedureEn } from '$lib/transforms/procedures';
	import ProcurementFamily from '$lib/charts/ProcurementFamily.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import { dmy, eur, eurShort, grInt } from '$lib/transforms/format';
	import { scopeLabel } from '$lib/transforms/scopes';
	import { loadMunicipalities, type MuniProps } from '$lib/maps/useGeo';
	import type { FeatureCollection, MultiPolygon } from 'geojson';
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
	/** swap the header slot to the procurement diagram and bring it into view */
	const showDiagram = () => {
		view = 'family';
		document.querySelector('.detailmap, .famslot')?.scrollIntoView({ block: 'center' });
	};
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
		completion: 'Completion',
		extension: 'Deadline extension'
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
		request: 0, approved_request: 1, notice: 2, auction: 3, contract: 4, extension: 4, completion: 5
	};
	// Diavgeia extension approvals (phase 1 of the lifecycle layer, 2026-08-21):
	// the label says which kind, the title cell the deadline it grants
	const EXTKIND: Record<string, string> = {
		extension: 'Deadline extension',
		extension_partial: 'Partial deadline extension',
		extension_refused: 'Extension refused'
	};
	const ordinalEn = (n: number | null | undefined) =>
		n ? `${n}${n === 1 ? 'st' : n === 2 ? 'nd' : n === 3 ? 'rd' : 'th'} ` : '';

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
	// the per-area lanes (user, 2026-08-21): where the extension acts name
	// forest services, each gets its own line under the contract bar — its
	// steps, and its own part-acceptance where ΥΠΕΝ signed one
	const partEnds = $derived(
		timeline
			.filter((t) => t.kind === 'completion' && t.part_auth && t.d)
			.map((t) => ({ auth: t.part_auth!, d: t.d!, ref: t.adam }))
	);
	const laneData = $derived(
		buildLanes(
			(c.authorities ?? []).map((a) => a.name),
			c.deadlines?.extensions ?? [],
			partEnds,
			completion?.d ? { d: completion.d, ref: completion.adam } : null,
			(n) => authEnShort(n)
		)
	);
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
		if (!t.adam) return null; // a call cited by date only has no record
		if (t.kind === 'completion' || t.kind === 'extension') return `/pdf/diavgeia/${t.adam}`;
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
					: t.kind === 'extension'
						? ordinalEn(t.ordinal) + (EXTKIND[t.ckind ?? ''] ?? KIND.extension).toLowerCase().replace(/^./, (ch) => ch.toUpperCase())
						: (t.kind === 'contract'
								? (DOCKIND[t.doc_kind ?? ''] ?? KIND.contract)
								: (KIND[t.kind] ?? t.kind)) + (t.self ? ' — this document' : ''),
			code: t.adam ?? '(no ΑΔΑΜ)',
			// an extension row says what it granted: «→ 27.01.2026» (the latest
			// date, «per area» when the act grants several), or that the act
			// could not be read — the subject stays as the title
			title:
				t.kind === 'extension'
					? `${
							t.ckind === 'extension_refused'
								? 'the request was refused'
								: t.deadline
									? `→ ${t.deadline.split('-').reverse().join('.')}${t.per_area ? ' (per area)' : ''}${
											// the act's own typo («05.02.2025» on an act of 23.12.2025):
											// printed as written, said to be so, never drawn on the bar
											t.flag === 'deadline_before_issue'
												? ' — as written in the act, earlier than the act itself'
												: ''
										}`
									: `deadline not read (${t.flag ?? 'no date'})`
						}${
							t.scope === 'study'
								? ` · the study's submission${t.scope_text ? ` («${t.scope_text}»)` : ''}`
								: t.scope === 'stage'
									? ` · a stage${t.scope_text ? ` («${t.scope_text}»)` : ''}`
									: t.scope === 'area'
										? ` · for ${t.scope_text ?? 'the named area'}`
										: t.scope === 'whole'
											? ' · the whole contract'
											: t.ckind !== 'extension_refused' && t.deadline && (c.authorities?.length ?? 0) > 1
												? ' · all areas (the act names no subset)'
												: ''
						}${t.by_text ? ` · ${t.by_text}` : ''} — ${t.title ?? ''}`
					: (t.title ?? null),
			pdf: pdfHref(t),
			self: t.self,
			// rows the registry never published: they are in the trail because
			// this contract's text cites them, and the chip says so
			...(t.cited ? { chip: 'cited in this contract', chipBad: false } : {}),
			// the registry title stays verbatim — it IS the document's title and
			// the evidence of the error; the chip points at the explanation below
			// the twin of a re-posted record: the registry links the two
			// nowhere, so the row says which side of the re-posting it is
			...(t.twin
				? {
						chip: t.cancelled
							? 'cancelled record, re-posted as this contract'
							: 'the re-posting of the cancelled record',
						chipBad: false
					}
				: t.self && overrideNote
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
	const extNote = $derived.by(() => {
		const ex = c.deadlines?.extensions ?? [];
		if (!ex.length) return '';
		// the latest date any step granted (a per-area act may follow one that
		// already granted a later date for another area)
		const last = ex.reduce<string | null>(
			(m, e) => (e.deadline && (!m || e.deadline > m) ? e.deadline : m),
			null
		);
		return `, extended to ${dmy(last)} by ${ex.map((e) => e.ref).join(', ')}`;
	});

	/** the δήμοι the documents place the works in, one level finer than the
	 *  Π.Ε. layer; `outside_region` marks a δήμος whose Π.Ε. we never curated
	 *  for this contract — recorded as the document states it (2026-08-19) */
	/** the map's bottom edge meets the last line of the caveat, as on the
	 *  sponsored-works pages; the width is the template's and never moves */
	let leftH = $state(0);
	let mapW = $state(0);
	const mapH = $derived(Math.max(420, Math.round(leftH)));

	/**
	 * What the TYPE row's hover card says — and only what the row does not.
	 *
	 * The work-type category and the multi-label themes are two vocabularies
	 * over the same contract, so «Protection of archaeological sites and
	 * monuments» would print again as «Archaeological sites, monasteries and
	 * aesthetic forests» directly underneath. The mapping below says which
	 * theme a category already states; the rest go in the card, with the CPV
	 * coverage folded in — three water-tank codes are one fact, not three.
	 */
	const SAID_BY_CATEGORY: Record<string, string> = {
		miktes_zones: 'miktes_zones',
		arxaiologikoi: 'arxaiologikoi',
		meletes: 'meletes',
		antidiavrotika: 'antidiavrotika',
		anadasoseis: 'anadasoseis',
		ylotomies: 'ylotomies',
		ydatodexamenes: 'nero'
	};
	const typeDetail = $derived.by(() => {
		const said = SAID_BY_CATEGORY[c.category?.key ?? ''];
		const extra = themes.filter((t) => t.key !== said).map((t) => t.en.toLowerCase());
		const cpv = [...new Set(cpvNotes.map((n) => n.en.toLowerCase()))].filter(
			(x) => !extra.includes(x)
		);
		const parts: string[] = [];
		if (extra.length)
			parts.push(`the contract's own title also names ${list(extra)}`);
		else if (!themes.length)
			parts.push(
				"the contract's own title names no specific kind of work beyond fire protection, and nothing is inferred from the call, which lists the whole programme's menu"
			);
		if (cpv.length)
			parts.push(
				`its procurement's CPV codes also cover ${list(cpv)} — those codes belong to the call and are shared by every lot of it`
			);
		return parts.join('; ');
	});
	/** «a, b and c» — a list a reader can say out loud. Items that contain
	 *  «and» themselves («clearing of forests and forested areas») get
	 *  semicolons instead, or the sentence reads as one run-on. */
	const list = (xs: string[]): string => {
		if (xs.length <= 1) return xs[0] ?? '';
		const sep = xs.some((x) => x.includes(' and ')) ? '; ' : ', ';
		return `${xs.slice(0, -1).join(sep)}${sep}${xs[xs.length - 1]}`;
	};

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
	/** the regional units, English, without the «R.U.» prefix — the row now
	 *  says «in Regional Units: …» once (user, 2026-08-20) */
	const regionNames = $derived(c.regions.map((r) => peEn(r.region_pe)));
	/** which document named them — the contract itself, or the call it cites */
	const muniSource = $derived.by(() => {
		if (!munis.length) return '';
		const calls = [...new Set(munis.map((m) => m.from_call).filter(Boolean))];
		if (calls.length && munis.every((m) => m.from_call))
			return `as stated in the call ${calls.join(', ')}`;
		return calls.length ? 'as stated in the contract and its call' : 'as stated in the contract';
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
		// WHO signed it, where the registry named someone else (DATA_DECISIONS
		// 2026-08-20). A party fix moves no euro, so it carries no
		// correction_note — but the contractor row differs from the registry
		// and only this sentence says why
		...(c.party_correction?.evidence
			? [
					{
						label:
							c.party_correction.kind === 'party'
								? 'Contracting party — read from the signed contract'
								: 'Contracting party — the registry named companies the contract does not',
						text: c.party_correction.evidence,
						code: c.reference_number,
						href: `/pdf/contract/${c.reference_number}`,
						note: c.party_correction.note ?? undefined
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
		// WHERE the type chips come from: the contract's own project title —
		// or, where the title names no work, the CALL's works enumeration
		// (source `call:<PROC>`, DATA_DECISIONS 2026-08-22) — one quoted
		// clause per theme (user, 2026-08-19)
		...themes.map((t) => {
			const src = c.work_themes?.source ?? '';
			const fromCall = src.startsWith('call:');
			const doc = fromCall
				? src.slice(5)
				: src.startsWith('inherited:')
					? src.slice(10)
					: c.reference_number;
			return {
				label: `Type of work — ${t.en}${fromCall ? ' (from the call)' : ''}`,
				text: t.excerpt,
				code: doc,
				href: `/pdf/${fromCall ? 'notice' : 'contract'}/${doc}`,
				note: fromCall
					? 'The signed title names no specific work; the works are quoted from the call’s own description of this lot.'
					: null
			};
		}),
		// WHERE the SCOPE row comes from, when it is design-build: the clause
		// stating the contractor drafts the studies (user's 1-2-3 model,
		// DATA_DECISIONS 2026-08-22)
		...(c.deliverables?.kind === 'study_and_works' && c.deliverables.excerpt
			? [
					{
						label: 'Scope — study and works (design-build)',
						text: c.deliverables.excerpt,
						code: c.deliverables.source?.startsWith('call:')
							? c.deliverables.source.slice(5)
							: c.reference_number,
						href: c.deliverables.source?.startsWith('call:')
							? `/pdf/notice/${c.deliverables.source.slice(5)}`
							: `/pdf/contract/${c.reference_number}`,
						note: null
					}
				]
			: []),
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
				note: 'the contract sets no number of months: its works run within the fire season, 1 May – 31 October'
			};
		if (d?.n) {
			const unit = UNIT_EN[d.unit ?? ''] ?? d.unit ?? '';
			const reg = d.registry_n
				? `; ΚΗΜΔΗΣ records ${d.registry_n}${d.registry_unit ? ` ${d.registry_unit}` : ' with no unit'}`
				: '';
			return {
				text: `${d.n} ${unit}${d.n === 1 ? '' : 's'} ${BASIS_EN[d.basis ?? ''] ?? ''}`.trim(),
				note: `as stated in the contract${d.source_ref !== c.reference_number ? ` ${d.source_ref}` : ''}${reg}`
			};
		}
		// nothing curated for this record (a contract added since the last run)
		const n = c.contract_duration;
		if (!n) return { text: '—', note: null };
		const u = (c.contract_duration_unit ?? '').toUpperCase();
		const m = u.startsWith('ΗΜΕΡ') ? Math.round((n / 30.44) * 10) / 10 : n;
		return {
			text: `${m} month${m === 1 ? '' : 's'}`,
			note: 'from the ΚΗΜΔΗΣ record; the signed text was not read for this contract'
		};
	});

	/**
	 * What the bar means, said on the page it is drawn on (user, 2026-08-19).
	 * The wording follows THIS contract's own deadline source — never a
	 * generic sentence that would be wrong for most of them.
	 */
	/**
	 * The chart's legend — the symbols and nothing else (user, 2026-08-20).
	 * Where this contract's own deadline comes from is the DURATION row's
	 * business, and it says so there; repeating it here said it twice.
	 */
	const barNote = $derived.by(() =>
		[
			'▬  the bar — the time the contract was given: from signature to the deadline it announced',
			...(c.deadlines?.extensions?.length
				? [
						`▭  the lighter stretch — ${c.deadlines.extensions.length === 1 ? 'the extension' : `the ${c.deadlines.extensions.length} extensions`} that moved that deadline`
					]
				: []),
			'✔  the day the works were accepted, which may fall after the deadline',
			...(laneData.lanes.length
				? [
						`▭  the grey part is split into one strip per forest service (${laneData.lanes.filter((l) => !l.unplaced).length}), hover a strip to read its name at its end: each piece of it (alternating tones) is one partial extension the acts grant for that area, and a ✔ appears only where ΥΠΕΝ accepted that part on its own${laneData.lanes.some((l) => l.unplaced) ? '; an act naming a service the registry lacks sits on the last strip' : ''}; an act naming no area extends every strip`
					]
				: []),
			'€  a payment order',
			'•  the grey dots before the signature — the procurement that produced the contract'
		].join(String.fromCharCode(10))
	);

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
		'On the map: the regional units this contract worked in are shaded, the municipalities its ' +
			'documents name are outlined inside them, and each dot is the seat of a forest service ' +
			'responsible for the works' +
			(munis.some((m) => m.outside_region)
				? '. One municipality here falls outside the shaded units — that is what the document says, and the region layer is left as curated.'
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

<FactsHeader caveat={CAVEAT} bind:leftHeight={leftH}>
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
			{#if c.own_date_basis === 'published'}<Hint
					text="the date this record was posted to ΚΗΜΔΗΣ; the document itself states none"
				/>{:else if c.own_date_basis === 'inherited'}<Hint
					text="ΚΗΜΔΗΣ files later acts under the contract's own signature date; this is that date"
				/>{/if}
		</dd>
		<dt>Contractor</dt>
		<dd>
			{#each c.contractors as ct, i (ct.vat_number)}
				{#if i}{', '}{/if}<a href={`/antinero/contractor/${ct.vat_number}`}>{ct.name}</a
				>{#if c.contractor_status?.[ct.vat_number]}{@const st = c.contractor_status[
						ct.vat_number
					]}<Hint text={registryStatusNote(st)} />{#if st.gemi && st.gemi !== '-1'}<a
							class="reg"
							href={`https://publicity.businessportal.gr/company/${st.gemi}`}
							target="_blank"
							rel="noopener">ΓΕΜΗ</a
						>{/if}{/if}
			{/each}
			{#if c.contractors.length > 1}<Hint
					text="signed by two parties together; each company's own page counts half of it, so no euro is counted twice"
				/>{/if}
		</dd>
		<dt>Type</dt>
		<dd>
			{#if c.category}<span title={devGreek(c.category.label)}
					>{c.category.label_en ?? c.category.label}</span
				>{#if typeDetail}<Hint text={typeDetail} />{/if}{:else}—{/if}
		</dd>
		<dt>Scope</dt>
		<dd>
			{c.deliverables?.kind === 'study'
				? 'study only'
				: c.deliverables?.kind === 'study_and_works'
					? 'study & works'
					: 'works only'}{#if c.deliverables?.kind === 'study_and_works'}<Hint
					text="Design-build: the contract includes the drafting of the studies by the contractor, and the execution of the works those studies define — the clause is quoted in the extracts below."
				/>{/if}
		</dd>
		<dt>Budget <small class="muted">(excl. VAT)</small></dt>
		<dd>
			{eurShort(c.total_cost_without_vat ?? 0)}
		</dd>
		<dt>Awarding procedure</dt>
		<dd>
			<span title={devGreek(c.procedure_type ?? '')}>{procedureEn(c.procedure_type)}</span>
			{#if c.award_procedure}<Hint
					text={`ground stated in the registry: ${procedureEn(c.award_procedure).toLowerCase()}`}
				/>{/if}
			{#if c.bids_submitted === 1}<Hint
					text="one bid was submitted for this contract"
				/>{/if}
		</dd>
		<dt>Contracting authority</dt>
		<dd><span title={devGreek(c.organization_name)}>{orgEn(c.organization_name) || '—'}</span></dd>
		<!-- the user's header, revised 2026-08-19: WHERE the works were is its
		     own row and the service responsible for them follows it -->
		<dt>Areas of intervention</dt>
		<dd>
			{#if munis.length}
				<span class="lead">Municipalities:</span>
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
										: (m.note ?? m.region_pe ?? '')}>{m.name}</span
					>
				{/each}
				{#if regionNames.length}
					<span class="lead">
						in {regionNames.length === 1 ? 'Regional Unit' : 'Regional Units'}:</span
					>
					{regionNames.join(', ')}
				{/if}{#if muniSource}<Hint text={muniSource} />{/if}
			{:else}
				{#if regionNames.length}<span class="lead"
						>Regional {regionNames.length === 1 ? 'Unit' : 'Units'}:</span
					>
					{regionNames.join(', ')}{:else}—{/if}<Hint
					text="the contract's documents place the works in these regional units but name no municipality"
				/>
			{/if}
		</dd>
		<dt>Responsible forest service body</dt>
		<dd>
			{#if c.authorities?.length}
				{#each c.authorities as a, i (a.name)}
					{#if i}{', '}{/if}<span title={devGreek(a.name)}>{authEn(a.name)}</span>
				{/each}
				<!-- a region-scoped «άμεσης διαχείρισης» contract names no forest
				     service at all; the only ones on record are those an acceptance
				     act happened to name, and one of those acts covers one part -->
				{#if c.authorities.every((a) => a.source?.startsWith('completion_act'))}
					<Hint
						text={c.authorities.some((a) => a.source?.endsWith('|part'))
							? 'the contract names no forest service; this one is named by an acceptance act that covers a single part of the works, so it is not the contract’s whole jurisdiction'
							: 'the contract names no forest service; these are the ones its acceptance acts name'}
					/>
				{/if}
			{:else}
				<span title={devGreek(c.units_operator_name)}>{bodyEn(c.units_operator_name) || '—'}</span>
			{/if}
		</dd>
		<dt>Duration</dt>
		<dd>
			{duration.text}{#if duration.note}<Hint text={duration.note} />{/if}
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
			<div class="famslot" style:min-height="{mapH}px">
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
		<div class="detailmap" bind:clientWidth={mapW}>
			<PaperMap
				width={mapW || 460}
				height={mapH}
				fitPoints={worksPoints}
				fitPes={worksPes}
				fitPad={0.15}
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
						tipCorner="top-left"
					/>
				{/snippet}
			</PaperMap>
		</div>
		{/if}
	{/snippet}
</FactsHeader>

<section class="plain">
	<!-- the legend rides on the ⓘ after the heading and stands above and to
	     the right of it, clear of the chart it explains (user, 2026-08-20) -->
	<h2 class="withhint">
		Timeline<Hint text={barNote} width="21rem" up heading />
		<a class="mth" href="/methodology#validation">Methodology</a>
	</h2>
	<div class="tlrow">
		<ChainTimeline
		signed={chain[0]?.d ?? iso(c.own_date ?? c.contract_signed_date)}
		signedRef={chain[0]?.ref ?? c.reference_number}
		end={completion?.d ?? null}
		endRef={completion?.adam ?? null}
		deadline={c.deadlines?.deadline ?? null}
		deadlineBasis={c.deadlines?.basis ?? null}
		extensions={laneData.main}
		lanes={laneData.lanes}
		today={todayIso}
		{chain}
		payments={payTicks}
		runUp={runUpActs}
		callInfo={hasFamily
			? { ref: c.family!.call, lots: c.family!.contracts.length, total: c.family!.total_eur }
			: null}
		onCallClick={showDiagram}
		highlightRef={hoverRow}
			onActHover={(ref) => (hoverAct = ref)}
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
	<!-- the other lots of the same procurement are not documents of THIS
	     contract, so they left the table; the relationship they belong to is
	     the diagram's, and this line is the way in (user, 2026-08-19) -->
	{#if hasFamily}
		<p class="muted">
			<small
				>One of {grInt(c.family!.contracts.length)} contracts awarded under call
				<span class="tabular">{c.family!.call}</span> —
				<button class="linkish" onclick={showDiagram}>see the diagram</button>
			</small>
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
	/* the register's own page for a company whose status the card mentions */
	a.reg {
		font-family: var(--font-ui);
		font-size: var(--fs-12);
		margin-left: 4px;
		white-space: nowrap;
	}
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
	/* the whole sentence is one colour (user, 2026-08-20): «Municipalities»
	   and «in Regional Units» carry a little weight, nothing else changes */
	.lead {
		font-weight: 600;
	}
	/* the heading carries its ⓘ on the left and the methodology link on the
	   right, so nothing sits between the chart and the trail */
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
	/* the switch rides ON the frame's top-right corner, so choosing a view
	   costs no vertical space and the two views stay the same size */
	/* the site's segmented toggle (user, 2026-08-26), sitting to the LEFT
	   of the map's own +/−/⌂ stack, which keeps its usual corner */
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
		background: var(--ink);
		color: #fff;
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
	/* the diagram's shapes sit at the centre of the slot — the same box the
	   map fills, as tall as the facts column — with the caption at its foot
	   (user, 2026-08-21) */
	.famslot {
		position: relative;
		display: flex;
		flex-direction: column;
		justify-content: center;
		padding-bottom: 3.2rem;
		box-sizing: border-box;
	}
	.famslot > p.muted {
		position: absolute;
		left: 0;
		right: 0;
		bottom: 0;
		margin: 0;
	}
	.crumb a {
		text-decoration: none;
		color: var(--ink-soft);
	}
	/* template map look — same as the sponsored-works maps:
	   grey sea, no border, no paper shadow */
	.detailmap :global(.map) {
		background: #f2f2f2;
		border: 1px solid var(--line); /* the maps' hairline — the zoom buttons' outline tone (user, 2026-08-22) */
		--map-accent: var(--c-antinero); /* the zoom buttons' circle hue */
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
	.muted {
		color: var(--ink-soft);
	}
</style>
