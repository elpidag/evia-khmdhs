import { describe, expect, it } from 'vitest';
import { CHAPTERS } from './chapters';

describe('story chapters', () => {
	it('have unique kebab-case ids (they are anchors and file names)', () => {
		const ids = CHAPTERS.map((c) => c.id);
		expect(new Set(ids).size).toBe(ids.length);
		expect(ids.every((id) => /^[a-z][a-z0-9-]*$/.test(id))).toBe(true);
		expect(ids).toContain('chronology');
	});
});
