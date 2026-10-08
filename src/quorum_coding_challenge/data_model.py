from dataclasses import dataclass
from enum import Enum


class VoteType(Enum):
    """Supported choices recorded for a legislator's vote."""

    yea = 1
    nay = 2


@dataclass
class Data:
    """Base record identified by a numeric ID."""

    id: int


@dataclass
class Bill(Data):
    """A bill and the ID of its primary sponsor."""

    id: int
    title: str
    sponsor_id: int


@dataclass
class Legislator(Data):
    """A legislator identified by their name and numeric ID."""

    id: int
    name: str


@dataclass
class Vote(Data):
    """A roll-call vote associated with a bill."""

    id: int
    bill: Bill


@dataclass
class VoteResult(Data):
    """One legislator's recorded choice on a roll-call vote."""

    id: int
    legislator: Legislator
    vote: Vote
    vote_type: VoteType


@dataclass
class LegislatorSupport:
    """Support and opposition totals accumulated for one legislator."""

    legislator: Legislator
    supported_bills: int
    opposed_bills: int

    def add_vote(self, vote_type: VoteType):
        """Increment the appropriate total for a recorded vote."""
        if vote_type == VoteType.yea:
            self.supported_bills += 1
        else:
            self.opposed_bills += 1


@dataclass
class BillSupport:
    """Support and opposition totals and sponsor name for one bill."""

    bill: Bill
    supporter_count: int
    opposer_count: int
    primary_sponsor: str

    def add_vote(self, vote_type: VoteType):
        """Increment the appropriate total for a recorded vote."""
        if vote_type == VoteType.yea:
            self.supporter_count += 1
        else:
            self.opposer_count += 1


class DataContainer:
    """A small iterable collection of records with linear ID lookup."""

    def __init__(self, data: list[Data] | None = None):
        """Initialize the container with records, or with an empty collection."""
        self._data_container = data or []

    def __iter__(self):
        """Iterate over the contained records in insertion order."""
        yield from self._data_container

    def append(self, other: Data):
        """Append a record to the collection."""
        self._data_container.append(other)

    def find_by_id(self, id: int) -> Data | None:
        """Return the first record matching ``id``, or None if no match exists."""
        for i in self._data_container:
            if i.id == id:
                return i

    @property
    def data(self):
        """Return the underlying record list."""
        return self._data_container

    @data.setter
    def data(self, other: list[Data]):
        """Replace all contained records with ``other``."""
        self._data_container = other
