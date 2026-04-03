---
layout: page
title: CTR/CVR Modeling Benchmark
---

# CTR/CVR Modeling Leaderboard

电商场景点击率/转化率预估论文性能排行榜。

{% assign ctr_data = site.data.benchmarks["ctr-cvr"] %}
{% if ctr_data %}

{% for item in ctr_data %}
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
暂无 CTR/CVR Benchmark 数据。

运行以下命令提取数据：
```bash
python scripts/benchmark_extractor.py
```
{% endif %}

[← 返回 Benchmark 首页](/benchmark/)
