#!/usr/bin/env python3
"""
arXiv 论文爬虫
搜索推荐算法相关最新论文
"""

import arxiv
import os
from datetime import datetime, timedelta
from typing import List


# 搜索关键词配置
SEARCH_QUERIES = [
    "recommendation system",
    "collaborative filtering",
    "recommender system ranking",
    "graph neural network recommendation",
    "sequential recommendation",
]

# 每次最多获取论文数
MAX_RESULTS = 5


def search_papers(days_back: int = 7, max_results: int = MAX_RESULTS) -> List[dict]:
    """
    搜索最近N天的推荐算法相关论文

    Args:
        days_back: 搜索最近多少天的论文
        max_results: 最多返回多少篇

    Returns:
        论文列表，每篇包含 id, title, authors, abstract, published
    """
    # 计算日期范围
    start_date = datetime.now() - timedelta(days=days_back)

    # 构建搜索查询
    query_parts = [" OR ".join([f'all:"{q}"' for q in SEARCH_QUERIES])]
    query = f"({query_parts[0]}) AND (cat:cs.IR OR cat:cs.LG)"

    print(f"Searching arXiv with query: {query}")

    # 使用 arxiv 库搜索
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    papers = []
    try:
        results = client.results(search)

        for result in results:
            # 过滤日期
            if result.published.replace(tzinfo=None) < start_date.replace(tzinfo=None):
                continue

            paper_info = {
                "id": result.entry_id.split("/")[-1],
                "title": result.title,
                "authors": [a.name for a in result.authors],
                "abstract": result.summary,
                "published": result.published.isoformat(),
                "pdf_url": result.pdf_url,
                "comment": result.comment if hasattr(result, 'comment') else None,
                "journal_ref": result.journal_ref if hasattr(result, 'journal_ref') else None,
            }
            papers.append(paper_info)
            print(f"  Found: {paper_info['title'][:60]}...")

    except Exception as e:
        print(f"Error searching arXiv: {e}")

    return papers


def load_processed_ids(filepath: str = "processed_ids.txt") -> set:
    """加载已处理的论文 ID"""
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def save_processed_id(paper_id: str, filepath: str = "processed_ids.txt"):
    """保存已处理的论文 ID"""
    with open(filepath, "a") as f:
        f.write(f"{paper_id}\n")


def main():
    """主函数"""
    print(f"[{datetime.now().isoformat()}] Starting paper search...")

    papers = search_papers(days_back=7, max_results=MAX_RESULTS)
    print(f"\nFound {len(papers)} papers")

    # 过滤已处理的论文
    processed = load_processed_ids()
    new_papers = [p for p in papers if p["id"] not in processed]

    print(f"New papers to process: {len(new_papers)}")

    # 输出 JSON 格式供后续脚本使用
    import json
    print("\n---PAPERS_JSON---")
    print(json.dumps(new_papers, ensure_ascii=False, indent=2))
    print("---END_JSON---")

    return new_papers


if __name__ == "__main__":
    main()
