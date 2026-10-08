import csv
import logging

import pytest

from quorum_coding_challenge import legislative_data as legislative_data_module
from quorum_coding_challenge import resource as resource_module


def write_csv(path, fieldnames, rows):
    """Write test rows to a CSV file with the provided columns."""
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path):
    """Read a CSV file into dictionaries for assertions."""
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


@pytest.fixture
def legislative_data(tmp_path, monkeypatch):
    """Create isolated sample inputs and a LegislativeData instance."""
    resources = tmp_path / "resources"
    output = tmp_path / "out"
    resources.mkdir()
    output.mkdir()

    write_csv(
        resources / "legislators.csv",
        ["id", "name"],
        [
            {"id": "1", "name": "Rep. Alice Sponsor"},
            {"id": "2", "name": "Rep. Bob Member"},
            {"id": "3", "name": "Rep. Carol No Votes"},
        ],
    )
    write_csv(
        resources / "bills.csv",
        ["id", "title", "sponsor_id"],
        [
            {"id": "10", "title": "Bill With Votes", "sponsor_id": "1"},
            {"id": "20", "title": "Bill Without Votes", "sponsor_id": "2"},
            {"id": "30", "title": "Bill With Unknown Sponsor", "sponsor_id": "99"},
        ],
    )
    write_csv(
        resources / "votes.csv",
        ["id", "bill_id"],
        [{"id": "100", "bill_id": "10"}],
    )
    write_csv(
        resources / "vote_results.csv",
        ["id", "legislator_id", "vote_id", "vote_type"],
        [
            {"id": "1000", "legislator_id": "1", "vote_id": "100", "vote_type": "1"},
            {"id": "1001", "legislator_id": "2", "vote_id": "100", "vote_type": "2"},
        ],
    )

    monkeypatch.setattr(
        legislative_data_module, "legislators_csv", resources / "legislators.csv"
    )
    monkeypatch.setattr(legislative_data_module, "bills_csv", resources / "bills.csv")
    monkeypatch.setattr(legislative_data_module, "votes_csv", resources / "votes.csv")
    monkeypatch.setattr(
        legislative_data_module, "vote_results_csv", resources / "vote_results.csv"
    )
    monkeypatch.setattr(
        legislative_data_module,
        "legislators_support_oppose_count",
        output / "legislators-support-oppose-count.csv",
    )
    monkeypatch.setattr(
        legislative_data_module, "supported_bills_count", output / "bills.csv"
    )

    return legislative_data_module.LegislativeData(), output


def test_writes_counts_for_all_legislators_including_ones_without_votes(
    legislative_data, caplog
):
    """Include every legislator and report zeroes for legislators without votes."""
    data, output = legislative_data

    with caplog.at_level(logging.INFO):
        data.write_supported_data()
    rows = read_csv(output / "legislators-support-oppose-count.csv")

    assert "Wrote 3 rows to" in caplog.text
    assert rows == [
        {
            "id": "1",
            "name": "Rep. Alice Sponsor",
            "num_supported_bills": "1",
            "num_opposed_bills": "0",
        },
        {
            "id": "2",
            "name": "Rep. Bob Member",
            "num_supported_bills": "0",
            "num_opposed_bills": "1",
        },
        {
            "id": "3",
            "name": "Rep. Carol No Votes",
            "num_supported_bills": "0",
            "num_opposed_bills": "0",
        },
    ]


def test_writes_counts_for_all_bills_and_resolves_sponsors(legislative_data, caplog):
    """Include every bill and resolve known and unknown primary sponsors."""
    data, output = legislative_data

    with caplog.at_level(logging.WARNING):
        data.write_supported_bills()
    rows = read_csv(output / "bills.csv")

    assert "unknown sponsor ID 99" in caplog.text
    assert rows == [
        {
            "id": "10",
            "title": "Bill With Votes",
            "supporter_count": "1",
            "opposer_count": "1",
            "primary_sponsor": "Rep. Alice Sponsor",
        },
        {
            "id": "20",
            "title": "Bill Without Votes",
            "supporter_count": "0",
            "opposer_count": "0",
            "primary_sponsor": "Rep. Bob Member",
        },
        {
            "id": "30",
            "title": "Bill With Unknown Sponsor",
            "supporter_count": "0",
            "opposer_count": "0",
            "primary_sponsor": "Unknown",
        },
    ]


def test_missing_csv_logs_an_error(tmp_path, caplog):
    """Log a clear error before raising when a required CSV is missing."""
    missing_path = tmp_path / "missing.csv"

    with caplog.at_level(logging.ERROR), pytest.raises(RuntimeError):
        resource_module.load_csv_data(missing_path)

    assert f"CSV input file does not exist: {missing_path}" in caplog.text


def test_vote_result_with_unknown_legislator_logs_and_raises(legislative_data, caplog):
    """Reject vote results that reference a legislator absent from the source."""
    vote_results_path = legislative_data_module.vote_results_csv
    write_csv(
        vote_results_path,
        ["id", "legislator_id", "vote_id", "vote_type"],
        [{"id": "1002", "legislator_id": "999", "vote_id": "100", "vote_type": "1"}],
    )

    with (
        caplog.at_level(logging.ERROR),
        pytest.raises(ValueError, match="unknown legislator ID 999"),
    ):
        legislative_data_module.LegislativeData()

    assert "references unknown legislator ID 999" in caplog.text
