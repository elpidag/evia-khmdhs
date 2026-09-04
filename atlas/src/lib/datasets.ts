/**
 * The site's five symbols — ONE list feeding the header strip, the data hub
 * and the dataset cards (user mocks, 2026-08-27). The labels are the mock's
 * placeholders until the user names the streams; the symbol images arrive
 * later and replace the placeholder squares in DatasetSymbol.svelte alone.
 */
export type DatasetKey = 'anadohoi' | 'antinero' | 'dase';
export type SymbolKey = DatasetKey | 'search' | 'actors';

export interface SiteSymbol {
	key: SymbolKey;
	href: string;
	/** the caption under the symbol */
	label: string;
	/** the wording inside the header's 60 px square (Artboard 4) */
	short?: string;
	/** the card headline's own line breaks, as the artboard sets them */
	titleLines?: string[];
	/** the square's fill on the header band (Artboard 4, user 2026-08-27;
	 *  the band is a gradient of the three stream hues since 2026-09-03) —
	 *  the dataset hue where it reads on the dark band, a pale FADE of the
	 *  same hue where it does not, so every square follows its token */
	chip: string;
	/** the dataset hue token; the two tools take the ink */
	color: string;
	/** the author's own SYMBOL, an SVG under static/img/symbols, drawn as a
	 *  mask in the stream's hue on the hub and the card (2026-09-04, the
	 *  co-op's first); the header band keeps its lettered squares */
	symbol?: string;
	/** hub rank: the three streams large, the two tools small */
	rank: 'stream' | 'tool';
}

export const SYMBOLS: SiteSymbol[] = [
	{
		key: 'anadohoi',
		href: '/anadohoi',
		// renamed by the user on 2026-08-27: the stream's name everywhere
		label: 'financed by private companies',
		// the 59,5 px square cannot hold the whole name at a readable size
		short: 'private companies',
		titleLines: ['financed', 'by', 'private companies'],
		color: 'var(--c-anadohoi)',
		symbol: '/img/symbols/financed.svg',
		chip: 'var(--c-anadohoi)',
		rank: 'stream'
	},
	{
		key: 'antinero',
		href: '/antinero',
		label: 'anti-nero programme',
		color: 'var(--c-antinero)',
		// the Anti-nero hue is black, which cannot sit on the dark band —
		// a 5% fade of it into paper (#f2f2f2 at the default palette)
		chip: 'color-mix(in srgb, var(--c-antinero) 5%, var(--paper))',
		rank: 'stream'
	},
	{
		key: 'dase',
		href: '/dase',
		label: "works executed by forest workers' co-operatives",
		short: "forest workers' co-ops",
		color: 'var(--c-dase)',
		symbol: '/img/symbols/coop.svg',
		chip: 'var(--c-dase)',
		rank: 'stream'
	},
	{
		key: 'search',
		href: '/explore',
		label: 'search',
		color: 'var(--ink)',
		symbol: '/img/symbols/search.svg',
		chip: 'color-mix(in srgb, var(--ink) 5.8%, var(--paper))',
		rank: 'tool'
	},
	{
		key: 'actors',
		href: '/authorities',
		label: 'network of actors',
		color: 'var(--ink)',
		chip: 'color-mix(in srgb, var(--c-dase) 43.3%, var(--paper))',
		rank: 'tool'
	}
];

export const DATASETS = SYMBOLS.filter((s) => s.rank === 'stream');

export function symbolFor(key: SymbolKey): SiteSymbol {
	const s = SYMBOLS.find((x) => x.key === key);
	if (!s) throw new Error(`unknown symbol ${key}`);
	return s;
}

/** which symbol a pathname belongs to (the entity pages count with their dataset) */
export function symbolOfPath(pathname: string): SymbolKey | null {
	if (pathname === '/authorities' || pathname.startsWith('/authority/')) return 'actors';
	for (const s of SYMBOLS) {
		if (pathname === s.href || pathname.startsWith(s.href + '/')) return s.key;
	}
	return null;
}
