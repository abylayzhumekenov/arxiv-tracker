# arxiv-tracker

A small Python utility to track new arXiv papers in a category (e.g., `stat.CO`), keep history, and produce delta output for manual review or LLM ingestion.

## Features

- Uses the `arxiv` Python library and arXiv API
- Stateful run tracking (`arxiv_state.json`) to only capture newly published papers
- Saves full cumulative history in `arxiv_history.jsonl`
- Saves only newly found papers each run in `arxiv_new.jsonl`
- Includes key metadata fields (authors, title, abstract, categories, DOI, etc.)

## Files

- `fetch_arxiv.py` : main script
- `config.json` : configuration file for categories and settings
- `arxiv_state.json` : state file with `last_run` and total counter
- `arxiv_history.jsonl` : append-only JSONL history
- `arxiv_new.jsonl` : JSONL snapshot containing only papers from the latest run

## Setup

1. Create and activate a virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # venv\Scripts\activate   # On Windows
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

The script uses settings from `config.json` by default. This allows you to customize the tracked categories without editing the script or using command line flags.

### Command line override

```bash
python3 fetch_arxiv.py --category stat.CO,stat.ML,cs.LG --max-results 200
```

CLI options:

- `--category` : arXiv category (default `stat.CO`)
- `--max-results` : max entries to fetch per run (default `200`)
- `--state-file` : override state file path
- `--history-file` : override history file path
- `--new-file` : override new file path
- `--reset` : ignore prior state and treat fetched set as new

## Example workflow

1. Run regularly (daily/weekly). 2. `arxiv_new.jsonl` has new papers since last run. 3. Feed into your LLM prompt with your fixed keywords file (e.g. `research_keywords.txt`) for relevance classification.

## Output format

Each line in JSONL has fields:

- `id`, `arxiv_id`, `title`, `abstract`, `authors`, `institutions`, `published`, `updated`, `categories`, `doi`, `journal_ref`, `comment`, `keywords`, `fetched_at`

## Notes

- `institutions` is empty because arXiv Atom feed doesn’t provide structured affiliations.
- Use `comment`, `journal_ref`, and `doi` for extra signal.

## Optional enhancements

- Add keyword-scoring on `title`+`abstract` against a user keyword file
- Support more categories like `stat.ML`, `cs.LG`, etc.
- Save results to CSV/SQLite for advanced filtering.
