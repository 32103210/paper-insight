---
layout: page
title: Benchmark Leaderboard
---

# Benchmark Leaderboard

推荐算法领域论文性能排行榜。数据从已分析的论文中自动提取，涵盖 CTR/CVR 建模和 LLM4Rec 两个核心领域。

## 领域分类

<div class="benchmark-cards">

<div class="benchmark-card">
### CTR/CVR 建模
电商场景点击率/转化率预估

{% assign ctr_data = site.data.benchmarks["ctr-cvr"] %}
{% if ctr_data %}
| 数据集 | 论文数 |
|--------|--------|
{% for item in ctr_data %}
{% assign dataset = item[1] %}
| {{ dataset.dataset }} | {{ dataset.entries.size }} |
{% endfor %}

[View CTR/CVR Leaderboard →](ctr-cvr.html)
{% else %}
暂无数据
{% endif %}
</div>

<div class="benchmark-card">
### LLM4Rec
大语言模型在推荐系统中的应用

{% assign llm_data = site.data.benchmarks["llm4rec"] %}
{% if llm_data %}
| 数据集 | 论文数 |
|--------|--------|
{% for item in llm_data %}
{% assign dataset = item[1] %}
| {{ dataset.dataset }} | {{ dataset.entries.size }} |
{% endfor %}

[View LLM4Rec Leaderboard →](llm4rec.html)
{% else %}
暂无数据
{% endif %}
</div>

</div>

## 说明

- 排名数据从论文分析文章中自动提取
- 表格按主要指标（如 AUC、NDCG@10）降序排列
- 点击算法名可查看完整论文分析
- 运行 `python scripts/benchmark_extractor.py` 更新数据

## 数据来源

```bash
cd paper-insight
python scripts/benchmark_extractor.py
```
