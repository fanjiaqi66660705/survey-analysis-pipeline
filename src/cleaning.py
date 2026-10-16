# -*- coding: utf-8 -*-
"""
问卷数据清洗与质量控制。

处理顺序（顺序本身有讲究，不能乱）：
  1. 越界值置空（五级量表出现 1-5 之外的值）
  2. 记录直线作答（所有量表题答案完全一致）
  3. 反向计分题翻转
  4. 缺失过多的问卷整份剔除；其余用题项中位数插补
  5. 注意力检验题失败者剔除
  6. 计算各量表维度合成分（题项均值）
"""
from __future__ import annotations

import pandas as pd


def reverse_code(series: pd.Series, min_score: int, max_score: int) -> pd.Series:
    """反向计分：新值 = min + max - 原值。"""
    return min_score + max_score - series


def clean(df: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, dict]:
    """
    返回:
        analytic : 可用于统计分析的干净数据（含量表合成分）
        report   : 清洗各环节的样本量与剔除原因统计
    """
    likert_min = cfg["likert"]["min"]
    likert_max = cfg["likert"]["max"]
    reverse_items = cfg.get("reverse_items", [])
    scales: dict = cfg["scales"]
    q = cfg["quality"]

    scale_items: list[str] = [c for items in scales.values() for c in items]
    straight_items: list[str] = q["straightline_items"]
    attn_item: str = q["attention_item"]
    attn_correct = q["attention_correct"]
    max_missing_ratio: float = q["max_missing_ratio"]

    report: dict = {"原始样本量": len(df)}
    work = df.copy()

    # ---- 1. 越界值置空 ----
    invalid_cells = 0
    for col in scale_items:
        bad = work[col].notna() & ~work[col].between(likert_min, likert_max)
        invalid_cells += int(bad.sum())
        work.loc[bad, col] = pd.NA
    report["越界值单元格数"] = invalid_cells

    # ---- 2. 直线作答检测（在插补之前判断，否则会被中位数掩盖）----
    straight_mask = pd.Series(False, index=work.index)
    valid_resp = work[straight_items].notna().sum(axis=1)
    nunique = work[straight_items].nunique(axis=1)
    straight_mask = (valid_resp >= 5) & (nunique == 1)
    report["直线作答剔除数"] = int(straight_mask.sum())

    # ---- 3. 反向计分翻转 ----
    for col in reverse_items:
        work[col] = reverse_code(pd.to_numeric(work[col], errors="coerce"),
                                 likert_min, likert_max)

    # ---- 4. 缺失处理 ----
    missing_ratio = work[scale_items].isna().sum(axis=1) / len(scale_items)
    too_many_missing = missing_ratio > max_missing_ratio
    report["缺失过多剔除数"] = int(too_many_missing.sum())
    work = work.loc[~too_many_missing].copy()
    straight_mask = straight_mask.loc[work.index]

    # 剩余缺失用题项中位数插补（量表分析中最常用的保守做法）
    imputed_cells = 0
    for col in scale_items:
        n_miss = int(work[col].isna().sum())
        if n_miss:
            median = work[col].median()
            work[col] = work[col].fillna(median)
            imputed_cells += n_miss
    report["中位数插补单元格数"] = imputed_cells

    # ---- 5. 注意力检验 ----
    attn_fail = pd.to_numeric(work[attn_item], errors="coerce") != attn_correct
    report["注意力检验失败剔除数"] = int(attn_fail.sum())

    # ---- 6. 合成分析样本 ----
    keep = (~straight_mask) & (~attn_fail)
    analytic = work.loc[keep].copy()
    report["有效分析样本量"] = len(analytic)
    report["累计剔除率"] = f"{(1 - len(analytic) / report['原始样本量']) * 100:.1f}%"

    # ---- 7. 量表合成分（题项均值）----
    for name, items in scales.items():
        analytic[name] = analytic[items].mean(axis=1)

    return analytic.reset_index(drop=True), report
