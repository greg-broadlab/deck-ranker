PPTX_BASE = r"C:\Users\GregBrenner\Broadlab\Broadlab - NEW STRUCTURE - Documents"
SOFFICE = r"C:\Users\GregBrenner\LibreOffice\program\soffice.exe"
CACHE_DIR = "cache"
DB_PATH = "data/rankings.db"
PORT = 5050

CATEGORIES = {
    "intro": "Intro",
    "rtb": "RTB",
    "optimisation": "Optimisation",
    "eoc": "EOC",
    "qbr": "QBR",
}

# Match by filename keyword (case-insensitive)
CATEGORY_PATTERNS = {
    "rtb": ["rtb"],
    "optimisation": ["optim"],
    "eoc": ["eoc"],
    "qbr": ["qbr"],
}

# Match by folder path substring (case-insensitive) — checked before filename patterns
FOLDER_CATEGORIES = {
    "intro": ["business development\\bl presentations", "business development/bl presentations"],
}

SKIP_DIRS = ["_archive", "archive", "old"]

# Only include decks with these year markers in the filename
YEAR_MARKERS = ["_25", "_26", "25.", "26.", "2025", "2026", "oct25", "nov25", "dec25",
                "jan26", "feb26", "mar26", "apr26", "may26", "jun26"]

# Max decks per category (takes most recently modified)
MAX_PER_CATEGORY = 60
