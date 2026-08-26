/**
 * A dataset page opens as a CARD — symbol, text, three KPIs, its key
 * frames — and «explore more» unfolds the rest below it on the same URL
 * (user, 2026-08-27). The unfolded state is not a parameter of its own: a
 * link into a frame (`#flows`) or one carrying a chart's lens (`?view=…`)
 * must open unfolded, so the state is READ from what the URL already says;
 * the button sets the `#more` hash.
 */
export const MORE_HASH = 'more';

export function isExpanded(url: URL, params: readonly string[]): boolean {
	if (url.hash && url.hash !== '#') return true;
	return params.some((p) => url.searchParams.has(p));
}

/** the URL «explore more» navigates to: the same page, hash `#more` */
export function moreHref(url: URL): string {
	return `${url.pathname}${url.search}#${MORE_HASH}`;
}

/** and «show less»: the same page, no hash */
export function lessHref(url: URL): string {
	return `${url.pathname}${url.search}`;
}
