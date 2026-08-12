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
export const COLOR: Record<string, string> = {
	completed: 'var(--c-anadohoi)',
	active: '#52b788',
	no_completion_recorded: '#8F8F8F',
	revoked: '#000000',
	superseded: '#CFCFCF'
};

// statuses with their own extension fill (others reuse the row colour
// at low opacity)
export const EXT_COLOR: Record<string, string> = {
	active: '#b7e4c7'
};

/** running projects whose act sets no calendar deadline (duration wording
 *  only, or none) — no bar can be drawn to a deadline, so they get their
 *  own colour (NOTE: same pale green as the active extension segment) */
export const NODATE_COLOR = '#b7e4c7';

export const noDate = (p: GanttProject): boolean => p.status === 'active' && !p.deadline;

