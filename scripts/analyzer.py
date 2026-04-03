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
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

# 确保可以导入同目录下的模块
sys.path.insert(0, str(Path(__file__).parent))

# 加载环境变量
load_dotenv()

# MiniMax API 配置
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1")

# 并行分析的最大线程数
MAX_WORKERS = 3

# 导入 prompt 模板
from prompts import SYSTEM_PROMPT, build_user_prompt


def create_client() -> OpenAI:
    """创建 OpenAI 兼容客户端"""
    return OpenAI(
        api_key=MINIMAX_API_KEY,
        base_url=MINIMAX_BASE_URL,
    )


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
    match = re.search(r'(\d+\.\d+)', url)
    return match.group(1) if match else "unknown"


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
    # 查找 ```yaml ... ``` 代码块
    yaml_match = re.search(r'```yaml\s*\n(categories:.*?)```', analysis, re.DOTALL)
    if yaml_match:
        yaml_content = yaml_match.group(1).strip()
        # 解析 YAML 格式的分类
        categories = []
        for line in yaml_content.split('\n'):
            line = line.strip()
            # 处理多种格式："- 任务类型: CTR预估" 或 "- 任务类型 CTR预估"
            if '任务类型' in line:
                # 提取标签值（冒号或空格分隔）
                val = re.sub(r'^-\s*任务类型[:\s]+', '', line).strip()
                categories.append(f"任务类型: {val}")
            elif '应用场景' in line:
                val = re.sub(r'^-\s*应用场景[:\s]+', '', line).strip()
                categories.append(f"应用场景: {val}")
            elif '技术方向' in line:
                val = re.sub(r'^-\s*技术方向[:\s]+', '', line).strip()
                categories.append(f"技术方向: {val}")
        return categories
    return []


def generate_frontmatter(paper: dict, categories: list = None) -> str:
    """生成 Jekyll frontmatter"""
    arxiv_id = extract_arxiv_id(paper['pdf_url'])
    date_str = datetime.now().strftime("%Y-%m-%d")

    # 提取一句话摘要用于 description
    abstract_first_line = paper['abstract'].split('.')[0] + '.'

    frontmatter = f"""---
title: "{paper['title']}"
date: {date_str}
arxiv_id: {arxiv_id}
authors: "{', '.join(paper['authors'])}"
source: {paper['pdf_url'].replace('.pdf', '')}
description: "{abstract_first_line[:200]}"
"""
    # 添加分类
    if categories:
        frontmatter += "categories:\n"
        for cat in categories:
            frontmatter += f"  - {cat}\n"
    else:
        frontmatter += "categories:\n  - 任务类型: 通用\n  - 应用场景: 通用\n  - 技术方向: 通用\n"

    frontmatter += "---\n\n"
    return frontmatter


def save_analysis(paper: dict, analysis: str, output_dir: str = "_posts"):
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

    # 移除 YAML 代码块（如果存在）
    analysis_content = re.sub(r'```yaml\s*\n.*?```\s*', '', analysis, flags=re.DOTALL).strip()

    # 清理模型输出的内部标记
    analysis_content = re.sub(r'&\lt;!--.*?--&gt;', '', analysis_content, flags=re.DOTALL)  # HTML注释
    analysis_content = re.sub(r'&lt;!--.*?--&gt;', '', analysis_content, flags=re.DOTALL)  # HTML注释变体
    analysis_content = re.sub(r'&lt;!--.*', '', analysis_content)  # 未闭合注释
    analysis_content = re.sub(r'&lt;!--.*', '', analysis_content)  # 未闭合注释
    analysis_content = analysis_content.strip()

    # 生成文件名
    date_str = datetime.now().strftime("%Y-%m-%d")
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


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='论文分析脚本')
    parser.add_argument('--parallel', action='store_true', help='启用并行分析')
    parser.add_argument('--workers', type=int, default=MAX_WORKERS, help=f'并行工作线程数 (默认 {MAX_WORKERS})')
    args = parser.parse_args()

    # 检查 API Key
    if not MINIMAX_API_KEY:
        print("Error: MINIMAX_API_KEY not set")
        sys.exit(1)

    # 从 stdin 读取论文列表（由 crawler.py 输出）
    stdin_input = sys.stdin.read()
    papers_json = None

    # 解析 JSON
    if "---PAPERS_JSON---" in stdin_input:
        parts = stdin_input.split("---PAPERS_JSON---")
        if len(parts) > 1:
            json_part = parts[1].split("---END_JSON---")[0].strip()
            papers_json = json.loads(json_part)

    if not papers_json:
        print("No papers to analyze")
        sys.exit(0)

    print(f"Analyzing {len(papers_json)} papers...")

    if args.parallel and len(papers_json) > 1:
        # 并行分析
        print(f"Using parallel mode with {args.workers} workers")
        client = create_client()

        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(analyze_single_paper, paper, client): paper for paper in papers_json}

            for i, future in enumerate(as_completed(futures), 1):
                paper, analysis, error = future.result()
                if error:
                    print(f"[{i}/{len(papers_json)}] {paper['title'][:60]}... Error: {error}")
                else:
                    save_analysis(paper, analysis)
                    print(f"[{i}/{len(papers_json)}] {paper['title'][:60]}... Done!")
    else:
        # 串行分析
        client = create_client()
        for i, paper in enumerate(papers_json, 1):
            print(f"\n[{i}/{len(papers_json)}] Analyzing: {paper['title'][:60]}...")

            try:
                analysis = analyze_paper(client, paper)
                save_analysis(paper, analysis)
                print(f"  Done!")
            except Exception as e:
                print(f"  Error: {e}")
                continue

    print("\nAll papers analyzed!")


if __name__ == "__main__":
    main()