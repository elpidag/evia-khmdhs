import type { PageLoad } from './$types';
import { apiGet } from '$lib/api';

export interface ContractDetail {
	reference_number: string;
	title: string | null;
	contract_signed_date: string | null;
	start_date: string | null;
	end_date: string | null;
	cancelled: number;
	cancellation_reason: string | null;
	organization_name: string | null;
	units_operator_name: string | null;
	signer_name: string | null;
	procedure_type: string | null;
	award_procedure: string | null;
	contract_type: string | null;
	legal_context: string | null;
	public_funding_ref: string | null;
	notice_reference_number: string | null;
	prev_reference_no: string | null;
	next_reference_no: string | null;
	/** registry double-posting: the kept twin's ΑΔΑΜ (this row is excluded) */
	duplicate_of?: string | null;
	/** out of scope — the signed PDF names no qualifying party. Holds the
	 *  in-scope sibling ΑΔΑΜ of the same procurement, '' when there is none.
	 *  NOT a cancellation and NOT a duplicate (DATA_DECISIONS 2026-08-17). */
	related_to?: string | null;
	/** curated correction note (dase corrections) */
	correction_note?: string | null;
	/** curated correction of WHO signed, with the preamble sentence it was
	 *  read from (DATA_DECISIONS 2026-08-20) */
	party_correction?: {
		kind: 'party' | 'keep';
		evidence: string | null;
		note: string | null;
	} | null;
	/** ΓΕΜΗ's CURRENT word on a contractor that is no longer active, keyed by
	 *  ΑΦΜ — a joint venture is wound up once its job ends (user 2026-08-20) */
	contractor_status?: Record<string, { status: string; gemi: string | null }>;
	document_kind?: {
		kind: string;
		label_el: string;
		label_en: string;
		evidence: string | null;
		source: string | null;
	} | null;
	/** ΑΔΑΜs of double-postings of THIS contract (kept side) */
	duplicates?: string[];
	bids_submitted: number | null;
	contract_duration: number | null;
	contract_duration_unit: string | null;
	total_cost_with_vat: number | null;
	total_cost_without_vat: number | null;
	paid_with_vat: number | null;
	paid_without_vat: number | null;
	effective_cost_with_vat: number | null;
	scope: { scope: string; in_scope: number; superseded_by: string | null } | null;
	contractors: {
		vat_number: string;
		name: string;
		country: string | null;
		/** curated ΔΑΣΕ display names (added on /api/dase contract detail only) */
		display_el?: string;
		display_en?: string;
	}[];
	cpvs: { cpv_code: string; cpv_description: string | null }[];
	nuts: { nuts_code: string; nuts_name: string | null }[];
	objects: {
		quantity: number | null;
		unit_type: string | null;
		cost_without_vat: number | null;
		vat_percent: number | null;
		short_description: string | null;
	}[];
	payments: {
		payment_ref: string;
		signed_date: string | null;
		/** ISO date resolved by the API: signed_date, else the submission
		 *  stamp — the timeline needs one for every tick */
		d?: string | null;
		title: string | null;
		amount_with_vat: number | null;
		amount_without_vat: number | null;
		cancelled: number;
		credit: number;
		ada: string | null;
		correction_note: string | null;
	}[];
	/** the registry's incl-VAT figures (the site's primary basis is net) */
	gross?: {
		stated_gross: number | null;
		paid_gross?: number | null;
		payments?: Record<string, number | null>;
	};
	/** curated work-type category + its evidence: the descriptive project
	 *  title from the signed PDF ('pdf') or the parent's ('inherited:<ref>') */
	category: {
		key: string;
		label: string;
		/** English display label — the card is an English page */
		label_en?: string;
		note: string | null;
		title: string;
		source: string;
	} | null;
	regions: { region_pe: string; source: string | null; note: string | null }[];
	/** the whole procurement family the registry's chain returns — the ΔΑΣΕ
	 *  page draws its FamilyTree from this, while `timeline` holds only the
	 *  contract's own records (user, 2026-08-19) */
	family_acts?: ContractDetail['timeline'];
	/** the δήμοι the contract's documents place the works in (2026-08-19) */
	municipalities?: {
		code: string;
		name: string;
		region_pe: string | null;
		authority: string | null;
		source_ref: string | null;
		from_call: string | null;
		excerpt: string;
		outside_region: number;
		/** why it sits outside the curated regions, when something does
		 *  account for it: covers_pe | seat | curated verdict */
		outside_pe_explained: string | null;
		note: string | null;
	}[];
	/** what the contract's own title says the works ARE — multi-label, with
	 *  the verbatim clause each theme comes from; `cpv_notes` are codes that
	 *  name work the title does not (a note, never a theme) */
	work_themes?: {
		themes: { key: string; el: string; en: string; excerpt: string }[];
		cpv_notes: { cpv: string; key: string; el: string; en: string }[];
		source: string | null;
	} | null;
	/** the deadline the CONTRACT states, with the ΚΗΜΔΗΣ figure beside it */
	stated_duration?: {
		n: number | null;
		unit: string | null;
		days: number | null;
		basis: string | null;
		fire_season: number | null;
		starts?: string | null;
		deadline?: string | null;
		anchor: string;
		excerpt: string;
		source_ref: string;
		registry_n: number | null;
		registry_unit: string | null;
	} | null;
	/** what the contract PROMISED: the deadline it announced and the acts
	 *  that moved it — the timeline bar draws this, not the paperwork */
	deadlines?: {
		deadline: string | null;
		/** where the deadline came from: the contract's own sentence
		 *  ('document'), its fire season ('document_season'), or — only when
		 *  no curated reading exists — the registry's own fields */
		basis: 'document' | 'document_season' | 'end_date' | 'duration' | 'act' | null;
		source_ref: string | null;
		duration: number | null;
		unit: string | null;
		assumed: boolean;
		/** the registry fields the deadline was actually read from */
		fields?: {
			ref: string;
			duration: number | null;
			unit: string | null;
			start_date: string | null;
			end_date: string | null;
		} | null;
		extensions: {
			/** the ΚΗΜΔΗΣ record's ΑΔΑΜ, or the Diavgeia act's ΑΔΑ (2026-08-21) */
			ref: string;
			ada?: string | null;
			source?: 'khmdhs' | 'diavgeia';
			ordinal?: number | null;
			per_area?: boolean;
			by_text?: string | null;
			excerpt?: string | null;
			later?: boolean;
			in_force?: string | null;
			/** what the act extends, the verbatim object, and — for an area act —
			 *  the registry's canonical service names it resolved to (the lanes) */
			scope?: string | null;
			scope_text?: string | null;
			scope_auth?: string[];
			d: string | null;
			deadline: string | null;
			n: number;
			kind?: string | null;
		}[];
	} | null;
	/** linked forest authorities with their office seats (detail map) */
	authorities?: {
		name: string;
		source: string | null;
		/** curated evidence, present when source is `override`: why these units
		 *  and not the ones the registry title names */
		excerpt?: string | null;
		kind: string | null;
		lat: number | null;
		lon: number | null;
		region_pe: string | null;
		seat_precision: string | null;
	}[];
	sites: { site_name: string; region_pe: string; page: number | null; excerpt: string | null }[];
	/** procurement family read from the contract's own text: the πρόσκληση
	 *  it cites and every sibling citing the same one. Null for direct
	 *  awards and negotiations, which publish no call. */
	family?: {
		call: string;
		role: string;
		source: string;
		excerpt: string;
		amendments: string[];
		total_eur: number;
		contracts: { ref: string; title: string | null; d: string | null; eur: number | null }[];
	} | null;
	/** ΔΑΣΕ detail map geo (region + awarding-unit seat); absent on kh side */
	geo?: { pe: string | null; unit_seat: { name: string; lat: number; lon: number } | null };
	/** the contract's own version chain, oldest → newest: what each ΚΗΜΔΗΣ
	 *  record of it IS, when, and the value it stated. [] when posted once —
	 *  the registry's adamChain does not carry these links. */
	/** the date of THIS document, and where it came from: `signed` (the
	 *  registry's own field, correct for an original contract), `signature`
	 *  (the digital-signature block of a later act), `published` (its ΚΗΜΔΗΣ
	 *  stamp) or `inherited` (the registry's field, which for a later act is
	 *  the contract's date, not its own) */
	own_date?: string | null;
	own_date_basis?: 'signed' | 'signature' | 'published' | 'inherited';
	chain?: {
		ref: string;
		d: string | null;
		d_basis?: string;
		kind: string | null;
		eur: number | null;
		title: string | null;
		self: boolean;
	}[];
	timeline: {
		adam: string;
		kind: 'request' | 'approved_request' | 'notice' | 'auction' | 'contract' | 'completion' | 'extension';
		title: string | null;
		d: string | null;
		cancelled: number;
		/** in-db contract rows — WHY the sibling is excluded, so the trail
		 *  never prints «cancelled» over a double-posting or an out-of-scope
		 *  contract (both carry cancelled = 1 as their exclusion mechanism) */
		duplicate_of?: string | null;
		doc_kind?: string | null;
		related_to?: string | null;
		in_db: boolean;
		/** the re-posted twin of a registry-cancelled record (2026-08-19) */
		twin?: boolean;
		/** in-db contract rows: first contractor name (family diagram labels) */
		who?: string | null;
		/** the contract's own text cites this act; the registry never
		 *  declared it, so it has no linked_acts row */
		cited?: boolean;
		role?: string;
		/** completion acts only (Diavgeia) */
		ckind?: 'oristiki_paralavi' | 'paralavi' | 'peraiosi' | 'oloklirosi' | 'extension' | 'extension_partial' | 'extension_refused';
		end_basis?: 'protocol_date' | 'act_date';
		end_excerpt?: string | null;
		/** the ONE service whose part this completion act accepts («για το τμήμα
		 *  περιοχής ευθύνης Δασαρχείου Χ»), canonical; null = the whole */
		part_auth?: string | null;
		/** extension acts only (Diavgeia, 2026-08-21): the deadline the act
		 *  grants, its ordinal, per-area flag, duration wording, the verbatim
		 *  clause, and the extractor's flag when it could not read a date */
		ordinal?: number | null;
		deadline?: string | null;
		per_area?: boolean;
		by_text?: string | null;
		excerpt?: string | null;
		flag?: string | null;
		/** what the act extends: 'study' | 'stage' | 'area' | 'whole' | null, and the
		 *  verbatim object (the services named, or the stage phrase) */
		scope?: string | null;
		scope_text?: string | null;
		scope_auth?: string[];
	}[];
}

export const load: PageLoad = async ({ fetch, params }) => {
	return {
		c: await apiGet<ContractDetail>(fetch, `/api/antinero/contract/${params.adam}`)
	};
};
