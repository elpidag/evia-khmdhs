import { describe, expect, it } from 'vitest';
import { FIGURE_IMAGES } from './figureImages';

// the author's own markers, read from the story sources the Vite way
const sources = import.meta.glob('/src/content/story/*.md', {
	eager: true,
	query: '?raw',
	import: 'default'
}) as Record<string, string>;

// every built derivative on disk — the glob's keys ARE the files
const built = new Set(
	Object.keys(
		import.meta.glob('/static/img/story/**/*.webp', { eager: true, query: '?url' })
	)
);

function markerNumbers(): Set<number> {
	const out = new Set<number>();
	for (const s of Object.values(sources)) {
		for (const m of s.matchAll(/\[FIGURE (\d+):/g)) out.add(Number(m[1]));
	}
	return out;
}

describe('the delivered figure images', () => {
	it('keys every entry to one of the author’s own markers', () => {
		const markers = markerNumbers();
		for (const n of Object.keys(FIGURE_IMAGES).map(Number)) {
			expect(markers.has(n), `figure ${n}`).toBe(true);
		}
	});

	it('points every src at a built derivative on disk', () => {
		for (const [n, cfg] of Object.entries(FIGURE_IMAGES)) {
			for (const src of cfg.srcs) {
				expect(built.has(`/static${src}`), `figure ${n}: ${src}`).toBe(true);
			}
		}
	});

	it('lays figure 01 as the author numbered it: 18 cells, six rows of three', () => {
		const g = FIGURE_IMAGES[1];
		expect(g.kind).toBe('grid');
		expect(g.srcs).toHaveLength(18);
		// filename order IS the reading order — 01 top-left … 18 bottom-right
		expect(g.srcs[0].endsWith('01.webp')).toBe(true);
		expect(g.srcs[17].endsWith('18.webp')).toBe(true);
	});
});
