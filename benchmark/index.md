---
layout: page
title: Benchmark Leaderboard
---

<section class="benchmark-hero">
  <div class="benchmark-hero-meta">
    <span class="cover-meta-item">Benchmark Ledger</span>
    <span class="cover-meta-item">CTR/CVR · LLM4Rec</span>
  </div>

  <div class="benchmark-hero-grid">
    <div>
      <p class="cover-kicker">Experimental Index</p>
      <h1 class="benchmark-hero-title">推荐算法实验台账</h1>
      <p class="benchmark-hero-copy">把论文中的关键实验结果整理成一份可浏览的研究台账，按数据集、指标和时间线建立统一索引，并连接到真实论文与本站分析页面。</p>
    </div>

    <aside class="rail-panel benchmark-note-card">
      <span class="benchmark-note-label">Editorial Note</span>
      <p class="benchmark-note">这一页不只是排行榜。它更像研究参考册：一边保留模型表现，一边给出时间线与热门论文索引，方便快速回到原文和分析稿。</p>
    </aside>
  </div>
</section>

<div class="benchmark-layout">
  <main class="benchmark-main">
    <div class="domain-tabs">
      <button class="domain-tab active" data-domain="ctr-cvr">
        CTR/CVR Modeling
      </button>
      <button class="domain-tab" data-domain="llm4rec">
        LLM4Rec
      </button>
    </div>

    <div id="ctr-cvr-section" class="domain-section active">
      <div class="section-header">
        <h2 class="section-title">CTR/CVR Modeling Leaderboard</h2>
        <span class="dataset-badge">Click-Through Rate Prediction</span>
      </div>

      <div class="table-container">
        <table class="benchmark-table" id="ctr-table">
          <thead>
            <tr>
              <th class="rank-header">Rank</th>
              <th>Algorithm</th>
              <th class="metric-header">AUC</th>
              <th>Improvement</th>
              <th>Paper</th>
            </tr>
          </thead>
          <tbody id="ctr-tbody"></tbody>
        </table>
      </div>

      <div class="section-header">
        <h3 class="section-title">Taobao Dataset</h3>
        <span class="dataset-badge">Taobao Ad CTR</span>
      </div>

      <div class="table-container">
        <table class="benchmark-table" id="taobao-table">
          <thead>
            <tr>
              <th class="rank-header">Rank</th>
              <th>Algorithm</th>
              <th class="metric-header">AUC</th>
              <th>Improvement</th>
              <th>Paper</th>
            </tr>
          </thead>
          <tbody id="taobao-tbody"></tbody>
        </table>
      </div>
    </div>

    <div id="llm4rec-section" class="domain-section" style="display:none;">
      <div class="section-header">
        <h2 class="section-title">LLM4Rec Leaderboard</h2>
        <span class="dataset-badge">Large Language Models for Recommendation</span>
      </div>

      <div class="section-header">
        <h3 class="section-title">MovieLens Dataset</h3>
        <span class="dataset-badge">Movie Recommendation</span>
      </div>

      <div class="table-container">
        <table class="benchmark-table" id="movielens-table">
          <thead>
            <tr>
              <th class="rank-header">Rank</th>
              <th>Algorithm</th>
              <th class="metric-header">HR@10</th>
              <th class="metric-header">NDCG@10</th>
              <th>Paper</th>
            </tr>
          </thead>
          <tbody id="movielens-tbody"></tbody>
        </table>
      </div>

      <div class="section-header">
        <h3 class="section-title">Amazon Dataset</h3>
        <span class="dataset-badge">Product Recommendation</span>
      </div>

      <div class="table-container">
        <table class="benchmark-table" id="amazon-llm-table">
          <thead>
            <tr>
              <th class="rank-header">Rank</th>
              <th>Algorithm</th>
              <th class="metric-header">HR@10</th>
              <th class="metric-header">NDCG@10</th>
              <th>Paper</th>
            </tr>
          </thead>
          <tbody id="amazon-llm-tbody"></tbody>
        </table>
      </div>
    </div>
  </main>

  <aside class="right-panel">
    <div class="right-panel-section">
      <h3 class="right-panel-title">时间线</h3>
      <div id="panel-timeline"></div>
    </div>
    <div class="right-panel-section">
      <h3 class="right-panel-title">热门论文</h3>
      <div id="panel-popular"></div>
    </div>
  </aside>
</div>

<script>
const DATA = {
{% for domain in site.data.benchmarks %}
  "{{ domain[0] }}": {
    {% for item in domain[1] %}
    "{{ item[0] }}": {
      dataset: "{{ item[1].dataset }}",
      metrics: {{ item[1].metrics | jsonify }},
      entries: [
        {% for entry in item[1].entries %}
        {
          algorithm: "{{ entry.algorithm }}",
          sources: [
            {% for source in entry.sources %}
            {
              arxiv_id: "{{ source.arxiv_id }}",
              paper_title: "{{ source.paper_title }}",
              source: "{{ source.source }}",
              post_url: "{{ source.post_url }}",
              results: {{ source.results | jsonify }}
            }{% if forloop.last != true %},{% endif %}
            {% endfor %}
          ]
        },
        {% endfor %}
      ]
    },
    {% endfor %}
  },
{% endfor %}
};

const POSTS = [
{% for post in site.posts %}
  {
    title: "{{ post.title }}",
    url: "{{ post.url | relative_url }}",
    date: "{{ post.date | date: "%Y-%m-%d" }}",
    arxiv_id: "{{ post["arxiv_id"] }}",
    has_analysis: {% if post.analysis_generated or post.content contains '一句话增量' or post.content contains '论文分析报告' %}true{% else %}false{% endif %},
    categories: [{% for cat in post["categories"] %}"{{ cat }}"{% if forloop.last != true %},{% endif %}{% endfor %}]
  }{% if forloop.last != true %},{% endif %}
{% endfor %}
];

function normalizeArxivId(arxivId) {
  return String(arxivId || '').replace(/v\d+$/i, '');
}

const POSTS_BY_ARXIV = POSTS.reduce((acc, post) => {
  const arxivId = normalizeArxivId(post.arxiv_id);
  if (!arxivId) return acc;

  if (!acc[arxivId] || (!acc[arxivId].has_analysis && post.has_analysis)) {
    acc[arxivId] = post;
  }
  return acc;
}, {});

function normalizeTitle(title) {
  return String(title || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
}

function normalizeAlgorithmName(name) {
  return normalizeTitle(name).replace(/\s+/g, '');
}

const POSTS_BY_TITLE = POSTS.reduce((acc, post) => {
  const titleKey = normalizeTitle(post.title);
  if (!titleKey) return acc;

  if (!acc[titleKey] || (!acc[titleKey].has_analysis && post.has_analysis)) {
    acc[titleKey] = post;
  }
  return acc;
}, {});

const POSTS_BY_ALGORITHM = POSTS.reduce((acc, post) => {
  const prefix = String(post.title || '').split(':')[0] || post.title;
  const algorithmKey = normalizeAlgorithmName(prefix);
  if (!algorithmKey) return acc;

  if (!acc[algorithmKey] || (!acc[algorithmKey].has_analysis && post.has_analysis)) {
    acc[algorithmKey] = post;
  }
  return acc;
}, {});

function resolvePost(source, algorithm) {
  const arxivId = normalizeArxivId(source.arxiv_id);
  if (arxivId && POSTS_BY_ARXIV[arxivId]) {
    return POSTS_BY_ARXIV[arxivId];
  }

  const titleKey = normalizeTitle(source.paper_title);
  if (titleKey && POSTS_BY_TITLE[titleKey]) {
    return POSTS_BY_TITLE[titleKey];
  }

  const algorithmKey = normalizeAlgorithmName(algorithm);
  if (algorithmKey && POSTS_BY_ALGORITHM[algorithmKey]) {
    return POSTS_BY_ALGORITHM[algorithmKey];
  }

  return null;
}

function resolveAnalysisUrl(source, algorithm) {
  return resolvePost(source, algorithm)?.url || null;
}

function renderAlgorithmName(name, analysisUrl) {
  if (!analysisUrl) {
    return `<span class="algo-name disabled">${name}</span>`;
  }
  return `<a href="${analysisUrl}" class="algo-name">${name}</a>`;
}

function renderPanelTimeline() {
  const timeline = {};
  POSTS.forEach(post => {
    if (!post.date) return;
    const [year, month] = post.date.split('-');
    const key = `${year}-${month}`;
    if (!timeline[key]) timeline[key] = [];
    timeline[key].push(post);
  });

  const sortedMonths = Object.keys(timeline).sort((a, b) => b.localeCompare(a));

  let html = '';
  sortedMonths.forEach((month, idx) => {
    const [year, m] = month.split('-');
    const monthName = `${year}年${parseInt(m)}月`;
    const posts = timeline[month];
    const isExpanded = idx === 0;

    html += `<div class="panel-timeline-month">`;
    html += `<div class="panel-timeline-header${isExpanded ? ' expanded' : ''}" data-month="${month}">`;
    html += `<div class="panel-timeline-title">`;
    html += `<span>${monthName}</span>`;
    html += `<span class="panel-timeline-count">${posts.length}</span>`;
    html += `</div>`;
    html += `<span class="panel-timeline-arrow">▼</span>`;
    html += `</div>`;
    html += `<div class="panel-timeline-content${isExpanded ? '' : ' collapsed'}">`;

    posts.forEach(post => {
      html += `<div class="panel-timeline-item">`;
      html += `<a href="${post.url}" title="${post.title}">${post.title}</a>`;
      html += `</div>`;
    });

    html += `</div>`;
    if (!isExpanded) {
      html += `<button class="panel-timeline-show-more" data-month="${month}">展开全部 ${posts.length} 篇</button>`;
    }
    html += `</div>`;
  });

  const container = document.getElementById('panel-timeline');
  if (container) container.innerHTML = html;

  container.querySelectorAll('.panel-timeline-header').forEach(header => {
    header.addEventListener('click', () => {
      const isExpanded = header.classList.toggle('expanded');
      const month = header.dataset.month;
      const showMore = container.querySelector(`.panel-timeline-show-more[data-month="${month}"]`);

      let contentDiv = header.nextElementSibling;
      while (contentDiv && !contentDiv.classList.contains('panel-timeline-content')) {
        contentDiv = contentDiv.nextElementSibling;
      }
      if (contentDiv) {
        contentDiv.classList.toggle('collapsed', !isExpanded);
      }
      if (showMore) {
        showMore.style.display = isExpanded ? 'none' : 'inline-flex';
      }
    });
  });

  container.querySelectorAll('.panel-timeline-show-more').forEach(btn => {
    btn.addEventListener('click', () => {
      const month = btn.dataset.month;
      const header = container.querySelector(`.panel-timeline-header[data-month="${month}"]`);
      if (header) {
        header.classList.add('expanded');
        const content = header.nextElementSibling;
        if (content && content.classList.contains('panel-timeline-content')) {
          content.classList.remove('collapsed');
        }
        btn.style.display = 'none';
      }
    });
  });
}

function renderPanelPopular() {
  const sorted = [...POSTS].sort((a, b) => {
    if (!a.date) return 1;
    if (!b.date) return -1;
    return b.date.localeCompare(a.date);
  });

  let html = '';
  sorted.slice(0, 10).forEach((post, index) => {
    const rank = index + 1;
    const rankClass = rank <= 3 ? `top-${rank}` : '';

    html += `<div class="panel-popular-item">`;
    html += `<span class="panel-popular-rank ${rankClass}">${rank}</span>`;
    html += `<div class="panel-popular-content">`;
    html += `<a href="${post.url}" class="panel-popular-title" title="${post.title}">${post.title}</a>`;
    if (post.date) {
      html += `<div class="panel-popular-meta">${post.date}</div>`;
    }
    html += `</div>`;
    html += `</div>`;
  });

  const container = document.getElementById('panel-popular');
  if (container) container.innerHTML = html;
}

function flattenEntriesWithSources(entries) {
  const result = [];
  for (const entry of entries) {
    for (let i = 0; i < entry.sources.length; i++) {
      result.push({
        algorithm: entry.algorithm,
        source: entry.sources[i],
        isFirstSource: i === 0
      });
    }
  }
  return result;
}

function renderRow(flatEntry, rank, metric, baseline, showRank) {
  const source = flatEntry.source;
  const analysisUrl = resolveAnalysisUrl(source, flatEntry.algorithm);
  const value = source.results[metric];
  if (value === undefined) return '';

  const improvement = baseline ? (((value - baseline) / baseline * 100)).toFixed(2) + '%' : '';
  const isBest = rank === 1;

  let rankHtml = '';
  if (showRank) {
    if (rank === 1) rankHtml = '<span class="rank-badge gold">1</span>';
    else if (rank === 2) rankHtml = '<span class="rank-badge silver">2</span>';
    else if (rank === 3) rankHtml = '<span class="rank-badge bronze">3</span>';
    else rankHtml = `<span class="rank-num">${rank}</span>`;
  }

  return `
    <tr>
      <td class="rank-cell">${rankHtml}</td>
      <td class="algo-cell">
        ${renderAlgorithmName(flatEntry.algorithm, analysisUrl)}
        <div class="algo-meta">${source.arxiv_id || ''}</div>
      </td>
      <td class="metric-cell${isBest ? ' best' : ''}">${value.toFixed(4)}</td>
      <td class="improvement-cell">${improvement}</td>
      <td class="paper-cell">
        <span class="paper-title" title="${source.paper_title}">${source.paper_title}</span>
        <div class="paper-links">
          <a href="${source.source}" target="_blank" class="paper-link">Paper</a>
          ${analysisUrl ? `<a href="${analysisUrl}" class="paper-link">Analysis</a>` : `<span class="paper-link disabled">Analysis</span>`}
        </div>
      </td>
    </tr>
  `;
}

function renderDualRow(flatEntry, rank, showRank) {
  const source = flatEntry.source;
  const analysisUrl = resolveAnalysisUrl(source, flatEntry.algorithm);
  const hr10 = source.results['HR@10'];
  const ndcg10 = source.results['NDCG@10'];
  if (hr10 === undefined && ndcg10 === undefined) return '';

  const isBest = rank === 1;

  let rankHtml = '';
  if (showRank) {
    if (rank === 1) rankHtml = '<span class="rank-badge gold">1</span>';
    else if (rank === 2) rankHtml = '<span class="rank-badge silver">2</span>';
    else if (rank === 3) rankHtml = '<span class="rank-badge bronze">3</span>';
    else rankHtml = `<span class="rank-num">${rank}</span>`;
  }

  return `
    <tr>
      <td class="rank-cell">${rankHtml}</td>
      <td class="algo-cell">
        ${renderAlgorithmName(flatEntry.algorithm, analysisUrl)}
        <div class="algo-meta">${source.arxiv_id || ''}</div>
      </td>
      <td class="metric-cell${isBest ? ' best' : ''}">${hr10 !== undefined ? hr10.toFixed(4) : '-'}</td>
      <td class="metric-cell${isBest ? ' best' : ''}">${ndcg10 !== undefined ? ndcg10.toFixed(4) : '-'}</td>
      <td class="paper-cell">
        <span class="paper-title" title="${source.paper_title}">${source.paper_title}</span>
        <div class="paper-links">
          <a href="${source.source}" target="_blank" class="paper-link">Paper</a>
          ${analysisUrl ? `<a href="${analysisUrl}" class="paper-link">Analysis</a>` : `<span class="paper-link disabled">Analysis</span>`}
        </div>
      </td>
    </tr>
  `;
}

function renderCTRSection() {
  const ctrData = DATA['ctr-cvr'];
  if (!ctrData) return;

  const amazonEntries = ctrData['amazon']?.entries || [];
  const flattenedAmazon = flattenEntriesWithSources(amazonEntries);
  const sortedAmazon = [...flattenedAmazon].sort((a, b) => {
    const aVal = a.source.results['AUC'] || 0;
    const bVal = b.source.results['AUC'] || 0;
    return bVal - aVal;
  });
  const baselineAmazon = sortedAmazon[sortedAmazon.length - 1]?.source.results['AUC'] || 0;

  let amazonRank = 0;
  let lastAlgorithm = null;
  document.getElementById('ctr-tbody').innerHTML = sortedAmazon
    .map(e => {
      if (e.algorithm !== lastAlgorithm) {
        amazonRank++;
        lastAlgorithm = e.algorithm;
      }
      return renderRow(e, amazonRank, 'AUC', baselineAmazon, e.isFirstSource);
    })
    .join('');

  const taobaoEntries = ctrData['taobao']?.entries || [];
  const flattenedTaobao = flattenEntriesWithSources(taobaoEntries);
  const sortedTaobao = [...flattenedTaobao].sort((a, b) => {
    const aVal = a.source.results['AUC'] || 0;
    const bVal = b.source.results['AUC'] || 0;
    return bVal - aVal;
  });
  const baselineTaobao = sortedTaobao[sortedTaobao.length - 1]?.source.results['AUC'] || 0;

  let taobaoRank = 0;
  lastAlgorithm = null;
  document.getElementById('taobao-tbody').innerHTML = sortedTaobao
    .map(e => {
      if (e.algorithm !== lastAlgorithm) {
        taobaoRank++;
        lastAlgorithm = e.algorithm;
      }
      return renderRow(e, taobaoRank, 'AUC', baselineTaobao, e.isFirstSource);
    })
    .join('');
}

function renderLLMSection() {
  const llmData = DATA['llm4rec'];
  if (!llmData) return;

  const mlEntries = llmData['movielens']?.entries || [];
  const flattenedML = flattenEntriesWithSources(mlEntries);
  const sortedML = [...flattenedML].sort((a, b) => {
    const aVal = a.source.results['HR@10'] || 0;
    const bVal = b.source.results['HR@10'] || 0;
    return bVal - aVal;
  });

  let mlRank = 0;
  let lastAlgorithm = null;
  document.getElementById('movielens-tbody').innerHTML = sortedML
    .map(e => {
      if (e.algorithm !== lastAlgorithm) {
        mlRank++;
        lastAlgorithm = e.algorithm;
      }
      return renderDualRow(e, mlRank, e.isFirstSource);
    })
    .join('');

  const amazonEntries = llmData['amazon']?.entries || [];
  const flattenedAmazon = flattenEntriesWithSources(amazonEntries);
  const sortedAmazon = [...flattenedAmazon].sort((a, b) => {
    const aVal = a.source.results['HR@10'] || 0;
    const bVal = b.source.results['HR@10'] || 0;
    return bVal - aVal;
  });

  let amazonRank = 0;
  lastAlgorithm = null;
  document.getElementById('amazon-llm-tbody').innerHTML = sortedAmazon
    .map(e => {
      if (e.algorithm !== lastAlgorithm) {
        amazonRank++;
        lastAlgorithm = e.algorithm;
      }
      return renderDualRow(e, amazonRank, e.isFirstSource);
    })
    .join('');
}

document.querySelectorAll('.domain-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.domain-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.domain-section').forEach(s => s.style.display = 'none');

    tab.classList.add('active');
    const section = document.getElementById(tab.dataset.domain + '-section');
    if (section) section.style.display = 'block';

    if (tab.dataset.domain === 'ctr-cvr') renderCTRSection();
    else renderLLMSection();
  });
});

renderCTRSection();
renderLLMSection();
renderPanelTimeline();
renderPanelPopular();

if (window.location.hash === '#llm4rec') {
  document.querySelector('[data-domain="llm4rec"]').click();
}
</script>
