#!/usr/bin/env python3
"""
Benchmark Extractor - 从已分析的论文中提取 benchmark 数据
自动从 _posts/ 目录的论文分析文章中提取实验结果，生成 leaderboard 数据
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
    """从单篇论文分析中提取 benchmark 数据"""
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
    algorithm = title.split(':')[0].split('-')[0].strip() if title else ''
    if not algorithm or len(algorithm) < 2:
        # 尝试从分类中提取
        for cat in categories:
            if cat not in ['通用', '电商', '短视频', '多模态', '序列推荐', 'CTR预估', 'LLM推荐']:
                algorithm = cat
                break

    return {
        'algorithm': algorithm or 'Unknown',
        'paper_title': title,
        'arxiv_id': arxiv_id,
        'source': source,
        'authors': str(authors)[:100],  # 截断
        'post_url': post_url,
        'domain': domain,
        'datasets': datasets,
        'metrics': metrics,
        'categories': categories,
        'improvement': get_improvement_text(body),
    }


def aggregate_benchmarks(posts_data: List[dict]) -> Dict[str, Dict[str, dict]]:
    """将论文数据聚合成 benchmark 数据"""
    # 按领域-数据集组织
    benchmarks = defaultdict(lambda: defaultdict(lambda: {
        'dataset': '',
        'domain': '',
        'description': '',
        'metrics': [],
        'entries': []
    }))

    for post in posts_data:
        if not post or not post['metrics']:
            continue

        domain = post['domain']
        datasets = post['datasets'] if post['datasets'] else ['Unknown']

        for dataset in datasets:
            key = f"{domain}/{dataset}"
            bench = benchmarks[domain][dataset]

            bench['dataset'] = dataset
            bench['domain'] = DOMAIN_NAMES.get(domain, domain)

            # 添加指标到列表
            for metric in post['metrics']:
                metric_name = metric['metric']
                if metric_name not in bench['metrics']:
                    bench['metrics'].append(metric_name)

            # 添加条目
            entry = {
                'algorithm': post['algorithm'],
                'paper_title': post['paper_title'],
                'arxiv_id': post['arxiv_id'],
                'source': post['source'],
                'results': post['metrics'],
                'post_url': post['post_url'],
            }
            bench['entries'].append(entry)

    return benchmarks


def sort_entries_by_metric(entries: List[dict], primary_metric: str) -> List[dict]:
    """按指定指标排序条目"""
    def get_metric_value(entry):
        for result in entry['results']:
            if result['metric'] == primary_metric:
                return result['value']
        return -1

    return sorted(entries, key=get_metric_value, reverse=True)


def main():
    """主函数"""
    # 路径配置
    posts_dir = Path('_posts')
    output_dir = Path('_data/benchmarks')

    print(f"Scanning {posts_dir} for benchmark data...")

    # 提取所有论文的 benchmark 数据
    posts_data = []
    for filepath in posts_dir.glob('*.md'):
        print(f"  Processing: {filepath.name}")
        data = extract_benchmark_from_post(filepath)
        if data:
            posts_data.append(data)
            print(f"    -> Found {len(data['metrics'])} metrics, {len(data['datasets'])} datasets")
        else:
            print(f"    -> No benchmark data found")

    print(f"\nExtracted data from {len(posts_data)} posts")

    # 聚合成 benchmark
    benchmarks = aggregate_benchmarks(posts_data)

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    # 保存到 YAML 文件
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
            with open(filename, 'w', encoding='utf-8') as f:
                yaml.dump(bench, f, allow_unicode=True, sort_keys=False)
            total_files += 1
            print(f"  Written: {filename}")

    print(f"\nDone! Generated {total_files} benchmark files in {output_dir}/")


if __name__ == '__main__':
    main()
