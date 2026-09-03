/**
 * The story's content, read at PARAGRAPH granularity from the author's own
 * .md files — the machinery behind everything on /story that follows the
 * reader (the author's ruling, 2026-09-02): the figure in force changes at
 * their `[FIGURE xx: name]` markers, the footnotes shown are those of the
 * paragraphs on screen, and the timeline follows the passage being read.
 *
 * The files stay the single source of truth. This module parses their RAW
 * text into ordered BLOCKS (paragraphs and sub-headings), each knowing its
 * section, its footnote superscripts, and the figure marker it carries; the
 * page pairs these one-to-one with the rendered elements. A vitest pins the
 * pairing invariants so an edit that breaks the correspondence fails loudly.
 */
import { CHAPTERS } from '$lib/story/chapters';

export interface StoryBlock {
	/** `${section}-b${i}` — also the rendered element's id, so a timeline
	 *  bullet can scroll to the exact paragraph */
	id: string;
	section: string;
	kind: 'p' | 'h3';
	/** the block's text with tags stripped — what needles match against */
	text: string;
	/** the footnote numbers this block references */
	sups: number[];
	/** the `[FIGURE xx: name]` marker this block carries, if any */
	figure: { n: number; name: string } | null;
}

const RAW = import.meta.glob('/src/content/story/*.md', {
	eager: true,
	query: '?raw',
	import: 'default'
}) as Record<string, string>;

const rawOf = (id: string): string => RAW[`/src/content/story/${id}.md`] ?? '';

/** the body (before the notes list) and the notes of one section's file */
function split(id: string): { body: string; notes: Map<number, string> } {
	let raw = rawOf(id).replace(/^<script>[\s\S]*?<\/script>\s*/, '');
	const notes = new Map<number, string>();
	const cut = raw.lastIndexOf('\n---\n');
	if (cut !== -1) {
		for (const line of raw.slice(cut + 5).split('\n')) {
			const m = /^(\d+)\.\s+(.*\S)/.exec(line);
			if (m) notes.set(Number(m[1]), m[2]);
		}
		raw = raw.slice(0, cut);
	}
	return { body: raw, notes };
}

function blocksOf(section: string): StoryBlock[] {
	const { body } = split(section);
	const out: StoryBlock[] = [];
	for (const part of body.split(/\n{2,}/)) {
		const t = part.trim();
		if (!t) continue;
		const h3 = t.startsWith('### ');
		// the author writes `[FIGURE 05: Press conference]` as plain text since
		// 2026-09-03 (the span is added at build time); the name is optional —
		// the caption itself lives in captions.md
		const fig = /\[FIGURE\s*(\d+)\s*(?::\s*([^\]]+?))?\s*\]/.exec(t);
		out.push({
			id: `${section}-b${out.length}`,
			section,
			kind: h3 ? 'h3' : 'p',
			text: t
				.replace(/^###\s+/, '')
				.replace(/<span class="figmark">[^<]*<\/span>/g, ' ')
				.replace(/\[FIGURE\s*\d+\s*(?::[^\]]*)?\]/g, ' ')
				.replace(/<[^>]+>/g, '')
				.replace(/\s+/g, ' ')
				.trim(),
			sups: [...t.matchAll(/<sup>(\d+)<\/sup>/g)].map((m) => Number(m[1])),
			figure: fig ? { n: Number(fig[1]), name: (fig[2] ?? '').trim() } : null
		});
	}
	return out;
}

/** every narrative block, in reading order (the disclaimer is the timeline's) */
export const BLOCKS: StoryBlock[] = CHAPTERS.flatMap((c) => blocksOf(c.id));
export const BLOCK_INDEX = new Map(BLOCKS.map((b, i) => [b.id, i]));

export interface NotePart {
	text: string;
	/** set on a citation chunk: the URL that followed it in the note */
	href?: string;
}
export interface NoteEntry {
	/** the note in reading order: linked citation chunks and plain glue */
	parts: NotePart[];
}

/**
 * A note may cite SEVERAL sources (the author's 13 and 14 carry two each):
 * every URL leaves the display text and the citation chunk BEFORE it becomes
 * the link; the separators between citations stay as plain glue, and text
 * after the last URL stays plain. Tracking params are stripped from targets.
 */
function noteEntry(t: string): NoteEntry {
	const parts: NotePart[] = [];
	const re = /https?:\/\/\S+/g;
	let pos = 0;
	let m: RegExpExecArray | null;
	while ((m = re.exec(t))) {
		let chunk = t.slice(pos, m.index);
		const lead = /^[\s,;:]+/.exec(chunk)?.[0];
		if (lead && parts.length) parts.push({ text: lead.replace(/\s+/g, ' ') });
		chunk = (lead ? chunk.slice(lead.length) : chunk).replace(/[\s,;:]+$/, '');
		const punct = /[.,;:\u002f]*$/.exec(m[0])?.[0] ?? '';
		const href = m[0]
			.replace(/[.,;:]+$/, '')
			.replace(/[?&]utm_source=chatgpt\.com/, '');
		// a «see:» inside the chunk marks where the citation begins — only
		// that tail carries the link (the author, 2026-09-02, on note 6: a
		// long explanatory note ending in one cited source must not be
		// underlined whole)
		const at = chunk.toLowerCase().lastIndexOf('see:');
		if (at > 0) {
			parts.push({ text: chunk.slice(0, at) });
			chunk = chunk.slice(at);
		}
		if (chunk) parts.push({ text: chunk, href });
		pos = re.lastIndex;
		// «…-pyrkagies/; Papageorgiou…»: the separator the URL swallowed stays
		// as glue between the citations
		const sep = punct.replace(/[\u002f.]/g, '');
		if (sep && t.slice(pos).trim()) parts.push({ text: `${sep} ` });
	}
	const tail = t.slice(pos).replace(/^[\s,;:]+/, '').replace(/\s+$/, '');
	if (tail) parts.push({ text: tail });
	if (!parts.length) parts.push({ text: t.trim() });
	return { parts };
}

/** footnote number → its entry, across all sections (numbering is document-wide) */
export const NOTES: Map<number, NoteEntry> = (() => {
	const all = new Map<number, NoteEntry>();
	for (const c of CHAPTERS) for (const [n, t] of split(c.id).notes) all.set(n, noteEntry(t));
	return all;
})();

/** the figure IN FORCE at a block: its own marker, or the last one before it */
export function figureAt(index: number): { n: number; name: string } | null {
	for (let i = Math.min(index, BLOCKS.length - 1); i >= 0; i--) {
		if (BLOCKS[i].figure) return BLOCKS[i].figure;
	}
	return null;
}

/** the timeline's disclaimer, printed under the collapsed axis */
export function timelineNote(): string {
	return split('timelinedisclaimer').body.trim();
}
