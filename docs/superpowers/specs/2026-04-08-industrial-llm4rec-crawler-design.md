# 工业界推荐论文抓取增强设计

## 背景

当前抓取逻辑集中在 [scripts/crawler.py](/Users/bin.ou/myData/my_project/Info_Me/paper-insight/scripts/crawler.py)，通过一组通用推荐 query 从 arXiv 拉取最近论文，再抓取 arXiv HTML 页面中的作者单位，提取 `industry_affiliations`。

现有实现有两个明显缺口：

1. 对 `LLM for recommendation` 的召回不足，容易漏掉生成式推荐、对话式推荐、RAG recommendation 等文章。
2. 工业界识别只依赖作者单位，无法利用作者邮箱域名；同时当前没有在抓取阶段硬过滤纯学术论文。

目标是将每日抓取改成“推荐相关 + 工业界优先，尤其关注 LLM4Rec”，并且在进入后续分析前直接过滤掉没有工业界信号的论文。

## 需求范围

### 目标

1. 只保留推荐相关论文。
2. 明显加强 `LLM for recommendation` 相关论文的召回。
3. 以 arXiv HTML 中的作者单位和作者邮箱共同判断是否属于工业界。
4. 纯学术论文直接过滤，不进入后续分析和发布流程。
5. “工业界 + 高校联合发表”保留。

### 非目标

1. 不引入新的外部数据源或第三方 API。
2. 不修改站点渲染逻辑，除非后续实现需要消费新增字段。
3. 不改变 analyzer 的分析提示词和文章生成结构。

## 当前实现观察

1. `search_papers()` 只构造一条通用 arXiv query，关键词覆盖推荐系统、协同过滤、序列推荐等主题，但没有单独强化 LLM4Rec。
2. `fetch_industry_affiliations()` 会抓取 `https://arxiv.org/html/<id>`，并通过 `ltx_affiliation_institution` 提取作者单位。
3. `extract_industry_affiliations_from_html()` 目前仅返回工业界单位列表，没有邮箱域名回退识别，也没有“是否保留该论文”的显式判断逻辑。
4. `main()` 只做去重，不做工业界硬过滤，因此纯学术文章也会进入后续分析链路。

## 方案对比

### 方案 A：抓取阶段硬过滤

做法：

1. 将 query 拆成“推荐通用”和“LLM4Rec 强化”两组。
2. 对每篇候选抓取 arXiv HTML。
3. 从作者单位和邮箱域名提取工业界信号。
4. 只输出存在工业界信号的论文。

优点：

1. 与目标完全一致。
2. 改动集中在抓取层，流水线改动最小。
3. 后续 analyzer 和站点逻辑基本不需要理解“纯学术过滤”。

缺点：

1. 抓取 HTML 的次数变多，运行时间会增加。

### 方案 B：保留全部论文，仅做排序

做法：

1. 扩大 LLM4Rec query。
2. 工业界论文排在前面，纯学术保留但不优先分析。

优点：

1. 召回更高。

缺点：

1. 不满足“过滤纯学术文章”的明确要求。

### 方案 C：二阶段增强识别

做法：

1. arXiv 初筛。
2. 再通过其他来源补作者单位或邮箱映射。

优点：

1. 识别准确率潜在更高。

缺点：

1. 引入额外依赖，复杂度和故障面都变大。
2. 与当前仓库规模不匹配。

## 选型

采用方案 A：抓取阶段硬过滤。

理由：

1. 直接满足“只要工业界文章”的要求。
2. 能在当前架构内完成，不需要改工作流和分析器主流程。
3. 与已有 `industry_affiliations` 机制兼容，只是在其基础上补强邮箱识别和过滤决策。

## 设计细节

### 1. Query 设计

将单一 `SEARCH_QUERIES` 拆成两类关键词：

1. 通用推荐：
   `recommendation system`、`recommender system ranking`、`collaborative filtering`、`sequential recommendation`、`retrieval recommendation` 等。
2. LLM4Rec 强化：
   `llm for recommendation`、`large language model recommendation`、`generative recommendation`、`llm recommender system`、`conversational recommendation`、`retrieval augmented recommendation` 等。

实现上仍然合成一条 arXiv query，但候选集合会覆盖更多 LLM4Rec 主题。考虑到后续要做工业界硬过滤，上游 `max_results` 应放大，例如使用 `max_results * 3` 作为抓取候选上限，再在过滤后截断到最终上限。

### 2. 主题识别

增加轻量主题标记函数，用标题、摘要和 query 命中词判断论文是否属于：

1. `llm4rec`
2. `general_rec`

标记结果可写入 `paper_topics`，便于后续理解为什么某篇论文被召回。主题标记不参与硬过滤，只用于解释和调试。

### 3. 工业界识别

工业界信号来自两条路径：

1. 作者单位：
   继续沿用 arXiv HTML 中 `ltx_affiliation_institution` 的提取逻辑，命中公司名或企业后缀则记为工业界单位。
2. 作者邮箱域名：
   从 arXiv HTML 中提取 `mailto:` 或邮箱文本。
   对域名做归一化，过滤 `gmail.com`、`outlook.com`、`hotmail.com`、`qq.com`、`163.com` 等公共邮箱。
   如果域名属于企业域名，例如 `meituan.com`、`bytedance.com`、`research.google.com`，则记为工业界信号。

识别结果建议拆成两个字段：

1. `industry_affiliations`
2. `industry_email_domains`

只要任一路径存在工业界信号，该论文就视为工业界论文。

### 4. 保留与过滤规则

保留条件：

1. 论文标题/摘要满足推荐相关 query 召回。
2. 至少满足以下之一：
   - 存在 `industry_affiliations`
   - 存在 `industry_email_domains`

过滤条件：

1. 没有任何工业界单位。
2. 没有任何工业界邮箱域名。

联合发表规则：

1. 同时出现高校和企业时保留。
2. 只有高校、研究院、实验室等学术单位且没有工业界邮箱时过滤。

### 5. 结果输出

`search_papers()` 输出的单篇论文结构新增：

1. `industry_email_domains`
2. `paper_topics`

保留现有字段不变，避免破坏 analyzer 的兼容性。

### 6. 错误与降级策略

1. 如果 arXiv HTML 拉取失败，默认视为“没有工业界证据”，该论文不进入最终结果。
2. 如果 HTML 中没有作者单位，但能提取到公司邮箱域名，则仍然保留。
3. 如果单位和邮箱都缺失，则过滤。

这种策略偏保守，目标是减少纯学术论文误入，而不是保证最大召回。

## 实施步骤

1. 在 `tests/test_crawler.py` 先补失败测试：
   - 单位识别工业界
   - 邮箱域名识别工业界
   - 公共邮箱不算工业界
   - 工业界与高校联合发表保留
   - 无工业界信号的论文被过滤
   - LLM4Rec query 被纳入搜索构造
2. 在 `scripts/crawler.py` 实现：
   - query 扩展
   - 邮箱提取与域名归一化
   - 工业界硬过滤
   - `paper_topics` 与 `industry_email_domains` 输出
3. 运行最小必要测试并修正。

## 风险

1. 企业域名识别存在漏判，尤其是子域名和研究品牌名不统一时。
2. arXiv HTML 结构变化会影响单位和邮箱提取。
3. 硬过滤会牺牲一部分“工业界未显式暴露邮箱/单位”的论文召回。

## 验证策略

1. 单元测试覆盖核心识别规则和过滤规则。
2. 本地运行 `tests/test_crawler.py`，确认新增逻辑稳定。
3. 若条件允许，可用一两个真实 arXiv ID 做手动抽样验证，但不把外网结果写死到测试中。

## 开放决定

当前实现阶段默认采用“宁可漏一些，也不放进纯学术论文”的保守策略。若后续观察到工业界论文漏判明显，再考虑：

1. 扩大公司别名词典。
2. 单独维护企业邮箱域名映射。
3. 调整 HTML 失败时的降级策略。
