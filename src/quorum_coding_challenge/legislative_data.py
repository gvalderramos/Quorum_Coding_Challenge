import logging

from quorum_coding_challenge.data_model import (
    Bill,
    BillSupport,
    DataContainer,
    Legislator,
    LegislatorSupport,
    Vote,
    VoteResult,
    VoteType,
)
from quorum_coding_challenge.resource import (
    bills_csv,
    legislators_csv,
    legislators_support_oppose_count,
    load_csv_data,
    supported_bills_count,
    vote_results_csv,
    votes_csv,
    write_csv_data,
)

logger = logging.getLogger(__name__)


class LegislativeData:
    """Load legislative CSV data and generate vote-summary CSV files."""

    def __init__(self):
        """Initialize the data containers and load all source records."""
        self._legislators = DataContainer()
        self._bills = DataContainer()
        self._votes = DataContainer()
        self._votes_result = DataContainer()

        self._load_data()
        logger.info(
            "Loaded legislative data: %d legislators, %d bills, %d votes, "
            "%d vote results",
            len(self._legislators.data),
            len(self._bills.data),
            len(self._votes.data),
            len(self._votes_result.data),
        )

    def _get_bills_data(self) -> list[Bill]:
        """Load bill records from the configured bills CSV."""
        data = load_csv_data(bills_csv)
        return [Bill(int(i["id"]), i["title"], int(i["sponsor_id"])) for i in data]

    def _get_legislators(self) -> list[Legislator]:
        """Load legislator records from the configured legislators CSV."""
        data = load_csv_data(legislators_csv)
        return [Legislator(int(i["id"]), i["name"]) for i in data]

    def _get_votes(self) -> list[Vote]:
        """Load roll-call votes and associate them with their bills."""
        data = load_csv_data(votes_csv)
        votes = []
        for vote in data:
            bill_id = int(vote["bill_id"])
            bill = self._bills.find_by_id(bill_id)
            if bill is None:
                logger.warning(
                    "Vote %s references unknown bill ID %d; using placeholder",
                    vote["id"],
                    bill_id,
                )
                bill = Bill(bill_id, "Unknown", -1)
            votes.append(Vote(int(vote["id"]), bill))
        return votes

    def _get_votes_result(self) -> list[VoteResult]:
        """Load vote results and associate each with its legislator and vote."""
        data = load_csv_data(vote_results_csv)
        result = []
        for vote_result in data:
            legislator_id = int(vote_result["legislator_id"])
            vote_id = int(vote_result["vote_id"])
            vote_type = int(vote_result["vote_type"])
            try:
                parsed_vote_type = VoteType(vote_type)
            except ValueError as error:
                logger.error(
                    "Vote result %s has unsupported vote type %d",
                    vote_result["id"],
                    vote_type,
                )
                raise ValueError(
                    f"Vote result {vote_result['id']} has unsupported vote type "
                    f"{vote_type}"
                ) from error

            legislator = self._legislators.find_by_id(legislator_id)
            vote = self._votes.find_by_id(vote_id)

            if legislator is None:
                logger.error(
                    "Vote result %s references unknown legislator ID %d",
                    vote_result["id"],
                    legislator_id,
                )
                raise ValueError(
                    f"Vote result {vote_result['id']} references unknown "
                    f"legislator ID {legislator_id}"
                )
            if vote is None:
                logger.error(
                    "Vote result %s references unknown vote ID %d",
                    vote_result["id"],
                    vote_id,
                )
                raise ValueError(
                    f"Vote result {vote_result['id']} references unknown vote ID "
                    f"{vote_id}"
                )

            result.append(
                VoteResult(int(vote_result["id"]), legislator, vote, parsed_vote_type)
            )
        return result

    def _load_data(self):
        """Load source records in dependency order and populate each container."""
        self._legislators.data = self._get_legislators()
        self._bills.data = self._get_bills_data()
        self._votes.data = self._get_votes()
        self._votes_result.data = self._get_votes_result()

    def write_supported_data(self):
        """Write support and opposition totals for every legislator to CSV."""
        data = {}
        for legislator in self._legislators:
            legislator_support = LegislatorSupport(legislator, 0, 0)
            data.setdefault(legislator.id, legislator_support)

        for vote_result in self._votes_result:
            legislator_id = vote_result.legislator.id
            data[legislator_id].add_vote(vote_result.vote_type)

        supported_data = list(data.values())
        write_csv_data(
            legislators_support_oppose_count,
            [
                {
                    "id": i.legislator.id,
                    "name": i.legislator.name,
                    "num_supported_bills": i.supported_bills,
                    "num_opposed_bills": i.opposed_bills,
                }
                for i in supported_data
            ],
            ["id", "name", "num_supported_bills", "num_opposed_bills"],
        )

    def write_supported_bills(self):
        """Write support and opposition totals and sponsor names for every bill."""
        data = {}
        for bill in self._bills:
            sponsor = self._legislators.find_by_id(bill.sponsor_id)
            if sponsor is None:
                logger.warning(
                    "Bill %d has unknown sponsor ID %d; writing sponsor as Unknown",
                    bill.id,
                    bill.sponsor_id,
                )
                sponsor_name = "Unknown"
            else:
                sponsor_name = sponsor.name
            data[bill.id] = BillSupport(bill, 0, 0, sponsor_name)

        for vote_result in self._votes_result:
            bill = vote_result.vote.bill
            if bill.id not in data:
                sponsor = self._legislators.find_by_id(bill.sponsor_id)
                if sponsor is None:
                    logger.warning(
                        "Bill %d has unknown sponsor ID %d; writing sponsor as Unknown",
                        bill.id,
                        bill.sponsor_id,
                    )
                    sponsor_name = "Unknown"
                else:
                    sponsor_name = sponsor.name
                data[bill.id] = BillSupport(bill, 0, 0, sponsor_name)
            data[bill.id].add_vote(vote_result.vote_type)

        supported_bills = list(data.values())
        write_csv_data(
            supported_bills_count,
            [
                {
                    "id": bill.bill.id,
                    "title": bill.bill.title,
                    "supporter_count": bill.supporter_count,
                    "opposer_count": bill.opposer_count,
                    "primary_sponsor": bill.primary_sponsor,
                }
                for bill in supported_bills
            ],
            ["id", "title", "supporter_count", "opposer_count", "primary_sponsor"],
        )
