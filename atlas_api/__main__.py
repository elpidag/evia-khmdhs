"""Run with `python -m atlas_api` — starts the JSON API on 127.0.0.1:5050."""
import argparse
from pathlib import Path

from atlas_api.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m atlas_api")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5050)
    parser.add_argument("--db", type=Path, default=None)
    parser.add_argument("--dase-db", type=Path, default=None)
    parser.add_argument("--cache", type=Path, default=None)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    app = create_app(db_path=args.db, dase_db_path=args.dase_db,
                     pdf_cache_dir=args.cache)
    # threaded: the SvelteKit pages fan out parallel API calls
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


if __name__ == "__main__":
    main()
