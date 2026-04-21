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
import io
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib import error, request
from dotenv import load_dotenv
from openai import OpenAI
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
RATE_LIMIT_RETRY_DELAYS = (30, 60, 120)

ANALYSIS_MARKERS = (
    "## 一句话增量",
    "## 1. 一句话增量",
    "# 论文分析报告",
    "## 博导审稿",
)

PDF_REQUEST_TIMEOUT = 30
PDF_USER_AGENT = "paper-insight/1.0 (+https://github.com/32103210/paper-insight)"
PDF_AFFILIATION_SCAN_CHAR_LIMIT = 4000
EMAIL_PATTERN = re.compile(
    r'([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})',
    flags=re.IGNORECASE,
)
AFFILIATION_LINE_HINTS = (
    "university", "college", "institute", "school", "academy", "hospital",
    "faculty", "department", "laboratory", "lab", "research", "center",
    "centre", "group", "company", "corporation", "corp", "inc", "ltd",
    "llc", "gmbh", "plc", "ag", "meituan", "google", "amazon", "microsoft",
    "meta", "facebook", "alibaba", "tencent", "baidu", "huawei", "xiaomi",
    "shopee", "sea", "openai", "anthropic", "bytedance", "kuaishou",
)
AFFILIATION_STOP_MARKERS = ("abstract", "1 introduction", "introduction")
TITLE_NOISE_KEYWORDS = (
    "recommendation", "rerank", "method", "framework", "model", "system",
    "learning", "generative", "retrieval", "ranking",
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


def normalize_string_list(raw_values) -> list:
    """将 frontmatter 中的字符串或列表统一转换成去重字符串列表。"""
    if not raw_values:
        return []

    if not isinstance(raw_values, list):
        raw_values = [raw_values]

    normalized = []
    for item in raw_values:
        if isinstance(item, str):
            value = item.strip()
            if value and value not in normalized:
                normalized.append(value)

    return normalized


def normalize_pdf_url(url: str) -> str:
    """将 abs/pdf 链接统一归一化为可下载的 PDF 链接。"""
    normalized = str(url or "").strip()
    if not normalized:
        return ""

    if "/abs/" in normalized:
        normalized = normalized.replace("/abs/", "/pdf/")
    if not normalized.endswith(".pdf"):
        normalized = normalized.rstrip("/") + ".pdf"
    return normalized


def fetch_pdf_first_page_text(pdf_url: str) -> str:
    """抓取 PDF 首页文本，用于解析作者单位。"""
    normalized_url = normalize_pdf_url(pdf_url)
    if not normalized_url:
        return ""

    req = request.Request(normalized_url, headers={"User-Agent": PDF_USER_AGENT})
    try:
        with request.urlopen(req, timeout=PDF_REQUEST_TIMEOUT) as resp:
            pdf_bytes = resp.read()
    except (error.HTTPError, error.URLError, TimeoutError):
        return ""

    try:
        from pypdf import PdfReader
    except ImportError:
        return ""

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        if not reader.pages:
            return ""
        return (reader.pages[0].extract_text() or "").strip()
    except Exception:
        return ""


def clean_affiliation_line(line: str) -> str:
    """清理 PDF 首页中疑似单位行的噪声。"""
    cleaned = EMAIL_PATTERN.sub("", line or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,;:-")
    cleaned = re.sub(r"^[\d\W_]+", "", cleaned)
    cleaned = re.sub(r"[\d\W_]+$", "", cleaned)
    return cleaned.strip()


def looks_like_affiliation_line(line: str) -> bool:
    """判断一行文本是否像作者单位。"""
    normalized = str(line or "").strip()
    if not normalized:
        return False

    lower = normalized.lower()
    has_affiliation_hint = any(
        re.search(rf"\b{re.escape(hint)}\b", lower)
        for hint in AFFILIATION_LINE_HINTS
    )
    if "@" in lower:
        return False
    if any(lower.startswith(marker) for marker in AFFILIATION_STOP_MARKERS):
        return False
    if " at " in lower and len(normalized.split()) > 3:
        return False
    if any(keyword in lower for keyword in TITLE_NOISE_KEYWORDS) and not any(
        hint in lower for hint in (
            "university", "college", "institute", "school", "academy", "hospital",
            "faculty", "department", "laboratory", "lab", "research", "center",
            "centre", "group", "company", "corporation", "corp", "inc", "ltd",
            "llc", "gmbh", "plc", "ag",
        )
    ):
        return False
    if len(normalized.split()) <= 1 and not has_affiliation_hint:
        return False

    return has_affiliation_hint


def extract_author_affiliations_from_pdf_text(text: str) -> list:
    """从 PDF 首页文本中提取作者单位集合。"""
    excerpt = str(text or "")[:PDF_AFFILIATION_SCAN_CHAR_LIMIT]
    if not excerpt:
        return []

    affiliations = []
    for raw_line in excerpt.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue

        lower = line.lower()
        if any(lower.startswith(marker) for marker in AFFILIATION_STOP_MARKERS):
            break

        cleaned = clean_affiliation_line(line)
        if looks_like_affiliation_line(cleaned) and cleaned not in affiliations:
            affiliations.append(cleaned)

    try:
        from crawler import infer_company_from_email_domain, is_industry_affiliation
    except Exception:
        infer_company_from_email_domain = None
        is_industry_affiliation = None

    if infer_company_from_email_domain:
        for _local_part, domain in EMAIL_PATTERN.findall(excerpt):
            company = infer_company_from_email_domain(domain)
            if company and company not in affiliations:
                affiliations.append(company)

    if is_industry_affiliation:
        normalized = []
        for affiliation in affiliations:
            if not affiliation:
                continue
            if affiliation not in normalized:
                normalized.append(affiliation)
        return normalized

    return affiliations


def enrich_paper_author_affiliations(paper: dict, force_refresh: bool = False) -> dict:
    """在分析前补充 PDF 首页解析出的作者单位。"""
    author_affiliations = [] if force_refresh else normalize_string_list(paper.get("author_affiliations", []))
    if not author_affiliations:
        pdf_text = fetch_pdf_first_page_text(paper.get("pdf_url") or paper.get("source_url", ""))
        author_affiliations = extract_author_affiliations_from_pdf_text(pdf_text)
        if author_affiliations:
            paper["author_affiliations"] = author_affiliations

    try:
        from crawler import is_industry_affiliation
    except Exception:
        is_industry_affiliation = None

    if is_industry_affiliation:
        current_industry = [] if force_refresh else normalize_string_list(paper.get("industry_affiliations", []))
        if not current_industry and author_affiliations:
            paper["industry_affiliations"] = [
                affiliation
                for affiliation in author_affiliations
                if is_industry_affiliation(affiliation)
            ]

    return paper


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
    industry_affiliations = normalize_string_list(frontmatter.get("industry_affiliations", []))
    author_affiliations = normalize_string_list(frontmatter.get("author_affiliations", []))

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
        "industry_affiliations": industry_affiliations,
        "author_affiliations": author_affiliations,
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
    enrich_paper_author_affiliations(paper)
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


def is_rate_limit_error(exc: Exception) -> bool:
    """判断是否为可重试的限流/拥堵错误。"""
    status_code = getattr(exc, "status_code", None)
    if status_code in {429, 529}:
        return True

    response = getattr(exc, "response", None)
    response_status = getattr(response, "status_code", None)
    if response_status in {429, 529}:
        return True

    message = str(exc or "")
    rate_limit_markers = (
        "Error code: 429",
        "Error code: 529",
        "'http_code': '429'",
        "'http_code': '529'",
        '"http_code": "429"',
        '"http_code": "529"',
        "rate_limit_error",
        "overloaded_error",
        "Too Many Requests",
    )
    return any(marker in message for marker in rate_limit_markers)


def analyze_single_paper(paper: dict, client: OpenAI) -> tuple:
    """分析单篇论文，返回 (paper, analysis, error)。"""
    for attempt in range(len(RATE_LIMIT_RETRY_DELAYS) + 1):
        try:
            analysis = analyze_paper(client, paper)
            return (paper, analysis, None)
        except Exception as exc:
            if not is_rate_limit_error(exc) or attempt >= len(RATE_LIMIT_RETRY_DELAYS):
                return (paper, None, str(exc))

            delay = RATE_LIMIT_RETRY_DELAYS[attempt]
            print(f"  Rate limited, waiting {delay}s before retry...")
            time.sleep(delay)


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

    industry_affiliations = normalize_string_list(paper.get("industry_affiliations", []))
    if industry_affiliations:
        frontmatter += "industry_affiliations:\n"
        for affiliation in industry_affiliations:
            frontmatter += f"  - {affiliation}\n"

    author_affiliations = normalize_string_list(paper.get("author_affiliations", []))
    if author_affiliations:
        frontmatter += "author_affiliations:\n"
        for affiliation in author_affiliations:
            frontmatter += f"  - {affiliation}\n"

    frontmatter += "---\n\n"
    return frontmatter


def strip_author_affiliations_section(content: str) -> str:
    """移除正文中已有的作者单位段落，避免重复插入。"""
    return re.sub(r'## 作者单位\s*.*?(?=\n##\s+|\Z)', '', content or '', flags=re.DOTALL).lstrip()


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

    analysis_content = strip_author_affiliations_section(analysis_content)

    author_affiliations = normalize_string_list(paper.get("author_affiliations", []))
    author_affiliation_section = ""
    if author_affiliations:
        author_affiliation_section = "## 作者单位\n\n" + "\n".join(
            f"- {affiliation}" for affiliation in author_affiliations
        ) + "\n\n"

    # 生成 frontmatter + 分析内容
    frontmatter = generate_frontmatter(paper, categories)
    content = frontmatter + author_affiliation_section + analysis_content

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Saved: {filepath}")
    if categories:
        print(f"  Categories: {', '.join(categories)}")
    return filepath


def refresh_author_affiliations_in_post(filepath: Path) -> bool:
    """为已有分析文章补充作者单位 frontmatter 和正文段落。"""
    frontmatter, body = load_post(filepath)
    if not frontmatter:
        return False

    title = str(frontmatter.get("title", "")).strip()
    source = str(frontmatter.get("source", "")).strip()
    authors_text = str(frontmatter.get("authors", "")).strip()
    abstract = extract_abstract_from_post(body, frontmatter)
    categories = normalize_categories(frontmatter.get("categories", []))
    industry_affiliations = normalize_string_list(frontmatter.get("industry_affiliations", []))
    author_affiliations = normalize_string_list(frontmatter.get("author_affiliations", []))

    if not title or not source:
        return False

    paper = {
        "id": normalize_arxiv_id(str(frontmatter.get("arxiv_id", "")) or source) or filepath.stem,
        "title": title,
        "authors": [a.strip() for a in authors_text.split(",") if a.strip()] or ["Unknown"],
        "abstract": abstract,
        "published": str(frontmatter.get("date", "")).strip(),
        "pdf_url": source,
        "source_url": source,
        "post_date": str(frontmatter.get("date", "")).strip()[:10],
        "categories": categories,
        "industry_affiliations": industry_affiliations,
        "author_affiliations": author_affiliations,
    }

    enrich_paper_author_affiliations(paper, force_refresh=True)
    if not paper.get("author_affiliations"):
        return False

    frontmatter_text = generate_frontmatter(paper, categories)
    body_content = strip_author_affiliations_section(body)
    author_section = "## 作者单位\n\n" + "\n".join(
        f"- {affiliation}" for affiliation in normalize_string_list(paper["author_affiliations"])
    ) + "\n\n"

    filepath.write_text(frontmatter_text + author_section + body_content, encoding="utf-8")
    return True


def backfill_author_affiliations(posts_dir: str, limit: Optional[int] = None) -> int:
    """为已有文章批量补充作者单位信息。"""
    updated = 0
    for index, filepath in enumerate(sorted(Path(posts_dir).glob("*.md")), 1):
        if limit is not None and updated >= limit:
            break
        if refresh_author_affiliations_in_post(filepath):
            updated += 1
            print(f"[{index}] Updated author affiliations: {filepath.name}")
    return updated


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
        print("Parallel mode requested, but disabled for rate-limit protection; using serial mode.")

    for i, paper in enumerate(papers_json, 1):
        print(f"\n[{i}/{len(papers_json)}] Analyzing: {paper['title'][:60]}...")

        paper, analysis, error = analyze_single_paper(paper, client)
        if error:
            summary.failed += 1
            print(f"  Error: {error}")
            continue

        try:
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
    parser.add_argument('--backfill-author-affiliations', action='store_true', help='为已有文章补充作者单位信息')
    parser.add_argument('--posts-dir', default='_posts', help='文章目录（默认 _posts）')
    parser.add_argument('--limit', type=int, help='限制处理文章数')
    args = parser.parse_args(argv)

    if args.backfill_author_affiliations:
        updated = backfill_author_affiliations(args.posts_dir, args.limit)
        print(f"Backfilled author affiliations for {updated} posts")
        return 0

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
