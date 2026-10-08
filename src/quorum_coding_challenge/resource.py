import csv
import logging
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESOURCES = PROJECT_ROOT / "resources"
OUT = PROJECT_ROOT / "out"

bills_csv = RESOURCES / "bills.csv"
legislators_csv = RESOURCES / "legislators.csv"
vote_results_csv = RESOURCES / "vote_results.csv"
votes_csv = RESOURCES / "votes.csv"
legislators_support_oppose_count = OUT / "legislators-support-oppose-count.csv"
supported_bills_count = OUT / "bills.csv"


def load_csv_data(path: Path) -> list[dict[Any, Any]]:
    """Read a CSV file into a list of dictionaries keyed by column name.

    Raises:
        RuntimeError: If the specified path does not exist.
    """
    if not path.exists():
        logger.error("CSV input file does not exist: %s", path)
        raise RuntimeError(f"Path {path} not found")

    try:
        with open(path, newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            rows = list(reader)
    except OSError:
        logger.exception("Unable to read CSV file: %s", path)
        raise

    logger.info("Loaded %d rows from %s", len(rows), path)
    return rows


def write_csv_data(path: Path, data: list[Any], data_fields=None, newline=""):
    """Write dictionaries or dataclass instances to a CSV file.

    Args:
        path: Destination path for the CSV file.
        data: Rows to serialize.
        data_fields: Optional ordered column names; inferred from the first row
            when omitted.
        newline: Newline argument passed to ``open``.
    """
    data_fields = data_fields or fields(data[0])
    try:
        with open(path, "w", newline=newline, encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=data_fields)

            writer.writeheader()

            for row in data:
                if not isinstance(row, dict):
                    row = asdict(row)
                writer.writerow(row)
    except OSError:
        logger.exception("Unable to write CSV file: %s", path)
        raise

    logger.info("Wrote %d rows to %s", len(data), path)
