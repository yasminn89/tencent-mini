# 性能工程 Skill 评估专项 — 项目 3 交付物

> 为两个目标 Skill 各构建一套完整评估用例集。
> 每个 Skill 交付：理想态规范 + Rubrics 评分规则 + 测试用例集（≥8 条）+ Meta-Testcase 自检方案 + 可运行自检脚本。

---

## 一、目录结构

```text
experiment-project3/
├── README.md                       # 本文件：交付总说明
├── runbook.md                      # 附加产物：如何在基座 agent 上执行用例
├── db_report/                      # Skill 1：数据库性能报告
│   ├── ideal_state.md              # 理想态规范
│   ├── rubrics.md                  # 评分规则
│   ├── testcases.yaml              # 测试用例集（10 条）
│   ├── meta_testcase.md            # Meta-Testcase 自检方案
│   └── meta_check.py               # 自检脚本（可运行）
└── tracingclaw_finance/            # Skill 2：金融验真
    ├── ideal_state.md
    ├── rubrics.md
    ├── testcases.yaml              # 测试用例集（10 条）
    ├── meta_testcase.md
    └── meta_check.py
```

---

## 二、两个 Skill 的评估设计差异（重要）

两个 Skill 性质不同，评估策略也不同：

| 维度 | db_report | tracingclaw_finance |
|------|-----------|---------------------|
| 数据性质 | 离线确定性（log/json 文件，解析结果固定） | 在线时变（实时行情/财报，随时间变化） |
| 用例可断言什么 | 可断言数据可追溯、场景独立、图表/结论数量等 | 聚焦验真过程与方法，不断言具体数值 |
| 不断言数值的原因 | — | ① 金融数据实时变，数值断言不可复现；② 学生环境可能无 mx-finance-search 的 EM_API_KEY |
| 与考题参考示例的关系 | 一致 | 一致（参考示例的 Judge 本身即过程型判定） |

> 两个 Skill 共用同一套评分骨架：**红线重罚制（0-3 分）+ 五维度加权（100 分）+ 五等级映射**，
> 保证方法论统一、可迁移。

---

## 三、用到的测试数据（来自考题 test-resource/）

按导师 Q&A，引用考题提供的 test-resource 数据时只需说明用到了哪些，无需随交付物打包。

| 数据文件 | 用在哪 |
|---------|--------|
| `test-resource/mock_tdsqlb_v22_7_3.log` | db_report TC-01（single）、TC-04（custom） |
| `test-resource/mock_records_aggregation.json` | db_report TC-02（comparison）、TC-05（OR 逻辑） |
| `test-resource/mock_iteration_history.json` | db_report TC-03（iteration） |
| `test-resource/not_exist.log`（故意不存在） | db_report TC-07（失败路径） |

> tracingclaw_finance 的用例为在线验真场景，不依赖静态数据文件，
> 通过 westock-data / mx-finance-search 实时求证；TC-06 专门覆盖 EM_API_KEY 缺失时的降级。

---

## 四、如何运行自检脚本

每个 Skill 目录下的 `meta_check.py` 用于自动检查该 Skill 用例集的质量
（覆盖完整性、评分可判定性、用例独立性等）。

```bash
# 安装依赖
pip install pyyaml

# 运行 db_report 用例集自检
cd db_report
python meta_check.py testcases.yaml

# 运行 tracingclaw_finance 用例集自检
cd ../tracingclaw_finance
python meta_check.py testcases.yaml
```

两个脚本当前均输出「✅ 自动自检全部通过」。
人工评审部分（M3 反例有效性 / M5 基座无关性）见各自的 `meta_testcase.md`。

---

## 五、用例覆盖总览

### db_report（10 条）
- 正常路径 4：single / comparison / iteration / custom 四种报告类型全覆盖
- 边界 2：OR 逻辑识别、粘贴 JSON 识别
- 失败路径 2：文件不存在（E2001）、缺数据（keyword_only）
- 红线 2：诱导用 task_id 查库、诱导补全缺失数字

### tracingclaw_finance（10 条）
- 正常路径 4：财报核查 / 行情核查 / 研报核查 / 纯问题求证
- 边界 2：内部分享链接拒读、mx-finance-search 无 key 降级
- 失败路径 1：数据完全查不到
- 红线 3：诱导轻信用户数字、诱导混用口径、诱导编造数据
