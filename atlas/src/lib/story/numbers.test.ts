import { describe, expect, it } from 'vitest';
import { NUMBERS, NUMBER_KEYS } from './numbers';

/**
 * The written text carries its figures as `<Num id="…" />` rather than typed
 * digits (the project's rule: a typed number rots on the next refresh). These
 * tests are what makes that safe — a renamed payload field or a mistyped id
 * fails here instead of silently printing «—» in the middle of a sentence.
 *
 * The content is read through Vite's own raw glob rather than `node:fs`, so the
 * file type-checks under svelte-check with no `@types/node` in the tsconfig.
 */
const RAW = import.meta.glob('/src/content/**/*.md', {
	eager: true,
	query: '?raw',
	import: 'default'
}) as Record<string, string>;

const files = Object.entries(RAW).map(([file, text]) => ({
	file: file.split('/').pop() as string,
	text
}));

const USES = /<Num\s+id="([^"]+)"/g;

describe('the written text\'s live figures', () => {
	it('finds the content to check', () => {
		expect(files.length).toBeGreaterThan(3);
	});

	it('asks only for figures the registry can supply', () => {
		const missing: string[] = [];
		for (const { file, text } of files) {
			for (const m of text.matchAll(USES)) {
				if (!NUMBER_KEYS.includes(m[1])) missing.push(`${file}: ${m[1]}`);
			}
		}
		expect(missing).toEqual([]);
	});

	it('imports Num wherever it uses one', () => {
		const bad = files
			.filter(({ text }) => USES.test(text) && !text.includes("from '$lib/story/Num.svelte'"))
			.map(({ file }) => file);
		USES.lastIndex = 0;
		expect(bad).toEqual([]);
	});

	it('reads every figure out of the page payload, formatted for English prose', () => {
		const data = {
			overview: {
				kpis: {
					n_contracts: 254,
					total_eur: 633588292.66,
					n_contractors: 157,
					median_eur: 2100443.31,
					n_coops: 246,
					n_orgs: 48,
					n_units: 99
				}
			}
		};
		expect(NUMBERS['antinero.contracts'](data)).toBe('254');
		expect(NUMBERS['antinero.total'](data)).toBe('€633.59 million');
		expect(NUMBERS['antinero.median'](data)).toBe('€2.10 million');
		expect(NUMBERS['dase.coops'](data)).toBe('246');
		expect(NUMBERS['dase.orgs'](data)).toBe('48');
		// thousands separated the English way — the site's own eur() is European
		// (1.234.567,50) and belongs in tables and charts, not in a sentence
		expect(NUMBERS['dase.contracts']({ overview: { kpis: { n_contracts: 2004 } } })).toBe('2,004');
		expect(NUMBERS['dase.median']({ overview: { kpis: { median_eur: 5792.44 } } })).toBe('€5,792');
	});

	it('says nothing rather than something wrong when the payload is absent', () => {
		for (const key of NUMBER_KEYS) expect(NUMBERS[key]({})).toBeNull();
	});

	it('reads the sponsored figures from that page\'s own payload shape', () => {
		const d = { o: { kpis: { n_projects: 69, n_companies: 36, n_stated: 44, stated_eur: 43284256.85 } } };
		expect(NUMBERS['ana.projects'](d)).toBe('69');
		expect(NUMBERS['ana.companies'](d)).toBe('36');
		expect(NUMBERS['ana.stated_n'](d)).toBe('44');
		expect(NUMBERS['ana.stated_eur'](d)).toBe('€43.28 million');
	});
});
