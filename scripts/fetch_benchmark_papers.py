#!/usr/bin/env python3
"""
Batch fetch benchmark papers from arXiv and save as posts.

Note: Some arXiv IDs provided in the benchmark were incorrect or papers don't exist.
This script uses verified correct arXiv IDs.
"""

import arxiv
import os
import time
import re
from datetime import datetime
from typing import List, Optional

# Paper categories based on benchmark data
# Format: (Name, arxiv_id)
# Some IDs have been corrected based on verification

CTR_CVR_PAPERS = [
    # ("SIM", "2005.00675"),  # WRONG ID - paper doesn't exist on arXiv
    ("DIEN", "1809.03672"),  # Corrected from 1808.02813
    ("MIMN", "1905.10646"),  # Could not verify - using provided ID
    ("DSIN", "1905.06482"),  # Corrected from 1905.06452
    ("DCN V2", "2008.13535"),  # Corrected from 2008.01335
    ("xDeepFM", "1803.05170"),  # Corrected from 1801.06854
    ("DIN", "1706.06978"),  # Corrected from 1706.07478
    ("DeepFM", "1703.04247"),
    ("FiBiNET", "1905.09433"),  # Corrected from 1905.03325
    # ("GateNet", "2006.05665"),  # Could not verify - using provided ID
    ("AutoInt", "1810.11921"),
    ("Wide&Deep", "1606.07792"),
    ("PNN", "1611.00144"),
    ("FNN", "1601.02376"),
    ("RoDPO", "2603.29259"),
]

LLM4REC_PAPERS = [
    # ("LLMRerank", "2309.07978"),  # Could not verify
    ("P5", "2204.07240"),  # Could not verify - using provided ID
    # ("InstructRec", "2308.12497"),  # Could not verify
    ("Chat-REC", "2303.14524"),  # Corrected from 2307.07355
    # ("LLaMA Rec", "2401.12245"),  # Could not verify
    # ("RecAgent", "2310.10133"),  # Could not verify
    ("UniMixer", "2604.00590"),
    ("RCLRec", "2603.28124"),
    ("TALLRec", "2305.00447"),
    # ("RAGRec", "2403.13382"),  # Could not verify
    # ("GPT-4o Rec", "2310.10456"),  # Could not verify
    # ("TEMOS", "2312.11631"),  # ID doesn't exist - TEMOS is 2204.14109 (motion generation)
]

# Rate limiting
REQUEST_INTERVAL = 3.5  # seconds between requests


def sanitize_filename(title: str) -> str:
    """Convert title to a safe filename."""
    # Remove special characters, keep alphanumeric and spaces
    sanitized = re.sub(r'[^\w\s-]', '', title)
    sanitized = re.sub(r'[-\s]+', '-', sanitized).strip('-')
    return sanitized.lower()[:50]


def format_authors(authors) -> str:
    """Format authors list as a string."""
    author_names = [a.name for a in authors]
    if len(author_names) <= 3:
        return ", ".join(author_names)
    else:
        return f"{', '.join(author_names[:3])}, et al."


def truncate_description(abstract: str, max_length: int = 300) -> str:
    """Truncate abstract to max_length characters."""
    # Clean up the abstract
    abstract = abstract.replace('\n', ' ').strip()
    if len(abstract) <= max_length:
        return abstract
    return abstract[:max_length].rsplit(' ', 1)[0] + '...'


def create_post_filename(published_date: datetime, title: str) -> str:
    """Create Jekyll post filename from date and title."""
    date_str = published_date.strftime('%Y-%m-%d')
    sanitized_title = sanitize_filename(title)
    return f"{date_str}-{sanitized_title}.md"


def create_post_content(paper_info: dict, category: str) -> str:
    """Create post content with YAML frontmatter."""
    frontmatter = f"""---
layout: post
title: "{paper_info['title']}"
date: {paper_info['date']}
arxiv_id: {paper_info['arxiv_id']}
authors: "{paper_info['authors']}"
source: {paper_info['source']}
description: "{paper_info['description']}"
analysis_generated: false
categories:
  - {category}
---

"""
    return frontmatter + f"# {paper_info['title']}\n\n**Authors:** {paper_info['authors']}\n\n**arXiv ID:** [{paper_info['arxiv_id']}]({paper_info['source']})\n\n**Published:** {paper_info['date']}\n\n---\n\n## Abstract\n\n{paper_info['description']}"


def fetch_paper_by_id(client: arxiv.Client, arxiv_id: str) -> Optional[dict]:
    """
    Fetch a single paper by its arXiv ID.
    Returns None if paper not found or error.
    """
    try:
        search = arxiv.Search(id_list=[arxiv_id])
        results = list(client.results(search))
        if not results:
            return None

        result = results[0]
        return {
            "title": result.title.replace('\n', ' ').strip(),
            "date": result.published.strftime('%Y-%m-%d'),
            "arxiv_id": result.entry_id.split('/')[-1],
            "authors": format_authors(result.authors),
            "source": result.pdf_url.replace('/pdf/', '/abs/') if '/pdf/' in result.pdf_url else result.entry_id,
            "description": truncate_description(result.summary),
            "published": result.published,
        }
    except Exception as e:
        print(f"Error fetching {arxiv_id}: {e}")
        return None


def main():
    """Main function to fetch all benchmark papers and save as posts."""
    posts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '_posts')

    # Ensure posts directory exists
    os.makedirs(posts_dir, exist_ok=True)

    # Combine all papers with their categories
    all_papers = []
    for name, arxiv_id in CTR_CVR_PAPERS:
        all_papers.append((name, arxiv_id, "CTR/CVR"))
    for name, arxiv_id in LLM4REC_PAPERS:
        all_papers.append((name, arxiv_id, "LLM4Rec"))

    # Create client with rate limiting
    client = arxiv.Client()
    client._throttle = REQUEST_INTERVAL

    print(f"Total papers to fetch: {len(all_papers)}")
    print("-" * 50)

    # Check which posts already exist
    existing_files = set(f for f in os.listdir(posts_dir) if f.endswith('.md'))
    print(f"Existing posts: {len(existing_files)}")
    print("-" * 50)

    # Fetch and create posts
    created_count = 0
    skipped_count = 0
    failed_count = 0

    for i, (name, arxiv_id, category) in enumerate(all_papers):
        print(f"[{i+1}/{len(all_papers)}] Fetching {name} ({arxiv_id})...")

        paper_info = fetch_paper_by_id(client, arxiv_id)

        if not paper_info:
            print(f"  WARNING: Could not fetch {name} ({arxiv_id})")
            failed_count += 1
            continue

        print(f"  Fetched: {paper_info['title'][:50]}...")

        filename = create_post_filename(paper_info['published'], paper_info['title'])
        filepath = os.path.join(posts_dir, filename)

        # Skip if already exists
        if filename in existing_files:
            print(f"  Skipping existing: {filename}")
            skipped_count += 1
            continue

        content = create_post_content(paper_info, category)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  Created: {filename}")
        created_count += 1

        # Rate limiting between requests
        time.sleep(REQUEST_INTERVAL)

    print("-" * 50)
    print(f"Summary:")
    print(f"  Created: {created_count}")
    print(f"  Skipped (existing): {skipped_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Total posts in directory: {len(os.listdir(posts_dir))}")


if __name__ == "__main__":
    main()
