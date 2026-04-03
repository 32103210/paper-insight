---
layout: page
title: CTR/CVR Modeling Benchmark
---

# CTR/CVR Modeling Leaderboard

电商场景点击率/转化率预估论文性能排行榜。

{% if site.data.benchmarks.ctr-cvr %}

{% for dataset in site.data.benchmarks.ctr-cvr %}
## {{ dataset[1].dataset }} {#{{ dataset[0] }}}

{{ dataset[1].description }}

{% if dataset[1].metrics %}
**主要指标:** {{ dataset[1].metrics | join: ', ' }}
{% endif %}

{% if dataset[1].entries.size > 0 %}
{% include benchmark_table.html data=dataset[1] %}
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
