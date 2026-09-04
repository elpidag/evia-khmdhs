/**
 * The two AWARDING PROCESS diagrams as pure graph builders (2026-09-04),
 * shared by the dataset pages and the story's full-width band so the
 * story can never draw a different diagram from the pages:
 *
 *   Anti-nero — the Ministry (one node) → its operating units → the ten
 *   biggest contractors + everyone else, from `/api/antinero/unit-flow`
 *   (`queries_extra.unit_flows`, even split, pinned to the basis);
 *
 *   forest co-ops — awarding bodies → operating units (forest
 *   directorates, local forest service offices, «the body's own
 *   services») → the biggest co-ops + one pooled node, from the
 *   `kind_mix` of `/api/dase/overview` (`queries_extra.dase_kind_mix`).
 *
 * Colours are CSS strings over the tokens (the palette doctrine of
 * 2026-09-03). The Anti-nero units are greys in rank order; the co-op
 * diagram reuses the /dase map's two forest greens.
 */
import type { DaseOverview } from '$lib/api';
import type { FlowLink, FlowNode } from '$lib/charts/KindFlow.svelte';
import { grInt } from '$lib/transforms/format';
import { unitEn } from '$lib/transforms/names';

/** `/api/antinero/unit-flow` */
export interface UnitFlowPayload {
	nodes: { id: string; label: string; side: 'l' | 'r'; n: number; eur: number; color?: string }[];
	links: FlowLink[];
	total_eur: number;
	n_units: number;
}

/** the /dase map's greens for the two forest kinds — the one place they
 *  are written, so the map and both diagrams cannot drift apart */
export const FOREST_KIND_COLOR = {
	dd: 'color-mix(in srgb, color-mix(in oklab, var(--c-dase) 84%, white) 56%, black)',
	dx: 'color-mix(in srgb, color-mix(in oklab, var(--c-dase) 75%, white) 87%, black)'
} as const;

/** the ΥΠΕΝ units in greys (ribbons take the unit's tone) */
const UNIT_GREYS = [
	'var(--ink)',
	'color-mix(in srgb, var(--ink) 73.5%, var(--paper))',
	'color-mix(in srgb, var(--ink) 52.2%, var(--paper))',
	'color-mix(in srgb, var(--ink) 33.5%, var(--paper))',
	'color-mix(in srgb, var(--ink) 21%, var(--paper))'
];

/** three columns, as the forest co-op diagram (user, 2026-08-22, for
 *  comparability): the awarding body — the Ministry, one node — → its
 *  operating units → contractors */
export function antineroAwardingFlow(uf: UnitFlowPayload): { nodes: FlowNode[]; links: FlowLink[] } {
	const unitNodes: FlowNode[] = uf.nodes.map((n, i) => ({
		...n,
		side: (n.side === 'l' ? 'm' : n.side) as 'l' | 'm' | 'r',
		label: n.side === 'l' ? unitEn(n.label) : n.label,
		color:
			n.side === 'l'
				? UNIT_GREYS[Math.min(i, UNIT_GREYS.length - 1)]
				: n.id === 'rest'
					? 'color-mix(in srgb, var(--ink) 44.5%, var(--paper))'
					: 'color-mix(in srgb, var(--ink) 87.8%, var(--paper))'
	}));
	const units = uf.nodes.filter((n) => n.side === 'l');
	const nodes: FlowNode[] = [
		{
			id: 'ministry',
			label: 'Ministry of Environment & Energy',
			side: 'l',
			n: units.reduce((s, n) => s + n.n, 0),
			eur: uf.total_eur,
			color: 'color-mix(in srgb, var(--ink) 53.3%, black)'
		},
		...unitNodes
	];
	const links: FlowLink[] = [
		...units.map((n) => ({ s: 'ministry', t: n.id, n: n.n, eur: n.eur })),
		...uf.links
	];
	return { nodes, links };
}

/** awarding-body categories, smallest first, in neutral greys — the first
 *  column of the delegation diagram */
export const BODY_KINDS: [string, string, string][] = [
	['region', 'regions', 'color-mix(in srgb, var(--ink) 17.4%, var(--paper))'],
	['other_public', 'other public bodies', 'color-mix(in srgb, var(--ink) 29.9%, var(--paper))'],
	['municipality', 'municipalities', 'color-mix(in srgb, var(--ink) 44.9%, var(--paper))'],
	[
		'decentralized_administration',
		'decentralized administrations',
		'color-mix(in srgb, var(--ink) 65.5%, var(--paper))'
	],
	['ministry', 'ministries', 'color-mix(in srgb, var(--ink) 86.4%, var(--paper))'],
	['unknown', 'unclassified', 'color-mix(in srgb, var(--ink) 11.2%, var(--paper))']
];

/** in the middle column the two non-forest kinds collapse into ONE node:
 *  «regional or municipal authorities» merely repeats what column 1
 *  already says, and «other public bodies» is wrong there anyway (the
 *  Ephorate of Antiquities is a unit OF the ministry, not another body);
 *  what they have in common is the honest label: the body's own services */
export const OWN = 'own';
export const MIDDLE_KINDS: [string, string, string][] = [
	[OWN, "the body's own services", 'color-mix(in srgb, var(--ink) 44.5%, var(--paper))'],
	['dd', 'forest directorates', FOREST_KIND_COLOR.dd],
	['dx', 'local forest service offices', FOREST_KIND_COLOR.dx]
];
export const midKind = (unit: string) => (unit === 'dx' || unit === 'dd' ? unit : OWN);

/** delegation diagram: awarding body → operating unit → contractor, ribbon
 *  width = € net; the pooled co-op node is co-ops too — a different colour
 *  would read as a different kind of contractor */
export function daseAwardingFlow(km: DaseOverview['kind_mix']): {
	nodes: FlowNode[];
	links: FlowLink[];
} {
	const f = km.flows ?? [];
	const bodies: FlowNode[] = BODY_KINDS.map(([k, label, color]) => ({
		id: `l:${k}`,
		label,
		color,
		side: 'l' as const,
		n: f.filter((x) => x.body === k).reduce((a, x) => a + x.n, 0),
		eur: f.filter((x) => x.body === k).reduce((a, x) => a + x.eur, 0)
	}));
	const units: FlowNode[] = MIDDLE_KINDS.map(([k, label, color]) => ({
		id: `m:${k}`,
		label,
		color,
		side: 'm' as const,
		n: f.filter((x) => midKind(x.unit) === k).reduce((a, x) => a + x.n, 0),
		eur: f.filter((x) => midKind(x.unit) === k).reduce((a, x) => a + x.eur, 0)
	}));
	const coops: FlowNode[] = (km.coops ?? []).map((c) => ({
		id: `r:${c.vat ?? 'other'}`,
		label: c.label ?? `${grInt(c.n_coops ?? 0)} other co-ops`,
		color: 'var(--c-dase)',
		side: 'r' as const,
		n: c.n,
		eur: c.eur,
		href: c.vat ? `/dase/coop/${c.vat}` : undefined
	}));
	const nodes = [...bodies, ...units, ...coops]
		.filter((n) => n.n > 0)
		.sort((a, b) => (a.side === b.side ? b.eur - a.eur : 0));
	const merge = (rows: { key: string; n: number; eur: number }[]) => {
		const m = new Map<string, FlowLink>();
		for (const r of rows) {
			const [s, t] = r.key.split('>');
			const cur = m.get(r.key);
			if (cur) {
				cur.n += r.n;
				cur.eur += r.eur;
			} else m.set(r.key, { s, t, n: r.n, eur: r.eur });
		}
		return [...m.values()];
	};
	const links = [
		...merge(f.map((x) => ({ key: `l:${x.body}>m:${midKind(x.unit)}`, n: x.n, eur: x.eur }))),
		...merge(
			(km.coop_flows ?? []).map((x) => ({
				key: `m:${midKind(x.unit)}>r:${x.vat ?? 'other'}`,
				n: x.n,
				eur: x.eur
			}))
		)
	];
	return { nodes, links };
}
