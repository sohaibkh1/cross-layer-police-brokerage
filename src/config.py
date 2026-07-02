from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
TABLES_DIR = OUTPUTS_DIR / "tables"
FIGURES_DIR = OUTPUTS_DIR / "figures"
REPORT_DIR = PROJECT_ROOT / "report"
REPORT_FIGURES_DIR = REPORT_DIR / "figures"

DATA_PAGE_URL = "https://data.police.uk/data/"

FORCES = {
    "metropolitan": "Metropolitan Police Service",
    "west-midlands": "West Midlands Police",
    "south-wales": "South Wales Police",
}

FORCE_ORDER = ["metropolitan", "west-midlands", "south-wales"]

# Latest six months listed on data.police.uk at the time this project was built
# (checked on 2026-06-23).
MONTHS = ["2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04"]

KEEP_COLUMNS = [
    "force",
    "force_slug",
    "month",
    "crime_id",
    "crime_type",
    "outcome_category",
    "lsoa_code",
    "lsoa_name",
    "latitude",
    "longitude",
    "source_file",
]


def ensure_directories() -> None:
    for path in [
        RAW_DIR,
        PROCESSED_DIR,
        TABLES_DIR,
        FIGURES_DIR,
        REPORT_DIR,
        REPORT_FIGURES_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)

