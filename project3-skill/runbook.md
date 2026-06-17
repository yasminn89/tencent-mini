# Runbook：如何在基座 agent 上执行本评估用例集（附加产物）

> 本文档为附加产物，说明这套用例集如何被实际执行。
> 呼应课程 Q&A：用例最终要被某个「基座 agent × skill」组合执行；
> 不同基座效果不同，需选择性价比最高的基座。本套用例设计为基座无关，
> 任意能读懂规范的 LLM 基座均可执行。

---

## 一、执行模型

```
用例 Input  ──►  基座 agent（装载目标 Skill）  ──►  实际输出
                                                      │
                                                      ▼
                                       对照 ExpectedOutput / ProcessChecks
                                                      │
                                                      ▼
                                       按 rubrics.md 打分 → 得到该用例分数
```

- **基座 agent**：驱动 Skill 运行的 LLM（如 Claude / GPT / 通义 / DeepSeek 等）。
- **目标 Skill**：被评估对象（db_report 或 tracingclaw_finance）。
- **判分者**：人工，或另一个 LLM 按 rubrics.md 自动判分。

---

## 二、单条用例执行步骤

1. 选定一个基座 agent，并装载目标 Skill。
2. 取一条用例的 `Input`，原样发给 agent。
3. 收集 agent 的完整输出（含其调用工具/脚本的过程，若可见）。
4. 对照该用例的 `ExpectedOutput` 与 `ProcessChecks`，逐项核对。
5. 按 `rubrics.md`：先查红线（重罚制 0-3 分），未触发再做五维度加权打分。
6. 记录该用例的 total 分与 grade。

---

## 三、批量执行与「基座 × skill」对比

按 Q&A 思路，可对同一 Skill 用多个基座各跑一遍，做笛卡尔积对比，
选出性价比最高的基座：

| 基座 \ 用例 | TC-01 | TC-02 | ... | 平均分 | 成本 | 性价比 |
|------------|-------|-------|-----|--------|------|--------|
| 基座 A | | | | | | |
| 基座 B | | | | | | |
| 基座 C | | | | | | |

- **平均分**：该基座在全部用例上的 rubrics 总分均值。
- **成本**：token 消耗 / 调用费用 / 时延。
- **性价比**：平均分 / 成本，用于选型。

---

## 四、面向过程的检查怎么落地

每条用例的 `ProcessChecks` 字段是面向过程的检查点。执行时：

- 若 agent 的中间过程可见（如它声明"先调用 westock-data search"），
  直接核对 ProcessChecks 各步是否走到。
- 若中间过程不可见，则从最终输出反推：
  例如 tracingclaw 用例要求"先查 westock 再答"，
  可通过最终答案是否带可追溯来源与口径来间接判断是否真的求证过。

> 面向过程最终服务于结果：过程对了，结果才可信。

---

## 五、本环境已完成的自检

两个 Skill 的用例集均已通过 `meta_check.py` 自动自检
（覆盖完整性 / 评分可判定性 / 用例独立性 / 数值无关性）。
执行 `python meta_check.py testcases.yaml` 可复现「✅ 自动自检全部通过」。

人工评审项（反例有效性、基座无关性）见各 Skill 的 `meta_testcase.md`。
