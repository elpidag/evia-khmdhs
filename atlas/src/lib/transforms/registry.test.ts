import { describe, it, expect } from 'vitest';
import { registryStatusNote } from './registry';

describe('registry status', () => {
	it('glosses a known status and keeps the register’s own word', () => {
		const s = registryStatusNote({ status: 'Διαγραφή' });
		expect(s).toContain('struck off the register (Διαγραφή)');
		expect(s).toContain('stays the contractor');
	});

	it('prints an unknown status in Greek alone rather than guessing', () => {
		expect(registryStatusNote({ status: 'Κάτι Άλλο' })).toContain('as Κάτι Άλλο.');
	});

	it('never prints a date — the API field is the registration date, not the status date', () => {
		expect(registryStatusNote({ status: 'Λύση - Εκκαθάριση' })).not.toMatch(/\d{2}[./]\d{2}/);
	});
});
