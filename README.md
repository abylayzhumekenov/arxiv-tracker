# arxiv-tracker

A streamlined tool to track new arXiv papers, maintain a local database, and filter results using LLMs based on your specific research directions.

## Features

- Uses the `arxiv` Python library and arXiv API
- Stateful run tracking (`arxiv_state.json`) to only capture newly published papers
- Saves full cumulative history in `arxiv_history.json`
- Saves only newly found papers each run in `arxiv_new.json`
- Includes key metadata fields (authors, title, abstract, categories, DOI, etc.)

## Files

- `fetch_arxiv.py` : main script
- `config.json` : configuration file for categories and settings
- `research_interests.json` : (User defined) Your specific research focus and keywords
- `arxiv_state.json` : state file with `last_run` and total counter
- `arxiv_history.json` : cumulative JSON history
- `arxiv_new.json` : JSON snapshot containing only papers from the latest run

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/arxiv-tracker.git
   cd arxiv-tracker
   ```
2. Create and activate a virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # venv\Scripts\activate   # On Windows
   ```
3. Install dependencies:
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

1. Run regularly (daily/weekly).
2. `arxiv_new.json` contains new papers since the last run.
3. Upload `arxiv_new.json` and `research_interests.json` to your LLM.

### Suggested LLM Prompt
> "I've uploaded `arxiv_new.json` (recent papers) and `research_interests.json` (my nested research interests). Please filter the new papers and highlight the most relevant ones. Organize your response according to the 'research_directions' I've defined, explaining why each paper fits that specific direction and its preferred topics."

## Output format

The output is a JSON array of objects with fields:

- `id`, `arxiv_id`, `title`, `abstract`, `authors`, `institutions`, `published`, `updated`, `categories`, `doi`, `journal_ref`, `comment`, `keywords`, `fetched_at`

## Notes

- `institutions` is empty because arXiv Atom feed doesn’t provide structured affiliations.
- Use `comment`, `journal_ref`, and `doi` for extra signal.

## Optional enhancements

- Add keyword-scoring on `title`+`abstract` against a user keyword file
- Support more categories like `stat.ML`, `cs.LG`, etc.
- Save results to CSV/SQLite for advanced filtering.
