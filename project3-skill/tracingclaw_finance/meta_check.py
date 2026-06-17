#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tracingclaw_finance 测试用例集自检脚本（Meta-Testcase 自动部分）
检查 M1 覆盖完整性 / M2 评分可判定性 / M4 用例独立性 / M5.1 数值无关性。
用法: python meta_check.py testcases.yaml
"""
import sys
import re
import yaml
from collections import Counter

REQUIRED_INTENTS = {"财报类", "行情类", "研报类", "纯问题求证"}
REQUIRED_CATEGORIES = {"正常路径", "边界", "失败路径", "红线"}
RUBRIC_TAGS = re.compile(r"\b(D[1-5]|R[1-5])\b")
# 数值断言措辞（M5.1 应避免出现在 Judge 中）
NUMERIC_ASSERT = re.compile(r"(必须等于|应为\s*\d|准确数字为|数值必须是|等于\s*\d+\s*亿)")


def load_cases(path):
    return yaml.safe_load(open(path, encoding="utf-8")).get("cases", [])


def check_m1(cases):
    results = []
    intents = {c.get("intent_type") for c in cases}
    miss_i = REQUIRED_INTENTS - intents
    results.append(("M1.1 intent_type 四类全覆盖",
                    not miss_i, f"缺: {miss_i}" if miss_i else "OK"))

    cats = {c.get("category") for c in cases}
    miss_c = REQUIRED_CATEGORIES - cats
    results.append(("M1.2 category 四类全覆盖",
                    not miss_c, f"缺: {miss_c}" if miss_c else "OK"))

    blob = yaml.dump(cases, allow_unicode=True)
    rl = {tag: (tag in blob) for tag in ("R1", "R2", "R5")}
    results.append(("M1.3 红线 R1/R2/R5 各覆盖 ≥1 条",
                    all(rl.values()), str(rl)))

    tools_ok = ("westock-data" in blob) and ("mx-finance-search" in blob)
    results.append(("M1.4 两个工具均被用例涉及",
                    tools_ok, "OK" if tools_ok else "缺工具覆盖"))
    return results


def check_m2(cases):
    results = []
    fields_ok = True
    no_tag = []
    for c in cases:
        for f in ("Input", "ExpectedOutput", "Judge"):
            if not c.get(f) or not str(c.get(f)).strip():
                fields_ok = False
        if not RUBRIC_TAGS.search(str(c.get("Judge", ""))):
            no_tag.append(c.get("id"))
    results.append(("M2.1 每条含非空 Input/ExpectedOutput/Judge",
                    fields_ok, "OK" if fields_ok else "有空字段"))
    results.append(("M2.2 每条 Judge 引用 ≥1 个 Rubrics 标记",
                    not no_tag, f"缺标记: {no_tag}" if no_tag else "OK"))

    miss = []
    for c in cases:
        if c.get("category") in ("红线", "失败路径"):
            j = str(c.get("Judge", ""))
            if ("反例" not in j) and ("redline_check" not in j):
                miss.append(c.get("id"))
    results.append(("M2.3 红线/失败用例含反例对照说明",
                    not miss, f"缺: {miss}" if miss else "OK"))
    return results


def check_m4(cases):
    results = []
    ids = [c.get("id") for c in cases]
    dup = [i for i, n in Counter(ids).items() if n > 1]
    results.append(("M4.1 用例 id 唯一", not dup,
                    f"重复: {dup}" if dup else "OK"))

    inputs = [str(c.get("Input", "")).strip() for c in cases]
    dup_in = [i for i, n in Counter(inputs).items() if n > 1]
    results.append(("M4.3 无完全相同的 Input", not dup_in,
                    "OK" if not dup_in else "有重复 Input"))

    dep = [c.get("id") for c in cases
           if re.search(r"TC-\d+", str(c.get("Input", "")))]
    results.append(("M4.2 用例 Input 自包含", not dep,
                    f"有依赖: {dep}" if dep else "OK"))
    return results


def check_m5(cases):
    """数值无关性：Judge 不应出现精确数值断言措辞"""
    results = []
    bad = []
    for c in cases:
        if NUMERIC_ASSERT.search(str(c.get("Judge", ""))):
            bad.append(c.get("id"))
    results.append(("M5.1 Judge 不断言精确金融数值",
                    not bad, f"含数值断言: {bad}" if bad else "OK"))
    return results


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "testcases.yaml"
    cases = load_cases(path)
    print(f"=== tracingclaw 用例集自检 (共 {len(cases)} 条) ===\n")

    all_pass = True
    for name, fn in [("M1 覆盖完整性", check_m1),
                     ("M2 评分可判定性", check_m2),
                     ("M4 用例独立性", check_m4),
                     ("M5.1 数值无关性", check_m5)]:
        print(f"【{name}】")
        for item, ok, detail in fn(cases):
            if not ok:
                all_pass = False
            print(f"  [{'PASS' if ok else 'FAIL'}] {item}  — {detail}")
        print()

    print("=" * 40)
    print("总结论:", "✅ 自动自检全部通过" if all_pass
          else "❌ 存在 FAIL，需修订用例")
    print("提示: M3 反例有效性 / M5 基座无关 需人工评审（见 meta_testcase.md）")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
