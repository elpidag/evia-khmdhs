import type { PageLoad } from './$types';
import { apiGet } from '$lib/api';

export interface AuthorityProfile {
	name: string;
	slug: string;
	kind: string;
	pe: string;
	seat: { city: string | null; lat: number | null; lon: number | null };
	/** curated office address (ΥΠΕΝ directory, Diavgeia-confirmed) */
	contact: {
		street: string | null;
		postal_code: string | null;
		city: string | null;
		phone: string | null;
		email: string | null;
		precision: string | null;
	};
	antinero: {
		contracts: {
			reference_number: string;
			title: string | null;
			contract_signed_date: string | null;
			eff: number | null;
			n_auths: number;
			contractors: string | null;
			vat: string | null;
		}[];
		total_eur: number;
		exposure_eur: number;
		top_contractors: { vat: string; name: string; n: number; eur: number }[];
	};
	dase: {
		contracts: {
			reference_number: string;
			title: string | null;
			contract_signed_date: string | null;
			units_operator_name: string | null;
			total_cost_with_vat: number | null;
			contractor_name: string | null;
			vat: string | null;
		}[];
		total_eur: number;
		top_coops: { vat: string; name: string; n: number; eur: number }[];
		match_basis: string;
	};
}

export const load: PageLoad = async ({ fetch, params }) => {
	return { a: await apiGet<AuthorityProfile>(fetch, `/api/authority/${params.slug}`) };
};
