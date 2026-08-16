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

export const load: PageLoad = async ({ fetch }) => {
	const data = await apiGet<{ authorities: AuthorityRow[]; other_units: OtherUnit[] }>(
		fetch,
		'/api/authorities'
	);
	return { rows: data.authorities, otherUnits: data.other_units };
};
