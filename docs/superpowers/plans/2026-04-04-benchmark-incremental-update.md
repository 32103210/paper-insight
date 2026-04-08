# Benchmark 增量更新实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 benchmark 数据的自动化增量更新，同一模型的多来源结果全部保留

**Architecture:** benchmark_extractor.py 集成到 GitHub Actions，每次新论文分析后自动运行，YAML 数据按 arXiv ID 去重合并

**Tech Stack:** Python (yaml, arxiv), GitHub Actions, Jekyll

---

## 文件结构

```
paper-insight/
├── _data/benchmarks/           # YAML 数据文件
│   ├── ctr-cvr/
│   │   ├── amazon.yaml
│   │   └── taobao.yaml
│   └── llm4rec/
│       ├── amazon.yaml
│       └── movielens.yaml
├── scripts/
│   └── benchmark_extractor.py  # 修改：增量更新逻辑
├── benchmark/
│   └── index.md               # 修改：展示多来源
└── .github/workflows/
    ├── benchmark-update.yml    # 新增：触发 extractor
    └── daily-papers.yml       # 修改：触发 benchmark-update
```

---

## Task 1: 重写 benchmark_extractor.py 增量更新逻辑

**Files:**
- Modify: `scripts/benchmark_extractor.py`

- [ ] **Step 1: 读取设计文档确认数据模型**

确认新格式：`entries[].sources[]` 数组结构

- [ ] **Step 2: 编写 load_existing_data() 函数**

```python
def load_existing_data() -> Dict[str, Dict[str, dict]]:
    """加载现有 _data/benchmarks/*.yaml 数据"""
    benchmarks = defaultdict(lambda: defaultdict(lambda: {
        'dataset': '',
        'domain': '',
        'description': '',
        'metrics': [],
        'entries': []  # 每个 entry: {algorithm: str, sources: [source1, source2]}
    }))
    # 遍历 _data/benchmarks/**/*.yaml
    # 返回嵌套字典
```

- [ ] **Step 3: 编写 merge_entry() 函数**

```python
def merge_entry(existing_entries: list, new_entry: dict) -> list:
    """将新 entry 合并到现有 entries，按 arXiv ID 去重"""
    # 遍历 existing_entries.sources
    # 如果 new_entry 的 arXiv ID 不存在，append 到 sources
    # 如果已存在，保留两个（不覆盖）
```

- [ ] **Step 4: 修改 extract_benchmark_from_post() 返回新格式**

```python
def extract_benchmark_from_post(filepath: Path) -> dict:
    """返回格式变更：{algorithm, sources: [{arxiv_id, paper_title, source, post_url, results, paper_date}]}"""
```

- [ ] **Step 5: 修改 main() 函数实现增量更新**

```python
def main():
    # 1. load_existing_data() 加载现有数据
    # 2. 遍历 _posts/*.md 提取新数据
    # 3. 对每个新数据调用 merge_entry()
    # 4. 将合并结果写入 _data/benchmarks/*.yaml
```

- [ ] **Step 6: 测试本地运行**

Run: `cd paper-insight && python scripts/benchmark_extractor.py`
Expected: 更新 YAML 文件，不丢失现有数据

- [ ] **Step 7: 提交**

```bash
git add scripts/benchmark_extractor.py
git commit -m "feat: rewrite benchmark_extractor for incremental updates"
```

---

## Task 2: 创建 benchmark-update.yml workflow

**Files:**
- Create: `.github/workflows/benchmark-update.yml`

- [ ] **Step 1: 创建 workflow 文件**

```yaml
name: Benchmark Update

on:
  workflow_dispatch:  # 手动触发
  workflow_run:
    workflows: ["Daily Paper Insight"]
    types: [completed]

jobs:
  update-benchmark:
    runs-on: ubuntu-latest
    if: {% raw %}${{ github.event.workflow_run.conclusion == 'success' }}{% endraw %}

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install deps
        run: pip install pyyaml

      - name: Run extractor
        run: python scripts/benchmark_extractor.py

      - name: Commit changes
        run: |
          git config user.email "action@github.com"
          git config user.name "GitHub Action"
          git add _data/benchmarks/
          git diff --staged --quiet || git commit -m "chore: update benchmark data"
          git push
```

- [ ] **Step 2: 提交**

```bash
git add .github/workflows/benchmark-update.yml
git commit -m "feat: add benchmark-update workflow"
```

---

## Task 3: 修改 daily-papers.yml 触发 benchmark-update

**Files:**
- Modify: `.github/workflows/daily-papers.yml`

- [ ] **Step 1: 在 jobs 末尾添加 trigger step**

```yaml
      - name: Trigger Benchmark Update
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.actions.createWorkflowDispatch({
              owner: context.repo.owner,
              repo: context.repo.repo,
              workflow_id: 'benchmark-update.yml',
              ref: 'refs/heads/main'
            })
```

- [ ] **Step 2: 提交**

```bash
git add .github/workflows/daily-papers.yml
git commit -m "ci: trigger benchmark-update after paper analysis"
```

---

## Task 4: 迁移现有 YAML 数据到新格式

**Files:**
- Modify: `_data/benchmarks/ctr-cvr/amazon.yaml`
- Modify: `_data/benchmarks/ctr-cvr/taobao.yaml`
- Modify: `_data/benchmarks/llm4rec/amazon.yaml`
- Modify: `_data/benchmarks/llm4rec/movielens.yaml`

- [ ] **Step 1: 编写迁移脚本或手动迁移**

旧格式：
```yaml
entries:
  - algorithm: DeepFM
    paper_title: "DeepFM..."
    arxiv_id: "1703.04247"
    source: "https://..."
    results:
      AUC: 0.7965
```

新格式：
```yaml
entries:
  - algorithm: DeepFM
    sources:
      - arxiv_id: "1703.04247"
        paper_title: "DeepFM..."
        source: "https://..."
        results:
          AUC: 0.7965
        paper_date: ""  # 可留空或从 arxiv 获取
```

- [ ] **Step 2: 逐个文件迁移**

迁移 amazon.yaml, taobao.yaml, movielens.yaml, amazon.yaml 四个文件

- [ ] **Step 3: 验证 YAML 语法**

Run: `ruby -e "require 'yaml'; YAML.load_file('_data/benchmarks/ctr-cvr/amazon.yaml')"`

- [ ] **Step 4: 提交**

```bash
git add _data/benchmarks/
git commit -m "refactor: migrate benchmark data to sources format"
```

---

## Task 5: 更新前端 benchmark/index.md 展示多来源

**Files:**
- Modify: `benchmark/index.md`

- [ ] **Step 1: 修改 JS 数据加载逻辑**

```javascript
// 旧逻辑：entry.results = {AUC: 0.7965}
// 新逻辑：entry.sources = [{arxiv_id, paper_title, results: {AUC: 0.7965}}, ...]
```

- [ ] **Step 2: 修改 renderDualRow() 展示多来源**

```javascript
function renderMultiSourceRow(entry, rank) {
  // 每个 source 渲染一行
  // 显示：rank | algorithm | metric | paper | source
  // 同一算法的多个 source 并排或下方展开
}
```

- [ ] **Step 3: 更新 CSS 样式**

- [ ] **Step 4: 本地测试**

Run: `bundle exec jekyll serve`
Expected: 同一算法的多来源数据正确展示

- [ ] **Step 5: 提交**

```bash
git add benchmark/index.md assets/css/style.css
git commit -m "feat: display multiple sources per algorithm in benchmark"
```

---

## Task 6: 端到端测试

- [ ] **Step 1: 本地完整测试**

```bash
cd paper-insight
python scripts/benchmark_extractor.py
ruby -e "require 'yaml'; puts YAML.load_file('_data/benchmarks/ctr-cvr/amazon.yaml')['entries'].size"
bundle exec jekyll serve
```

- [ ] **Step 2: 推送到 GitHub**

```bash
git push
```

- [ ] **Step 3: 检查 GitHub Actions**

1. 手动触发 Daily Paper Insight workflow
2. 确认 benchmark-update 被触发
3. 确认 _data/benchmarks/ 更新成功

- [ ] **Step 4: 验证页面**

访问 https://32103210.github.io/paper-insight/benchmark/
确认数据正确展示

---

## 验证清单

- [ ] benchmark_extractor.py 正确处理增量更新
- [ ] 同一 arXiv ID 不会覆盖，已有数据保留
- [ ] GitHub Actions workflow 正确触发
- [ ] YAML 数据迁移到新格式
- [ ] 前端正确展示多来源
- [ ] GitHub Pages 显示正确
