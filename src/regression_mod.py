# -*- coding: utf-8 -*-
"""二元 Logistic 回归（购买行为的影响因素分析）。"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


def logistic_regression(df: pd.DataFrame, dependent: str, predictors: list[str],
                        predictor_labels: dict[str, str] | None = None) -> tuple[pd.DataFrame, dict]:
    """
    拟合 Logit 模型，输出回归系数表（B、SE、Wald-z、p、OR、OR 95%CI）。
    分类预测变量按问卷编码作为连续变量处理（适合定序变量，如学历 1-4）。
    """
    predictor_labels = predictor_labels or {}
    cols = [dependent] + predictors
    data = df[cols].apply(pd.to_numeric, errors="coerce").dropna()

    y = data[dependent].astype(int)
    X = sm.add_constant(data[predictors])
    model = sm.Logit(y, X).fit(disp=False, maxiter=200)

    conf = model.conf_int()
    table = pd.DataFrame({
        "变量": [predictor_labels.get(c, c) for c in model.params.index],
        "回归系数B": model.params.round(3).values,
        "标准误SE": model.bse.round(3).values,
        "Wald z": (model.params / model.bse).round(3).values,
        "p值": model.pvalues.round(4).values,
        "OR值": np.exp(model.params).round(3).values,
        "OR 95%CI下限": np.exp(conf[0]).round(3).values,
        "OR 95%CI上限": np.exp(conf[1]).round(3).values,
        "显著性": ["***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
                  for p in model.pvalues],
    })
    meta = {
        "样本量N": int(len(data)),
        "Pseudo R²": round(float(model.prsquared), 3),
        "模型p值": round(float(model.llr_pvalue), 4),
    }
    return table, meta
