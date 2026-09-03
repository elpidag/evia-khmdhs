/**
 * The story figures' CAPTIONS — the author's own file,
 * `src/content/story/captions.md` (their request, 2026-09-03: the caption
 * text must live where it can be written freely, long, and per carousel
 * slide, without touching the narrative's markup).
 *
 * The file is a list of blocks, each opened by a heading that names the
 * figure: `## 5` for a figure with one image, `## 2a` / `## 2b` for the
 * images of a figure the reader switches with the arrow (a = the first,
 * b = the second …). Anything after the number in the heading is a note to
 * the author and is ignored. The block's text is the caption; blank lines
 * make paragraphs; `[text](url)`, `*italic*` and `**bold**` are the only
 * mark-up — never raw HTML, which is the whole point of the move.
 *
 * Resolution order for a slot: the slide's own entry, then the figure's,
 * then the `[FIGURE nn: name]` marker's name (what the page printed before
 * this file existed) — so a figure with no entry keeps working.
 */
const RAW = import.meta.glob('/src/content/story/captions.md', {
	eager: true,
	query: '?raw',
	import: 'default'
}) as Record<string, string>;

const raw = RAW['/src/content/story/captions.md'] ?? '';

/** `2`, `2a` … → the caption's paragraphs, as written */
export const CAPTIONS: Map<string, string[]> = parse(raw);

function parse(text: string): Map<string, string[]> {
	const out = new Map<string, string[]>();
	// everything before the first heading is the file's own instructions
	const parts = text.split(/^##[ \t]+/m).slice(1);
	for (const part of parts) {
		const nl = part.indexOf('\n');
		const head = (nl === -1 ? part : part.slice(0, nl)).trim();
		const body = nl === -1 ? '' : part.slice(nl + 1);
		const key = normalise(head);
		if (!key) continue;
		const paras = body
			.split(/\n{2,}/)
			.map((p) => p.replace(/\s*\n\s*/g, ' ').trim())
			.filter(Boolean);
		if (paras.length) out.set(key, paras);
	}
	return out;
}

/** «02a», «FIGURE 2 A», «2» → `2a` / `2`; anything else → null */
function normalise(head: string): string | null {
	const m = /(\d+)\s*([a-z])?/i.exec(head.replace(/^figure\s*/i, ''));
	if (!m) return null;
	return String(Number(m[1])) + (m[2] ? m[2].toLowerCase() : '');
}

/**
 * The number a figure PRINTS (the author, 2026-09-03): the grid's 18 images
 * are figures 1-18, so every later figure shows its marker number + 17 —
 * marker 02 as «19», marker 13 as «30» — and a figure whose images the
 * reader pages through with the arrow adds the letter of the image on show
 * (the user, 2026-09-03): «19a», then «19b» … A single image adds nothing.
 */
export const DISPLAY_OFFSET = 17;
export function figureLabel(n: number, slot?: string): string {
	return String(n + DISPLAY_OFFSET).padStart(2, '0') + (slot ?? '');
}

/** the caption in force: the slide's own, else the figure's, else null */
export function captionFor(n: number, slot?: string): string[] | null {
	if (slot) {
		const own = CAPTIONS.get(`${n}${slot}`);
		if (own) return own;
	}
	return CAPTIONS.get(String(n)) ?? null;
}

/**
 * The author's small mark-up, rendered safely: every character is escaped
 * first, so the only tags in the result are the ones this function makes.
 */
export function renderCaption(text: string): string {
	return text
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, '<a href="$2">$1</a>')
		.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
		.replace(/\*([^*]+)\*/g, '<em>$1</em>');
}
