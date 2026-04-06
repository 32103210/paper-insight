#!/usr/bin/env python3
"""
Benchmark Extractor - 从已分析的论文中提取 benchmark 数据
自动从 _posts/ 目录的论文分析文章中提取实验结果，生成 leaderboard 数据
支持增量更新：同一模型的多来源结果全部保留
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict


# 数据集到领域的映射
DATASET_DOMAIN_MAP = {
    # CTR/CVR 领域
    'amazon': 'ctr-cvr',
    'taobao': 'ctr-cvr',
    'alibaba': 'ctr-cvr',
    '淘宝': 'ctr-cvr',
    '天猫': 'ctr-cvr',
    '淘宝广告': 'ctr-cvr',
    # LLM4Rec 领域
    'movielens': 'llm4rec',
    'movie-lens': 'llm4rec',
    'movie lens': 'llm4rec',
    'lastfm': 'llm4rec',
    'last-fm': 'llm4rec',
    'netflix': 'llm4rec',
}

# 领域显示名称
DOMAIN_NAMES = {
    'ctr-cvr': 'CTR/CVR Modeling',
    'llm4rec': 'LLM4Rec',
}

# 指标到领域的映射（用于确定主要指标）
METRIC_DOMAIN_PRIORITY = {
    'ctr-cvr': ['AUC', 'ROC-AUC', 'LogLoss', 'CrossEntropy'],
    'llm4rec': ['NDCG@', 'HR@', 'MRR@', 'Recall@', 'Precision@'],
}

# 已知指标全称映射
METRIC_ALIASES = {
    'AUC': 'AUC',
    'GAUC': 'GAUC',
    'NDCG': 'NDCG',
    'HR': 'HR',
    'MRR': 'MRR',
    'Recall': 'Recall',
    'Precision': 'Precision',
    'LogLoss': 'LogLoss',
    'Logloss': 'LogLoss',
}


def _convert_entry_to_new_format(entry: dict) -> dict:
    """Convert old format entry to new format with sources array."""
    if 'sources' in entry:
        # Already in new format
        return entry

    # Convert old format to new format
    # Old: {algorithm, paper_title, arxiv_id, source, results, post_url}
    # New: {algorithm, sources: [{arxiv_id, paper_title, source, results, post_url, paper_date}]}
    return {
        'algorithm': entry.get('algorithm', ''),
        'sources': [{
            'arxiv_id': entry.get('arxiv_id', ''),
            'paper_title': entry.get('paper_title', ''),
            'source': entry.get('source', ''),
            'post_url': entry.get('post_url', ''),
            'results': entry.get('results', {}),
            'paper_date': entry.get('paper_date', ''),
        }]
    }


def normalize_arxiv_id(value: str) -> str:
    """Normalize arXiv ID by dropping version suffix."""
    if not value:
        return ''

    match = re.search(r'(\d+\.\d+)(?:v\d+)?', str(value))
    return match.group(1) if match else str(value).strip()


def normalize_paper_title(value: str) -> str:
    """Normalize title for fuzzy identity matching."""
    if not value:
        return ''

    normalized = re.sub(r'[^a-z0-9]+', ' ', str(value).lower())
    return ' '.join(normalized.split())


def normalize_algorithm_name(value: str) -> str:
    """Normalize algorithm names for looser post matching."""
    return normalize_paper_title(value).replace(' ', '')


def extract_algorithm_name(title: str) -> str:
    """Extract a stable algorithm/model name from a paper title."""
    if not title:
        return ''

    if ':' in title:
        return title.split(':', 1)[0].strip()

    if ' - ' in title:
        return title.split(' - ', 1)[0].strip()

    return title.strip()


def build_known_posts_index(posts_data: List[dict]) -> dict:
    """Build lookup tables for benchmark posts by arXiv ID and title."""
    index = {
        'by_arxiv': {},
        'by_title': {},
        'by_algorithm': {},
    }

    for post in posts_data:
        algorithm_key = normalize_algorithm_name(post.get('algorithm', ''))
        for source in post.get('sources', []):
            arxiv_id = normalize_arxiv_id(source.get('arxiv_id', ''))
            title_key = normalize_paper_title(source.get('paper_title', ''))
            source_copy = {
                'arxiv_id': source.get('arxiv_id', ''),
                'paper_title': source.get('paper_title', ''),
                'source': source.get('source', ''),
                'post_url': source.get('post_url', ''),
                'paper_date': source.get('paper_date', ''),
            }
            if arxiv_id:
                index['by_arxiv'][arxiv_id] = source_copy
            if title_key:
                index['by_title'][title_key] = source_copy
            if algorithm_key and algorithm_key not in index['by_algorithm']:
                index['by_algorithm'][algorithm_key] = source_copy

    return index


def resolve_known_post(source: dict, known_posts: dict, algorithm: str = '') -> dict | None:
    """Resolve a benchmark source to a real post using arXiv ID or title."""
    arxiv_id = normalize_arxiv_id(source.get('arxiv_id', ''))
    if arxiv_id and arxiv_id in known_posts['by_arxiv']:
        return known_posts['by_arxiv'][arxiv_id]

    title_key = normalize_paper_title(source.get('paper_title', ''))
    if title_key and title_key in known_posts['by_title']:
        return known_posts['by_title'][title_key]

    algorithm_key = normalize_algorithm_name(algorithm)
    if algorithm_key and algorithm_key in known_posts['by_algorithm']:
        return known_posts['by_algorithm'][algorithm_key]

    return None


def load_existing_data() -> Dict[str, Dict[str, dict]]:
    """Load existing _data/benchmarks/*.yaml data"""
    benchmarks = defaultdict(lambda: defaultdict(lambda: {
        'dataset': '',
        'domain': '',
        'description': '',
        'metrics': [],
        'entries': []  # each entry: {algorithm: str, sources: [source1, source2]}
    }))

    output_dir = Path('_data/benchmarks')
    if not output_dir.exists():
        return benchmarks

    for domain_dir in output_dir.iterdir():
        if not domain_dir.is_dir():
            continue
        domain = domain_dir.name

        for yaml_file in domain_dir.glob('*.yaml'):
            dataset = yaml_file.stem
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data:
                        # Ensure entries are in new format
                        entries = data.get('entries', [])
                        converted_entries = [_convert_entry_to_new_format(e) for e in entries]
                        data['entries'] = converted_entries
                        benchmarks[domain][dataset] = data
                    else:
                        benchmarks[domain][dataset] = {
                            'dataset': dataset,
                            'domain': domain,
                            'description': '',
                            'metrics': [],
                            'entries': [],
                        }
            except Exception as e:
                print(f"  Warning: Failed to load {yaml_file}: {e}")
                benchmarks[domain][dataset] = {
                    'dataset': dataset,
                    'domain': domain,
                    'description': '',
                    'metrics': [],
                    'entries': [],
                }

    return benchmarks


def merge_entry(existing_entries: list, new_entry: dict) -> list:
    """Merge new entry into existing entries, deduplicate by arXiv ID.

    If the new entry's arXiv ID doesn't exist in any source, append it.
    If it exists, refresh the stored metadata/results in place.
    """
    # Find existing entry by algorithm name
    algorithm = new_entry.get('algorithm', '')
    existing_entry = None
    for entry in existing_entries:
        if entry.get('algorithm', '') == algorithm:
            existing_entry = entry
            break

    if existing_entry is None:
        # New algorithm, just append
        existing_entries.append(new_entry)
        return existing_entries

    # Algorithm exists - merge sources
    existing_sources = existing_entry.get('sources', [])
    new_sources = new_entry.get('sources', [])

    # Collect existing arXiv IDs and source index
    existing_arxiv_ids = set()
    existing_source_map = {}
    existing_title_map = {}
    for source in existing_sources:
        normalized_arxiv = normalize_arxiv_id(source.get('arxiv_id', ''))
        normalized_title = normalize_paper_title(source.get('paper_title', ''))
        if normalized_arxiv:
            existing_arxiv_ids.add(normalized_arxiv)
            existing_source_map[normalized_arxiv] = source
        if normalized_title:
            existing_title_map[normalized_title] = source

    # Add or refresh sources by arXiv ID
    for new_source in new_sources:
        new_arxiv_id = normalize_arxiv_id(new_source.get('arxiv_id', ''))
        new_title_key = normalize_paper_title(new_source.get('paper_title', ''))
        existing_source = None
        if new_arxiv_id and new_arxiv_id in existing_source_map:
            existing_source = existing_source_map[new_arxiv_id]
        elif new_title_key and new_title_key in existing_title_map:
            existing_source = existing_title_map[new_title_key]

        if existing_source is not None:
            if new_source.get('paper_title'):
                existing_source['paper_title'] = new_source['paper_title']
            if new_source.get('source'):
                existing_source['source'] = new_source['source']
            if new_source.get('post_url'):
                existing_source['post_url'] = new_source['post_url']
            if new_source.get('paper_date'):
                existing_source['paper_date'] = new_source['paper_date']
            if new_source.get('arxiv_id'):
                existing_source['arxiv_id'] = new_source['arxiv_id']
            if new_source.get('results'):
                existing_source.setdefault('results', {})
                existing_source['results'].update(new_source['results'])
            refreshed_arxiv_id = normalize_arxiv_id(existing_source.get('arxiv_id', ''))
            refreshed_title_key = normalize_paper_title(existing_source.get('paper_title', ''))
            if refreshed_arxiv_id:
                existing_arxiv_ids.add(refreshed_arxiv_id)
                existing_source_map[refreshed_arxiv_id] = existing_source
            if refreshed_title_key:
                existing_title_map[refreshed_title_key] = existing_source
        elif new_arxiv_id and new_arxiv_id not in existing_arxiv_ids:
            existing_sources.append(new_source)
            existing_arxiv_ids.add(new_arxiv_id)
            existing_source_map[new_arxiv_id] = new_source
            if new_title_key:
                existing_title_map[new_title_key] = new_source
        elif not new_arxiv_id:
            # If no arXiv ID, just append to avoid duplicates
            existing_sources.append(new_source)
            if new_title_key:
                existing_title_map[new_title_key] = new_source

    existing_entry['sources'] = existing_sources
    return existing_entries


def sanitize_benchmark_links(benchmarks: Dict[str, Dict[str, dict]], known_posts: dict):
    """Repair stale benchmark post links and clear unverifiable analysis URLs."""
    for datasets in benchmarks.values():
        for bench in datasets.values():
            for entry in bench.get('entries', []):
                for source in entry.get('sources', []):
                    known_post = resolve_known_post(source, known_posts, entry.get('algorithm', ''))
                    if not known_post:
                        source['post_url'] = ''
                        continue

                    source['post_url'] = known_post.get('post_url', '') or ''
                    if known_post.get('arxiv_id'):
                        source['arxiv_id'] = known_post['arxiv_id']
                    if known_post.get('paper_title'):
                        source['paper_title'] = known_post['paper_title']
                    if known_post.get('source'):
                        source['source'] = known_post['source']


def extract_frontmatter(content: str) -> tuple[dict, str]:
    """解析 markdown 文件的 frontmatter"""
    if not content.startswith('---'):
        return {}, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_text = parts[1]
    body = parts[2]

    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        return frontmatter or {}, body
    except:
        return {}, body


def extract_categories(body: str) -> List[str]:
    """从正文末尾提取分类信息"""
    categories = []
    # 查找 "分类：" 或 "分类信息" 后的内容
    match = re.search(r'(?:分类|标签)[:：]\s*(.+?)(?:\n|$)', body, re.MULTILINE)
    if match:
        cats = match.group(1).split(',')
        for cat in cats:
            cat = cat.strip().strip('*')
            if cat:
                categories.append(cat)
    return categories


def normalize_categories(categories) -> List[str]:
    """标准化分类数据，处理 dict 或 混合类型"""
    result = []
    if isinstance(categories, list):
        for cat in categories:
            if isinstance(cat, str):
                result.append(cat)
            elif isinstance(cat, dict):
                # 如果是 dict，取第一个 key
                result.extend(list(cat.keys()))
    elif isinstance(categories, dict):
        result.extend(list(categories.keys()))
    return result


def extract_metrics_from_text(text: str) -> List[dict]:
    """从文本中提取指标和数值"""
    results = []

    # 匹配模式: Metric@K: value 或 Metric@K = value
    # 例如: NDCG@5: 0.452, HR@10 = 0.682
    patterns = [
        r'([A-Za-z]+)@(\d+)\s*[:=]\s*([0-9.]+)',
        r'([A-Za-z]+)\s*@(\d+)\s*[:=]\s*([0-9.]+)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            metric_name = match[0]
            k = match[1]
            value = float(match[2])

            # 标准化指标名
            if metric_name in METRIC_ALIASES:
                metric_name = METRIC_ALIASES[metric_name]

            full_metric = f"{metric_name}@{k}"
            results.append({
                'metric': full_metric,
                'value': value
            })

    # 匹配独立指标: AUC: 0.8021, LogLoss = 0.123
    standalone_patterns = [
        r'\b(AUC|GAUC|LogLoss|CrossEntropy)\s*[:=]\s*([0-9.]+)',
    ]

    for pattern in standalone_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            metric_name = METRIC_ALIASES.get(match[0], match[0])
            value = float(match[1])
            results.append({
                'metric': metric_name,
                'value': value
            })

    return results


def extract_benchmark_section(text: str) -> tuple[List[str], List[dict]]:
    """从 'Benchmark数据' 章节提取结构化数据

    期望格式:
    Benchmark数据:
    - 数据集: Amazon
    - 指标: AUC, NDCG@5, HR@10
      - DeepFM: AUC=0.7965, NDCG@5=0.4521

    Returns:
        (datasets, metrics_with_values)
    """
    datasets = []
    results = []

    # 查找 Benchmark数据 章节
    match = re.search(r'Benchmark数据:\s*\n(.*?)(?:\n\n|\Z)', text, re.DOTALL)
    if not match:
        return datasets, results

    section = match.group(1)

    # 提取数据集
    dataset_matches = re.findall(r'- 数据集:\s*(.+)', section)
    for ds in dataset_matches:
        ds = ds.strip()
        # 标准化数据集名
        if 'amazon' in ds.lower():
            ds = 'Amazon'
        elif 'movie' in ds.lower() and 'lens' in ds.lower():
            ds = 'MovieLens'
        elif 'taobao' in ds.lower() or '淘宝' in ds:
            ds = 'Taobao'
        if ds not in datasets:
            datasets.append(ds)

    # 提取算法及其指标
    # 匹配: - 算法名: AUC=0.7965, NDCG@5=0.4521
    algo_pattern = r'-\s*([^:\n]+):\s*([\w@=0-9.,\s]+)'
    algo_matches = re.findall(algo_pattern, section)

    for algo_name, metrics_str in algo_matches:
        algo_name = algo_name.strip()
        # 提取指标
        # 匹配: AUC=0.7965 或 NDCG@5=0.4521
        metric_pattern = r'([A-Za-z]+)@?(\d*)=([0-9.]+)'
        metric_matches = re.findall(metric_pattern, metrics_str)

        for metric_name, k, value in metric_matches:
            metric_name = METRIC_ALIASES.get(metric_name, metric_name)
            if k:
                full_metric = f"{metric_name}@{k}"
            else:
                full_metric = metric_name

            results.append({
                'metric': full_metric,
                'value': float(value)
            })

    return datasets, results


def extract_datasets_from_text(text: str) -> List[str]:
    """从文本中提取数据集名称"""
    datasets = []

    # 已知数据集列表
    known_datasets = [
        'Amazon', 'Amazon Reviews', 'Amazon-Books', 'Amazon-CDs', 'Amazon-Electronics',
        'MovieLens', 'MovieLens-1M', 'MovieLens-10M', 'MovieLens-20M',
        'Taobao', 'Taobao Data', '淘宝', '天猫',
        'Alibaba', 'Alibaba-Offers',
        'LastFM', 'Last.FM', 'LastFM-1K',
        'Netflix', 'Yelp', 'Douban',
        'MIND', 'Pinterest', 'Goodreads',
        'CIKM', 'Diginetica', 'Nowplaying',
    ]

    text_lower = text.lower()
    for dataset in known_datasets:
        if dataset.lower() in text_lower:
            # 标准化数据集名
            normalized = dataset
            if 'amazon' in dataset.lower():
                normalized = 'Amazon'
            elif 'movie' in dataset.lower() and 'lens' in dataset.lower():
                normalized = 'MovieLens'
            elif 'taobao' in dataset.lower() or '淘宝' in dataset or '天猫' in dataset:
                normalized = 'Taobao'
            elif 'lastfm' in dataset.lower() or 'last.f' in dataset.lower():
                normalized = 'LastFM'
            elif 'netflix' in dataset.lower():
                normalized = 'Netflix'
            elif 'yelp' in dataset.lower():
                normalized = 'Yelp'
            elif 'douban' in dataset.lower():
                normalized = 'Douban'
            elif 'mind' in dataset.lower():
                normalized = 'MIND'

            if normalized not in datasets:
                datasets.append(normalized)

    return datasets


def determine_domain(categories: List[str], datasets: List[str]) -> str:
    """根据分类和数据集确定领域"""
    # 先检查数据集
    for dataset in datasets:
        dataset_lower = dataset.lower()
        for ds_key, domain in DATASET_DOMAIN_MAP.items():
            if ds_key in dataset_lower:
                return domain

    # 再检查分类
    category_text = ' '.join(categories).lower()
    if any(cat in category_text for cat in ['ctr', 'cvr', '点击率', '转化率', '广告', '电商排序']):
        return 'ctr-cvr'
    if any(cat in category_text for cat in ['llm', '大模型', 'gpt', '语言模型', '生成式推荐']):
        return 'llm4rec'
    if any(cat in category_text for cat in ['序列', 'sequential', 'next', 'next-item']):
        return 'llm4rec'  # 默认序列推荐到 LLM4Rec

    return 'ctr-cvr'  # 默认


def get_improvement_text(text: str) -> str:
    """提取性能提升描述"""
    patterns = [
        r'提升[了]?\s*([0-9.]+)%?\s*的?\s*([A-Za-z@0-9]+)',
        r'improve[ds]?\s*by?\s*([0-9.]+)%?\s*(?:in\s+)?([A-Za-z@0-9]+)',
        r'([0-9.]+)%\s*(?:improvement|improves|提升)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)

    return ''


def extract_benchmark_from_post(filepath: Path) -> dict:
    """从单篇论文分析中提取 benchmark 数据

    Returns new format: {
        algorithm: str,
        sources: [{
            arxiv_id: str,
            paper_title: str,
            source: str,
            post_url: str,
            results: dict,
            paper_date: str
        }]
    }
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    frontmatter, body = extract_frontmatter(content)

    if not frontmatter:
        return None

    # 提取基本信息
    title = frontmatter.get('title', '')
    arxiv_id = frontmatter.get('arxiv_id', '')
    authors = frontmatter.get('authors', '')
    source = frontmatter.get('source', '')
    date = frontmatter.get('date', '')

    # 从 URL 提取 arxiv_id
    if not arxiv_id and source:
        match = re.search(r'(\d+\.\d+)', source)
        if match:
            arxiv_id = match.group(1)

    # 提取分类
    categories = normalize_categories(frontmatter.get('categories', []))
    categories.extend(extract_categories(body))

    # 提取数据集（从全文）
    datasets = extract_datasets_from_text(body)

    # 提取指标（从全文）
    metrics = extract_metrics_from_text(body)

    # 从 Benchmark数据 章节提取结构化数据
    section_datasets, section_metrics = extract_benchmark_section(body)
    datasets = list(set(datasets + section_datasets))  # 合并去重
    metrics.extend(section_metrics)  # 合并指标

    # 确定领域
    domain = determine_domain(categories, datasets)

    # 从文件名提取 post_url
    filename = filepath.stem  # e.g., 2026-04-03-aligning-multimodal-...
    slug = '-'.join(filename.split('-')[3:])  # 去掉日期前缀
    post_url = f"/{filename.split('-')[0]}/{filename.split('-')[1]}/{filename.split('-')[2]}/{slug}/"

    # 提取算法名（从标题或分类）
    algorithm = extract_algorithm_name(title)
    if not algorithm or len(algorithm) < 2:
        # 尝试从分类中提取
        for cat in categories:
            if cat not in ['通用', '电商', '短视频', '多模态', '序列推荐', 'CTR预估', 'LLM推荐']:
                algorithm = cat
                break

    # 构建 results dict
    results_dict = {}
    for m in metrics:
        results_dict[m['metric']] = m['value']

    # 返回新格式（sources 数组）
    return {
        'algorithm': algorithm or 'Unknown',
        'domain': domain,
        'datasets': datasets,
        'sources': [{
            'arxiv_id': arxiv_id,
            'paper_title': title,
            'source': source,
            'post_url': post_url,
            'results': results_dict,
            'paper_date': date,
        }]
    }


def sort_entries_by_metric(entries: List[dict], primary_metric: str) -> List[dict]:
    """按指定指标排序条目"""
    def get_metric_value(entry):
        # Get best source result for the primary metric
        best_value = -1
        for source in entry.get('sources', []):
            results = source.get('results', {})
            value = results.get(primary_metric, -1)
            if value > best_value:
                best_value = value
        return best_value

    return sorted(entries, key=get_metric_value, reverse=True)


def main():
    """主函数 - 增量更新 benchmark 数据"""
    # 1. load_existing_data() 加载现有数据
    print("Loading existing benchmark data...")
    benchmarks = load_existing_data()
    total_existing = sum(len(d['entries']) for ds in benchmarks.values() for d in ds.values())
    print(f"  Loaded {total_existing} existing entries")

    # 2. 遍历 _posts/*.md 提取新数据
    posts_dir = Path('_posts')
    print(f"\nScanning {posts_dir} for new benchmark data...")

    posts_data = []
    for filepath in posts_dir.glob('*.md'):
        print(f"  Processing: {filepath.name}")
        data = extract_benchmark_from_post(filepath)
        if data and data.get('sources'):
            posts_data.append(data)
            print(f"    -> Found algorithm={data['algorithm']}, sources={len(data['sources'])}")
        else:
            print(f"    -> No benchmark data found")

    print(f"\nExtracted data from {len(posts_data)} posts")

    known_posts = build_known_posts_index(posts_data)

    # 3. 调用 merge_entry() for each new data
    for post in posts_data:
        domain = post['domain']
        datasets = post['datasets'] if post['datasets'] else ['Unknown']

        for dataset in datasets:
            # Normalize dataset name to prevent duplicates (Amazon vs amazon)
            normalized_dataset = dataset.lower().replace('-', '').replace(' ', '')
            bench = benchmarks[domain][normalized_dataset]

            # Ensure entries structure
            if 'entries' not in bench:
                bench['entries'] = []
            if 'metrics' not in bench:
                bench['metrics'] = []
            if 'dataset' not in bench or not bench['dataset']:
                bench['dataset'] = dataset
            if 'domain' not in bench or not bench['domain']:
                bench['domain'] = DOMAIN_NAMES.get(domain, domain)

            # Collect metrics from new sources
            for source in post['sources']:
                for metric_name in source.get('results', {}).keys():
                    if metric_name not in bench['metrics']:
                        bench['metrics'].append(metric_name)

            # Merge entry - pass only algorithm and sources, not the full post
            entry_to_merge = {
                'algorithm': post['algorithm'],
                'sources': post['sources']
            }
            bench['entries'] = merge_entry(bench['entries'], entry_to_merge)

    sanitize_benchmark_links(benchmarks, known_posts)

    # 4. 将合并结果写入 _data/benchmarks/*.yaml
    output_dir = Path('_data/benchmarks')
    output_dir.mkdir(parents=True, exist_ok=True)

    total_files = 0
    for domain, datasets in benchmarks.items():
        domain_dir = output_dir / domain
        domain_dir.mkdir(parents=True, exist_ok=True)

        for dataset, bench in datasets.items():
            # 按主要指标排序
            primary_metric = METRIC_DOMAIN_PRIORITY.get(domain, ['AUC'])[0]
            bench['entries'] = sort_entries_by_metric(bench['entries'], primary_metric)

            # 生成描述
            bench['description'] = f"{dataset} dataset for {DOMAIN_NAMES.get(domain, domain)}"

            # 写入文件
            filename = domain_dir / f"{dataset.lower().replace('-', '')}.yaml"
            # Normalize dataset name to prevent duplicate files for same dataset with different casing
            normalized_dataset = dataset.lower().replace('-', '').replace(' ', '')
            filename = domain_dir / f"{normalized_dataset}.yaml"
            with open(filename, 'w', encoding='utf-8') as f:
                yaml.dump(bench, f, allow_unicode=True, sort_keys=False)
            total_files += 1
            print(f"  Written: {filename}")

    print(f"\nDone! Updated {total_files} benchmark files in {output_dir}/")


if __name__ == '__main__':
    main()
