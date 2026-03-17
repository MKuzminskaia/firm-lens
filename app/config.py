import os

# --- BASIC UI SETTINGS ---
APP_TITLE = "0.9 Layer"
APP_HEADER = "Firm-Lens"
SIDEBAR_MIN_WIDTH = "300px"
SIDEBAR_MAX_WIDTH = "300px"

# --- FILE PATHS ---
# Calculate the absolute path to the project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RULES_FILE_PATH = os.path.join(BASE_DIR, "data", "rules.json") 

# ---  WIKIDATA API SETTINGS(for WikidataService) ---
WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"
WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
API_TIMEOUT = 15 # Timeout in seconds so that the application does not hang forever if the server crashes
USER_AGENT = "FirmLensBot/1.0 (contact@example.com)" # Wikidata requires a User-Agent
ACCEPT = "application/sparql-results+json"

# --- EXPORT SETTINGS ---
EXPORT_FILE_PREFIX = "firm_lens_report"
CSV_MIME_TYPE = "text/csv"
EXCEL_MIME_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"