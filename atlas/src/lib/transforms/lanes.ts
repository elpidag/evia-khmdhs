/**
 * Per-area lanes under the contract timeline (user, 2026-08-21).
 *
 * A «τμηματική παράταση» extends ONE τμηματική προθεσμία — most often the
 * works in one forest service's area — so a contract covering five
 * Δασαρχεία runs on five clocks. The single bar kept only the last of them.
 * Where the extension acts NAME areas (`scope_auth`, resolved against the
 * authority registry), the page draws one thin lane per service under the
 * contract bar: the steps that act names, and the service's own acceptance
 * where ΥΠΕΝ signed one («για το τμήμα περιοχής ευθύνης Δασαρχείου Χ»),
 * else the contract's shared acceptance, lighter.
 *
 * What stays on the contract bar: the studies' submission, a stage, the
 * whole — things that are not an area. An act that names NO area extends
 * every area the contract's title names (user rule, 2026-08-21: «no subset
 * named = all the areas»), so it sits on every linked service's strip,
 * flagged `all_areas`. What cannot be placed: an area act naming a service
 * the registry lacks — one honest lane of its own, never a guessed one.
 *
 * Pure function; the numbers are the page's, the rule is pinned by tests.
 */

export interface LaneStepLike {
	ref: string;
	d: string | null;
	deadline: string | null;
	n: number;
	scope?: string | null;
	scope_text?: string | null;
	scope_auth?: string[];
	/** one act, several dates: which service got which (hand-read) */
	area_dates?: Record<string, string> | null;
	/** set by buildLanes: the act names no subset, so it extends every
	 *  area the contract's title names (user rule, 2026-08-21) */
	all_areas?: boolean;
}

export interface LaneEnd {
	/** ISO date the part (or the contract) was accepted */
	d: string;
	/** the acceptance act — pairs the ✔ with its trail row */
	ref: string;
	/** true = the contract's single acceptance, not this area's own */
	shared: boolean;
}

export interface Lane<T extends LaneStepLike = LaneStepLike> {
	key: string;
	/** printed at the left of the lane (English service name on the page) */
	label: string;
	/** canonical Greek authority name, null for the unplaced lane */
	auth: string | null;
	/** the steps on this strip — an unsaid act carries `all_areas` */
	steps: (T & { all_areas?: boolean })[];
	end: LaneEnd | null;
	/** the service is named by an act but not linked to the contract */
	extra?: boolean;
	/** the acts that name no area / no service we know */
	unplaced?: boolean;
}

export interface PartEnd {
	auth: string;
	d: string;
	ref: string;
}

export interface LaneResult<T extends LaneStepLike> {
	lanes: Lane<T>[];
	/** the steps that stay on the contract bar */
	main: T[];
}

const MAIN_SCOPES = new Set(['study', 'stage', 'whole']);

/**
 * @param authorities the contract's linked services, canonical names, in order
 * @param steps every extension step of the chain (API order)
 * @param partEnds per-part acceptances (`part_auth` on completion acts)
 * @param sharedEnd the contract's acceptance, if any
 * @param labelOf canonical name → printed label
 */
export function buildLanes<T extends LaneStepLike>(
	authorities: string[],
	steps: T[],
	partEnds: PartEnd[],
	sharedEnd: { d: string; ref: string } | null,
	labelOf: (name: string) => string = (n) => n
): LaneResult<T> {
	const named = steps.filter((s) => s.scope === 'area' && (s.scope_auth?.length ?? 0) > 0);
	if (named.length === 0) return { lanes: [], main: steps };
	// no subset named → every area the contract covers (its linked services)
	const unstated = steps.filter((s) => !s.scope).map((s) => ({ ...s, all_areas: true }));

	const order = [...authorities];
	for (const s of named)
		for (const a of s.scope_auth ?? []) if (!order.includes(a)) order.push(a);

	const lanes: Lane<T>[] = order
		.map((auth) => {
			const own = partEnds.find((p) => p.auth === auth);
			return {
				key: auth,
				label: labelOf(auth),
				auth,
				// a step naming several services sits on each of their strips —
				// with ITS OWN date where the act granted different ones per area
				steps: [
					...named
						.filter((s) => (s.scope_auth ?? []).includes(auth))
						.map((s) => (s.area_dates?.[auth] ? { ...s, deadline: s.area_dates[auth] } : s)),
					...(authorities.includes(auth) ? unstated : [])
				].sort((a, b) => a.n - b.n),
				end: own
					? { d: own.d, ref: own.ref, shared: false }
					: sharedEnd
						? { d: sharedEnd.d, ref: sharedEnd.ref, shared: true }
						: null,
				extra: !authorities.includes(auth)
			};
		})
		// a service whose deadline was never extended and which has no
		// acceptance of its own has no grey part — and therefore no strip
		// (user, 2026-08-21: an empty row read as an unbalanced bar)
		.filter((l) => l.steps.length > 0 || (l.end !== null && !l.end.shared));

	const unmatched = steps.filter((s) => s.scope === 'area' && !(s.scope_auth?.length ?? 0));
	if (unmatched.length) {
		lanes.push({
			key: '_unplaced',
			label: 'service not matched',
			auth: null,
			steps: [...unmatched].sort((a, b) => a.n - b.n),
			end: null,
			unplaced: true
		});
	}

	return { lanes, main: steps.filter((s) => MAIN_SCOPES.has(s.scope ?? '')) };
}
