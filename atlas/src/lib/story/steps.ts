/**
 * Which passage the reader is on — the story's one piece of scroll machinery.
 *
 * ONE IntersectionObserver whose root is a ~1 px band 45 % down the viewport;
 * the passage crossing that line is ACTIVE. This is scrollama's technique,
 * hand-rolled: there is no scroll listener (the app has exactly one, in the
 * layout), IO callbacks are dispatched by the browser off the scroll path, so
 * nothing is throttled and nothing runs per frame. The callback reads only
 * `isIntersecting` — no getBoundingClientRect, so it forces no layout.
 *
 * Above the first passage nothing crosses the line and `active` is null, which
 * IS the timeline's collapsed state — no special case for the top of the page.
 *
 * The markup must TILE: vertical rhythm belongs in padding INSIDE a beat, never
 * in margin between beats. A gap lets the band fall between two passages and
 * the active one flickers to nothing.
 */

export interface StepsOptions {
	/** beat ids in document order — decides the winner when two cross at once */
	order: readonly string[];
	/** where the reading line sits: 0 is the viewport top, 1 the bottom */
	line?: number;
	onActive: (id: string | null) => void;
}

export interface Steps {
	/** `use:steps.step={id}` on every beat */
	step(node: HTMLElement, id: string): { update(next: string): void; destroy(): void };
	stop(): void;
}

export function createSteps({ order, line = 0.45, onActive }: StepsOptions): Steps {
	const ids = new WeakMap<Element, string>();
	const live = new Set<string>();
	let io: IntersectionObserver | null = null;
	let current: string | null = null;
	let rank = new Map(order.map((id, i) => [id, i]));

	function ensure(): IntersectionObserver | null {
		// SSR, and engines without IO: the page renders whole and stays collapsed
		if (io || typeof IntersectionObserver === 'undefined') return io;
		const top = (line * 100).toFixed(1);
		const bottom = (100 - line * 100 - 0.1).toFixed(1);
		io = new IntersectionObserver(
			(entries) => {
				for (const e of entries) {
					const id = ids.get(e.target);
					if (!id) continue;
					if (e.isIntersecting) live.add(id);
					else live.delete(id);
				}
				// the LAST live beat in document order — deterministic whichever
				// way the reader is going, and independent of entry ordering
				let hit: string | null = null;
				let best = -1;
				for (const id of live) {
					const r = rank.get(id) ?? -1;
					if (r > best) {
						best = r;
						hit = id;
					}
				}
				// the band can settle in a GAP — a paragraph margin, a section
				// seam. That is not a change of reading position: HOLD the
				// current passage (the author, 2026-09-02: the rail rewound to
				// 2007 mid-chronology). Step BACK only when the current
				// passage's own exit says the reader went above it — the
				// entry's rects ride on the callback, so nothing forces layout.
				if (!hit && current) {
					const ex = entries.find((e) => !e.isIntersecting && ids.get(e.target) === current);
					if (ex && ex.boundingClientRect.top >= (ex.rootBounds?.bottom ?? 0)) {
						const i = rank.get(current) ?? 0;
						hit = i > 0 ? order[i - 1] : null;
					} else {
						return;
					}
				}
				if (hit === current) return;
				current = hit;
				onActive(hit);
			},
			{ rootMargin: `-${top}% 0px -${bottom}% 0px`, threshold: 0 }
		);
		return io;
	}

	return {
		step(node: HTMLElement, id: string) {
			ids.set(node, id);
			ensure()?.observe(node);
			return {
				update(next: string) {
					const was = ids.get(node);
					if (was && was !== next && live.delete(was)) live.add(next);
					ids.set(node, next);
				},
				destroy() {
					const was = ids.get(node);
					if (was) live.delete(was);
					io?.unobserve(node);
				}
			};
		},
		stop() {
			io?.disconnect();
			io = null;
			live.clear();
			current = null;
			rank = new Map();
		}
	};
}
