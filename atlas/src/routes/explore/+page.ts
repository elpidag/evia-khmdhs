// The row payload (~2.3k rows) is fetched post-hydration via apiGetCached
// and filtered entirely client-side — no server round-trips per keystroke.
export const load = () => ({});
