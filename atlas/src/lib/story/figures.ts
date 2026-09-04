/**
 * The story's LIVE figures — the pattern for all thirteen (DATA_DECISIONS
 * 2026-09-02): keyed by the AUTHOR'S OWN figure number, the one their
 * `[FIGURE xx: name]` marker carries, so the slot shows a drawing exactly
 * where the text says the image changes and the caption stays theirs. A
 * figure declares its component and, where the material demands it, the
 * credit line printed under the caption (imagery and data attributions).
 *
 * figures.test.ts pins every key to an existing marker and the marker's
 * name, so a renumbering by the author fails loudly instead of showing a
 * drawing under the wrong caption.
 */
import type { Component } from 'svelte';
import AlertsMap from '$lib/story/figures/AlertsMap.svelte';
import ContractType from '$lib/story/figures/ContractType.svelte';

export interface LiveFigure {
	component: Component;
	/** the marker name the figure was built for — pinned against the text */
	name: string;
	credit?: string;
	/** the slot's shape: the artboard's SQUARE (default) or the drawing's own
	 *  height (`auto` — the CONTRACT TYPE bars, 2026-09-03) */
	frame?: 'square' | 'auto';
}

export const FIGURES: Record<number, LiveFigure> = {
	// no credit line under it (the author, 2026-09-04); the attributions the
	// imagery and burnt-area data require live in ALERTS_CREDIT
	// (transforms/alerts.ts) for the SOURCES section to carry
	4: { component: AlertsMap, name: '112 emergency alerts' },
	// the Anti-nero page's CONTRACT TYPE frame, live (the author, 2026-09-03)
	// no credit line under it (the author, 2026-09-03): the figure carries
	// the frame's own title and lens toggle instead
	10: { component: ContractType, name: 'types of work graph', frame: 'auto' }
};
