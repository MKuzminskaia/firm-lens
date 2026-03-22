import os

# --- BASIC UI SETTINGS ---
APP_TITLE = "Firm-Lens"
SIDEBAR_MIN_WIDTH = "300px"
SIDEBAR_MAX_WIDTH = "300px"

# --- FILE PATHS ---
# Calculate the absolute path to the project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RULES_FILE_PATH = os.path.join(BASE_DIR, "data", "rules.json") 

# ---  WIKIDATA API SETTINGS(for WikidataService) ---
WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"
WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
API_TIMEOUT = 25 # Timeout in seconds so that the application does not hang forever if the server crashes
USER_AGENT = 'FirmLensBot/1.0 (blackmarka@gmail.com)' # Wikidata requires a User-Agent
ACCEPT = "application/sparql-results+json"

# --- EXPORT SETTINGS ---
EXPORT_FILE_PREFIX = "firm_lens_report"
CSV_MIME_TYPE = "text/csv"
EXCEL_MIME_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# --- DEFAULT DICTIONARIES AND LISTS IN UYILS.PY---
GARBAGE_WORDS = ['llc', 'ltd', 'inc', 'corp']

POS_RULES = {
    "medical": 30,
    "health": 25,
    "clinic": 20,
    "ai": 10,
    "internet": 10,
}

NEG_RULES = {
    "gambling": -100,
    "adult": -100,
}


# --- DEFAULT DICTIONARIES AND LISTS IN SERVICES.PY---

BOOST_KEYWORDS = ['company', 
                  'enterprise', 
                  'business', 
                  'corporation', 
                  'firm', 
                  'manufacturer', 
                  'inc', 
                  'gmbh'
                  ]

PENALTY_KEYWORDS = ['film', 
                    'movie', 
                    'song', 
                    'album', 
                    'single', 
                    'human', 
                    'person', 
                    'biography', 
                    'fictional'
                    ]