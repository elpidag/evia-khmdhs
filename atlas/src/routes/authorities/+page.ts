import type { PageLoad } from './$types';
import { apiGet } from '$lib/api';

export interface AuthorityRow {
	name: string;
	slug: string;
	kind: string;
	pe: string;
	lat: number | null;
	lon: number | null;
	seat: string | null;
	antinero_n: number;
	antinero_eur: number;
	dase_n: number;
	dase_eur: number;
}

export interface OtherUnit {
	name: string;
	inspectorate: string;
	unit_kind: string;
	street: string | null;
	tk: string | null;
	city: string | null;
	phone: string | null;
	email: string | null;
	lat: number | null;
	lon: number | null;
}

/** a ΔΑΣΕ co-operative at its registered office (user, 2026-08-25) */
export interface CoopPoint {
	vat: string;
	name: string;
	name_en: string | null;
	lat: number;
	lon: number;
	pe: string | null;
	place: string | null;
	n_contracts: number;
	total_eur: number;
	[key: string]: unknown;
}

/** an Anti-nero contractor at its registered office */
export interface ContractorPoint {
	vat: string;
	name: string;
	registry_name?: string;
	lat: number;
	lon: number;
	pe: string | null;
	n_contracts: number;
	total_eur: number;
	[key: string]: unknown;
}

export const load: PageLoad = async ({ fetch }) => {
	const data = await apiGet<{
		authorities: AuthorityRow[];
		other_units: OtherUnit[];
		coops: CoopPoint[];
		contractors: ContractorPoint[];
	}>(fetch, '/api/authorities');
	return {
		rows: data.authorities,
		otherUnits: data.other_units,
		coops: data.coops ?? [],
		contractors: data.contractors ?? []
	};
};
