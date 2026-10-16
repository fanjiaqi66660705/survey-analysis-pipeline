# -*- coding: utf-8 -*-
"""交叉分析：列联表 + 卡方独立性检验 + Cramér's V 关联强度。"""
from __future__ import annotations

import pandas as pd
from scipy import stats


def cramers_v(chi2: float, n: int, n_rows: int, n_cols: int) -> float:
    """Cramér's V：0 表示独立，1 表示完全关联。"""
    return float((chi2 / (n * (min(n_rows, n_cols) - 1))) ** 0.5)


def crosstab_analysis(df: pd.DataFrame, row: str, col: str,
                      row_labels: dict | None = None,
                      col_labels: dict | None = None) -> dict:
    """
    返回:
        table      : 列联表（含行合计）
        row_pct    : 行百分比表（用于堆积图）
        result     : 卡方检验结果 DataFrame（单行）
        conclusion : 一句话论文式结论
    """
    row_labels = row_labels or {}
    col_labels = col_labels or {}

    table = pd.crosstab(df[row], df[col])
    chi2, p, dof, expected = stats.chi2_contingency(table.values)
    n = table.values.sum()
    v = cramers_v(chi2, n, table.shape[0], table.shape[1])
    min_expected = float(expected.min())

    sig = "在 0.05 水平上显著" if p < 0.05 else "在 0.05 水平上不显著"
    conclusion = (
        f"卡方检验结果：χ²({dof}) = {chi2:.3f}，p = {p:.3f}，"
        f"两变量{sig}；Cramér's V = {v:.3f}，关联强度"
        + ("较弱。" if v < 0.3 else "中等。" if v < 0.5 else "较强。")
    )

    # 重命名索引/列，让输出表可读
    display = table.copy()
    display.index = [f"{idx} {row_labels.get(int(idx), '')}".strip() for idx in display.index]
    display.columns = [f"{c} {col_labels.get(int(c), '')}".strip() for c in display.columns]
    display["合计"] = display.sum(axis=1)
    display.loc["合计"] = display.sum(axis=0)

    row_pct = pd.crosstab(df[row], df[col], normalize="index") * 100
    row_pct.index = [f"{idx} {row_labels.get(int(idx), '')}".strip() for idx in row_pct.index]
    row_pct.columns = [f"{c} {col_labels.get(int(c), '')}".strip() for c in row_pct.columns]

    result = pd.DataFrame([{
        "χ²": round(chi2, 3),
        "自由度 df": dof,
        "p 值": round(p, 4),
        "Cramér's V": round(v, 3),
        "最小期望频数": round(min_expected, 2),
        "期望频数是否均≥5": "是" if min_expected >= 5 else "否（建议配合 Fisher 检验或合并类别）",
        "检验结论": sig,
    }])

    return {"table": display, "row_pct": row_pct.round(2), "result": result,
            "conclusion": conclusion}
