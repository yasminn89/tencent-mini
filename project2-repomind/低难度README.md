# RepoMind — 代码语义检索 PE 优化

> 腾讯 Mini Project 2 答卷 | 难度：低难度方案

---

## 项目概述

针对 LLM 在代码语义检索任务上的瓶颈，本项目以 **psf/requests** 库为评测语料，构建 147 条评测用例（人工精选 50 + ast 自动解析 97），通过四维度 PE 优化（System Prompt + Few-shot + CoT + 后处理）的消融实验，量化每个维度的独立贡献，识别 LLM 的真实瓶颈。

### 核心结果

| 指标 | 数据 |
|------|------|
| 评测集 | 147 条（人工 50 + 自动 97） |
| 评测模型 | DeepSeek Chat (deepseek-chat) |
| **基线得分** | **68.7%** |
| **最优方案得分** | **80.3%**（System Prompt + CoT） |
| 绝对提升 | +11.6 个百分点 |
| 相对提升 | +16.9% |

### 关键研究发现

1. **CoT 是单维度最大提升**（+6.2% vs SystemPrompt），尤其改善冷门函数定位（+14.4%）
2. **Few-shot 出现负迁移现象**（-8.1%），符合 Min et al. 2022 提出的 in-context learning bias 理论
3. **后处理不直接加分**，但实现结构化输出（文件/函数提取），满足生产环境可用性
4. **冷门函数定位仍是主要瓶颈**（PE 后 71.6%），是引入 RAG 的核心动机

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `PE方案文档.md` | 可直接复用的 Prompt 模板（System Prompt + CoT + Few-shot 库 + 后处理代码） |
| `PE量化对比报告.md` | 完整研究报告（实验设计 + 五配置消融对比 + 瓶颈诊断 + 学术引用） |
| `RepoMind_Project2.ipynb` | 完整实验过程（含评分体系迭代、System Prompt v1→v2、Few-shot v1→v2） |
| `repomind_experiment_data.json` | 147 条用例 × 5 个配置 的全部模型回答和评分 |
| `repomind_artifacts.json` | 核心 Prompt 模板和后处理规则的纯净 JSON 存档 |

---

## 复现指南

### 环境要求
- Python 3.10+
- `openai` SDK（兼容 DeepSeek API）
- DeepSeek API Key

### 快速复现

1. **打开 `RepoMind_Project2.ipynb`**（推荐 Google Colab）
2. **在 Cell 1 填入你的 DeepSeek API Key**：
```python
   os.environ["DEEPSEEK_API_KEY"] = "你的Key"
```
3. **按顺序运行所有 Cell**（共约 20-25 分钟，含 API 调用间隔）
4. **最终输出**：5 个配置的得分对比表，以及 `repomind_experiment_data.json`

### 评测集分布

| 类别 | 数量 | 描述 |
|------|------|------|
| A_simple | 15 | 简单直接查询（单函数定位） |
| B_cross_file | 15 | 跨文件依赖（完整调用链） |
| C_fuzzy | 12 | 模糊语义表达（口语化查询） |
| D_edge | 8 | 边界/不支持情况 |
| auto_generated | 97 | ast 解析源码 + LLM 反向生成查询 |

---

## 方法亮点

### 1. 双轨制评测集
- **人工精选**：按四类难度梯度精心设计，针对性测试 LLM 各场景表现
- **自动解析**：`ast.parse()` 提取所有有 docstring 的函数/类，反向生成自然语言查询
- 两者互补，兼顾难度覆盖和真实性广度

### 2. 评分体系迭代（4 版）
- v1（宽松，关键词命中30%即给分）→ 基线虚高 76%
- v2（严格阈值 60%）→ 结构化输出无法识别，虚低至 47%
- v3（兼容结构化）→ 函数名带下划线被截断
- v4（完整标识符匹配 + 不依赖手写关键词）→ **最终客观可复现**

### 3. 学术理论对应
PE 实验发现的负迁移现象，与 Min et al. (2022) "Rethinking the Role of Demonstrations" 和 Zhao et al. (2021) "Calibrate Before Use" 提出的 in-context learning bias 理论一致。详见 `PE量化对比报告.md` 第四节。

---

## 后续优化方向

基于本次 PE 实验识别的瓶颈：

1. **RAG 增强** — 把 requests 源码向量化索引，检索后注入 Context，直接解决冷门函数定位
2. **LoRA 微调** — 扩展评测集至 500+ 条，领域适配训练让模型内化 requests 架构知识
3. **动态 Few-shot** — 基于查询语义相似度从示例库检索 K 条，解决固定示例的负迁移

---

## 作者

- **姓名**：[彭雅斯]
- **专业**：物联网工程
- **项目**：腾讯 Mini Project 2 — RepoMind
