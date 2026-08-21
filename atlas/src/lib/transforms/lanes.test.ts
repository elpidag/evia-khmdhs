import { describe, expect, it } from 'vitest';
import { buildLanes } from './lanes';

// the Καλαμπάκα shape (25SYMV016670155): five services, a study act first,
// then area acts — Σπερχειάδα accepted on its own, the rest still running
const AUTHS = [
	'Δασαρχείο Καλαμπάκας',
	'Δασαρχείο Λάρισας',
	'Δασαρχείο Μουζακίου',
	'Δασαρχείο Τρικάλων',
	'Δασαρχείο Σπερχειάδας'
];
const steps = [
	{ ref: 'A1', d: '2025-05-08', deadline: '2025-06-05', n: 1, scope: 'study', scope_auth: [] },
	{
		ref: 'A2',
		d: '2025-10-06',
		deadline: '2025-10-20',
		n: 2,
		scope: 'area',
		scope_auth: ['Δασαρχείο Μουζακίου', 'Δασαρχείο Σπερχειάδας']
	},
	{ ref: 'A3', d: '2025-12-05', deadline: '2025-12-31', n: 3, scope: 'area', scope_auth: ['Δασαρχείο Καλαμπάκας'] },
	{ ref: 'A4', d: '2026-01-09', deadline: '2026-02-14', n: 4, scope: null, scope_auth: [] },
	{ ref: 'A5', d: '2026-05-22', deadline: '2026-06-30', n: 5, scope: 'area', scope_auth: ['Δασαρχείο Καλαμπάκας'] }
];

describe('buildLanes', () => {
	it('returns no lanes when no act names an area — the single bar stays', () => {
		const r = buildLanes(AUTHS, steps.filter((s) => s.scope !== 'area'), [], null);
		expect(r.lanes).toEqual([]);
		expect(r.main.map((s) => s.ref)).toEqual(['A1', 'A4']);
	});

	it('one lane per linked service in order, a step on every lane it names', () => {
		const r = buildLanes(
			AUTHS,
			steps,
			[{ auth: 'Δασαρχείο Σπερχειάδας', d: '2025-11-11', ref: 'C1' }],
			{ d: '2026-07-01', ref: 'C0' },
			(n) => n.replace('Δασαρχείο ', '')
		);
		// Λάρισα and Τρίκαλα have no act and no acceptance of their own: no strip
		expect(r.lanes.map((l) => l.key)).toEqual([
			'Δασαρχείο Καλαμπάκας',
			'Δασαρχείο Μουζακίου',
			'Δασαρχείο Σπερχειάδας',
			'_unplaced'
		]);
		expect(r.lanes[0].label).toBe('Καλαμπάκας');
		expect(r.lanes[0].steps.map((s) => s.ref)).toEqual(['A3', 'A5']);
		// a step naming two services sits on both lanes
		expect(r.lanes[1].steps.map((s) => s.ref)).toEqual(['A2']);
		expect(r.lanes[2].steps.map((s) => s.ref)).toEqual(['A2']);
		// its own acceptance where one exists, the contract's (shared) otherwise
		expect(r.lanes[2].end).toEqual({ d: '2025-11-11', ref: 'C1', shared: false });
		expect(r.lanes[0].end).toEqual({ d: '2026-07-01', ref: 'C0', shared: true });
		// the studies stay on the contract bar; the unstated act gets its own lane
		expect(r.main.map((s) => s.ref)).toEqual(['A1']);
		const un = r.lanes[3];
		expect(un.unplaced).toBe(true);
		expect(un.label).toBe('area not stated');
		expect(un.steps.map((s) => s.ref)).toEqual(['A4']);
		expect(un.end).toBeNull();
	});

	it('a service with an own part-acceptance keeps its strip even without an act', () => {
		const r = buildLanes(
			['Δασαρχείο Λάρισας', 'Δασαρχείο Τρικάλων'],
			[{ ref: 'B1', d: '2025-01-01', deadline: '2025-02-01', n: 1, scope: 'area', scope_auth: ['Δασαρχείο Λάρισας'] }],
			[{ auth: 'Δασαρχείο Τρικάλων', d: '2025-03-01', ref: 'C9' }],
			null
		);
		expect(r.lanes.map((l) => l.key)).toEqual(['Δασαρχείο Λάρισας', 'Δασαρχείο Τρικάλων']);
		expect(r.lanes[1].end).toEqual({ d: '2025-03-01', ref: 'C9', shared: false });
	});

	it('a service named by an act but not linked to the contract is an extra lane', () => {
		const r = buildLanes(
			['Δασαρχείο Λάρισας'],
			[{ ref: 'B1', d: '2025-01-01', deadline: '2025-02-01', n: 1, scope: 'area', scope_auth: ['Δασαρχείο Ελασσόνας'] }],
			[],
			null
		);
		// the linked service has nothing to draw; the named one is an extra strip
		expect(r.lanes.map((l) => [l.key, l.extra ?? false])).toEqual([['Δασαρχείο Ελασσόνας', true]]);
		// no acceptance at all → no ✔ on any lane
		expect(r.lanes.every((l) => l.end === null)).toBe(true);
	});

	it('an area act whose service the registry lacks is said so, not guessed', () => {
		const r = buildLanes(
			['Δασαρχείο Λάρισας'],
			[
				{ ref: 'B1', d: '2025-01-01', deadline: '2025-02-01', n: 1, scope: 'area', scope_auth: ['Δασαρχείο Λάρισας'] },
				{ ref: 'B2', d: '2025-02-01', deadline: '2025-03-01', n: 2, scope: 'area', scope_auth: [] }
			],
			[],
			null
		);
		expect(r.lanes.at(-1)?.label).toBe('service not matched');
		expect(r.lanes.at(-1)?.steps.map((s) => s.ref)).toEqual(['B2']);
	});
});
