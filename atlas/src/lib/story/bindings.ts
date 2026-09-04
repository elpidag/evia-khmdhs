/**
 * WHICH PARAGRAPH each timeline event belongs beside — the binding the
 * author's spreadsheet does not carry, curated here under their policy
 * (agreed 2026-09-01, built at paragraph level 2026-09-02):
 *
 *  · an event the story text NAMES binds to the paragraph that names it;
 *  · a FIRE the text does not name binds to the paragraph covering its
 *    moment (the 2021 fires to the 2021-season paragraph, Rhodes to the
 *    2023 paragraph);
 *  · the ten acts the text never mentions stay UNBOUND — context on the
 *    timeline, lit by year, not clickable.
 *
 * Each binding is a VERBATIM needle from the author's own text; it is
 * resolved to a paragraph at runtime by substring match, so the author can
 * edit around it freely, and a vitest fails loudly when an edit removes the
 * phrase itself. Typographic apostrophes are the text's own.
 */
import { BLOCKS, type StoryBlock } from '$lib/story/content';

export interface Binding {
	/** the StoryEvent id */
	event: string;
	/** a verbatim phrase of the paragraph the event belongs beside */
	needle: string;
}

export const BINDINGS: Binding[] = [
	// ── named in the story text ────────────────────────────────────────────
	{ event: 'fires-in-the-peloponnese', needle: 'swept southern Greece in the summer of 2007' },
	{ event: 'fires-in-mati-attica', needle: 'surpassed in 2018 by the fire in Mati' },
	{ event: 'launch-of-the-interim-outbound', needle: 'pilot use of the outbound' },
	{ event: 'full-operational-launch', needle: 'During the COVID-19 lockdowns' },
	{ event: 'european-green-deal', needle: 'context of the European Green Deal' },
	{ event: 'eu-forest-strategy-for-2030', needle: 'EU Forest Strategy for 2030 followed' },
	{
		event: 'extensive-use-of-112-emergency',
		needle: 'The 2021 fire season was the first one during which 112'
	},
	{ event: 'fires-in-northern-evia', needle: '50,000 of them in North Evia alone' },
	{
		event: 'prime-minister-s-press-conference',
		needle: 'During a press conference the Prime Minister announced'
	},
	{
		event: 'emergency-legislative-act-on-fire',
		needle: 'enacted through an emergency legislative act'
	},
	{ event: 'law-4824-2021-ratified', needle: 'ratified by Parliament through Law 4824/2021' },
	{ event: 'law-4843-2021-introduces-special', needle: 'Article 74 of Law 4843/2021' },
	{ event: 'law-4876-2021-extends-exceptional', needle: 'Article 76 of Law 4876/2021' },
	{
		event: 'official-launch-of-the-antinero',
		needle: 'publicly presented by the Ministry of Environment and Energy on 8 July 2022'
	},
	{ event: 'fires-in-evros', needle: 'fires that broke out near Alexandroupolis' },
	{ event: 'establishment-of-a-special-committee', needle: 'chaired the new committee' },
	{
		event: 'law-5106-introduced-the-hybrid',
		needle: 'Law 5106/2024 introduced Hybrid Cooperative Schemes'
	},
	// ── fires the text does not name: the paragraph covering their moment ──
	{ event: 'fires-in-the-peloponese', needle: '125,000 hectares of forest and agricultural land' },
	{ event: 'fires-in-northern-attica', needle: '125,000 hectares of forest and agricultural land' },
	{ event: 'fires-in-western-attica', needle: '125,000 hectares of forest and agricultural land' },
	{ event: 'fires-in-rhodes', needle: 'fires that broke out near Alexandroupolis' }
	// everything else stays unbound: timeline context the narrative never
	// mentions (laws 3889/4423/4936/5281, the forest-maps and state-aid acts,
	// the EU directives and the carbon instruments)
];

/**
 * event id → the block it binds to. Resolved once against the blocks' own
 * text; a needle that no longer matches resolves to nothing (and fails the
 * pinning test, which is the point — the author's edits surface loudly).
 */
export function resolveBindings(blocks: StoryBlock[] = BLOCKS): Map<string, StoryBlock> {
	const out = new Map<string, StoryBlock>();
	for (const b of BINDINGS) {
		const hit = blocks.find((bl) => bl.text.includes(b.needle));
		if (hit) out.set(b.event, hit);
	}
	return out;
}
