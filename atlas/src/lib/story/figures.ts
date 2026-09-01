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
import { ALERTS_CREDIT } from '$lib/transforms/alerts';

export interface LiveFigure {
	component: Component;
	/** the marker name the figure was built for — pinned against the text */
	name: string;
	credit?: string;
}

export const FIGURES: Record<number, LiveFigure> = {
	4: { component: AlertsMap, name: '112 emergency alerts', credit: ALERTS_CREDIT }
};
