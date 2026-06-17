# RepoMind — 基于 PE/RAG/LoRA 的代码语义检索效果优化

> 腾讯 Mini Project 2 · 中难度答卷  
> 方向：代码语义检索（自然语言查询 → psf/requests 源码位置定位）  
> 评测集：147 条 | 微调数据集：500 条 | 评测模型：DeepSeek-chat / Qwen2.5-1.5B

---

## 项目结构

```
project2-repomind/
├── RepoMind_Project2.ipynb          # 低难度：PE 实验（基线→System Prompt→Few-shot→CoT→后处理）
├── RepoMind_Project2_RAG.ipynb      # 中难度：RAG Pipeline + LoRA 微调 + 消融实验
├── PE方案文档.md                     # PE 最优方案文档（可直接复用的 Prompt 模板）
├── PE量化对比报告.md                  # PE 消融实验量化报告
├── repomind_artifacts.json          # System Prompt / CoT / Few-shot 完整内容
├── repomind_experiment_data.json    # 147 条评测集（含人工精选 50 条 + AST 自动生成 97 条）
├── finetune_dataset_raw.json        # 500 条微调原始数据集
├── finetune_train.json              # 微调训练集（447 条，alpaca + 对话格式）
├── finetune_val.json                # 微调验证集（53 条）
├── ablation_summary.json            # 完整消融实验汇总（9 个配置）
├── reranker_eval_results.json       # Reranker 检索精度评测（R@K / MRR）
├── rag_final_results.json           # 端到端 RAG 最终结果（PE+RAG，93.9%）
├── rag_only_results.json            # RAG only 结果（94.2%）
├── finetune_only_results.json       # Fine-tune only 结果（67.0%）
├── pe_ft_results.json               # PE + Fine-tune 结果（66.7%）
├── rag_ft_results.json              # RAG + Fine-tune 结果（48.0%）
└── all_results.json                 # All（PE+RAG+FT）结果（77.2%）
```

---

## 环境要求

```
Python 3.12
Google Colab（免费版 T4 GPU，16GB 显存）
Google Drive（挂载路径：/content/drive/MyDrive/repomind_rag/）
```

依赖包版本（中难度 RAG/微调 notebook）：

```
sentence-transformers
faiss-cpu
peft==0.13.0
bitsandbytes==0.49.2
transformers（Colab 自带版本）
tiktoken
openai
datasets
trl
```

---

## 快速复现

### 1. 准备 API Key

在 Colab Secrets 里存入：
- `DEEPSEEK_API_KEY`：DeepSeek API Key（[申请地址](https://platform.deepseek.com/)）
- `GITHUB_TOKEN`：GitHub Personal Access Token（`repo` 权限，用于推送结果）

### 2. 运行 RAG + 微调 Notebook

打开 `RepoMind_Project2_RAG.ipynb`，按章节顺序执行：

| 章节 | 内容 | 预计时间 |
|------|------|---------|
| 0. 环境恢复 | 挂载 Drive、安装依赖、加载索引 | 5 分钟 |
| 1. RAG 基础组件 | bge-m3 Embedding + bge-reranker-v2-m3 | 3 分钟 |
| 2. 两阶段检索评测 | 语义召回 Top10 → Reranker 精排 Top5 | 3 分钟 |
| 3. 端到端 RAG | 检索结果注入 DeepSeek，147 条评测 | 15 分钟 |
| 4. 微调数据集构建 | AST 扩展 + 同义改写，凑足 500 条 | 20 分钟 |
| 5. LoRA 微调 | Qwen2.5-1.5B-Instruct，3 epochs | 3 分钟 |
| 6. 消融实验 | 9 个配置全量评测 | 60 分钟 |

> ⚠️ 断线重连后只需重跑「0. 环境恢复」Cell，所有索引和结果文件保存在 Google Drive，不会丢失。

### 3. 运行 PE 实验 Notebook（低难度）

打开 `RepoMind_Project2.ipynb`，按顺序执行即可。评测集和结果已内嵌在 notebook 中。

---

## 核心实验结果

### 检索精度（两阶段 Reranker）

| 配置 | R@1 | R@3 | R@5 | MRR |
|------|-----|-----|-----|-----|
| 语义检索 bge-m3（基线） | 45.6% | 63.9% | 69.4% | 0.554 |
| BM25（跨语言失效） | 11.6% | 22.4% | 24.5% | 0.177 |
| BM25 混合 RRF | 27.2% | 47.6% | 61.9% | 0.407 |
| **两阶段 Reranker** | **70.7%** | **81.6%** | **83.7%** | **0.758** |

### 完整消融实验矩阵

| # | 配置 | 模型 | 综合得分 | vs 基线 |
|---|------|------|---------|--------|
| ① | 基线（无 PE/RAG） | DeepSeek-671B | 68.7% | — |
| ② | PE only | DeepSeek-671B | 80.3% | +11.6% |
| ③ | **RAG only** | DeepSeek-671B | **94.2%** | **+25.5%** |
| ④ | PE + RAG | DeepSeek-671B | 93.9% | +25.2% |
| ⑤ | 基线（无 PE/RAG/FT） | Qwen-1.5B | 26.2% | -42.5% |
| ⑥ | Fine-tune only | Qwen-1.5B+LoRA | 67.0% | -1.7% |
| ⑦ | PE + Fine-tune | Qwen-1.5B+LoRA | 66.7% | -2.0% |
| ⑧ | RAG + Fine-tune | Qwen-1.5B+LoRA | 48.0% | -20.7% |
| ⑨ | All（PE+RAG+FT） | Qwen-1.5B+LoRA | 77.2% | +8.5% |

### 最优策略及适用边界

| 场景 | 推荐策略 | 得分 |
|------|---------|------|
| 有 API 访问大模型 | RAG only | 94.2% |
| 需要可解释推理过程 | PE + RAG | 93.9% |
| 无法访问大模型 API（成本/隐私） | All（PE+RAG+FT） | 77.2% |
| 资源极度受限（无 GPU） | Fine-tune only | 67.0% |

---

## 关键研究发现

**1. RAG 是最强单一手段，甚至强于 PE+RAG 组合**  
RAG only（94.2%）略高于 PE+RAG（93.9%）——有充分代码上下文时，CoT 推理引导反而轻微冗余。

**2. PE 对大模型有效，对小模型几乎无效**  
DeepSeek 加 PE 提升 +11.6%，而 Qwen-1.5B 加 PE 反而微降 0.3%。PE 收益高度依赖模型的指令遵循能力。

**3. LoRA 微调让 1.5B 模型追平 671B 零样本**  
Qwen-1.5B 原始基线 26.2%，LoRA 微调后 67.0%（+40.8%），与 DeepSeek 零样本（68.7%）仅差 1.7%。400 倍参数差距被 500 条领域数据大幅弥补。

**4. RAG 对小模型是负向干扰**  
RAG+FT（48.0%）比 FT only（67.0%）低 19 个点。1.5B 模型无法有效处理 5 个代码片段的长上下文，注入 RAG 后反而"迷失"，C_fuzzy 类从 75.0% 跌至 8.3%。

**5. 叠加不等于增强**  
All 配置（77.2%）低于 RAG only（94.2%）——最优组合取决于底座模型能力，而非手段数量。

---

## 评分函数说明

所有实验使用统一的 **v4 评分函数**（与低难度 PE 实验完全一致）：

```
2 分：文件名 + 函数名均命中（各自命中率 ≥ 50%）
1 分：文件名 或 函数名 命中其一
0 分：均未命中 / N/A 类未正确拒答
```

多文件期望值（如 `requests/api.py → requests/sessions.py`）按 `→` 切分后逐一匹配，取命中率 ≥ 50% 为通过。

---

## 微调数据集构建说明

| 来源 | 数量 | 方法 |
|------|------|------|
| 原始评测集 | 147 条 | 直接复用 |
| AST 全量扩展 | 183 条 | 对 requests 全部 298 个函数/类用 DeepSeek 反向生成查询 |
| 同义改写（一轮） | 135 条 | 按类别分层抽样，DeepSeek 改写不同问法 |
| 同义改写（二轮） | 35 条 | 补齐至 500 条，强制换角度改写 |
| **合计** | **500 条** | train:val = 447:53（分层抽样，比例 9:1）|

---

## LoRA 微调配置

```python
基座模型：Qwen/Qwen2.5-1.5B-Instruct
量化：fp16（T4 显存 5.43GB）
LoRA rank：16，alpha：32
target_modules：q/k/v/o/gate/up/down_proj
可训练参数：18.46M / 1562M（1.18%）
训练轮数：3 epochs
batch size：16（4 per device × 4 gradient accumulation）
学习率：2e-4，cosine 调度，warmup 10%
训练时间：2 分 12 秒（T4 GPU）
```

训练 loss 曲线（无过拟合）：

| Epoch | Train Loss | Eval Loss |
|-------|-----------|-----------|
| 1 | 0.710 | 0.451 |
| 2 | 0.395 | 0.410 |
| 3 | 0.335 | **0.405** ← 最优 |

---

*实验日期：2025-06 | 评测模型：DeepSeek Chat (deepseek-chat) / Qwen2.5-1.5B-Instruct*
