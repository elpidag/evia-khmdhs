import { describe, expect, it } from 'vitest';
import { BLOCKS, NOTES, figureAt, timelineNote } from './content';
import { BINDINGS, resolveBindings } from './bindings';
import { EVENTS } from './events';

describe("the story's paragraph blocks (the author's own files)", () => {
	it('have unique ids in reading order', () => {
		const ids = BLOCKS.map((b) => b.id);
		expect(new Set(ids).size).toBe(ids.length);
		expect(BLOCKS.length).toBeGreaterThan(30);
	});

	it("carry the author's 13 figure markers, once each, in order", () => {
		const figs = BLOCKS.filter((b) => b.figure).map((b) => b.figure!.n);
		expect(figs).toEqual(Array.from({ length: 13 }, (_, i) => i + 1));
	});

	it("carry the document's 26 footnotes, referenced once each, in order", () => {
		// 19 until the author's chronology rewrite of 2026-09-18 (seven notes
		// on the programme's financing, contestation and the EU petition)
		const sups = BLOCKS.flatMap((b) => b.sups);
		expect(sups).toEqual(Array.from({ length: 26 }, (_, i) => i + 1));
		for (const n of sups) expect(NOTES.get(n)?.parts.length, `note ${n}`).toBeTruthy();
		expect(NOTES.size).toBe(26);
	});

	it('strip their markup: no tags, markers or clamped whitespace in the match text', () => {
		for (const b of BLOCKS) {
			expect(b.text).not.toMatch(/<|\[FIGURE|\n/);
			// a heading rank the parser does not know would surface as a
			// `#`-led paragraph — and pair with nothing on the page
			expect(b.text, b.id).not.toMatch(/^#/);
		}
	});

	it('carries the figure forward between markers', () => {
		const first = BLOCKS.findIndex((b) => b.figure);
		expect(figureAt(first)!.n).toBe(1);
		// a block after figure 1 and before figure 2 still shows figure 1
		const second = BLOCKS.findIndex((b) => b.figure && b.figure.n === 2);
		expect(figureAt(second - 1)!.n).toBe(1);
		expect(figureAt(BLOCKS.length - 1)).not.toBeNull();
	});

	it('links every citation chunk to the URL that followed it', () => {
		const n1 = NOTES.get(1)!.parts;
		expect(n1).toHaveLength(1);
		expect(n1[0].href).toContain('doi.org/10.1029/2020RG000726');
		expect(n1[0].href).not.toContain('utm_source');
		expect(n1[0].text.endsWith('e2020RG000726')).toBe(true);
		// NO URL is ever printed as text, in any part of any note
		for (const [, e] of NOTES) {
			for (const p of e.parts) {
				expect(p.text).not.toMatch(/https?:\/\//);
				if (p.href) expect(p.href).toMatch(/^https?:\/\//);
			}
		}
		// a note with no URL stays one plain part
		expect(NOTES.get(2)!.parts).toHaveLength(1);
		expect(NOTES.get(2)!.parts[0].href).toBeUndefined();
		// «see here: URL» reads as a clean link
		expect(NOTES.get(9)!.parts[0].text).toBe('For more information, see here');
		// a long note ending in one citation links only its «see:» tail
		// (the author, 2026-09-02, on note 6 — note 7 since the field-visit
		// note of 2026-09-03 became 5)
		const n6 = NOTES.get(7)!.parts;
		expect(n6).toHaveLength(2);
		expect(n6[0].href).toBeUndefined();
		expect(n6[0].text.includes('in spatial planning in Greece')).toBe(true);
		expect(n6[1].text.startsWith('see: Loukas Triantis')).toBe(true);
		expect(n6[1].href).toContain('doi.org/10.15488/18216');
		// the two-source notes carry TWO links, each on its own citation
		// (16 and 18 = Papageorgiou's pairs, 23 = the Court of Audit + Data
		// Journalists, since the 2026-09-18 renumbering)
		for (const nn of [16, 18, 23]) {
			const links = NOTES.get(nn)!.parts.filter((p) => p.href);
			expect(links, `note ${nn}`).toHaveLength(2);
			for (const p of links) expect(p.text.length).toBeGreaterThan(20);
		}
		// `[text](url)` links that text ALONE — the author's Word anchors
		// (2026-09-18): note 19 ends in two, note 20 in one, note 6 links the
		// word «link» and nothing before it
		const n19 = NOTES.get(19)!.parts;
		expect(n19.filter((p) => p.href).map((p) => p.text)).toEqual([
			'Parliamentary question',
			'Commission answer'
		]);
		expect(n19[0].href).toBeUndefined();
		expect(n19[0].text.startsWith('European Parliament')).toBe(true);
		expect(n19.map((p) => p.text).join('')).toContain('2025. Parliamentary question Commission answer');
		const n20 = NOTES.get(20)!.parts.filter((p) => p.href);
		expect(n20.map((p) => p.text)).toEqual(['Official petition record']);
		expect(n20[0].href).toContain('PETI-CM-785139_EN.pdf');
		const n6l = NOTES.get(6)!.parts.filter((p) => p.href);
		expect(n6l.map((p) => p.text)).toEqual(['link']);
		expect(n6l[0].href).toBe('https://2014-2020.espa.gr/el/Pages/staticOXE.aspx');
		expect(NOTES.get(6)!.parts.map((p) => p.text).join('')).toContain('development plan link. Overall');
	});

	it("the timeline's disclaimer comes from its own file, whole", () => {
		const note = timelineNote();
		expect(note).toContain('selective rather than exhaustive');
		expect(note).not.toContain('<');
	});
});

describe("the timeline bindings (the author's policy, at paragraph level)", () => {
	const bound = resolveBindings();

	it('every needle still matches a paragraph of the text', () => {
		const missing = BINDINGS.filter((b) => !bound.has(b.event)).map((b) => b.event);
		expect(missing).toEqual([]);
	});

	it('binds 21 events and names a real event in each binding', () => {
		const ids = new Set(EVENTS.map((e) => e.id));
		for (const b of BINDINGS) expect(ids, b.event).toContain(b.event);
		expect(new Set(BINDINGS.map((b) => b.event)).size).toBe(21);
	});

	it('every FIRE is bound to the paragraph covering its moment', () => {
		for (const e of EVENTS.filter((e) => e.lane === 'fire')) {
			expect(bound.has(e.id), e.id).toBe(true);
		}
	});

	it('the acts the text never mentions stay as unbound context', () => {
		const context = [
			'law-3889-2010-formalised',
			'law-4423-2016-redefined',
			'european-electronic-communications-code-directive',
			'european-climate-law-entered-into',
			'greek-national-climate-law',
			'initial-ratification-of-forest-maps',
			'a-subcommittee-of-the-government',
			'adoption-of-the-eu-carbon',
			'law-5281-2026-reformed-wildfire',
			'tender-for-forest-carbon-units'
		];
		for (const id of context) {
			expect(EVENTS.some((e) => e.id === id), id).toBe(true);
			expect(bound.has(id), id).toBe(false);
		}
	});

	it('binds the story to the timeline at its hinges, inside the chronology', () => {
		expect(bound.get('law-4824-2021-ratified')!.section).toBe('chronology');
		expect(bound.get('fires-in-evros')!.section).toBe('chronology');
		// the four 2021 fires share the season's paragraph
		const season = bound.get('fires-in-northern-evia')!.id;
		for (const id of ['fires-in-the-peloponese', 'fires-in-northern-attica', 'fires-in-western-attica']) {
			expect(bound.get(id)!.id).toBe(season);
		}
	});
});
