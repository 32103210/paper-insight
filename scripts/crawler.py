#!/usr/bin/env python3
"""
arXiv 论文爬虫
搜索推荐算法相关最新论文
"""

import arxiv
import json
import os
import time
from datetime import datetime, timedelta
from typing import List
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

# arXiv API 速率限制: 每秒最多 1 次请求
# 为安全起见，使用 3.5 秒间隔
REQUEST_INTERVAL = 3.5

# 最大重试次数
MAX_RETRIES = 5

# 初始重试等待时间（秒）
INITIAL_RETRY_DELAY = 10


def search_with_retry(client, search, max_retries=MAX_RETRIES):
    """
    带重试的搜索，使用指数退避策略处理速率限制

    Args:
        client: arxiv.Client
        search: arxiv.Search
        max_retries: 最大重试次数

    Returns:
        list of results (论文列表)

    Raises:
        Exception: 所有重试都失败后抛出异常
    """
    all_results = []

    for attempt in range(max_retries):
        try:
            # 每次请求前等待，避免触发速率限制
            if attempt > 0:
                wait_time = INITIAL_RETRY_DELAY * (2 ** (attempt - 1))
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)

            # 执行搜索
            results = client.results(search)

            # 收集所有结果
            for result in results:
                all_results.append(result)

            # 如果有结果，返回它们
            if all_results:
                return all_results
            else:
                # 空结果，可能是速率限制
                if attempt < max_retries - 1:
                    wait_time = INITIAL_RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Empty results from arXiv (attempt {attempt + 1}/{max_retries}). Waiting {wait_time}s...")
                    continue
                else:
                    return []

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower() or "timeout" in error_str.lower():
                # 速率限制或超时，使用指数退避
                wait_time = INITIAL_RETRY_DELAY * (2 ** attempt)
                logger.warning(f"arXiv error (attempt {attempt + 1}/{max_retries}): {e}. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                # 其他错误，重试一次后放弃
                if attempt < max_retries - 1:
                    logger.warning(f"Error searching arXiv (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(INITIAL_RETRY_DELAY)
                else:
                    raise

    return all_results if all_results else []


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

    # 使用 arxiv 库搜索，带速率限制
    client = arxiv.Client()

    # 设置下载延迟（每秒请求数限制）
    client._throttle = REQUEST_INTERVAL

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    papers = []
    try:
        # 使用带重试的搜索（返回列表）
        results = search_with_retry(client, search)

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
        with open(filepath, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def save_processed_id(paper_id: str, filepath: str = "processed_ids.txt"):
    """保存已处理的论文 ID"""
    with open(filepath, "a", encoding="utf-8") as f:
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
    for p in new_papers:
        save_processed_id(p["id"])

    # 输出 JSON 格式供后续脚本使用
    print("\n---PAPERS_JSON---")
    print(json.dumps(new_papers, ensure_ascii=False, indent=2))
    print("---END_JSON---")

    return new_papers


if __name__ == "__main__":
    main()
