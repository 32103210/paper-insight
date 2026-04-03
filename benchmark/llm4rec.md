---
layout: page
title: LLM4Rec Benchmark
---

# LLM4Rec Leaderboard

大语言模型在推荐系统中应用的论文性能排行榜。

{% assign llm_data = site.data.benchmarks["llm4rec"] %}
{% if llm_data %}

{% for item in llm_data %}
{% assign dataset_name = item[0] %}
{% assign dataset = item[1] %}
## {{ dataset.dataset }}

{{ dataset.description }}

{% if dataset.metrics %}
**主要指标:** {{ dataset.metrics | join: ', ' }}
{% endif %}

{% if dataset.entries.size > 0 %}
{% include benchmark_table.html data=dataset %}
{% else %}
暂无数据
{% endif %}

---
{% endfor %}

{% else %}
暂无 LLM4Rec Benchmark 数据。

运行以下命令提取数据：
```bash
python scripts/benchmark_extractor.py
```
{% endif %}

[← 返回 Benchmark 首页](/benchmark/)
