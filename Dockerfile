# Forestry Works Tracker — one container, two processes:
#
#   $PORT  ─►  node atlas/server.mjs        SvelteKit SSR + /api,/pdf proxy
#                └─► 127.0.0.1:5050         gunicorn atlas_api.app:create_app()
#
# Every byte the site serves is committed to the repository (three SQLite DBs,
# the pdftotext sidecars, the geo layers, the story images), so a deploy is a
# pure function of a git commit — there is no database to migrate and nothing
# to upload by hand. Built and rolled out by .github/workflows/deploy.yml.

# ---------------------------------------------------------------- stage 1
FROM node:22-bookworm-slim AS web
WORKDIR /app/atlas
COPY atlas/package.json atlas/package-lock.json ./
RUN npm ci
COPY atlas/ ./
# adapter-node precompresses html/js/json/css/svg/xml/wasm (its default), but
# not .geojson — the 1.2 MB EFFIS layer and the municipality outlines would
# ship raw. A .gz beside each one is served by the handler's static server.
RUN npm run build \
 && find build/client -name '*.geojson' -exec gzip -9k {} + \
 && npm prune --omit=dev

# ---------------------------------------------------------------- stage 2
FROM node:22-bookworm-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-venv \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# ATLAS_PDF_CACHE_BUDGET_MB: Cloud Run's writable filesystem is in-memory, so
# the on-demand PDF cache must stop growing at some point (DEPLOYMENT.md).
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    ATLAS_API_ORIGIN=http://127.0.0.1:5050 \
    ATLAS_PDF_CACHE_BUDGET_MB=200 \
    PORT=8080

# Python side: the JSON API and everything it imports read-only
RUN python3 -m venv /opt/venv
COPY requirements.txt deploy/requirements-deploy.txt ./
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt -r requirements-deploy.txt
COPY khmdhs/ ./khmdhs/
COPY webui/ ./webui/
COPY atlas_api/ ./atlas_api/

# Data read at request time (see .dockerignore for what is left out and why)
COPY data/processed/khmdhs.sqlite data/processed/dase.sqlite \
     data/processed/anadohoi.sqlite ./data/processed/
COPY data/processed/pdf_cache/ ./data/processed/pdf_cache/
COPY data/raw/ ./data/raw/
# the two geo layers the API itself reads (queries_extra: EFFIS fire dates,
# works-zone centroids) — the SvelteKit build serves its own copies
COPY atlas/static/geo/effis_fires.geojson atlas/static/geo/evia_works_zones.geojson \
     ./atlas/static/geo/

# Node side: adapter-node needs build/ + package.json + production node_modules
COPY --from=web /app/atlas/build ./atlas/build
COPY --from=web /app/atlas/node_modules ./atlas/node_modules
COPY atlas/package.json atlas/server.mjs ./atlas/

COPY deploy/start.sh ./deploy/start.sh
EXPOSE 8080
CMD ["bash", "deploy/start.sh"]
