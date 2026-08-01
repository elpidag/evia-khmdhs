/**
 * Standalone production server: SvelteKit SSR (adapter-node handler) plus a
 * built-in proxy for /api and /pdf to the Flask API — one origin, no
 * external reverse proxy needed.
 *
 * Run: npm run build && npm run serve
 * Env: PORT (default 3000), ATLAS_API_ORIGIN (default http://127.0.0.1:5050)
 */
import http from 'node:http';
import { handler } from './build/handler.js';

const API = new URL(process.env.ATLAS_API_ORIGIN ?? 'http://127.0.0.1:5050');
const PORT = Number(process.env.PORT ?? 3000);

const server = http.createServer((req, res) => {
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
	handler(req, res, () => {
		res.writeHead(404);
		res.end();
	});
});

server.listen(PORT, () => {
	console.log(`atlas serving on http://127.0.0.1:${PORT} (API → ${API.origin})`);
});
