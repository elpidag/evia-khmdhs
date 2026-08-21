import type { PageLoad } from './$types';
import { apiGet } from '$lib/api';

export interface ContractorBundle {
	summary: {
		vat_number: string;
		/** every registry spelling, comma-joined — kept as evidence */
		names: string;
		/** the curated display name (DATA_DECISIONS 2026-08-20) */
		name?: string;
		/** an official English name, where a body has one (ΤΑΙΠΕΔ → HRADF) */
		name_en?: string;
		/** the registry spelling the list was showing before the overlay */
		registry_name?: string;
		greek_vat: number;
		n_contracts: number;
		n_single_bidder: number;
		n_consortium: number;
		pct_direct: number | null;
		total_eur: number;
		total_eur_no_vat: number | null;
		first_signed: string | null;
		last_signed: string | null;
		countries: string | null;
		/** even share of each contract this company signed together with
		 *  others, keyed by ΑΔΑΜ (DATA_DECISIONS 2026-08-20) */
		shares?: Record<
			string,
			{ ref: string; n_parties: number; full_eur: number; share_eur: number }
		>;
	};
	contracts: {
		reference_number: string;
		title: string | null;
		contract_signed_date: string | null;
		procedure_type: string | null;
		units_operator_name: string | null;
		n_partners: number;
		bids_submitted: number | null;
		cancelled: number;
		total_cost_with_vat: number | null;
		stated_cost_with_vat: number | null;
	}[];
	partners: { vat_number: string; name: string; n_shared: number }[];
	signers: { name: string; n_contracts: number; total_eur: number }[];
	location: {
		legal_name: string | null;
		address: string | null;
		postal_code: string | null;
		city: string | null;
		region_pe: string | null;
		source: string | null;
		source_url: string | null;
		gemi: string | null;
		/** ΓΕΜΗ's current word on the company, verbatim (user 2026-08-20) */
		gemi_status?: string | null;
		lat: number | null;
		lon: number | null;
		geo_precision: string | null;
		/** the seat layer of 2026-08-21: where the address comes from, the
		 *  contract or URL, the verbatim seat sentence, a note where sources
		 *  disagree, and number|street for an 'address' point */
		seat_source?: 'contract' | 'register' | 'website' | null;
		seat_ref?: string | null;
		seat_excerpt?: string | null;
		seat_note?: string | null;
		geo_level?: 'number' | 'street' | null;
	} | null;
	map_data: {
		home: { lat: number; lon: number; city: string | null; pe: string | null; precision: string } | null;
		regions: { pe: string; n_contracts: number; split_eur: number }[];
	};
	yearly: {
		years: { year: string; paid_eur: number; stated_eur: number; n_payments: number }[];
	};
}

export const load: PageLoad = async ({ fetch, params }) => {
	return { b: await apiGet<ContractorBundle>(fetch, `/api/antinero/contractor/${params.vat}`) };
};
