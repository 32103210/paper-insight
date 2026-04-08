# Industrial LLM4Rec Crawler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让论文抓取只保留工业界推荐论文，并显著加强 LLM for recommendation 相关文章的召回。

**Architecture:** 在 `scripts/crawler.py` 中扩展 arXiv query、提取邮箱域名工业界信号，并在抓取阶段硬过滤纯学术论文。通过 `tests/test_crawler.py` 先写失败测试，再最小化实现，最后推送到 `main` 触发现有 GitHub Pages 部署流程。

**Tech Stack:** Python 3.11, `arxiv`, `unittest`, GitHub Actions

---

### Task 1: Create Rollback Baseline

**Files:**
- Modify: `docs/superpowers/plans/2026-04-08-industrial-llm4rec-crawler.md`

- [ ] **Step 1: Inspect current branch and head**

```bash
git rev-parse --short HEAD
git rev-parse --abbrev-ref HEAD
git status --short
```

Expected: `main` on a clean worktree.

- [ ] **Step 2: Create annotated rollback tag**

```bash
git tag -a pre-industrial-llm4rec-20260408 -m "Rollback point before industrial LLM4Rec crawler changes"
git show --stat --oneline pre-industrial-llm4rec-20260408
```

Expected: tag points at the pre-implementation baseline commit.

- [ ] **Step 3: Push rollback tag to origin**

```bash
git push origin pre-industrial-llm4rec-20260408
```

Expected: remote accepts the tag so rollback is available after deployment.

### Task 2: Add Failing Tests for Search Expansion and Industrial Filtering

**Files:**
- Modify: `tests/test_crawler.py`
- Test: `tests/test_crawler.py`

- [ ] **Step 1: Write the failing test for query expansion**

```python
    @patch.object(crawler.time, "sleep")
    @patch.object(crawler, "search_with_retry", return_value=[])
    def test_search_papers_builds_query_with_llm4rec_terms(self, mock_search_with_retry, _mock_sleep):
        crawler.search_papers(days_back=1, max_results=2)

        search = mock_search_with_retry.call_args.args[1]
        self.assertIn('all:"llm for recommendation"', search.query)
        self.assertIn('all:"large language model recommendation"', search.query)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_crawler.CrawlerTests.test_search_papers_builds_query_with_llm4rec_terms -v`
Expected: FAIL because the current query still only includes the generic recommendation terms.

- [ ] **Step 3: Write the failing test for pure academic filtering**

```python
    @patch.object(crawler.time, "sleep")
    @patch.object(crawler, "fetch_industry_signals")
    @patch.object(crawler, "search_with_retry")
    def test_search_papers_filters_out_pure_academic_results(
        self,
        mock_search_with_retry,
        mock_fetch_industry_signals,
        _mock_sleep,
    ):
        mock_search_with_retry.return_value = [
            SimpleNamespace(
                entry_id="http://arxiv.org/abs/2604.00001v1",
                title="Academic Rec Paper",
                authors=[SimpleNamespace(name="Alice")],
                summary="Recommendation with LLMs",
                published=crawler.datetime.now(),
                pdf_url="https://arxiv.org/pdf/2604.00001v1",
                comment=None,
                journal_ref=None,
            )
        ]
        mock_fetch_industry_signals.return_value = {"industry_affiliations": [], "industry_email_domains": []}

        papers = crawler.search_papers(days_back=1, max_results=1)

        self.assertEqual(papers, [])
```

- [ ] **Step 4: Run test to verify it fails**

Run: `python -m unittest tests.test_crawler.CrawlerTests.test_search_papers_filters_out_pure_academic_results -v`
Expected: FAIL because the crawler currently keeps papers even when no industrial signal exists.

- [ ] **Step 5: Write the failing test for joint affiliation retention and metadata output**

```python
    @patch.object(crawler.time, "sleep")
    @patch.object(crawler, "fetch_industry_signals")
    @patch.object(crawler, "search_with_retry")
    def test_search_papers_keeps_joint_industry_academic_papers_and_outputs_topics(
        self,
        mock_search_with_retry,
        mock_fetch_industry_signals,
        _mock_sleep,
    ):
        mock_search_with_retry.return_value = [
            SimpleNamespace(
                entry_id="http://arxiv.org/abs/2604.05314v1",
                title="LLM for Recommendation at Scale",
                authors=[SimpleNamespace(name="Shuli Wang")],
                summary="A large language model recommendation system for reranking.",
                published=crawler.datetime.now(),
                pdf_url="https://arxiv.org/pdf/2604.05314v1",
                comment=None,
                journal_ref=None,
            )
        ]
        mock_fetch_industry_signals.return_value = {
            "industry_affiliations": ["Meituan"],
            "industry_email_domains": ["meituan.com"],
        }

        papers = crawler.search_papers(days_back=1, max_results=1)

        self.assertEqual(papers[0]["industry_affiliations"], ["Meituan"])
        self.assertEqual(papers[0]["industry_email_domains"], ["meituan.com"])
        self.assertEqual(papers[0]["paper_topics"], ["llm4rec"])
```

- [ ] **Step 6: Run test to verify it fails**

Run: `python -m unittest tests.test_crawler.CrawlerTests.test_search_papers_keeps_joint_industry_academic_papers_and_outputs_topics -v`
Expected: FAIL because `fetch_industry_signals`, `industry_email_domains`, and `paper_topics` do not exist in the output yet.

### Task 3: Implement Query Expansion, Industrial Signal Extraction, and Hard Filtering

**Files:**
- Modify: `scripts/crawler.py`
- Test: `tests/test_crawler.py`

- [ ] **Step 1: Write minimal helper structure for search configuration**

```python
GENERAL_SEARCH_QUERIES = [
    "recommendation system",
    "collaborative filtering",
    "recommender system ranking",
    "graph neural network recommendation",
    "sequential recommendation",
]

LLM4REC_SEARCH_QUERIES = [
    "llm for recommendation",
    "large language model recommendation",
    "generative recommendation",
    "llm recommender system",
    "conversational recommendation",
    "retrieval augmented recommendation",
]

SEARCH_CANDIDATE_MULTIPLIER = int(os.getenv("ARXIV_CANDIDATE_MULTIPLIER", "3"))
```

- [ ] **Step 2: Add helper functions for query building, topic classification, and signal extraction**

```python
def build_search_query() -> str:
    combined = GENERAL_SEARCH_QUERIES + LLM4REC_SEARCH_QUERIES
    query_terms = " OR ".join(f'all:"{term}"' for term in combined)
    return f"({query_terms}) AND (cat:cs.IR OR cat:cs.LG)"


def classify_paper_topics(title: str, abstract: str) -> List[str]:
    text = f"{title} {abstract}".lower()
    llm_markers = (
        "llm",
        "large language model",
        "language model",
        "generative recommendation",
        "conversational recommendation",
        "retrieval augmented recommendation",
    )
    return ["llm4rec"] if any(marker in text for marker in llm_markers) else ["general_rec"]


def fetch_industry_signals(arxiv_id: str) -> dict:
    html = fetch_arxiv_html(arxiv_id)
    if not html:
        return {"industry_affiliations": [], "industry_email_domains": []}
    return {
        "industry_affiliations": extract_industry_affiliations_from_html(html),
        "industry_email_domains": extract_industry_email_domains_from_html(html),
    }
```

- [ ] **Step 3: Update search flow to hard-filter academic-only results**

```python
    query = build_search_query()
    search = arxiv.Search(
        query=query,
        max_results=max_results * SEARCH_CANDIDATE_MULTIPLIER,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    for result in results:
        if result.published.replace(tzinfo=None) < start_date.replace(tzinfo=None):
            continue
        signals = fetch_industry_signals(result.entry_id.split("/")[-1])
        if not signals["industry_affiliations"] and not signals["industry_email_domains"]:
            continue
```

- [ ] **Step 4: Include metadata in output and cap final results**

```python
        paper_info = {
            "id": result.entry_id.split("/")[-1],
            "title": result.title,
            "authors": [a.name for a in result.authors],
            "abstract": result.summary,
            "published": result.published.isoformat(),
            "pdf_url": result.pdf_url,
            "comment": result.comment if hasattr(result, "comment") else None,
            "journal_ref": result.journal_ref if hasattr(result, "journal_ref") else None,
            "industry_affiliations": signals["industry_affiliations"],
            "industry_email_domains": signals["industry_email_domains"],
            "paper_topics": classify_paper_topics(result.title, result.summary),
        }
        papers.append(paper_info)
        if len(papers) >= max_results:
            break
```

- [ ] **Step 5: Run crawler tests to verify green**

Run: `python -m unittest tests.test_crawler -v`
Expected: PASS with all crawler tests green.

### Task 4: Verify, Commit, and Deploy

**Files:**
- Modify: `scripts/crawler.py`
- Modify: `tests/test_crawler.py`
- Modify: `docs/superpowers/plans/2026-04-08-industrial-llm4rec-crawler.md`

- [ ] **Step 1: Run focused verification and broader regression**

```bash
python -m unittest tests.test_crawler -v
python -m unittest tests.test_analyzer tests.test_workflows -v
```

Expected: all targeted tests pass.

- [ ] **Step 2: Review diff before commit**

```bash
git diff -- scripts/crawler.py tests/test_crawler.py docs/superpowers/plans/2026-04-08-industrial-llm4rec-crawler.md
git status --short
```

Expected: only intended files are modified.

- [ ] **Step 3: Commit implementation**

```bash
git add scripts/crawler.py tests/test_crawler.py docs/superpowers/plans/2026-04-08-industrial-llm4rec-crawler.md
git commit -m "feat: prioritize industrial llm4rec papers"
```

- [ ] **Step 4: Push code for deployment**

```bash
git push origin main
```

Expected: push succeeds and triggers the existing GitHub Pages deployment workflow on `main`.
