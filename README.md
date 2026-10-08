# Quorum Coding Challenge

This program reads legislative data from CSV files, aggregates recorded votes, and writes two summary CSV files.

## Questions and answers

### 1. For every legislator in the dataset, how many bills did the legislator support (voted for the bill)? How many bills did the legislator oppose?

The program writes each legislator's totals to `out/legislators-support-oppose-count.csv`. Legislators with no recorded votes are included with zero counts.

### 2. For every bill in the dataset, how many legislators supported the bill? How many legislators opposed the bill? Who was the primary sponsor of the bill?

The program writes support and opposition totals and the sponsor name to `out/bills.csv`. Bill totals are accumulated from vote-result rows. Every bill is included, including bills without associated results, which receive zero counts. Sponsor names are looked up using the bill's `sponsor_id`; if there is no matching legislator, the output reports `Unknown`.

The summaries count recorded vote-result rows. The input data is expected to contain one vote result per legislator and roll-call vote. If a legislator votes on more than one roll call for the same bill, each vote result contributes to the legislator's totals; the bill summary counts vote-result rows, not distinct legislators.

## Input files

Place the input CSV files in `resources/`:

- `legislators.csv`: legislator `id` and `name`.
- `bills.csv`: bill `id`, `title`, and `sponsor_id`.
- `votes.csv`: roll-call vote `id` and associated `bill_id`.
- `vote_results.csv`: result `id`, `legislator_id`, `vote_id`, and `vote_type`.

`vote_type` values are interpreted as `1` = yea/support and `2` = nay/oppose.

The sponsor name is looked up in `legislators.csv` using `sponsor_id`. If there is no matching legislator, the bill summary reports `Unknown`. For example, the provided Infrastructure Investment and Jobs Act record has sponsor ID `400100`, which is not present in the provided legislator list, so its sponsor name cannot be resolved from these inputs.

## Install and run

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/#installation-methods).

   Windows:

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   Linux/macOS:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. From the project root, sync dependencies:

   ```bash
   uv sync
   ```

3. Run the program:

   ```bash
   uv run quorum-coding-challenge
   ```

## Logging

The command-line program configures Python's standard `logging` package at INFO level. It reports data-loading and output-writing progress, warns when a vote refers to an unknown bill or a bill's sponsor cannot be resolved, and logs errors before raising when required input files or vote-result references are invalid. When using the package as a library, configure logging in the calling application to control the level and destination.

## Output files

The program writes the following files to `out/`:

- `legislators-support-oppose-count.csv`, with columns `id`, `name`, `num_supported_bills`, and `num_opposed_bills`. Every legislator in `legislators.csv` is included, including legislators with no recorded votes (zero counts).
- `bills.csv`, with columns `id`, `title`, `supporter_count`, `opposer_count`, and `primary_sponsor`. Every bill in `bills.csv` is included, even if it has no associated vote results (zero counts).

## Discussion

### 1. Discuss your solution’s time complexity. What tradeoffs did you make?

The input records are represented with dataclasses for legislators, bills, votes, and vote results. The program loads those records, links vote results to their legislator and roll-call vote, then accumulates counts and writes CSV summaries.

The current `DataContainer.find_by_id` searches records linearly. Let:

- `L` be the number of legislators,
- `B` be the number of bills,
- `V` be the number of roll-call votes, and
- `R` be the number of vote-result rows.

Loading votes takes O(V × B) in the worst case because each vote searches the bills. Loading vote results takes O(R × (L + V)) because each result searches for its legislator and vote. Sponsor lookups also use linear legislator searches. The overall running time is therefore O(V × B + R × (L + V)), with O(L + B + V + R) space to hold the input records and relationships. The count-aggregation passes are linear in the number of vote-result rows.

This approach keeps the relationships explicit and the aggregation straightforward, at the cost of repeated linear searches. For larger inputs, dictionaries keyed by IDs would make those joins approximately constant-time on average and reduce the loading and sponsor-lookup costs. A database could also perform the joins and grouped aggregations, but would add setup that is unnecessary for this small CSV-based challenge.

### 2. How would you change your solution to account for future columns that might be requested, such as “Bill Voted On Date” or “Co-Sponsors”?

For a field such as a vote date or co-sponsors, first identify which input record owns the field and how it relates to the existing records. Then update the corresponding dataclass, CSV parsing and validation, relationship handling if needed, and output schema. For example, a vote date belongs to a roll-call vote; a bill's co-sponsors belong to the bill and may need separate parsing or a normalized input format if a bill can have multiple co-sponsors. Keeping input parsing, aggregation, and output generation distinct would help limit changes to the relevant parts.

### 3. How would you change your solution if instead of receiving CSVs of data, you were given a list of legislators or bills that you should generate a CSV for?

I would separate aggregation from file I/O so it can accept typed records or iterables regardless of their source. The existing CSV workflow could parse files into those records; another caller could pass a list directly, and the same aggregation logic could produce summary records for a CSV writer. To calculate support and opposition totals, the input must also include the relevant bills, votes, and vote results; a list of legislators or bills alone does not contain enough information to derive those totals.

### 4. How long did you spend working on the assignment?

Approximately 3 hours, including understanding the requirements, designing and implementing the solution, and checking the generated output.
