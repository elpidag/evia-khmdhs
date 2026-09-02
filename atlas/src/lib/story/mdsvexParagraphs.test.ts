import { describe, expect, it } from 'vitest';
import { compile } from 'mdsvex';
import { tagParagraphs } from '../../../scripts/remark-tag-paragraphs';
import { BLOCKS } from './content';
import { CHAPTERS } from './chapters';

const opts = { extensions: ['.md'], remarkPlugins: [tagParagraphs] };

// the author's files, raw — the same glob content.ts reads
const FILES = import.meta.glob('/src/content/story/*.md', {
	eager: true,
	query: '?raw',
	import: 'default'
}) as Record<string, string>;

describe('paragraphs that begin with a tag', () => {
	it('are wrapped in <p> like any other paragraph', async () => {
		const md =
			'First.\n\n<span class="figmark">[FIGURE 04: 112 emergency alerts]</span> The 2021 fire season<sup>4</sup>. More.\n\n<Num id="x" /> contracts were signed.\n\nPlain <span class="figmark">[FIGURE 05: x]</span> mid.\n';
		const out = (await compile(md, opts))!.code;
		expect(out).toContain(
			'<p><span class="figmark">[FIGURE 04: 112 emergency alerts]</span> The 2021 fire season<sup>4</sup>. More.</p>'
		);
		expect(out).toContain('<p><Num id="x" /> contracts were signed.</p>');
		expect(out).toContain('<p>Plain <span class="figmark">[FIGURE 05: x]</span> mid.</p>');
	});

	it('leaves block-level HTML and lone tags alone', async () => {
		const md = '<div class="x">\nblock\n</div>\n\n<hr>\n\nText.\n';
		const out = (await compile(md, opts))!.code;
		expect(out).not.toContain('<p><div');
		expect(out).not.toContain('<p><hr>');
		expect(out).toContain('<p>Text.</p>');
	});

	it("renders the author's files with one <p> or <h3> per parsed block", async () => {
		let rendered = 0;
		// only the sections the story RENDERS count — the folder also holds the
		// timeline disclaimer and the three dataset-card texts (author,
		// 2026-09-02: those appear on the card pages only)
		const shown = new Set(CHAPTERS.map((c) => `/src/content/story/${c.id}.md`));
		for (const [path, raw] of Object.entries(FILES)) {
			if (!shown.has(path)) continue;
			const code = (await compile(raw, opts))!.code;
			rendered += (code.match(/<p>/g) ?? []).length + (code.match(/<h3>/g) ?? []).length;
		}
		expect(rendered).toBe(BLOCKS.length);
	});

	it("the author's tag-led paragraphs carry no markdown that raw HTML would drop", () => {
		let checked = 0;
		for (const [path, raw] of Object.entries(FILES)) {
			for (const line of raw.split('\n')) {
				if (!/^<(span|Num)/.test(line)) continue;
				checked++;
				expect(line, `${path}: ${line.slice(0, 60)}`).not.toMatch(/\]\(|\*\*|(^|\s)_[^_]+_(\s|$)/);
			}
		}
		expect(checked).toBeGreaterThan(0);
	});
});
