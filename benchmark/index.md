---
layout: page
title: Benchmark Leaderboard
---

# Benchmark Leaderboard

推荐算法领域论文性能排行榜。追踪学术界最新算法在各大基准数据集上的表现。

## Benchmark 数据集

<div class="benchmark-tabs">
  <button class="tab-btn active" data-tab="ctr-cvr">CTR/CVR 建模</button>
  <button class="tab-btn" data-tab="llm4rec">LLM4Rec</button>
</div>

<!-- CTR/CVR Section -->
<div id="ctr-cvr" class="tab-content active">
  <div class="benchmark-header">
    <h2>CTR/CVR 建模 Leaderboard</h2>
    <p>电商场景点击率/转化率预估任务主流算法性能对比</p>
  </div>

  <div class="benchmark-filters">
    <div class="filter-group">
      <label>数据集:</label>
      <select id="ctr-dataset-filter">
        <option value="all">全部</option>
        <option value="amazon">Amazon Reviews</option>
        <option value="taobao">Taobao</option>
      </select>
    </div>
    <div class="filter-group">
      <label>指标:</label>
      <select id="ctr-metric-filter">
        <option value="AUC">AUC</option>
      </select>
    </div>
  </div>

  <div id="ctr-table-container">
    <!-- Tables will be rendered here by JS -->
  </div>
</div>

<!-- LLM4Rec Section -->
<div id="llm4rec" class="tab-content">
  <div class="benchmark-header">
    <h2>LLM4Rec Leaderboard</h2>
    <p>大语言模型在推荐系统中应用的性能对比</p>
  </div>

  <div class="benchmark-filters">
    <div class="filter-group">
      <label>数据集:</label>
      <select id="llm-dataset-filter">
        <option value="all">全部</option>
        <option value="movielens">MovieLens</option>
        <option value="amazon">Amazon Reviews</option>
      </select>
    </div>
    <div class="filter-group">
      <label>指标:</label>
      <select id="llm-metric-filter">
        <option value="HR@10">HR@10</option>
        <option value="NDCG@10">NDCG@10</option>
      </select>
    </div>
  </div>

  <div id="llm-table-container">
    <!-- Tables will be rendered here by JS -->
  </div>
</div>

## 数据来源

所有数据均来自论文中报告的实验结果。如有遗漏或错误，欢迎提交 PR。

<script>
// Benchmark data - loaded from Jekyll data files
const BENCHMARK_DATA = {
{% for domain in site.data.benchmarks %}
  "{{ domain[0] }}": {
    {% for item in domain[1] %}
    "{{ item[0] }}": {
      dataset: "{{ item[1].dataset }}",
      domain: "{{ item[1].domain }}",
      description: "{{ item[1].description }}",
      metrics: {{ item[1].metrics | jsonify }},
      entries: [
        {% for entry in item[1].entries %}
        {
          algorithm: "{{ entry.algorithm }}",
          paper_title: "{{ entry.paper_title }}",
          arxiv_id: "{{ entry.arxiv_id }}",
          source: "{{ entry.source }}",
          post_url: "{{ entry.post_url }}",
          results: [
            {% for r in entry.results %}
            { metric: "{{ r.metric }}", value: {{ r.value }} },
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

// Render table for a specific dataset
function renderTable(domain, datasetKey, metric) {
  const data = BENCHMARK_DATA[domain]?.[datasetKey];
  if (!data) return '<p class="no-data">暂无数据</p>';

  const entries = data.entries
    .map(e => {
      const metricResult = e.results.find(r => r.metric === metric);
      return { ...e, metricValue: metricResult?.value || null };
    })
    .filter(e => e.metricValue !== null)
    .sort((a, b) => b.metricValue - a.metricValue);

  if (entries.length === 0) return '<p class="no-data">该数据集暂无此指标数据</p>';

  let html = `
  <h3>{{ item[1].dataset }} - ${metric}</h3>
  <table class="leaderboard-table">
    <thead>
      <tr>
        <th class="rank-col">#</th>
        <th class="algo-col">Algorithm</th>
        <th class="metric-col">${metric}</th>
        <th class="paper-col">Paper</th>
        <th class="source-col">Source</th>
      </tr>
    </thead>
    <tbody>
  `;

  entries.forEach((entry, idx) => {
    const rank = idx + 1;
    let rankBadge = '';
    if (rank === 1) rankBadge = '<span class="rank-badge gold">1</span>';
    else if (rank === 2) rankBadge = '<span class="rank-badge silver">2</span>';
    else if (rank === 3) rankBadge = '<span class="rank-badge bronze">3</span>';
    else rankBadge = `<span class="rank-number">${rank}</span>`;

    html += `
      <tr>
        <td class="rank-cell">${rankBadge}</td>
        <td class="algo-cell">
          <a href="${entry.post_url}" class="algorithm-name">${entry.algorithm}</a>
        </td>
        <td class="metric-cell"><span class="metric-value">${entry.metricValue.toFixed(4)}</span></td>
        <td class="paper-cell">
          <span class="paper-title" title="${entry.paper_title}">${entry.paper_title.substring(0, 40)}...</span>
        </td>
        <td class="source-cell">
          <a href="${entry.source}" target="_blank" class="source-link">Paper</a>
        </td>
      </tr>
    `;
  });

  html += '</tbody></table>';
  return html;
}

// Initialize tabs
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
    window.location.hash = btn.dataset.tab;
  });
});

// Handle URL hash on load
window.addEventListener('load', () => {
  const hash = window.location.hash.replace('#', '');
  if (hash) {
    const btn = document.querySelector(`.tab-btn[data-tab="${hash}"]`);
    if (btn) btn.click();
  }
});

// Initial render for CTR
document.getElementById('ctr-table-container').innerHTML =
  renderTable('ctr-cvr', 'amazon', 'AUC') +
  '<br>' +
  renderTable('ctr-cvr', 'taobao', 'AUC');

// Initial render for LLM
document.getElementById('llm-table-container').innerHTML =
  renderTable('llm4rec', 'movielens', 'HR@10') +
  '<br>' +
  renderTable('llm4rec', 'amazon', 'HR@10');

// Handle filter changes
document.getElementById('ctr-dataset-filter').addEventListener('change', (e) => {
  const dataset = e.target.value;
  const metric = document.getElementById('ctr-metric-filter').value;
  const container = document.getElementById('ctr-table-container');

  if (dataset === 'all') {
    container.innerHTML =
      renderTable('ctr-cvr', 'amazon', metric) +
      '<br>' +
      renderTable('ctr-cvr', 'taobao', metric);
  } else {
    container.innerHTML = renderTable('ctr-cvr', dataset, metric);
  }
});

document.getElementById('llm-dataset-filter').addEventListener('change', (e) => {
  const dataset = e.target.value;
  const metric = document.getElementById('llm-metric-filter').value;
  const container = document.getElementById('llm-table-container');

  if (dataset === 'all') {
    container.innerHTML =
      renderTable('llm4rec', 'movielens', metric) +
      '<br>' +
      renderTable('llm4rec', 'amazon', metric);
  } else {
    container.innerHTML = renderTable('llm4rec', dataset, metric);
  }
});

document.getElementById('llm-metric-filter').addEventListener('change', (e) => {
  const dataset = document.getElementById('llm-dataset-filter').value;
  const metric = e.target.value;
  const container = document.getElementById('llm-table-container');

  if (dataset === 'all') {
    container.innerHTML =
      renderTable('llm4rec', 'movielens', metric) +
      '<br>' +
      renderTable('llm4rec', 'amazon', metric);
  } else {
    container.innerHTML = renderTable('llm4rec', dataset, metric);
  }
});
</script>
