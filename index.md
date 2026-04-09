---
layout: page
title: Paper Insight
---

{% assign industrial_posts = site.posts | where_exp: "post", "post.industry_affiliations and post.industry_affiliations != empty" %}

<script>
window.POSTS_DATA = [
{% for post in industrial_posts %}
  {
    title: {{ post.title | jsonify }},
    url: {{ post.url | relative_url | jsonify }},
    date: {{ post.date | date: "%Y-%m-%d" | jsonify }},
    arxiv_id: {{ post.arxiv_id | jsonify }},
    categories: {{ post.categories | jsonify }},
    industry_affiliations: {{ post.industry_affiliations | jsonify }},
    description: {{ post.description | default: post.excerpt | strip_html | strip_newlines | jsonify }}
  }{% unless forloop.last %},{% endunless %}
{% endfor %}
];
</script>

<!-- Breadcrumb navigation -->
<nav class="breadcrumb" id="breadcrumb">
  <li><a href="{{ "/" | relative_url }}">首页</a></li>
  <li class="separator">/</li>
  <li class="current">全部文章</li>
</nav>

<!-- Search box -->
{% include header.html %}

<div class="home-content-grid">
  <!-- Posts container -->
  <div id="posts-container">
    {% for post in industrial_posts %}
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
        {% for category in post.categories | uniq %}
        <span class="post-card-tag">{{ category }}</span>
        {% endfor %}
      </div>
      {% endif %}
      {% if post.industry_affiliations %}
      <div class="post-card-tags">
        {% for affiliation in post.industry_affiliations %}
        <span class="post-card-tag post-card-tag-industry">业界 · {{ affiliation }}</span>
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

  <aside id="home-rail" class="home-rail">
    <section class="rail-card">
      <div class="rail-card-header">
        <h2 class="rail-card-title">按月份归档</h2>
        <span class="rail-card-meta">跟随当前筛选</span>
      </div>
      <div id="archive-timeline" class="archive-timeline"></div>
    </section>

    <section class="rail-card">
      <div class="rail-card-header">
        <h2 class="rail-card-title">最新文章</h2>
        <span class="rail-card-meta">按当前结果排序</span>
      </div>
      <div id="latest-posts" class="latest-posts"></div>
    </section>
  </aside>
</div>
