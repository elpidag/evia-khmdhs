"""Atlas JSON API — read-only Flask backend for the Atlas (SvelteKit) web UI.

Imports the frozen query modules from webui/ but never modifies them; all
new SQL lives in atlas_api/queries_extra.py.
"""
__version__ = "0.1.0"
