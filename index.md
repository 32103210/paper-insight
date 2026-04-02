---
layout: page
title: Paper Insight
---

# Paper Insight

每天自动抓取工业界推荐算法相关论文，AI 生成结构化分析报告。

论文来源: [arXiv](https://arxiv.org/)
分析方法: 基于李继刚论文深读框架

{% for post in site.posts %}
## [{{ post.title }}]({{ post.url }})

{{ post.date | date: "%Y-%m-%d" }} | arXiv: {{ post.arxiv_id }}

{{ post.description }}
{% endfor %}