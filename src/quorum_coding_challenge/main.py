import logging

from quorum_coding_challenge.legislative_data import LegislativeData

logger = logging.getLogger(__name__)


def main() -> None:
    """Generate the legislator and bill vote-summary CSV files."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger.info("Starting legislative vote summary generation")
    data = LegislativeData()
    data.write_supported_data()
    data.write_supported_bills()
    logger.info("Finished legislative vote summary generation")
