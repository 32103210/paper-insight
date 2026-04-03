---
layout: page
title: Paper Insight
---

<!-- Breadcrumb navigation -->
<nav class="breadcrumb" id="breadcrumb">
  <li><a href="{{ "/" | relative_url }}">首页</a></li>
  <li class="separator">/</li>
  <li class="current">全部文章</li>
</nav>

<!-- Search box -->
{% include header.html %}

<!-- Posts container -->
<div id="posts-container">
  {% for post in site.posts %}
  <article class="post-card">
    <div class="post-card-header">
      <h3 class="post-card-title">
        <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
      </h3>
      <span class="post-card-date">{{ post.date | date: "%Y-%m-%d" }}</span>
    </div>
    <div class="post-card-meta">
      {% if post.arxiv_id %}
      <span class="arxiv-id">ArXiv: {{ post.arxiv_id }}</span>
      {% endif %}
      {% if post.categories %}
      <div class="post-card-tags">
        {% for category in post.categories %}
        <span class="post-card-tag">{{ category }}</span>
        {% endfor %}
      </div>
      {% endif %}
    </div>
    {% if post.description %}
    <p class="post-card-excerpt">{{ post.description }}</p>
    {% endif %}
  </article>
  {% endfor %}
</div>
