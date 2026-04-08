---
layout: page
title: Paper Insight
---

<script>
window.POSTS_DATA = [
{% for post in site.posts %}
  {
    title: {{ post.title | jsonify }},
    url: {{ post.url | relative_url | jsonify }},
    date: {{ post.date | date: "%Y-%m-%d" | jsonify }},
    arxiv_id: {{ post.arxiv_id | jsonify }},
    categories: {{ post.categories | jsonify }},
    description: {{ post.description | default: post.excerpt | strip_html | strip_newlines | jsonify }}
  }{% unless forloop.last %},{% endunless %}
{% endfor %}
];
</script>

{% assign lead_post = site.posts.first %}
{% assign lead_categories = lead_post.categories | uniq %}

<section class="cover-hero">
  <div class="cover-meta">
    <span class="cover-meta-item">Editorial Review</span>
    <span class="cover-meta-item">{{ site.time | date: "%Y.%m.%d" }} 更新</span>
  </div>

  <div class="cover-grid">
    <div class="cover-copy">
      <p class="cover-kicker">Recommendation Research Review</p>
      <h1 class="cover-title">把推荐算法论文整理成一份持续更新的研究评论刊。</h1>
      <p class="cover-standfirst">Paper Insight 以刊物式目录重组 arXiv 推荐系统论文，补充中文分析、研究归档与 benchmark 索引，让最新论文不再只是摘要流。</p>
      <div class="cover-actions">
        <a href="#catalog" class="cover-action primary">进入最新分析</a>
        <a href="{{ '/benchmark/' | relative_url }}" class="cover-action">查看 Benchmark</a>
      </div>
    </div>

    {% if lead_post %}
    <article class="cover-feature">
      <span class="cover-feature-label">Lead Essay</span>
      <h2 class="cover-feature-title">
        <a href="{{ lead_post.url | relative_url }}">{{ lead_post.title }}</a>
      </h2>
      <p class="cover-feature-excerpt">{{ lead_post.description | default: lead_post.excerpt | strip_html | strip_newlines }}</p>
      <div class="cover-feature-meta">
        <span>{{ lead_post.date | date: "%Y-%m-%d" }}</span>
        {% if lead_post.arxiv_id %}
        <span>arXiv {{ lead_post.arxiv_id }}</span>
        {% endif %}
      </div>
    </article>
    {% endif %}
  </div>

  <div class="cover-support-grid">
    {% for post in site.posts offset:1 limit:2 %}
    <article class="cover-support-card">
      <span class="cover-support-label">Recent</span>
      <h3 class="cover-support-title">
        <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
      </h3>
      <p class="cover-support-excerpt">{{ post.description | default: post.excerpt | strip_html | strip_newlines }}</p>
      <span class="cover-support-date">{{ post.date | date: "%Y-%m-%d" }}</span>
    </article>
    {% endfor %}
  </div>
</section>

<div class="home-directory" id="catalog">
  <div class="home-directory-main">
    <nav class="breadcrumb" id="breadcrumb">
      <li><a href="{{ "/" | relative_url }}">首页</a></li>
      <li class="separator">/</li>
      <li class="current">全部文章</li>
    </nav>

    <section class="directory-tools">
      <div class="section-intro">
        <span class="section-kicker">Archive Index</span>
        <h2 class="section-title">研究目录</h2>
      </div>
      {% include header.html %}
    </section>

    <div id="posts-container">
      {% if lead_post %}
      <section class="editorial-lead">
        <article class="post-card post-card-lead">
          <div class="post-card-frame">
            <div class="post-card-meta">
              <span class="post-card-date">{{ lead_post.date | date: "%Y-%m-%d" }}</span>
              {% if lead_post.arxiv_id %}
              <span class="post-card-arxiv">arXiv {{ lead_post.arxiv_id }}</span>
              {% endif %}
            </div>
            <h3 class="post-card-title">
              <a href="{{ lead_post.url | relative_url }}">{{ lead_post.title }}</a>
            </h3>
            <p class="post-card-excerpt">{{ lead_post.description | default: lead_post.excerpt | strip_html | strip_newlines }}</p>
            {% if lead_categories %}
            <div class="post-card-tags">
              {% for category in lead_categories %}
              <span class="post-card-tags-item">{{ category }}</span>
              {% endfor %}
            </div>
            {% endif %}
          </div>
        </article>
      </section>
      {% endif %}

      <section class="editorial-support">
        {% for post in site.posts offset:1 limit:2 %}
        <article class="post-card post-card-support">
          <div class="post-card-frame">
            <div class="post-card-meta">
              <span class="post-card-date">{{ post.date | date: "%Y-%m-%d" }}</span>
              {% if post.arxiv_id %}
              <span class="post-card-arxiv">arXiv {{ post.arxiv_id }}</span>
              {% endif %}
            </div>
            <h3 class="post-card-title">
              <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
            </h3>
            <p class="post-card-excerpt">{{ post.description | default: post.excerpt | strip_html | strip_newlines }}</p>
            {% assign support_categories = post.categories | uniq %}
            {% if support_categories %}
            <div class="post-card-tags">
              {% for category in support_categories %}
              <span class="post-card-tags-item">{{ category }}</span>
              {% endfor %}
            </div>
            {% endif %}
          </div>
        </article>
        {% endfor %}
      </section>

      <section class="editorial-archive">
        <div class="section-intro">
          <span class="section-kicker">Research Archive</span>
          <h2 class="section-title">最新论文目录</h2>
        </div>

        <div class="post-archive-list">
          {% for post in site.posts offset:3 %}
          <article class="post-card post-card-archive">
            <div class="post-card-frame">
              <div class="post-card-meta">
                <span class="post-card-date">{{ post.date | date: "%Y-%m-%d" }}</span>
                {% if post.arxiv_id %}
                <span class="post-card-arxiv">arXiv {{ post.arxiv_id }}</span>
                {% endif %}
              </div>
              <h3 class="post-card-title">
                <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
              </h3>
              <p class="post-card-excerpt">{{ post.description | default: post.excerpt | strip_html | strip_newlines }}</p>
              {% assign archive_categories = post.categories | uniq %}
              {% if archive_categories %}
              <div class="post-card-tags">
                {% for category in archive_categories %}
                <span class="post-card-tags-item">{{ category }}</span>
                {% endfor %}
              </div>
              {% endif %}
            </div>
          </article>
          {% endfor %}
        </div>
      </section>
    </div>
  </div>

  <aside class="home-directory-rail">
    <section class="rail-panel">
      <span class="rail-kicker">Editorial Note</span>
      <h2 class="rail-title">把论文流重新整理成可读的研究入口。</h2>
      <p class="rail-copy">首页先提供刊物式封面，再回到可检索的目录；榜单和文章页也共享同一套视觉秩序，而不是分裂成几个工具页。</p>
    </section>

    <section class="rail-panel rail-panel-compact">
      <span class="rail-kicker">Current Issue</span>
      <div class="rail-stats">
        <div class="rail-stat">
          <span class="rail-stat-number">{{ site.posts.size }}</span>
          <span class="rail-stat-label">篇论文分析</span>
        </div>
        <div class="rail-stat">
          <span class="rail-stat-number">2</span>
          <span class="rail-stat-label">个 benchmark 主题</span>
        </div>
      </div>
      <a href="{{ '/benchmark/' | relative_url }}" class="rail-link">打开实验排行榜</a>
    </section>
  </aside>
</div>
