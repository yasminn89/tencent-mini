#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db_report 测试用例集自检脚本（Meta-Testcase 自动部分）
检查 M1 覆盖完整性 / M2 评分可判定性 / M4 用例独立性。
用法: python meta_check.py testcases.yaml
"""
import sys
import re
import yaml
from collections import Counter

REQUIRED_REPORT_TYPES = {"single", "comparison", "iteration", "custom"}
REQUIRED_CATEGORIES = {"正常路径", "边界", "失败路径", "红线"}
RUBRIC_TAGS = re.compile(r"\b(D[1-5]|R[1-5])\b")


def load_cases(path):
    data = yaml.safe_load(open(path, encoding="utf-8"))
    return data.get("cases", [])


def check_m1(cases):
    """覆盖完整性"""
    results = []
    rtypes = {c.get("report_type") for c in cases}
    miss_rt = REQUIRED_REPORT_TYPES - rtypes
    results.append(("M1.1 report_type 四类全覆盖",
                    not miss_rt, f"缺: {miss_rt}" if miss_rt else "OK"))

    cats = {c.get("category") for c in cases}
    miss_cat = REQUIRED_CATEGORIES - cats
    results.append(("M1.2 category 四类全覆盖",
                    not miss_cat, f"缺: {miss_cat}" if miss_cat else "OK"))

    blob = yaml.dump(cases, allow_unicode=True)
    has_r1 = "R1" in blob
    has_r3 = "R3" in blob
    results.append(("M1.3 红线 R1/R3 至少各覆盖 1 条",
                    has_r1 and has_r3,
                    f"R1={has_r1}, R3={has_r3}"))

    # 数据源类型覆盖：从 ExpectedOutput / ProcessChecks 文本里找
    blob2 = blob
    ds_ok = all(k in blob2 for k in
                ["local_file", "local_data", "keyword_only"])
    results.append(("M1.4 数据源类型三类全覆盖",
                    ds_ok, "OK" if ds_ok else "缺某数据源类型"))
    return results


def check_m2(cases):
    """评分可判定性"""
    results = []
    all_fields_ok = True
    no_tag = []
    for c in cases:
        for f in ("Input", "ExpectedOutput", "Judge"):
            if not c.get(f) or not str(c.get(f)).strip():
                all_fields_ok = False
        if not RUBRIC_TAGS.search(str(c.get("Judge", ""))):
            no_tag.append(c.get("id"))
    results.append(("M2.1 每条含非空 Input/ExpectedOutput/Judge",
                    all_fields_ok, "OK" if all_fields_ok else "有空字段"))
    results.append(("M2.2 每条 Judge 引用 ≥1 个 Rubrics 标记",
                    not no_tag, f"缺标记: {no_tag}" if no_tag else "OK"))

    # 红线/失败用例需含反例对照或 redline_check
    miss_counter = []
    for c in cases:
        if c.get("category") in ("红线", "失败路径"):
            j = str(c.get("Judge", ""))
            if ("反例" not in j) and ("redline_check" not in j):
                miss_counter.append(c.get("id"))
    results.append(("M2.3 红线/失败用例含反例对照说明",
                    not miss_counter,
                    f"缺: {miss_counter}" if miss_counter else "OK"))
    return results


def check_m4(cases):
    """用例独立性"""
    results = []
    ids = [c.get("id") for c in cases]
    dup_id = [i for i, n in Counter(ids).items() if n > 1]
    results.append(("M4.1 用例 id 唯一",
                    not dup_id, f"重复: {dup_id}" if dup_id else "OK"))

    inputs = [str(c.get("Input", "")).strip() for c in cases]
    dup_in = [i for i, n in Counter(inputs).items() if n > 1]
    results.append(("M4.3 无完全相同的 Input",
                    not dup_in, "OK" if not dup_in else "有重复 Input"))

    # M4.2 依赖检查：Input 中不应引用其它用例 id
    dep = []
    for c in cases:
        if re.search(r"TC-\d+", str(c.get("Input", ""))):
            dep.append(c.get("id"))
    results.append(("M4.2 用例 Input 自包含（不引用其它用例）",
                    not dep, f"有依赖: {dep}" if dep else "OK"))
    return results


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "testcases.yaml"
    cases = load_cases(path)
    print(f"=== db_report 用例集自检 (共 {len(cases)} 条) ===\n")

    all_pass = True
    for name, fn in [("M1 覆盖完整性", check_m1),
                     ("M2 评分可判定性", check_m2),
                     ("M4 用例独立性", check_m4)]:
        print(f"【{name}】")
        for item, ok, detail in fn(cases):
            flag = "PASS" if ok else "FAIL"
            if not ok:
                all_pass = False
            print(f"  [{flag}] {item}  — {detail}")
        print()

    print("=" * 40)
    print("总结论:", "✅ 自动自检全部通过" if all_pass
          else "❌ 存在 FAIL，需修订用例")
    print("提示: M3 反例有效性 / M5 基座无关性 需人工评审（见 meta_testcase.md）")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
