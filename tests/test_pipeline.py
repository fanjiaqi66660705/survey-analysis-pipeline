# -*- coding: utf-8 -*-
"""
核心分析逻辑的单元测试。
运行：pytest -q
"""
import numpy as np
import pandas as pd

from src.cleaning import clean, reverse_code
from src.crosstab_analysis import cramers_v
from src.reliability import cronbach_alpha


# ---------- 反向计分 ----------
def test_reverse_code():
    s = pd.Series([1, 2, 3, 4, 5])
    result = reverse_code(s, 1, 5).tolist()
    assert result == [5, 4, 3, 2, 1]


# ---------- Cronbach's α：完全一致的题项信度应为 1 ----------
def test_cronbach_alpha_perfect_reliability():
    items = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [1, 2, 3, 4, 5]})
    assert abs(cronbach_alpha(items) - 1.0) < 1e-9


def test_cronbach_alpha_known_value():
    # 两列正相关但不完全一致，alpha 应在 (0, 1) 且与手算方向一致
    items = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [2, 2, 3, 4, 4]})
    alpha = cronbach_alpha(items)
    assert 0 < alpha < 1


# ---------- Cramér's V：完全关联时 V=1，独立时 V=0 ----------
def test_cramers_v_extremes():
    assert abs(cramers_v(chi2=50.0, n=50, n_rows=2, n_cols=2) - 1.0) < 1e-9
    assert cramers_v(chi2=0.0, n=50, n_rows=2, n_cols=2) == 0.0


# ---------- 清洗：构造 4 份问卷覆盖四类质量问题 ----------
def _toy_raw():
    likert = ["Q3_1", "Q3_2", "Q3_3", "Q4_1", "Q4_2", "Q4_3", "Q5_1", "Q5_2"]
    # A/B 为答案各不相同的正常问卷（B 含一处越界值）；C 注意力失败；D 直线作答
    patterns = {
        "A": [5, 5, 4, 5, 3, 4, 5, 4],
        "B": [5, 4, 3, 4, 5, 3, 4, 5],
        "C": [2, 3, 2, 3, 2, 3, 2, 3],
        "D": [4, 4, 4, 4, 4, 4, 4, 4],
    }
    # 逐行构造 4 份问卷
    rows = []
    for sid in ["A", "B", "C", "D"]:
        row = dict(zip(likert, patterns[sid]))
        row.update({"id": sid, "Q1_性别": {"A": 1, "B": 2, "C": 1, "D": 2}[sid],
                    "Q2_学历": {"A": 3, "B": 3, "C": 2, "D": 4}[sid],
                    "Q6_购买": {"A": 1, "B": 0, "C": 1, "D": 1}[sid],
                    "Q7_年龄": {"A": 20, "B": 21, "C": 22, "D": 23}[sid],
                    "Q8_月支出": {"A": 1000, "B": 1100, "C": 1200, "D": 1300}[sid],
                    "Q9_attn": {"A": 3, "B": 3, "C": 1, "D": 3}[sid],
                    "Q10_open": ""})
        rows.append(row)
    df = pd.DataFrame(rows)
    df.loc[1, "Q3_1"] = 9        # B 出现越界值（置空后中位数插补，保留）
    return df


def _toy_config():
    return {
        "likert": {"min": 1, "max": 5},
        "reverse_items": ["Q3_2"],
        "scales": {
            "环保态度": ["Q3_1", "Q3_2", "Q3_3"],
            "质量信任": ["Q4_1", "Q4_2", "Q4_3"],
            "购买意愿": ["Q5_1", "Q5_2"],
        },
        "quality": {
            "attention_item": "Q9_attn",
            "attention_correct": 3,
            "straightline_items": ["Q3_1", "Q3_2", "Q3_3", "Q4_1",
                                   "Q4_2", "Q4_3", "Q5_1", "Q5_2"],
            "max_missing_ratio": 0.2,
        },
    }


def test_clean_quality_controls():
    df = _toy_raw()
    analytic, rep = clean(df, _toy_config())

    # C 注意力失败、D 直线作答 → 剔除；B 越界值单题插补后保留
    assert set(analytic["id"]) == {"A", "B"}
    assert rep["注意力检验失败剔除数"] == 1
    assert rep["直线作答剔除数"] == 1
    assert rep["越界值单元格数"] == 1

    # 反向计分题被翻转：A 原始 5 → 1
    assert analytic.loc[analytic["id"] == "A", "Q3_2"].iloc[0] == 1
    # 越界位置被中位数插补为 1-5 之间的合法值
    val = analytic.loc[analytic["id"] == "B", "Q3_1"].iloc[0]
    assert val in range(1, 6)
    # 量表合成分已生成且无缺失
    assert not analytic[["环保态度", "质量信任", "购买意愿"]].isna().any().any()
