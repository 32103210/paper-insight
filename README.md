# Paper Insight

每天自动抓取工业界推荐算法相关论文，AI 生成结构化分析报告。

## 功能

- 自动从 arXiv 抓取推荐算法、协同过滤、图神经网络推荐等论文
- 使用 MiniMax M2.7 API + 李继刚论文分析框架生成深度报告
- 通过 GitHub Pages 静态展示

## 分析维度

1. 一句话增量
2. 缺口分析
3. 核心机制图 (ASCII)
4. 白话方法 (类比讲解)
5. 关键概念 (费曼式)
6. Before vs After
7. 博导审稿
8. 研究启发

## 技术栈

- 爬虫: Python + arxiv 库
- AI 分析: MiniMax M2.7 API
- 静态站点: Jekyll + GitHub Pages
- CI/CD: GitHub Actions

## 手动触发

在 GitHub Actions 页面点击 "Run workflow" 可手动触发。