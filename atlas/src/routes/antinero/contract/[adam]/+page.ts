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
		note: string | null;
		title: string;
		source: string;
	} | null;
	regions: { region_pe: string; source: string | null; note: string | null }[];
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
	timeline: {
		adam: string;
		kind: 'request' | 'approved_request' | 'notice' | 'auction' | 'contract' | 'completion';
		title: string | null;
		d: string | null;
		cancelled: number;
		/** in-db contract rows — WHY the sibling is excluded, so the trail
		 *  never prints «cancelled» over a double-posting or an out-of-scope
		 *  contract (both carry cancelled = 1 as their exclusion mechanism) */
		duplicate_of?: string | null;
		related_to?: string | null;
		in_db: boolean;
		/** in-db contract rows: first contractor name (family diagram labels) */
		who?: string | null;
		/** the contract's own text cites this act; the registry never
		 *  declared it, so it has no linked_acts row */
		cited?: boolean;
		role?: string;
		/** completion acts only (Diavgeia) */
		ckind?: 'oristiki_paralavi' | 'paralavi' | 'peraiosi' | 'oloklirosi';
		end_basis?: 'protocol_date' | 'act_date';
		end_excerpt?: string | null;
	}[];
}

export const load: PageLoad = async ({ fetch, params }) => {
	return {
		c: await apiGet<ContractDetail>(fetch, `/api/antinero/contract/${params.adam}`)
	};
};
