#!/usr/bin/env python3
"""Fetch STAT.CO (or any arXiv category) new papers and save JSON history + delta.

Usage:
    pip install arxiv
    python fetch_arxiv.py --category stat.CO --max-results 200

Outputs:
   arxiv_state.json
   arxiv_history.json
   arxiv_new.json

Each record:
   id, arxiv_id, title, abstract, authors, institutions (empty), published,
   updated, categories, doi, journal_ref, comment, keywords, fetched_at
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import arxiv

# Default configuration constants
DEFAULT_CATEGORIES = "stat.CO"
DEFAULT_MAX_RESULTS = 200
DEFAULT_STATE_FILE = "arxiv_state.json"
DEFAULT_HISTORY_FILE = "arxiv_history.json"
DEFAULT_NEW_FILE = "arxiv_new.json"
DEFAULT_CONFIG_FILE = "config.json"

def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load config file {path}: {e}")
        return {}

def parse_args(config: Dict[str, Any]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Fetch new papers from arXiv",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    p.add_argument("--category", default=config.get("category", DEFAULT_CATEGORIES), help="Comma-separated arXiv categories")
    p.add_argument("--max-results", type=int, default=config.get("max_results", DEFAULT_MAX_RESULTS), help="Max results to fetch per category")
    p.add_argument("--state-file", default=config.get("state_file", DEFAULT_STATE_FILE), help="State filename")
    p.add_argument("--history-file", default=config.get("history_file", DEFAULT_HISTORY_FILE), help="History json filename")
    p.add_argument("--new-file", default=config.get("new_file", DEFAULT_NEW_FILE), help="New json filename")
    p.add_argument("--reset", action="store_true", help="Reset state and treat all fetched as new")
    return p.parse_args()

def load_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_state(path: Path, state: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def to_iso(dt: Any) -> str:
    if isinstance(dt, str):
        return dt
    return dt.astimezone(timezone.utc).isoformat()

def paper_to_dict(entry: arxiv.Result) -> Dict[str, Any]:
    return {
        "id": entry.entry_id,
        "arxiv_id": entry.entry_id.split('/')[-1],
        "title": (entry.title or "").strip(),
        "abstract": (entry.summary or "").strip(),
        "authors": [a.name for a in entry.authors],
        "institutions": [],
        "published": to_iso(entry.published),
        "updated": to_iso(entry.updated),
        "categories": entry.categories,
        "doi": entry.doi,
        "journal_ref": entry.journal_ref,
        "comment": entry.comment,
        "keywords": list(entry.categories),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

def save_json(path: Path, items: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

def update_history_json(path: Path, new_items: List[Dict[str, Any]]) -> None:
    history = []
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                history = json.load(f)
                if not isinstance(history, list):
                    history = []
        except Exception:
            history = []
    history.extend(new_items)
    save_json(path, history)

def main():
    config_data = load_config(Path(DEFAULT_CONFIG_FILE))
    args = parse_args(config_data)
    state_path = Path(args.state_file)
    history_path = Path(args.history_file)
    new_path = Path(args.new_file)

    categories = [c.strip() for c in args.category.split(",")]
    state = {} if args.reset else load_state(state_path)
    
    # Initialize category states if missing (supporting migration from old format)
    if "categories" not in state:
        legacy_last_run = state.pop("last_run", None)
        state["categories"] = {}
        if legacy_last_run and len(categories) == 1:
            state["categories"][categories[0]] = {"last_run": legacy_last_run, "total_fetched": state.pop("total_fetched", 0)}

    client = arxiv.Client()
    all_new_papers = []
    seen_ids = set()

    for cat in categories:
        cat_state = state["categories"].get(cat, {})
        last_run = cat_state.get("last_run")
        print(f"\n--- Checking category: {cat} (last_run: {last_run or 'Never'}) ---")

        search = arxiv.Search(
            query=f"cat:{cat}",
            max_results=args.max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
        )

        try:
            entries = list(client.results(search))
        except Exception as e:
            print(f"Error fetching {cat}: {e}")
            continue

        if not entries:
            continue

        papers = [paper_to_dict(e) for e in entries]
        papers.sort(key=lambda x: x["published"], reverse=True)

        if last_run:
            cat_new = [p for p in papers if p["published"] > last_run]
        else:
            cat_new = papers

        # Deduplicate: don't add the same paper twice if it appears in multiple categories
        unique_new = []
        for p in cat_new:
            if p["id"] not in seen_ids:
                unique_new.append(p)
                seen_ids.add(p["id"])

        if cat_new:
            # Update state for this specific category
            state["categories"][cat] = {
                "last_run": cat_new[0]["published"],
                "total_fetched": cat_state.get("total_fetched", 0) + len(cat_new)
            }
            all_new_papers.extend(unique_new)
            print(f"Found {len(cat_new)} new papers ({len(unique_new)} unique in this run).")

    if all_new_papers:
        save_json(new_path, all_new_papers)
        update_history_json(history_path, all_new_papers)
        save_state(state_path, state)
        print(f"\nTotal new unique papers: {len(all_new_papers)}")
        print(f"Updated {new_path} and {history_path}")
    else:
        print("No new papers since last run.")


if __name__ == "__main__":
    main()
