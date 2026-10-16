# -*- coding: utf-8 -*-
"""描述统计：分类变量频数表 + 数值/量表变量描述统计。"""
from __future__ import annotations

import pandas as pd


def frequency_table(df: pd.DataFrame, col: str, labels: dict | None = None) -> pd.DataFrame:
    """输出频数、百分比、有效百分比、累计百分比（含缺失行）。"""
    labels = labels or {}
    total = len(df)
    vc = df[col].value_counts(dropna=False).sort_index()

    rows = []
    valid_cum = 0.0
    valid_n = df[col].notna().sum()
    for value, count in vc.items():
        pct = count / total * 100
        if pd.isna(value):
            rows.append({"取值": "缺失", "频数": count, "百分比%": round(pct, 2),
                         "有效百分比%": "-", "累计百分比%": "-"})
            continue
        valid_pct = count / valid_n * 100 if valid_n else 0.0
        valid_cum += valid_pct
        name = labels.get(int(value), value)
        rows.append({
            "取值": f"{value} {name}".strip(),
            "频数": count,
            "百分比%": round(pct, 2),
            "有效百分比%": round(valid_pct, 2),
            "累计百分比%": round(valid_cum, 2),
        })
    rows.append({"取值": "合计", "频数": total, "百分比%": 100.0,
                 "有效百分比%": "-", "累计百分比%": "-"})
    return pd.DataFrame(rows)


def describe_numeric(df: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
    """
    columns: {列名: 展示名}，输出 N、均值、标准差、中位数、最小值、最大值、偏度。
    """
    rows = []
    for col, display in columns.items():
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        rows.append({
            "变量": display,
            "N": int(s.count()),
            "均值": round(s.mean(), 3),
            "标准差": round(s.std(ddof=1), 3),
            "中位数": round(s.median(), 3),
            "最小值": round(s.min(), 2),
            "最大值": round(s.max(), 2),
            "偏度": round(s.skew(), 3),
        })
    return pd.DataFrame(rows)
