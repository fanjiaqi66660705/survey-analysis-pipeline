# -*- coding: utf-8 -*-
"""量表信度分析：Cronbach's α 与“删除该题后的 α”。"""
from __future__ import annotations

import numpy as np
import pandas as pd


def cronbach_alpha(items: pd.DataFrame) -> float:
    """
    Cronbach's α = k/(k-1) * (1 - Σ方差(各题) / 方差(总分))
    """
    data = items.dropna().astype(float)
    k = data.shape[1]
    if k < 2:
        return float("nan")
    item_var_sum = data.var(axis=0, ddof=1).sum()
    total_var = data.sum(axis=1).var(ddof=1)
    if total_var == 0:
        return float("nan")
    return float(k / (k - 1) * (1 - item_var_sum / total_var))


def item_total_corr(items: pd.DataFrame) -> pd.Series:
    """校正的项总计相关性：该题与“其余题项总分”的 Pearson 相关。"""
    corrs = {}
    for col in items.columns:
        rest = items.drop(columns=[col]).sum(axis=1)
        corrs[col] = np.corrcoef(items[col].astype(float), rest.astype(float))[0, 1]
    return pd.Series(corrs)


def reliability_table(scales: dict, df: pd.DataFrame) -> pd.DataFrame:
    """
    对每个量表维度输出：题数、Cronbach's α、删除后 α 区间、判定建议。
    """
    rows = []
    for name, items in scales.items():
        data = df[items].astype(float)
        alpha = cronbach_alpha(data)
        if len(items) == 2:
            alpha_range = "—（两题量表不适用）"
        else:
            alpha_if_deleted = {
                col: cronbach_alpha(data.drop(columns=[col])) for col in items
            }
            alpha_range = f"{min(alpha_if_deleted.values()):.3f} ~ {max(alpha_if_deleted.values()):.3f}"
        if alpha >= 0.8:
            verdict = "信度良好"
        elif alpha >= 0.7:
            verdict = "信度可接受"
        elif alpha >= 0.6:
            verdict = "信度一般，需说明"
        else:
            verdict = "信度不足，需修订题项"
        rows.append({
            "量表维度": name,
            "题项数": len(items),
            "Cronbach's α": round(alpha, 3),
            "删除单题后α范围": alpha_range,
            "判定": verdict,
        })
    return pd.DataFrame(rows)
