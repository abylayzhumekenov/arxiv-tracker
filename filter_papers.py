#!/usr/bin/env python3
"""
Filter papers using local Ollama embeddings (e.g., nomic-embed-text).
Requires: pip install numpy requests
Usage: python filter_papers.py

The script uses settings from config.json for defaults, which can be
overridden by command-line arguments.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import requests
from tqdm import tqdm

# Default configuration constants
DEFAULT_CONFIG_FILE = "config.json"
DEFAULT_MODEL = "nomic-embed-text"
DEFAULT_URL = "http://localhost:11434"
DEFAULT_THRESHOLD = 0.7
DEFAULT_OUTPUT_FILE = "arxiv_filtered.json"
DEFAULT_INTERESTS_FILE = "research_interests.json"
DEFAULT_TOP_N = 10


def get_embedding(text: str, model: str, url: str) -> np.ndarray:
    """Fetch embedding from Ollama API."""
    try:
        response = requests.post(
            f"{url}/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=30
        )
        response.raise_for_status()
        vector = response.json().get("embedding")
        if not vector:
            raise ValueError("No embedding found in response")
        return np.array(vector)
    except requests.RequestException as e:
        print(f"Error communicating with Ollama: {e}")
        sys.exit(1)

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return np.dot(v1, v2) / (norm1 * norm2)

def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

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
    parser = argparse.ArgumentParser(
        description="Filter papers using Ollama embeddings.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--papers", default=config.get("new_file", "arxiv_new.json"), help="Input papers JSON file (from config: new_file)")
    parser.add_argument("--history-file", default=config.get("history_file", "arxiv_history.json"), help="History file (from config: history_file)")
    parser.add_argument("--interests", default=DEFAULT_INTERESTS_FILE, help="Research interests JSON file")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_FILE, help="Output filtered JSON file")
    parser.add_argument("--model", default=config.get("ollama_model", DEFAULT_MODEL), help="Ollama model name (from config: ollama_model)")
    parser.add_argument("--url", default=config.get("ollama_url", DEFAULT_URL), help="Ollama URL (from config: ollama_url)")
    parser.add_argument("--threshold", type=float, default=config.get("relevance_threshold", DEFAULT_THRESHOLD), help="Similarity threshold (from config: relevance_threshold)")
    parser.add_argument("--use-history", action="store_true", help="Filter from the history file instead of new papers")
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N, help="Number of top papers to display in summary")
    return parser.parse_args()

def print_summary(papers: List[Dict[str, Any]], top_n: int):
    """Prints a summary table of the top N papers."""
    if not papers:
        return

    print(f"\n--- Top {min(top_n, len(papers))} Relevant Papers ---")

    for i, paper in enumerate(papers):
        if i >= top_n:
            break

        title = paper.get('title', '')
        authors = ", ".join(paper.get('authors', []))
        score = f"{paper.get('relevance_score', 0.0):.3f}"
        interest = paper.get('matched_interest', 'N/A')

        print(f"\n[{i+1}] Score: {score} | Matched: {interest}\n    Title: {title}\n    Authors: {authors}")

def main():
    config_data = load_config(Path(DEFAULT_CONFIG_FILE))
    args = parse_args(config_data)

    if args.use_history:
        papers_path = Path(args.history_file)
    else:
        papers_path = Path(args.papers)

    interests_path = Path(args.interests)
    output_path = Path(args.output)

    if not papers_path.exists():
        print(f"File not found: {papers_path}")
        return

    print(f"Loading papers from {papers_path}...")
    papers = load_json(papers_path)
    if not papers:
        print("No papers to process.")
        return

    print(f"Loading interests from {interests_path}...")
    interests_data = load_json(interests_path)
    
    # Prepare interest vectors
    # We treat research directions as "queries" (search_query prefix is often used with Nomic)
    interest_vectors = []
    for item in interests_data.get("research_directions", []):
        text = f"search_query: {item['direction']} " + ", ".join(item.get("topics", []))
        vector = get_embedding(text, args.model, args.url)
        interest_vectors.append((item['direction'], vector))

    print(f"Computed embeddings for {len(interest_vectors)} research directions.")
    print(f"Processing {len(papers)} papers...")

    filtered_papers = []

    for paper in tqdm(papers, desc="Embedding and comparing papers"):
        # We treat papers as "documents"
        content = f"search_document: {paper.get('title', '')}\n{paper.get('abstract', '')}"
        paper_vec = get_embedding(content, args.model, args.url)
        
        best_score = -1.0
        best_match = "None"

        for label, int_vec in interest_vectors:
            score = cosine_similarity(paper_vec, int_vec)
            if score > best_score:
                best_score = score
                best_match = label
        
        if best_score >= args.threshold:
            paper["relevance_score"] = float(best_score)
            paper["matched_interest"] = best_match
            filtered_papers.append(paper)

    # Sort by relevance
    filtered_papers.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    save_json(output_path, filtered_papers)
    print(f"\nSaved {len(filtered_papers)} relevant papers to {output_path}")

    # Display summary of top papers
    print_summary(filtered_papers, args.top_n)

if __name__ == "__main__":
    main()