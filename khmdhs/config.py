"""Paths and constants. Importing this module never touches the filesystem."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"

DEFAULT_INPUT = DATA_RAW / "contracts_search_results.xlsx"
DEFAULT_OUTPUT = DATA_PROCESSED / "contracts_search_results_enriched.xlsx"
DEFAULT_DB = DATA_PROCESSED / "khmdhs.sqlite"
DEFAULT_LOG = LOGS_DIR / "enrich_contracts.log"

API_URL = "https://cerpp.eprocurement.gov.gr/khmdhs-opendata/contract?page=0"
REQUEST_TIMEOUT = 30
THROTTLE_SECONDS = 0.2          # ~5 req/s; the API allows 350/min
RETRY_BACKOFFS = (1, 3, 8)      # extra retries beyond the first attempt

NEW_HEADERS = [
    "Επωνυμία Αναδόχου",
    "ΑΦΜ Αναδόχου",
    "Διαδικασία Ανάθεσης",
    "Οργανική Μονάδα",
    "Γεωγραφική Περιοχή (NUTS)",
    "Αποφαινόμενο Όργανο",
    "Συνολική Αξία με ΦΠΑ",
    "Κωδικοί CPV",
]
