#!/usr/bin/env python3
"""
论文分析脚本
调用 MiniMax API 生成论文分析报告
支持并行分析（使用 --parallel 参数）
"""

import os
import json
import sys
import re
import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml

# 确保可以导入同目录下的模块
sys.path.insert(0, str(Path(__file__).parent))

# 加载环境变量
load_dotenv()

# MiniMax API 配置
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1")

# 并行分析的最大线程数
MAX_WORKERS = 3

ANALYSIS_MARKERS = (
    "## 一句话增量",
    "## 1. 一句话增量",
    "# 论文分析报告",
    "## 博导审稿",
)

# 导入 prompt 模板
from prompts import SYSTEM_PROMPT, build_user_prompt


@dataclass
class AnalysisSummary:
    total: int
    succeeded: int = 0
    failed: int = 0

    @property
    def total_failure(self) -> bool:
        return self.total > 0 and self.succeeded == 0 and self.failed > 0


def create_client() -> OpenAI:
    """创建 OpenAI 兼容客户端"""
    return OpenAI(
        api_key=MINIMAX_API_KEY,
        base_url=MINIMAX_BASE_URL,
    )


def normalize_arxiv_id(value: str) -> str:
    """标准化 arXiv ID，去掉版本号。"""
    if not value:
        return ""

    match = re.search(r'(\d+\.\d+)(?:v\d+)?', value)
    return match.group(1) if match else value.strip()


def has_analysis_content(text: str) -> bool:
    """判断正文里是否已经包含结构化分析。"""
    return any(marker in (text or "") for marker in ANALYSIS_MARKERS)


def normalize_categories(raw_categories) -> list:
    """将 frontmatter categories 统一转换成字符串列表。"""
    if not raw_categories:
        return []

    if not isinstance(raw_categories, list):
        raw_categories = [raw_categories]

    categories = []
    for item in raw_categories:
        if isinstance(item, str):
            categories.append(item.strip())
        elif isinstance(item, dict):
            for _, value in item.items():
                if isinstance(value, str):
                    categories.append(value.strip())

    return list(dict.fromkeys([c for c in categories if c]))


def load_post(filepath: Path) -> tuple[dict, str]:
    """读取 markdown post，返回 frontmatter 和正文。"""
    content = filepath.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    frontmatter = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip()
    return frontmatter, body


def extract_abstract_from_post(body: str, frontmatter: dict) -> str:
    """从旧文章里提取摘要，优先取 Abstract 段落。"""
    match = re.search(r'##\s+Abstract\s*(.*?)(?:\n##\s+|\Z)', body, re.DOTALL)
    if match:
        abstract = match.group(1).strip()
    else:
        abstract = str(frontmatter.get("description", "")).strip()

    abstract = re.sub(r'\n{2,}', '\n', abstract)
    return abstract.strip()


def build_paper_from_post(filepath: Path) -> Optional[dict]:
    """从现有 post 反解析出 paper 信息，用于补分析。"""
    frontmatter, body = load_post(filepath)
    if not frontmatter:
        return None

    if frontmatter.get("analysis_generated") or has_analysis_content(body):
        return None

    title = str(frontmatter.get("title", "")).strip()
    source = str(frontmatter.get("source", "")).strip()
    authors_text = str(frontmatter.get("authors", "")).strip()
    abstract = extract_abstract_from_post(body, frontmatter)
    categories = normalize_categories(frontmatter.get("categories", []))

    if not title or not abstract:
        return None

    authors = [a.strip() for a in authors_text.split(",") if a.strip()] or ["Unknown"]
    post_date = str(frontmatter.get("date", "")).strip()[:10]
    arxiv_id = normalize_arxiv_id(str(frontmatter.get("arxiv_id", "")) or source)

    return {
        "id": arxiv_id or filepath.stem,
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "published": post_date,
        "pdf_url": source,
        "source_url": source,
        "post_date": post_date,
        "categories": categories,
        "output_path": str(filepath),
    }


def cleanup_analysis_content(analysis: str) -> str:
    """清理模型输出中的内部思考和控制信息。"""
    analysis_content = re.sub(r'<think>.*?</think>', '', analysis, flags=re.DOTALL | re.IGNORECASE).strip()
    analysis_content = re.sub(r'```\s*分类:.*?```', '', analysis_content, flags=re.DOTALL).strip()
    analysis_content = re.sub(r'^分类:.*$', '', analysis_content, flags=re.MULTILINE).strip()
    analysis_content = re.sub(r'<!--.*?-->', '', analysis_content, flags=re.DOTALL)
    analysis_content = re.sub(r'<!--.*', '', analysis_content)
    return analysis_content.strip()


def save_processed_id(paper_id: str, filepath: str = "processed_ids.txt"):
    """仅在分析成功后记录已处理论文。"""
    if not paper_id:
        return

    existing_ids = set()
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            existing_ids = {line.strip() for line in f if line.strip()}

    if paper_id in existing_ids:
        return

    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"{paper_id}\n")


def analyze_paper(client: OpenAI, paper: dict) -> str:
    """
    调用 MiniMax API 分析单篇论文

    Args:
        client: OpenAI 客户端
        paper: 论文信息字典

    Returns:
        Markdown 格式的分析报告
    """
    user_prompt = build_user_prompt(paper)

    response = client.chat.completions.create(
        model="MiniMax-M2.7",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=8192,
    )

    return response.choices[0].message.content


def extract_arxiv_id(url: str) -> str:
    """从 URL 提取 arXiv ID"""
    normalized = normalize_arxiv_id(url)
    return normalized or "unknown"


def slugify(title: str, max_length: int = 50) -> str:
    """将标题转换为 URL 友好的 slug"""
    # 移除非字母数字字符
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    # 替换空格为连字符
    slug = re.sub(r'[-\s]+', '-', slug)
    # 限制长度
    slug = slug[:max_length].strip('-')
    return slug


def extract_categories(analysis: str) -> list:
    """从分析报告中提取分类标签"""
    # 预定义的标签集合（严格匹配）
    VALID_TAGS = {
        # 任务类型
        "CTR预估", "序列推荐", "KG推荐", "GNN推荐", "冷启动", "多兴趣", "对比学习", "通用",
        # 应用场景
        "电商", "新闻", "短视频", "音乐", "POI",
        # 技术方向
        "自监督", "对比学习", "LLM增强", "多模态", "偏差修正", "因果推断", "知识蒸馏", "缩放定律",
    }

    cat_match = re.search(r'分类:\s*([^\\n]+)', analysis)
    if not cat_match:
        return []

    cats = cat_match.group(1).strip().split(',')
    result = []
    for c in cats:
        tag = c.strip()
        # 清理可能的多余符号（如 **）
        tag = tag.strip('*').strip()
        # 只接受有效标签
        if tag in VALID_TAGS:
            result.append(tag)

    # 最多返回3个标签
    return result[:3]


def generate_frontmatter(paper: dict, categories: list = None) -> str:
    """生成 Jekyll frontmatter"""
    source_url = paper.get('source_url') or paper.get('pdf_url', '')
    source_url = source_url.replace('/pdf/', '/abs/').replace('.pdf', '')
    arxiv_id = extract_arxiv_id(source_url)
    date_str = paper.get('post_date') or datetime.now().strftime("%Y-%m-%d")

    # 提取一句话摘要用于 description
    abstract_text = (paper.get('abstract') or '').replace('\n', ' ').strip()
    sentence_match = re.match(r'(.{1,200}?[。.!?])(?:\s|$)', abstract_text)
    abstract_first_line = sentence_match.group(1) if sentence_match else abstract_text[:200]

    final_categories = categories or normalize_categories(paper.get('categories', [])) or ['通用']

    frontmatter = f"""---
layout: post
analysis_generated: true
title: {json.dumps(paper['title'], ensure_ascii=False)}
date: {date_str}
arxiv_id: {json.dumps(arxiv_id, ensure_ascii=False)}
authors: {json.dumps(', '.join(paper['authors']), ensure_ascii=False)}
source: {json.dumps(source_url, ensure_ascii=False)}
description: {json.dumps(abstract_first_line[:200], ensure_ascii=False)}
"""
    # 添加分类
    frontmatter += "categories:\n"
    for cat in final_categories:
        frontmatter += f"  - {cat}\n"

    frontmatter += "---\n\n"
    return frontmatter


def save_analysis(paper: dict, analysis: str, output_dir: str = "_posts", output_path: Optional[str] = None):
    """
    保存分析报告到 _posts 目录

    Args:
        paper: 论文信息
        analysis: Markdown 分析报告
        output_dir: 输出目录
    """
    Path(output_dir).mkdir(exist_ok=True)

    # 提取分类
    categories = extract_categories(analysis)

    analysis_content = cleanup_analysis_content(analysis)

    # 生成文件名
    if output_path:
        filepath = Path(output_path)
    else:
        date_str = paper.get('post_date') or datetime.now().strftime("%Y-%m-%d")
        slug = slugify(paper['title'])
        filename = f"{date_str}-{slug}.md"
        filepath = Path(output_dir) / filename

    # 生成 frontmatter + 分析内容
    frontmatter = generate_frontmatter(paper, categories)
    content = frontmatter + analysis_content

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Saved: {filepath}")
    if categories:
        print(f"  Categories: {', '.join(categories)}")
    return filepath


def analyze_single_paper(paper: dict, client: OpenAI) -> tuple:
    """分析单篇论文，返回 (paper, analysis, error)"""
    try:
        analysis = analyze_paper(client, paper)
        return (paper, analysis, None)
    except Exception as e:
        return (paper, None, str(e))


def collect_missing_posts(posts_dir: str, limit: Optional[int] = None) -> list:
    """收集还没有 AI 分析的历史文章。"""
    missing_posts = []

    for filepath in sorted(Path(posts_dir).glob("*.md")):
        paper = build_paper_from_post(filepath)
        if paper:
            missing_posts.append(paper)

    if limit is not None:
        missing_posts = missing_posts[:limit]

    return missing_posts


def run_analysis_batch(
    papers_json: list,
    *,
    parallel: bool,
    workers: int,
    backfill_missing: bool,
) -> AnalysisSummary:
    """执行一批论文分析，并返回成功/失败统计。"""
    summary = AnalysisSummary(total=len(papers_json))
    client = create_client()

    if parallel and len(papers_json) > 1:
        print(f"Using parallel mode with {workers} workers")
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(analyze_single_paper, paper, client): paper for paper in papers_json}

            for i, future in enumerate(as_completed(futures), 1):
                paper, analysis, error = future.result()
                if error:
                    summary.failed += 1
                    print(f"[{i}/{len(papers_json)}] {paper['title'][:60]}... Error: {error}")
                    continue

                save_analysis(paper, analysis, output_path=paper.get('output_path'))
                if not backfill_missing:
                    save_processed_id(paper.get('id', ''))
                summary.succeeded += 1
                print(f"[{i}/{len(papers_json)}] {paper['title'][:60]}... Done!")

        return summary

    for i, paper in enumerate(papers_json, 1):
        print(f"\n[{i}/{len(papers_json)}] Analyzing: {paper['title'][:60]}...")

        try:
            analysis = analyze_paper(client, paper)
            save_analysis(paper, analysis, output_path=paper.get('output_path'))
            if not backfill_missing:
                save_processed_id(paper.get('id', ''))
            summary.succeeded += 1
            print("  Done!")
        except Exception as e:
            summary.failed += 1
            print(f"  Error: {e}")

    return summary


def main(argv: Optional[list[str]] = None, stdin_input: Optional[str] = None) -> int:
    """主函数"""
    parser = argparse.ArgumentParser(description='论文分析脚本')
    parser.add_argument('--parallel', action='store_true', help='启用并行分析')
    parser.add_argument('--workers', type=int, default=MAX_WORKERS, help=f'并行工作线程数 (默认 {MAX_WORKERS})')
    parser.add_argument('--backfill-missing', action='store_true', help='为已有但缺少 AI 分析的文章补全分析')
    parser.add_argument('--posts-dir', default='_posts', help='文章目录（默认 _posts）')
    parser.add_argument('--limit', type=int, help='限制处理文章数')
    args = parser.parse_args(argv)

    # 检查 API Key
    if not MINIMAX_API_KEY:
        print("Error: MINIMAX_API_KEY not set")
        return 1

    if args.backfill_missing:
        papers_json = collect_missing_posts(args.posts_dir, args.limit)
        if not papers_json:
            print("No legacy posts need analysis backfill")
            return 0
    else:
        # 从 stdin 读取论文列表（由 crawler.py 输出，grep 已提取 JSON 部分）
        payload = stdin_input if stdin_input is not None else sys.stdin.read()
        stdin_payload = payload.strip()

        # 解析 JSON
        papers_json = None
        if stdin_payload:
            try:
                papers_json = json.loads(stdin_payload)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                print(f"Received input: {stdin_payload[:500]}...")
                return 1

        if not papers_json:
            print("No papers to analyze")
            return 0

    print(f"Analyzing {len(papers_json)} papers...")

    summary = run_analysis_batch(
        papers_json,
        parallel=args.parallel,
        workers=args.workers,
        backfill_missing=args.backfill_missing,
    )

    print(
        f"\nAnalysis complete: {summary.succeeded}/{summary.total} succeeded, "
        f"{summary.failed} failed."
    )
    if summary.total_failure:
        print("Analysis failed: no paper was analyzed successfully.")
        return 1
    if summary.failed:
        print("Analysis completed with partial failures.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
