#!/usr/bin/env python3
"""
arXiv 论文爬虫
搜索推荐算法相关最新论文
"""

import arxiv
import json
import os
import sys
import time
import logging
import re
from datetime import datetime, timedelta
from typing import List
from html import unescape
from urllib import error, request

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
MAX_RESULTS = int(os.getenv("ARXIV_MAX_RESULTS", "20"))

# 搜索时间窗口，默认回看 2 天，兼容偶发调度失败
DAYS_BACK = int(os.getenv("ARXIV_DAYS_BACK", "2"))

# arXiv API 速率限制: 每秒最多 1 次请求
# 为安全起见，使用 3.5 秒间隔
REQUEST_INTERVAL = 3.5

# 最大重试次数
MAX_RETRIES = 5

# 初始重试等待时间（秒）
INITIAL_RETRY_DELAY = 15

HTML_REQUEST_TIMEOUT = 20
HTML_USER_AGENT = "paper-insight/1.0 (+https://github.com/32103210/paper-insight)"

INDUSTRY_KEYWORDS = (
    "google", "alphabet", "meta", "facebook", "amazon", "apple", "microsoft",
    "netflix", "bytedance", "bytedance", "alibaba", "ant group", "tencent",
    "meituan", "kuaishou", "baidu", "huawei", "xiaomi", "jd.com", "jingdong",
    "didi", "uber", "airbnb", "spotify", "linkedin", "openai", "anthropic",
    "salesforce", "yahoo", "shopify", "shopee", "grab", "paypal", "ebay",
    "rakuten", "instacart", "pinterest", "snap", "booking.com", "trip.com",
    "doordash", "intel", "samsung", "nvidia", "qualcomm", "adobe", "oracle",
    "ibm", "microsoft research", "google research", "noah's ark", "sea ai lab",
)

ACADEMIC_KEYWORDS = (
    "university", "college", "institute", "school", "academy", "hospital",
    "faculty", "department", "laboratory", "lab", "research center",
)

AFFILIATION_PATTERN = re.compile(
    r'ltx_affiliation_institution">([^<]+)</span>',
    flags=re.IGNORECASE,
)
EMAIL_PATTERN = re.compile(
    r'([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})',
    flags=re.IGNORECASE,
)
PUBLIC_EMAIL_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "msn.com",
    "icloud.com",
    "me.com",
    "mac.com",
    "163.com",
    "126.com",
    "yeah.net",
    "qq.com",
    "foxmail.com",
    "sina.com",
    "sina.cn",
    "sohu.com",
    "aol.com",
    "gmx.com",
    "proton.me",
    "protonmail.com",
}
EMAIL_DOMAIN_COMPANY_MAP = {
    "meituan.com": "Meituan",
    "google.com": "Google",
    "deepmind.com": "DeepMind",
    "amazon.com": "Amazon",
    "amazon.science": "Amazon",
    "apple.com": "Apple",
    "microsoft.com": "Microsoft",
    "meta.com": "Meta",
    "fb.com": "Meta",
    "bytedance.com": "ByteDance",
    "tiktok.com": "ByteDance",
    "alibaba.com": "Alibaba",
    "alibaba-inc.com": "Alibaba",
    "antgroup.com": "Ant Group",
    "tencent.com": "Tencent",
    "baidu.com": "Baidu",
    "huawei.com": "Huawei",
    "xiaomi.com": "Xiaomi",
    "jd.com": "JD.com",
    "kuaishou.com": "Kuaishou",
    "shopee.com": "Shopee",
    "sea.com": "Sea",
    "openai.com": "OpenAI",
    "anthropic.com": "Anthropic",
    "linkedin.com": "LinkedIn",
    "airbnb.com": "Airbnb",
    "uber.com": "Uber",
    "booking.com": "Booking.com",
    "trip.com": "Trip.com",
    "adobe.com": "Adobe",
    "ibm.com": "IBM",
    "oracle.com": "Oracle",
    "intel.com": "Intel",
    "nvidia.com": "NVIDIA",
    "qualcomm.com": "Qualcomm",
    "paypal.com": "PayPal",
    "ebay.com": "eBay",
    "shopify.com": "Shopify",
    "instacart.com": "Instacart",
    "pinterest.com": "Pinterest",
    "doordash.com": "DoorDash",
    "grab.com": "Grab",
    "spotify.com": "Spotify",
    "snap.com": "Snap",
    "rakuten.com": "Rakuten",
}


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
        # 每次请求前等待，避免触发速率限制
        if attempt > 0:
            wait_time = INITIAL_RETRY_DELAY * (2 ** (attempt - 1))
            print(f"Waiting {wait_time}s before retry...")
            time.sleep(wait_time)

        try:
            # 执行搜索 - 注意: arxiv 库返回懒加载迭代器
            # 实际 HTTP 请求在迭代时发生
            results = client.results(search)

            # 手动迭代收集结果，这样可以在迭代过程中捕获异常
            collected = []
            try:
                for result in results:
                    collected.append(result)
            except Exception as e:
                # 迭代过程中出错，可能是速率限制
                error_str = str(e).lower()
                if "429" in str(e) or "rate" in error_str or "timeout" in error_str:
                    print(f"Rate limit or timeout during iteration (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        raise
                else:
                    raise

            # 如果有结果，返回它们
            if collected:
                print(f"Got {len(collected)} papers from arXiv")
                return collected
            else:
                # 空结果，可能是速率限制
                print(f"Empty results from arXiv (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    continue
                else:
                    return []

        except Exception as e:
            print(f"Error searching arXiv (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                wait_time = INITIAL_RETRY_DELAY * (2 ** attempt)
                print(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                raise

    return all_results if all_results else []


def normalize_affiliation_name(name: str) -> str:
    """规范化单位名称。"""
    if not name:
        return ""

    normalized = unescape(str(name))
    normalized = re.sub(r"\s+", " ", normalized).strip(" ,;")
    return normalized


def normalize_affiliation_lookup(name: str) -> str:
    """将单位名归一化为适合关键词匹配的 token 串。"""
    normalized = normalize_affiliation_name(name).lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def is_industry_affiliation(name: str) -> bool:
    """判断单位是否属于工业界。"""
    normalized = normalize_affiliation_name(name).lower()
    lookup = normalize_affiliation_lookup(name)
    if not normalized or not lookup:
        return False

    if any(re.search(rf"\b{re.escape(normalize_affiliation_lookup(keyword))}\b", lookup) for keyword in INDUSTRY_KEYWORDS):
        return True

    has_corporate_suffix = any(
        re.search(rf"\b{suffix}\b", lookup)
        for suffix in ("inc", "ltd", "llc", "corp", "corporation", "company", "gmbh", "plc", "ag")
    )
    if has_corporate_suffix and not any(keyword in lookup for keyword in ACADEMIC_KEYWORDS):
        return True

    return False


def infer_company_from_email_domain(domain: str) -> str:
    """从邮箱域名推断公司名，排除公共邮箱。"""
    normalized = normalize_affiliation_lookup(domain)
    if not normalized:
        return ""

    labels = normalized.split()
    if not labels:
        return ""

    candidates = [".".join(labels[index:]) for index in range(len(labels) - 1)]
    for candidate in candidates:
        if candidate in PUBLIC_EMAIL_DOMAINS:
            return ""
        if candidate in EMAIL_DOMAIN_COMPANY_MAP:
            return EMAIL_DOMAIN_COMPANY_MAP[candidate]

    if any(
        re.search(rf"\b{re.escape(normalize_affiliation_lookup(keyword))}\b", normalized)
        for keyword in INDUSTRY_KEYWORDS
    ):
        company_token = labels[-2] if len(labels) >= 2 else labels[0]
        return company_token.upper() if len(company_token) <= 4 else company_token.title()

    return ""


def extract_industry_affiliations_from_emails(html: str) -> List[str]:
    """从邮箱域名中提取工业界单位。"""
    affiliations = []
    for _local_part, domain in EMAIL_PATTERN.findall(html or ""):
        affiliation = infer_company_from_email_domain(domain)
        if affiliation and affiliation not in affiliations:
            affiliations.append(affiliation)

    return affiliations


def extract_industry_affiliations_from_html(html: str) -> List[str]:
    """从 arXiv HTML 页面中提取工业界单位。"""
    affiliations = []
    for match in AFFILIATION_PATTERN.findall(html or ""):
        affiliation = normalize_affiliation_name(match)
        if affiliation and is_industry_affiliation(affiliation) and affiliation not in affiliations:
            affiliations.append(affiliation)

    for affiliation in extract_industry_affiliations_from_emails(html):
        if affiliation not in affiliations:
            affiliations.append(affiliation)

    return affiliations


def fetch_industry_affiliations(arxiv_id: str) -> List[str]:
    """抓取 arXiv HTML 页面中的工业界单位。"""
    if not arxiv_id:
        return []

    html_url = f"https://arxiv.org/html/{arxiv_id}"
    req = request.Request(html_url, headers={"User-Agent": HTML_USER_AGENT})

    try:
        with request.urlopen(req, timeout=HTML_REQUEST_TIMEOUT) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except (error.HTTPError, error.URLError, TimeoutError) as exc:
        logger.warning("Failed to fetch affiliation HTML for %s: %s", arxiv_id, exc)
        return []

    return extract_industry_affiliations_from_html(html)


def search_papers(days_back: int = DAYS_BACK, max_results: int = MAX_RESULTS) -> List[dict]:
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

    # 首次请求前等待，避免被限流
    print("Waiting 5s before first request to avoid rate limiting...")
    time.sleep(5)

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
    results = search_with_retry(client, search)

    # 在处理结果前等待一段时间，避免触发速率限制
    if results:
        print(f"Got {len(results)} papers from arXiv, processing...")

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
            "industry_affiliations": fetch_industry_affiliations(result.entry_id.split("/")[-1]),
        }
        papers.append(paper_info)
        print(f"  Found: {paper_info['title'][:60]}...")

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


def main() -> int:
    """主函数"""
    print(f"[{datetime.now().isoformat()}] Starting paper search...")

    try:
        papers = search_papers(days_back=DAYS_BACK, max_results=MAX_RESULTS)
    except Exception as e:
        print(f"Fatal error searching arXiv: {e}")
        return 1

    print(f"\nFound {len(papers)} papers")

    # 过滤已处理的论文
    processed = load_processed_ids()
    new_papers = [p for p in papers if p["id"] not in processed]

    print(f"New papers to process: {len(new_papers)}")

    # 输出 JSON 格式供后续脚本使用
    print("\n---PAPERS_JSON---")
    print(json.dumps(new_papers, ensure_ascii=False, indent=2))
    print("---END_JSON---")

    return 0


if __name__ == "__main__":
    sys.exit(main())
