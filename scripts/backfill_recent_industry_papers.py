#!/usr/bin/env python3
"""
批量补充近两年工业界推荐论文。

策略：
1. 使用更宽的推荐检索词扫描 arXiv
2. 仅保留推荐/排序/广告强相关论文
3. 必须存在工业界单位或公司邮箱信号
4. 跳过仓库中已有的 arXiv ID
"""

import os
import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List

import arxiv

from crawler import (
    REQUEST_INTERVAL,
    classify_paper_topics,
    fetch_industry_signals,
    load_existing_post_ids,
    load_processed_ids,
    normalize_arxiv_id,
    search_with_retry,
)

TOPIC_QUERY_TERMS = [
    "recommendation system",
    "recommender system ranking",
    "click-through rate prediction",
    "conversion rate prediction",
    "advertising ranking",
    "reranking recommendation",
    "sequential recommendation",
    "multimodal recommendation",
    "e-commerce recommendation",
    "short video recommendation",
    "candidate generation recommendation",
    "retrieval recommendation",
    "conversational recommendation",
    "generative recommendation",
    "retrieval augmented recommendation",
]

COMPANY_QUERY_TERMS = [
    "Meituan recommendation",
    "Kuaishou recommendation",
    "ByteDance recommendation",
    "Alibaba recommendation",
    "Google recommendation",
    "Amazon recommendation",
    "Meta recommendation",
    "Tencent recommendation",
    "Shopee recommendation",
    "Spotify recommendation",
    "LinkedIn recommendation",
]

RECOMMENDATION_KEYWORDS = (
    "recommendation",
    "recommender",
    "ranking",
    "rerank",
    "click-through rate",
    "ctr",
    "conversion rate",
    "cvr",
    "advertising",
    "ads",
    "retrieval",
    "candidate generation",
    "personalization",
    "sequential recommendation",
    "session recommendation",
)

TARGET_RESULTS = int(os.getenv("BACKFILL_TARGET_RESULTS", "40"))
MAX_RESULTS_PER_QUERY = int(os.getenv("BACKFILL_MAX_RESULTS_PER_QUERY", "18"))
DAYS_BACK = int(os.getenv("BACKFILL_DAYS_BACK", "730"))
START_DATE = datetime.now() - timedelta(days=DAYS_BACK)
END_DATE = datetime.now()


def build_search_terms() -> List[str]:
    """按优先级构建去重后的检索词。"""
    ordered_terms = []
    for term in TOPIC_QUERY_TERMS + COMPANY_QUERY_TERMS:
        if term not in ordered_terms:
            ordered_terms.append(term)
    return ordered_terms


def is_recommendation_paper(title: str, abstract: str) -> bool:
    """仅保留推荐/排序/广告强相关论文。"""
    combined = f"{title} {abstract}".lower()
    return any(keyword in combined for keyword in RECOMMENDATION_KEYWORDS)


def infer_seed_categories(paper: dict) -> List[str]:
    """为待分析文章提供初始分类，后续会被分析结果覆盖。"""
    combined = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
    paper_topics = paper.get("paper_topics", [])

    if "llm4rec" in paper_topics or any(
        keyword in combined for keyword in ("llm", "large language model", "generative recommendation")
    ):
        return ["LLM推荐"]
    if any(keyword in combined for keyword in ("click-through rate", "ctr", "conversion rate", "cvr", "advertising")):
        return ["CTR预估"]
    if any(keyword in combined for keyword in ("sequential recommendation", "session recommendation", "next-item")):
        return ["序列推荐"]
    if "multimodal" in combined:
        return ["多模态"]
    return ["通用"]


def sanitize_filename(title: str) -> str:
    """将论文标题转为安全文件名。"""
    sanitized = re.sub(r"[^\w\s-]", "", title)
    sanitized = re.sub(r"[-\s]+", "-", sanitized).strip("-")
    return sanitized.lower()[:60]


def format_authors(authors: Iterable) -> str:
    """格式化作者列表。"""
    author_names = [author.name for author in authors]
    if len(author_names) <= 3:
        return ", ".join(author_names)
    return f"{', '.join(author_names[:3])}, et al."


def truncate_description(abstract: str, max_length: int = 300) -> str:
    """截断摘要，避免 frontmatter 过长。"""
    normalized = str(abstract or "").replace("\n", " ").strip()
    if len(normalized) <= max_length:
        return normalized
    return normalized[:max_length].rsplit(" ", 1)[0] + "..."


def create_post_filename(paper: dict) -> str:
    """生成 Jekyll post 文件名。"""
    return f"{paper['date']}-{sanitize_filename(paper['title'])}.md"


def create_post_content(paper: dict) -> str:
    """生成待分析 post 内容。"""
    categories = infer_seed_categories(paper)
    frontmatter = f"""---
layout: post
title: {json.dumps(paper['title'], ensure_ascii=False)}
date: {paper['date']}
arxiv_id: {json.dumps(paper['arxiv_id'], ensure_ascii=False)}
authors: {json.dumps(paper['authors'], ensure_ascii=False)}
source: {json.dumps(paper['source'], ensure_ascii=False)}
description: {json.dumps(paper['description'], ensure_ascii=False)}
analysis_generated: false
categories:
"""
    for category in categories:
        frontmatter += f"  - {category}\n"

    if paper.get("industry_affiliations"):
        frontmatter += "industry_affiliations:\n"
        for affiliation in paper["industry_affiliations"]:
            frontmatter += f"  - {affiliation}\n"

    frontmatter += "---\n\n"
    return (
        frontmatter
        + f"# {paper['title']}\n\n"
        + f"**Authors:** {paper['authors']}\n\n"
        + f"**arXiv ID:** [{paper['arxiv_id']}]({paper['source']})\n\n"
        + f"**Published:** {paper['date']}\n\n"
        + "---\n\n"
        + "## Abstract\n\n"
        + paper["abstract"].strip()
        + "\n"
    )


def search_query_term(client: arxiv.Client, term: str) -> List:
    """按单个检索词拉取最近论文候选。"""
    search = arxiv.Search(
        query=f'(all:"{term}") AND (cat:cs.IR OR cat:cs.LG)',
        max_results=MAX_RESULTS_PER_QUERY,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    return search_with_retry(client, search, max_retries=1)


def build_paper_info(result, signals: dict) -> dict:
    """将 arXiv 结果映射成待保存的 post 元数据。"""
    paper_id = normalize_arxiv_id(result.entry_id.split("/")[-1])
    title = result.title.replace("\n", " ").strip()
    abstract = (result.summary or "").strip()
    source = result.pdf_url.replace("/pdf/", "/abs/") if "/pdf/" in result.pdf_url else result.entry_id

    return {
        "title": title,
        "date": result.published.strftime("%Y-%m-%d"),
        "arxiv_id": paper_id,
        "authors": format_authors(result.authors),
        "source": source.replace(".pdf", ""),
        "description": truncate_description(abstract),
        "abstract": abstract,
        "paper_topics": classify_paper_topics(title, abstract),
        "industry_affiliations": signals.get("industry_affiliations", []),
        "industry_email_domains": signals.get("industry_email_domains", []),
        "published": result.published,
    }


def search_recent_industry_papers(target_results: int = TARGET_RESULTS) -> List[dict]:
    """批量搜索近两年工业界推荐论文。"""
    client = arxiv.Client()
    client._throttle = REQUEST_INTERVAL

    excluded_ids = load_existing_post_ids() | load_processed_ids()
    collected = {}

    print(f"Existing/processed IDs to skip: {len(excluded_ids)}")

    for index, term in enumerate(build_search_terms(), 1):
        if len(collected) >= target_results:
            break

        print(f"[{index}] Query term: {term}")
        try:
            results = search_query_term(client, term)
        except Exception as exc:
            print(f"  Warning: failed query '{term}': {exc}")
            continue

        for result in results:
            published = result.published.replace(tzinfo=None)
            if published < START_DATE or published > END_DATE:
                continue

            paper_id = normalize_arxiv_id(result.entry_id.split("/")[-1])
            if not paper_id or paper_id in excluded_ids or paper_id in collected:
                continue

            title = result.title.replace("\n", " ").strip()
            abstract = (result.summary or "").strip()
            if not is_recommendation_paper(title, abstract):
                continue

            signals = fetch_industry_signals(paper_id, result.pdf_url)
            if not signals["industry_affiliations"] and not signals["industry_email_domains"]:
                continue

            paper_info = build_paper_info(result, signals)
            collected[paper_id] = paper_info
            print(f"  Added: {paper_info['date']} {paper_info['title'][:80]}")

            if len(collected) >= target_results:
                break

        time.sleep(REQUEST_INTERVAL)

    papers = sorted(
        collected.values(),
        key=lambda paper: paper["published"],
        reverse=True,
    )
    return papers


def save_posts(papers: List[dict], posts_dir: str = "_posts") -> int:
    """将候选论文落成待分析文章。"""
    output_dir = Path(posts_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    for paper in papers:
        filename = create_post_filename(paper)
        filepath = output_dir / filename
        if filepath.exists():
            continue

        filepath.write_text(create_post_content(paper), encoding="utf-8")
        created += 1
        print(f"Created: {filepath.name}")

    return created


def main() -> int:
    """主函数。"""
    print(
        f"Backfilling industrial recommendation papers from "
        f"{START_DATE.date()} to {END_DATE.date()}, target={TARGET_RESULTS}"
    )
    papers = search_recent_industry_papers(TARGET_RESULTS)
    print(f"Collected {len(papers)} candidate papers")

    created = save_posts(papers)
    print(f"Created {created} new posts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
