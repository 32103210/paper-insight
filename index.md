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
      <span class="arxiv-id">arXiv: {{ post.arxiv_id }}</span>
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

<!-- Embedded data for JavaScript -->
<script>
  // CATEGORIES object - built from Jekyll post categories
  window.CATEGORIES = {};

  // POSTS_DATA - embedded post metadata for JavaScript
  window.POSTS_DATA = [
    {% for post in site.posts %}
    {
      title: {{ post.title | jsonify }},
      url: {{ post.url | jsonify }},
      date: {{ post.date | date: "%Y-%m-%d" | jsonify }},
      arxiv_id: {{ post.arxiv_id | jsonify }},
      categories: {{ post.categories | jsonify }},
      excerpt: {{ post.description | jsonify }},
      tags: []
    }{% unless forloop.last %},{% endunless %}
    {% endfor %}
  ];

  // Build CATEGORIES structure from posts
  window.POSTS_DATA.forEach(function(post) {
    if (post.categories && post.categories.length > 0) {
      var level1 = post.categories[0];
      if (!window.CATEGORIES[level1]) {
        window.CATEGORIES[level1] = { children: {}, posts: [] };
      }

      if (post.categories.length > 1) {
        var level2 = post.categories[1];
        if (!window.CATEGORIES[level1].children[level2]) {
          window.CATEGORIES[level1].children[level2] = { children: {}, posts: [] };
        }

        if (post.categories.length > 2) {
          var level3 = post.categories[2];
          if (!window.CATEGORIES[level1].children[level2].children[level3]) {
            window.CATEGORIES[level1].children[level2].children[level3] = { posts: [] };
          }
          window.CATEGORIES[level1].children[level2].children[level3].posts.push(post);
        } else {
          window.CATEGORIES[level1].children[level2].posts.push(post);
        }
      } else {
        window.CATEGORIES[level1].posts.push(post);
      }
    }
  });
</script>
