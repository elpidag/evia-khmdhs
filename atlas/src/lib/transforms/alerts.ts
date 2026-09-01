/**
 * The «112» alerts of August 2021 — the data of the story's Figure 04
 * (DATA_DECISIONS 2026-09-02). The JSON is the curated source of truth
 * (scripts/bootstrap_alerts_112.py proposes and audits, every place verdict
 * is in the file with its evidence); this module types it, sorts it and
 * derives the few strings the figure prints, so no count or date is ever
 * typed into copy.
 */
import raw from '$lib/data/alerts_112_2021.json';

export type AlertType = 'evacuation' | 'shelter_in_place' | 'fire_danger' | 'general';

export interface Place {
	/** the hashtag as the message wrote it */
	tag: string;
	nameEn: string;
	lat: number | null;
	lon: number | null;
	/** gazetteer:evia-wildfire-timeline | hand | prose | unplaced */
	source: string;
	note?: string;
}

/** one instruction sentence: who was told to leave, and where to */
export interface Order {
	from: Place[];
	to: Place[];
}

export interface Alert {
	tweetId: string;
	/** ISO with the +03:00 offset the service posted in */
	timestamp: string;
	type: AlertType;
	region: string;
	orders: Order[];
	/** the tweet, verbatim */
	text: string;
	url: string;
	/** the English gloss the card prints when the message names no place */
	title?: string;
	note?: string;
}

interface AlertsFile {
	_meta: Record<string, unknown>;
	alerts: Alert[];
}

const FILE = raw as unknown as AlertsFile;

/** every alert, in the order it was sent */
export const ALERTS: Alert[] = [...FILE.alerts].sort(
	(a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp)
);

export type PlacedPlace = Place & { lat: number; lon: number };

export const placed = (p: Place): p is PlacedPlace => p.lat !== null && p.lon !== null;

export const placesOf = (a: Alert): Place[] => a.orders.flatMap((o) => [...o.from, ...o.to]);

/** the simulated window: midnight before the first day to midnight after
 *  the last, Athens time — the clock's [start, end] */
const DAY = 86_400_000;
const ATHENS = 3 * 3_600_000;
const dayStart = (ms: number) => Math.floor((ms + ATHENS) / DAY) * DAY - ATHENS;
export const START_MS = dayStart(Date.parse(ALERTS[0].timestamp));
export const END_MS = dayStart(Date.parse(ALERTS[ALERTS.length - 1].timestamp)) + DAY;

/** the mandatory attributions, printed under the author's caption */
export const ALERTS_CREDIT =
	'Imagery: EOxCloudless https://cloudless.eox.at by EOX IT Services GmbH ' +
	'(Contains modified Copernicus Sentinel data 2020) · Burnt area: NASA VIIRS ' +
	'VNP64A1, 500 m, mainland tile only (Rhodes and Grevena not covered) · ' +
	'Alerts: @112Greece, Γενική Γραμματεία Πολιτικής Προστασίας';

const MONTHS = [
	'January', 'February', 'March', 'April', 'May', 'June', 'July',
	'August', 'September', 'October', 'November', 'December'
];

/** «75 alerts · 1–23 August 2021» — the card's line before the first alert */
export function alertsIdleLine(alerts: Alert[] = ALERTS): string {
	const first = new Date(Date.parse(alerts[0].timestamp) + ATHENS);
	const last = new Date(Date.parse(alerts[alerts.length - 1].timestamp) + ATHENS);
	const span =
		first.getUTCMonth() === last.getUTCMonth()
			? `${first.getUTCDate()}–${last.getUTCDate()} ${MONTHS[first.getUTCMonth()]} ${first.getUTCFullYear()}`
			: `${first.getUTCDate()} ${MONTHS[first.getUTCMonth()]} – ${last.getUTCDate()} ${MONTHS[last.getUTCMonth()]} ${last.getUTCFullYear()}`;
	return `${alerts.length} alerts · ${span}`;
}
