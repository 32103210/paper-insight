---
layout: page
title: Benchmark Leaderboard
---

# Benchmark Leaderboard

推荐算法领域论文性能排行榜。从学术论文中提取实验数据，按数据集和指标分类展示。

<style>
/* Benchmark Page Specific Styles */
.benchmark-page {
  max-width: 1400px;
  margin: 0 auto;
}

/* Domain Tabs */
.domain-tabs {
  display: flex;
  border-bottom: 2px solid #e5e5e5;
  margin-bottom: 32px;
}

.domain-tab {
  padding: 16px 32px;
  font-size: 15px;
  font-weight: 500;
  color: #666;
  background: none;
  border: none;
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
}

.domain-tab:hover {
  color: #333;
}

.domain-tab.active {
  color: #2563eb;
}

.domain-tab.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 3px;
  background: #2563eb;
  border-radius: 3px 3px 0 0;
}

/* Section Header */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a2e;
}

.dataset-badge {
  display: inline-block;
  padding: 4px 12px;
  background: #f3f4f6;
  color: #666;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
}

/* Table Container */
.table-container {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e5e5;
  overflow: hidden;
  margin-bottom: 40px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

/* Table */
.benchmark-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.benchmark-table thead {
  background: #f8f9fa;
}

.benchmark-table th {
  padding: 16px 20px;
  text-align: left;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #666;
  border-bottom: 1px solid #e5e5e5;
  white-space: nowrap;
}

.benchmark-table th.rank-header {
  width: 80px;
  text-align: center;
}

.benchmark-table th.metric-header {
  text-align: right;
}

/* Table Body */
.benchmark-table tbody tr {
  transition: background 0.15s;
}

.benchmark-table tbody tr:hover {
  background: #f8f9fa;
}

.benchmark-table td {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  vertical-align: middle;
}

.benchmark-table tbody tr:last-child td {
  border-bottom: none;
}

/* Rank Cell */
.rank-cell {
  text-align: center;
  width: 80px;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-weight: 700;
  font-size: 14px;
}

.rank-badge.gold {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  color: #000;
  box-shadow: 0 2px 8px rgba(255, 165, 0, 0.3);
}

.rank-badge.silver {
  background: linear-gradient(135deg, #E8E8E8 0%, #C0C0C0 100%);
  color: #333;
  box-shadow: 0 2px 8px rgba(192, 192, 192, 0.3);
}

.rank-badge.bronze {
  background: linear-gradient(135deg, #CD7F32 0%, #A0522D 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(160, 82, 45, 0.3);
}

.rank-num {
  font-weight: 600;
  color: #999;
}

/* Algorithm Cell */
.algo-cell {
  min-width: 180px;
}

.algo-name {
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.algo-name:hover {
  color: #2563eb;
}

.algo-meta {
  font-size: 12px;
  color: #999;
}

/* Metric Cell */
.metric-cell {
  text-align: right;
  font-family: 'SF Mono', 'Menlo', monospace;
  font-size: 15px;
  font-weight: 600;
  color: #2563eb;
  white-space: nowrap;
}

.metric-cell.best {
  color: #059669;
}

/* Improvement Cell */
.improvement-cell {
  text-align: right;
  font-size: 13px;
  color: #059669;
  white-space: nowrap;
}

/* Paper Cell */
.paper-cell {
  max-width: 300px;
}

.paper-title {
  display: block;
  font-size: 13px;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.paper-links {
  display: flex;
  gap: 8px;
}

.paper-link {
  font-size: 12px;
  color: #2563eb;
  text-decoration: none;
}

.paper-link:hover {
  text-decoration: underline;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.empty-state-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

/* Responsive */
@media (max-width: 768px) {
  .domain-tabs {
    overflow-x: auto;
  }

  .domain-tab {
    padding: 12px 20px;
    font-size: 14px;
  }

  .table-container {
    overflow-x: auto;
  }

  .benchmark-table {
    min-width: 800px;
  }
}
</style>

<div class="benchmark-page">

  <!-- Domain Tabs -->
  <div class="domain-tabs">
    <button class="domain-tab active" data-domain="ctr-cvr">
      CTR/CVR Modeling
    </button>
    <button class="domain-tab" data-domain="llm4rec">
      LLM4Rec
    </button>
  </div>

  <!-- CTR/CVR Section -->
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
        <tbody id="ctr-tbody">
          <!-- Populated by JS -->
        </tbody>
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
        <tbody id="taobao-tbody">
          <!-- Populated by JS -->
        </tbody>
      </table>
    </div>
  </div>

  <!-- LLM4Rec Section -->
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
        <tbody id="movielens-tbody">
          <!-- Populated by JS -->
        </tbody>
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
        <tbody id="amazon-llm-tbody">
          <!-- Populated by JS -->
        </tbody>
      </table>
    </div>
  </div>

</div>

<script>
// Benchmark Data - New format with sources array
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
              results: {
                {% for r in source.results %}
                "{{ r.metric }}": {{ r.value }}{% if forloop.last != true %},{% endif %}
                {% endfor %}
              }
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

// Flatten entries with sources for sorting and rendering
// Each source becomes a separate row, but we track algorithm groups for rank display
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

// Render CTR/CVR row (single metric AUC)
function renderRow(flatEntry, rank, metric, baseline, showRank) {
  const source = flatEntry.source;
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
  } else {
    rankHtml = '';
  }

  return `
    <tr>
      <td class="rank-cell">${rankHtml}</td>
      <td class="algo-cell">
        <a href="${source.post_url}" class="algo-name">${flatEntry.algorithm}</a>
        <div class="algo-meta">${source.arxiv_id || ''}</div>
      </td>
      <td class="metric-cell${isBest ? ' best' : ''}">${value.toFixed(4)}</td>
      <td class="improvement-cell">${improvement}</td>
      <td class="paper-cell">
        <span class="paper-title" title="${source.paper_title}">${source.paper_title}</span>
        <div class="paper-links">
          <a href="${source.source}" target="_blank" class="paper-link">Paper</a>
          <a href="${source.post_url}" class="paper-link">Analysis</a>
        </div>
      </td>
    </tr>
  `;
}

// Render dual metric row (for LLM4Rec with HR@10 and NDCG@10)
function renderDualRow(flatEntry, rank, showRank) {
  const source = flatEntry.source;
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
  } else {
    rankHtml = '';
  }

  return `
    <tr>
      <td class="rank-cell">${rankHtml}</td>
      <td class="algo-cell">
        <a href="${source.post_url}" class="algo-name">${flatEntry.algorithm}</a>
        <div class="algo-meta">${source.arxiv_id || ''}</div>
      </td>
      <td class="metric-cell${isBest ? ' best' : ''}">${hr10 !== undefined ? hr10.toFixed(4) : '-'}</td>
      <td class="metric-cell${isBest ? ' best' : ''}">${ndcg10 !== undefined ? ndcg10.toFixed(4) : '-'}</td>
      <td class="paper-cell">
        <span class="paper-title" title="${source.paper_title}">${source.paper_title}</span>
        <div class="paper-links">
          <a href="${source.source}" target="_blank" class="paper-link">Paper</a>
          <a href="${source.post_url}" class="paper-link">Analysis</a>
        </div>
      </td>
    </tr>
  `;
}

// Sort and render CTR table
function renderCTRSection() {
  const ctrData = DATA['ctr-cvr'];
  if (!ctrData) return;

  // Amazon table
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

  // Taobao table
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

// Sort and render LLM4Rec section
function renderLLMSection() {
  const llmData = DATA['llm4rec'];
  if (!llmData) return;

  // MovieLens table
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

  // Amazon table
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

// Tab switching
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

// Initial render
renderCTRSection();
renderLLMSection();

// Handle hash
if (window.location.hash === '#llm4rec') {
  document.querySelector('[data-domain="llm4rec"]').click();
}
</script>
