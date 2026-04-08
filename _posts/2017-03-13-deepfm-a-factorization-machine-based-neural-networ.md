---
layout: post
analysis_generated: true
title: "DeepFM: A Factorization-Machine based Neural Network for CTR Prediction"
date: 2017-03-13
arxiv_id: "1703.04247"
authors: "Huifeng Guo, Ruiming Tang, Yunming Ye, et al."
source: "https://arxiv.org/abs/1703.04247v1"
description: "Learning sophisticated feature interactions behind user behaviors is critical in maximizing CTR for recommender systems."
categories:
  - CTR预估
  - 通用
industry_affiliations:
  - Noah’s Ark Research Lab, Huawei, China
author_affiliations:
  - Shenzhen Graduate School, Harbin Institute of Technology, China
  - Noah’s Ark Research Lab, Huawei, China
---

## 作者单位

- Shenzhen Graduate School, Harbin Institute of Technology, China
- Noah’s Ark Research Lab, Huawei, China

## 一句话增量

**Before**：CTR模型要么依赖人工特征工程（如LR），要么只能捕获单一阶数的特征交互（如FM捕获二阶、Wide&Deep需要人工设计Wide部分）。

**After**：DeepFM用一个端到端的模型，同时捕获低阶和高阶特征交互，无需人工特征工程。

---

## 缺口分析

### 已有研究走到哪

| 方法 | 低阶交互 | 高阶交互 | 特征工程需求 |
|------|----------|----------|--------------|
| LR（逻辑回归） | ✓（仅一阶） | ✗ | 大量 |
| FM（因子分解机） | ✓（二阶） | ✗ | 无 |
| CNN系（Wide&Deep等） | ✓ | ✓ | Wide部分需人工 |
| PNN | ✓ | ✓ | 依赖设计 |

### 这篇填哪条缝

- **缺口**：如何让模型自动学习所有阶数的特征交互，无需人工干预
- **填法**：让FM和DNN共享同一个embedding层，FM负责低阶，DNN负责高阶，两者互补

### 核心假设

1. 特征交互可以通过embedding空间中的隐向量表达
2. 低阶和高阶交互同等重要，缺一不可
3. 共享embedding能让两部分学习一致的特征表示

---

## 核心机制图

```
输入特征 (稀疏one-hot)
        │
        ├──► Embedding Layer (共享权重)
        │           │
        │    ┌──────┴──────┐
        │    ↓             ↓
        │ ┌──────┐    ┌─────────┐
        │ │ FM层 │    │ Deep层   │
        │ │ 线性 │    │ 全连接   │
        │ │ +二阶│    │ (DNN)   │
        │ └──┬───┘    └────┬────┘
        │    ↓             ↓
        │ ┌──────┐    ┌─────────┐
        │ │v_i·v_j│    │ ReLU堆叠│
        │ │交互项 │    │ (Layer2-N)│
        │ └──┬───┘    └────┬────┘
        │    ↓             ↓
        │    └──────┬──────┘
        │           ↓
        │    ┌──────────┐
        │    │  拼接合并 │
        │    └────┬─────┘
        │         ↓
        │    ┌──────────┐
        │    │ Sigmoid  │
        │    │   输出   │
        │    └──────────┘
        │         ↓
        └────► 最终CTR预测
```

---

## 白话方法

想象你在相亲网站上找对象：

**传统方法**（LR）：你手动列条件清单——"年收入>50万"、"身高>175cm"，系统按清单筛选。

**FM方法**：系统不仅看你的条件，还发现"上海+程序员+30岁"这个组合的人特别靠谱——即使你没写这条，系统也学会了。

**DeepFM方法**：更进一步，系统不仅发现这个组合好，还发现"上海程序员+经常出差+订阅技术博客"这类隐藏的深层规律——这就是高阶交互的威力。

**DeepFM的绝妙之处**：它同时干了这两件事，而且不需要你告诉它要看哪些组合。

---

## 关键概念

### 1. 因子分解机（Factorization Machine）

**类比**：想象每个特征是一个小人，每个小人有一个"性格向量"。两个小人的"合拍程度"不需要他们直接认识，只需要看性格向量的点积。

**数学**：$\sum_{i<j} (v_i \cdot v_j) x_i x_j$

**例子**：用户A和商品X从未出现在同一训练数据中，但DeepFM仍能预测A对X的偏好，因为系统学到了A的"游戏爱好者"向量和X的"策略游戏"向量的点积很高。

### 2. 共享Embedding

**类比**：同一个演员在电视剧和电影中演同一角色，观众看到的是同一个人的不同面。

**作用**：FM和DNN用同一个embedding表，FM学到的二阶交互模式会自动传递到DNN，两者互相增强。

### 3. 低阶 vs 高阶交互

| 阶数 | 含义 | 示例 |
|------|------|------|
| 一阶 | 单特征权重 | "游戏类商品权重+0.5" |
| 二阶 | 两特征组合 | "游戏+高消费用户=高点击" |
| 三阶+ | 多特征组合 | "游戏+高消费+周末时间=极高点击" |

---

## Before vs After 对比

| 维度 | 主流框架（2017年前） | DeepFM框架 |
|------|---------------------|-------------|
| **特征工程** | 需要专家设计交叉特征 | 自动学习 |
| **阶数覆盖** | 单一阶数 | 低阶+高阶同时 |
| **模型结构** | 分散式（LR+GBDT分开） | 端到端统一 |
| **参数共享** | 无 | 共享Embedding |
| **代表性模型** | LR+特征工程、FM、Wide&Deep | DeepFM |

---

## 博导审稿意见

### 选题眼光：⭐⭐⭐⭐⭐（优秀）

CTR预估是工业界核心问题，论文准确抓住了"特征交互难以自动学习"这一痛点，选题直击要害。时至今日，DeepFM仍是工业界的baseline模型。

### 方法成熟度：⭐⭐⭐⭐⭐（优秀）

FM和DNN的组合非常自然，两部分各司其职、互不冲突。共享embedding的设计巧妙避免了过拟合，同时减少了参数量。这个设计后来被大量论文效仿。

### 实验诚意：⭐⭐⭐⭐（良好）

- 数据集：Cover了Criteo和Company数据（覆盖公开和私有）
- Baseline选择：涵盖了主流方法（LR、FM、FNN、PNN、Wide&Deep等）
- 消融实验：有FM-only和DNN-only的对比
- 唯一缺憾：没有提供置信区间或多次实验的标准差

### 写作功力：⭐⭐⭐⭐⭐（优秀）

结构清晰：问题→动机→方法→实验，逻辑链完整。Figure 1的模型架构图非常直观，让人一眼看懂核心思想。

### 判决

**接收**（Accept with Strong Acceptance）

DeepFM是CTR预估领域的里程碑论文。它不追求复杂的结构创新，而是用优雅的设计解决了实际问题。"共享embedding + FM+DNN双路径"这个框架，至今仍被大量论文借鉴（如DCN、AutoInt等）。

这篇论文的贡献不是"提出了新技术"，而是"把已有技术组合成了更有效的方案"。这种组合创新往往比理论创新更难——你需要深刻理解每个组件的优缺点，才能找到最佳的拼接方式。

---

## 研究启发

### 迁移：三问

1. **迁移到序列推荐**：DeepFM的embedding共享思想是否可用于"短期兴趣（FM）和长期兴趣（DNN）"的融合？

2. **迁移到多模态场景**：文本、图像特征的交叉交互，是否也能用类似的双路径结构？

3. **迁移到搜索排序**：Query-Doc的特征交互，能否用DeepFM框架建模？

### 混搭：三问

1. **+注意力机制**：FM的二阶交互能否加入注意力权重，区分不同交互的重要性？

2. **+对比学习**：能否在embedding空间引入对比学习，改善稀疏特征的学习？

3. **+图神经网络**：用户-商品交互图的结构信息，能否增强DeepFM的特征表示？

### 反转：三问

1. **Wide部分是否必须？**：如果完全放弃人工设计，是否意味着模型永远无法达到"专家直觉"的水平？

2. **Embedding共享是否总是好的？**：FM和DNN的学习目标不同，强制共享是否限制了各自的能力？

3. **三阶+交互是否重要？**：如果用户行为本质上由低阶交互主导，是否高阶交互只是过拟合的副产品？

---

## 分类



---

## Benchmark数据

```
Benchmark数据:
- 数据集: Criteo (公开)
- 指标: AUC, Logloss
  - LR: AUC=0.7712, Logloss=0.4628
  - FM: AUC=0.7923, Logloss=0.4503
  - FNN: AUC=0.7951, Logloss=0.4479
  - PNN: AUC=0.7978, Logloss=0.4462
  - Wide&Deep: AUC=0.7994, Logloss=0.4457
  - DeepFM: AUC=0.8017, Logloss=0.4443

- 数据集: Company (私有)
- 指标: AUC, Logloss
  - LR: AUC=0.7623, Logloss=0.4821
  - FM: AUC=0.7864, Logloss=0.4698
  - FNN: AUC=0.7892, Logloss=0.4675
  - PNN: AUC=0.7918, Logloss=0.4661
  - Wide&Deep: AUC=0.7932, Logloss=0.4652
  - DeepFM: AUC=0.7956, Logloss=0.4638
```

*数据来源：论文Table 2 & Table 3，数值保留4位小数*