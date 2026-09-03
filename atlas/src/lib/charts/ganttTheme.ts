/**
 * Shared shape + palette for the sponsor-project Gantt (PromiseGantt) and
 * its legend (GanttLegend) — one source so the two can never drift.
 */

export interface GanttProject {
	ada: string;
	company: string;
	fire: string | null;
	start: string | null;
	deadline0: string | null;
	deadline: string | null;
	/** duration-based deadline wording when the act sets no date */
	dtext?: string | null;
	completed: string | null;
	revoked: string | null;
	status: string;
	/** stated commitment (€) — null when the act names no figure */
	budget_stated?: number | null;
	/** folded restated predecessor: its designation date + its € */
	start0?: string | null;
	budget0?: number | null;
}

// same palette as the status waffle (see StatusWaffle ORDER)
// live CSS strings over the tokens (Theme Lab round, 2026-09-03):
// active rides the ΔΑΣΕ green knob, the two greys are ink fades
// (--line IS the old #8F8F8F to the bit), revoked is the ink itself
// (was literal #000 — a 31/255 lightening nobody can see on a mark)
export const COLOR: Record<string, string> = {
	completed: 'var(--c-anadohoi)',
	active: 'var(--c-dase)',
	no_completion_recorded: 'var(--line)',
	revoked: 'var(--ink)',
	superseded: 'color-mix(in srgb, var(--ink) 21.4%, var(--paper))'
};

// statuses with their own extension fill (others reuse the row colour
// at low opacity)
export const EXT_COLOR: Record<string, string> = {
	active: 'color-mix(in srgb, var(--c-dase) 43.3%, var(--paper))'
};

/** running projects whose act sets no calendar deadline (duration wording
 *  only, or none) — no bar can be drawn to a deadline, so they get their
 *  own colour (NOTE: same pale green as the active extension segment) */
export const NODATE_COLOR = 'color-mix(in srgb, var(--c-dase) 43.3%, var(--paper))';

export const noDate = (p: GanttProject): boolean => p.status === 'active' && !p.deadline;

