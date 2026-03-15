# arXiv Tracker

A streamlined tool to track new arXiv papers, maintain a local database, and semantically filter results based on your specific research interests using local language models.

## Features

- **Stateful Fetching**: Uses the `arxiv` library to fetch new papers since the last run, avoiding duplicates.
- **Local Database**: Saves a full history of fetched papers (`arxiv_history.json`) and a snapshot of the latest additions (`arxiv_new.json`).
- **Semantic Filtering**: Ranks new papers by relevance to your research interests using local sentence embeddings via Ollama. No API keys or costs required.
- **Configurable**: Easily configure tracked arXiv categories, filenames, and filtering parameters in a central `config.json`.
- **Informative Output**: The filter script provides a clean, ranked summary of the most relevant papers directly in your terminal.
- **Robust Workflow**: Scripts are designed to work together, ensuring a smooth pipeline from fetching to filtering.

## File Overview

-   **Core Scripts**: `fetch_arxiv.py`, `filter_papers.py`
-   **Configuration (Tracked by Git)**:
    -   `config.json`: Main settings for categories, file paths, and filtering.
    -   `research_interests.json`: Your specific research topics for semantic filtering.
-   **Generated Data (Ignored by `.gitignore`)**:
    -   `arxiv_state.json`: Tracks the last run time to prevent duplicate fetching.
    -   `arxiv_history.json`: A cumulative database of all papers fetched.
    -   `arxiv_new.json`: Contains only the papers from the most recent fetch.
    -   `arxiv_filtered.json`: The output of the filtering script, containing relevant papers.
    -   `arxiv_filtered.txt`: A text summary of the top papers (human-readable).

## How It Works

The workflow is a simple two-step process:

1.  **`fetch_arxiv.py`**: Connects to the arXiv API, fetches papers from your specified categories that were published since the last run, and saves them to `arxiv_new.json` and `arxiv_history.json`.
2.  **`filter_papers.py`**:
    *   Loads your defined research interests from `research_interests.json`.
    *   Loads the newly fetched papers from `arxiv_new.json`.
    *   Uses a local Ollama model (like `nomic-embed-text`) to generate vector embeddings for your interests and the papers' titles/abstracts.
    *   Calculates relevance scores, weighing specific "topics" against the general research "direction" (configurable).
    *   Saves a sorted list of relevant papers to `arxiv_filtered.json` and prints a summary.

## Prerequisites

- Python 3.8+
- **Ollama**:
  - **macOS / Linux**: 
    ```bash
    curl -fsSL https://ollama.com/install.sh | sh
    ```
  - **Windows**: Download from ollama.com.
- An embedding model pulled via Ollama. We recommend `nomic-embed-text`:
  ```bash
  ollama pull nomic-embed-text
  ```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/abylayzhumekenov/arxiv-tracker.git
    cd arxiv-tracker
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On macOS/Linux
    # venv\Scripts\activate   # On Windows
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Before running, customize the following two files:

1.  **`config.json`**: Set your desired arXiv categories and filtering preferences.
    ```json
    {
      "category": "cs.LG,stat.ML",
      "max_results": 200,
      "ollama_model": "nomic-embed-text",
      "relevance_threshold": 0.6,
      "topic_weight": 0.7
    }
    ```

2.  **`research_interests.json`**: Define your research interests. The filter script will use these to calculate relevance.
    ```json
    {
      "research_directions": [
        {
          "direction": "Scalable Bayesian Computation",
          "topics": ["MCMC", "variational inference", "high-dimensional models"]
        }
      ],
      "overall_summary": "My research focuses on..."
    }
    ```

## Usage

Run the scripts in sequence.

**Step 1: Fetch New Papers**
```bash
python3 fetch_arxiv.py
```
This will update `arxiv_new.json` with the latest papers.

**Step 2: Filter for Relevance**
```bash
python3 filter_papers.py
```

**2. Filter all historical papers:**
```bash
python3 filter_papers.py --use-history
```

You can override settings from `config.json` via the command line:
```bash
python3 filter_papers.py --threshold 0.6 --topic-weight 0.8
```

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
