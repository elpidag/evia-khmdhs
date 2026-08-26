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
	/** the dataset hue token; the two tools take the ink */
	color: string;
	/** hub rank: the three streams large, the two tools small */
	rank: 'stream' | 'tool';
}

export const SYMBOLS: SiteSymbol[] = [
	{
		key: 'anadohoi',
		href: '/anadohoi',
		label: 'sponsored projects',
		color: 'var(--c-anadohoi)',
		rank: 'stream'
	},
	{
		key: 'antinero',
		href: '/antinero',
		label: 'anti-nero programme',
		color: 'var(--c-antinero)',
		rank: 'stream'
	},
	{
		key: 'dase',
		href: '/dase',
		label: "works executed by forest workers' co-operatives",
		color: 'var(--c-dase)',
		rank: 'stream'
	},
	{
		key: 'search',
		href: '/explore',
		label: 'search',
		color: 'var(--ink)',
		rank: 'tool'
	},
	{
		key: 'actors',
		href: '/authorities',
		label: 'network of actors',
		color: 'var(--ink)',
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
