#!/usr/bin/env bash
# Container entrypoint: the JSON API first, then the web server in front of it.
# If either process dies the script exits, which stops the container and lets
# Cloud Run start a fresh one.
set -euo pipefail
trap 'kill 0' EXIT

/opt/venv/bin/gunicorn \
    --bind 127.0.0.1:5050 \
    --workers 1 --threads 8 \
    --timeout 120 \
    --access-logfile - --error-logfile - \
    'atlas_api.app:create_app()' &

# Wait for the API to accept connections before the web server can proxy to it
# — on a cold start a page request otherwise races gunicorn's import of
# queries/queries_extra and gets the "API unavailable" 502.
/opt/venv/bin/python - <<'PY'
import socket, sys, time
for _ in range(240):
    try:
        socket.create_connection(("127.0.0.1", 5050), 0.5).close()
        sys.exit(0)
    except OSError:
        time.sleep(0.25)
print("API did not start within 60s", file=sys.stderr)
sys.exit(1)
PY

node atlas/server.mjs &
wait -n
