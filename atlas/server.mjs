/**
 * Standalone production server: SvelteKit SSR (adapter-node handler) plus a
 * built-in proxy for /api and /pdf to the Flask API — one origin, no
 * external reverse proxy needed.
 *
 * Run: npm run build && npm run serve
 * Env: PORT (default 3000), ATLAS_API_ORIGIN (default http://127.0.0.1:5050),
 *      ATLAS_BASIC_AUTH (unset = open; "user:password" = private preview)
 */
import http from 'node:http';
import compression from 'compression';
import { handler } from './build/handler.js';

const API = new URL(process.env.ATLAS_API_ORIGIN ?? 'http://127.0.0.1:5050');
const PORT = Number(process.env.PORT ?? 3000);

// Private-preview gate. Unset — every local run, and the site once it is
// public — leaves the server exactly as it was; set, it guards pages, /api
// and /pdf alike, and keeps search engines out while the preview is up.
const BASIC_AUTH = process.env.ATLAS_BASIC_AUTH;
const EXPECTED = BASIC_AUTH ? `Basic ${Buffer.from(BASIC_AUTH).toString('base64')}` : null;

// The SSR document is the one response nobody else compresses: adapter-node
// precompresses the static assets at build time and the API gzips its JSON,
// but a rendered page (~220 KB on the data pages) would travel raw. The
// middleware leaves already-encoded responses (the .br/.gz statics) alone.
const compress = compression();

const notFound = (res) => {
	res.writeHead(404);
	res.end();
};

const server = http.createServer((req, res) => {
	if (EXPECTED) {
		if (req.headers.authorization !== EXPECTED) {
			res.writeHead(401, {
				'WWW-Authenticate': 'Basic realm="Forestry Works Tracker", charset="UTF-8"',
				'content-type': 'text/plain; charset=utf-8'
			});
			res.end('Authentication required');
			return;
		}
		res.setHeader('X-Robots-Tag', 'noindex, nofollow');
	}
	if (req.url.startsWith('/api/') || req.url.startsWith('/pdf/')) {
		const proxy = http.request(
			{
				hostname: API.hostname,
				port: API.port,
				path: req.url,
				method: req.method,
				headers: { ...req.headers, host: API.host }
			},
			(pres) => {
				res.writeHead(pres.statusCode ?? 502, pres.headers);
				pres.pipe(res);
			}
		);
		proxy.on('error', () => {
			res.writeHead(502, { 'content-type': 'text/plain; charset=utf-8' });
			res.end('API unavailable — start it with: python -m atlas_api');
		});
		req.pipe(proxy);
		return;
	}
	compress(req, res, () => handler(req, res, () => notFound(res)));
});

server.listen(PORT, () => {
	console.log(`atlas serving on http://127.0.0.1:${PORT} (API → ${API.origin})`);
});
