import type { PageLoad } from './$types';
import { apiGet } from '$lib/api';

export interface CoopBundle {
	summary: {
		vat: string;
		name: string;
		/** curated English display name (dase_display_names) */
		name_en?: string;
		/** the pre-overlay curated/registry spelling */
		registry_name?: string;
		form: string | null;
		n_contracts: number;
		n_live: number;
		total_eur: number;
		first_date: string | null;
		last_date: string | null;
		name_variants: string[];
	};
	contracts: {
		reference_number: string;
		title: string | null;
		contract_signed_date: string | null;
		units_operator_name: string | null;
		total_cost_with_vat: number | null;
		/** set only on contracts signed jointly with other co-ops: how many
		 *  parties, and this co-op's even share (what the totals count) */
		n_parties?: number;
		share_eur?: number;
	}[];
	yearly: { year: string; n: number; eur: number }[];
	units: { unit: string | null; org: string | null; n_contracts: number; total_eur: number }[];
	/** the registered office (dase_coop_locations layer, 2026-08-24) */
	location?: {
		region_pe: string | null;
		lat: number | null;
		lon: number | null;
		geo_precision: string | null;
		city: string | null;
		address: string | null;
		postal_code: string | null;
		source: string | null;
	} | null;
}

export const load: PageLoad = async ({ fetch, params }) => {
	return { b: await apiGet<CoopBundle>(fetch, `/api/dase/coop/${params.vat}`) };
};
