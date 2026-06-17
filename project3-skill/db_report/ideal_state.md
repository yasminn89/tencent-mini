# db_report Skill 理想态规范（Ideal State Spec）

> 本规范定义「数据库性能报告 Skill」在各种输入、数据质量、报告类型下**应该**怎么表现。
> 它是后续 Rubrics 评分规则与测试用例集的判定依据。
> 适配版本：自包含版 db_report_skill（无外部副文件依赖，数据源标识为 local_file / local_data / keyword_only）。

---

## 1. 能力边界

### 1.1 支持的输入
- 本地文件：`.log`（sysbench 日志）/ `.xlsx` / `.json` / `.csv`
- 粘贴 JSON：标准 records 结构 `{meta, records}`，或字段一致的原始测试行数组

### 1.2 支持的报告类型
- `single`：单次测试报告（默认类型）
- `comparison`：多产品 / 多版本 / 多配置横向对比（≥ 2 份数据）
- `iteration`：版本迭代 / 历史趋势（≥ 3 个时间点）
- `custom`：用户指定维度的专项 / 深度分析

### 1.3 输出格式
- 必须独立生成 `report.md` + `report.docx` + `report.html` 三份
- 禁止用 pandoc 等工具将 md 批量转成另外两种格式

### 1.4 不支持的输入（必须拒绝或降级处理）
- 仅提供 `task_id` / `plan_id` / `report_id` 而无任何本地数据文件：
  按缺数据处理（`keyword_only`），要求补充本地数据，**不得**据此查询任何内部库
- 要求连接内部数据库或 HTTP API
- 仅有自然语言描述、无任何可读取的数据来源

---

## 2. 意图识别

### 2.1 数据源类型识别（detect_input）
| 输入特征 | data_source_type |
|---------|------------------|
| 含真实存在的 .log/.xlsx/.json/.csv 路径 | `local_file` |
| 含 product/scenario/tps 等字段的粘贴 JSON | `local_data` |
| 既无文件也无有效 JSON（仅关键词） | `keyword_only` |

### 2.2 报告类型识别（按优先级，命中即停）
1. 命中 `对比 / 比较 / vs / 差异 / 哪个更好` → `comparison`
2. 命中 `迭代 / 版本演进 / 历史趋势 / 变化趋势` → `iteration`
3. 命中 `客制化 / 专项 / 定制 / 深度分析 / 详细分析` → `custom`
4. 其他 → `single`

### 2.3 场景关键词中英映射（必须执行）
中文业务术语必须映射为标准英文字段，不得原样写入筛选条件：

| 中文 | 英文 |
|------|------|
| 只读 | read_only |
| 写入 / 写 | write_only |
| 读写 / 混合读写 | read_write |
| 更新索引 | update_index |
| 更新非索引 | update_non_index |
| 点查 / 点选 | point_select |
| tpcc | tpmC |

### 2.4 AND vs OR 逻辑（最易错）
- "集中式的只读场景"（同一场景的多个修饰词）
  → `test_name_keywords: ["集中式","read_only"]`（AND）
- "集中式只读场景 **和** 点查场景"（连接不同场景）
  → `test_name_keywords_or: [["集中式","read_only"],["集中式","point_select"]]`（OR）
- `test_name_keywords` 与 `test_name_keywords_or` 互斥，不得同时出现

---

## 3. 数据门控

### 3.1 进入分析阶段前应确认
- 数据源类型、文件路径或粘贴 JSON 摘要
- 产品数、场景数、并发档覆盖范围
- TPS / QPS / P95 关键字段空值率
- 缺失字段和不可比条件

### 3.2 数据质量硬要求
- records 长度必须 > 0
- TPS / QPS / P95 空值率必须 = 0%
- 单产品 × 场景的并发档应覆盖 `meta.concurrencies`
- 数据来源（source_info：type + value + rows_fetched）必须可追溯

### 3.3 缺数据 / 异常数据处理
- `keyword_only` → 停止流程，明确提示用户补充数据文件或粘贴 JSON
- 文件不存在 → 报 E2001 并停止
- 扩展名不识别 → 报 E2002 并停止
- 解析后无有效数据 → 报 E2004 并停止
- 空值率超标 → 报 E2005 并停止

---

## 4. 报告质量

### 4.1 分析章节
- 必须按 5 个 sysbench 场景独立输出
  （point_select / read_only / write_only / read_write / update_index）
- 禁止合并为均值

### 4.2 洞察分级
| 等级 | 含义 | 写入位置 |
|------|------|---------|
| L1 ✅ | Python 计算的客观事实 | 正文任意章节 |
| L2 📊 | 跨维度统计发现 | 正文任意章节 |
| L3 💡 | 数据模式推测 | 仅第 5 章「选型与调优建议」，必须标 `[待确认]` |

### 4.3 各报告类型最小图表数与结论数（A6 / D6 基线）
| report_type | 图表数 ≥ | 核心结论数 |
|-------------|---------|----------|
| single | 11（5 QPS 曲线 + 5 P95 曲线 + 1 峰值汇总） | 3-5 |
| comparison | 17 + N 产品 | 4-7 |
| iteration | 12 | 3-6（必含累计变化 + 至少 1 条回归 / 优化结论）|
| custom | 3 + custom_config 声明的额外图 | 2-4（必含主要发现 + 不确定性披露）|

### 4.4 各报告类型必含元素
- `comparison`：公平性说明（数据集 / 并发档 / 时长 / 硬件是否对等）
- `iteration`：趋势线、累计变化、回归点判断（默认阈值 5%）
- `single`：5 场景峰值、并发扩展性、P95 延迟稳定性
- `custom`：用户 focus_dimension 子节、不确定性披露

### 4.5 三格式独立生成要求
- `.md`：作为 source of truth 最先生成
- `.docx`：全文微软雅黑，表头浅蓝 #D9E2F3，图片完整嵌入
- `.html`：完整 head + 内联 CSS，中文字体 fallback 完整

### 4.6 文件大小达标下限（非质量上限）
- report.md ≥ 5KB
- report.docx ≥ 10KB
- report.html ≥ 8KB
> 说明：低于此线一定不合格；高于此线不代表优秀，内容质量仍需另行判定。

---

## 5. 红线行为（任一触发即判定不通过）

- ❌ 编造、估算、硬编码 TPS / QPS / P95 / P99 / duration 等性能数字
- ❌ 在数据未确认时强行生成正式报告
- ❌ 尝试连接内部数据库 / HTTP API / yunyu_test_results
- ❌ 用 task_id / plan_id / report_id 查询补全数据
- ❌ 将 5 个 sysbench 场景合并为均值输出
- ❌ L3 推测性洞察出现在第 1 / 2 / 3 / 4 章正文
- ❌ 用 pandoc 等工具将 md 转 docx / html（必须三格式独立生成）
- ❌ 中文业务术语原样作为筛选字段（必须做英文映射）
- ❌ 将"和 / 或"连接的不同场景误判为 AND 关系
- ❌ 报告中出现未替换的 `{X}` 占位符
