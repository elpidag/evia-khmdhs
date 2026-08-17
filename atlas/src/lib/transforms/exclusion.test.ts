import { describe, expect, it } from 'vitest';
import { isOutOfScope, trailChip } from './exclusion';

describe('trailChip', () => {
	it('says nothing about a live contract', () => {
		expect(trailChip({ cancelled: 0 })).toEqual({});
		expect(trailChip({ cancelled: 0, duplicate_of: null, related_to: null })).toEqual({});
	});

	it('calls a registry cancellation a cancellation, as a warning', () => {
		expect(trailChip({ cancelled: 1 })).toEqual({ chip: 'cancelled' });
	});

	it('never says «cancelled» for an out-of-scope contract', () => {
		// the curated exclusion sets cancelled = 1 as its mechanism — the
		// label must name the real reason (DATA_DECISIONS 2026-08-17)
		const chip = trailChip({ cancelled: 1, related_to: '25SYMV016885520' });
		expect(chip).toEqual({ chip: 'outside the dataset', chipBad: false });
	});

	it('treats an empty related_to (no in-scope sibling) the same way', () => {
		expect(trailChip({ cancelled: 1, related_to: '' })).toEqual({
			chip: 'outside the dataset',
			chipBad: false
		});
	});

	it('never says «cancelled» for a registry double-posting, but keeps warning', () => {
		// a duplicate upload IS a registry defect — it stays a warning chip;
		// only «outside the dataset» is a neutral statement of fact
		expect(trailChip({ cancelled: 1, duplicate_of: '24SYMV000000001' })).toEqual({
			chip: 'duplicate posting'
		});
	});

	it('prefers the out-of-scope reason when both markers are set', () => {
		expect(
			trailChip({ cancelled: 1, duplicate_of: '24SYMV000000001', related_to: '' }).chip
		).toBe('outside the dataset');
	});
});

describe('isOutOfScope', () => {
	it('is true only when related_to is present', () => {
		expect(isOutOfScope({ related_to: '' })).toBe(true);
		expect(isOutOfScope({ related_to: '25SYMV016885520' })).toBe(true);
		expect(isOutOfScope({ related_to: null })).toBe(false);
		expect(isOutOfScope({})).toBe(false);
	});
});
