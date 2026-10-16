# -*- coding: utf-8 -*-
"""图表输出（matplotlib/seaborn），统一中文字体与配色。"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # 服务器/无界面环境也能出图
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Windows 常见中文字体优先；找不到时退回 DejaVu（中文会乱码，日志里有提示）
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC",
                                   "PingFang SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
sns.set_theme(style="whitegrid", font=plt.rcParams["font.sans-serif"][0])

MAIN = "#2e7d5b"
ACCENT = "#c97b3c"


def purchase_rate_chart(df: pd.DataFrame, edu_col: str, purchase_col: str,
                        labels: dict, out: Path) -> Path:
    """不同学历组的购买率柱状图。"""
    rate = df.groupby(edu_col)[purchase_col].mean() * 100
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    bars = ax.bar([f"{v} {labels.get(v, '')}".strip() for v in rate.index],
                  rate.values, color=MAIN, width=0.55)
    for b, v in zip(bars, rate.values):
        ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.1f}%",
                ha="center", va="bottom", fontsize=10)
    ax.set_ylabel("已购买比例 (%)")
    ax.set_title("不同学历组的绿色农产品购买率")
    ax.set_ylim(0, max(rate.values) * 1.25)
    fig.tight_layout()
    path = out / "fig1_购买率_按学历.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def scale_box_chart(df: pd.DataFrame, scales: list[str], out: Path) -> Path:
    """各量表维度得分箱线图。"""
    long = df[scales].melt(var_name="维度", value_name="得分")
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    sns.boxplot(data=long, x="维度", y="得分", color=MAIN, ax=ax, width=0.5)
    ax.set_title("各量表维度得分分布（有效样本）")
    ax.set_ylim(1, 5)
    fig.tight_layout()
    path = out / "fig2_量表得分箱线图.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def corr_heatmap(df: pd.DataFrame, scales: list[str], out: Path) -> Path:
    """核心连续变量相关性热力图。"""
    cols = scales + ["Q7_年龄", "Q6_购买"]
    names = scales + ["年龄", "是否购买"]
    corr = df[cols].apply(pd.to_numeric, errors="coerce").corr()
    fig, ax = plt.subplots(figsize=(7, 5.5), dpi=150)
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdYlGn", center=0,
                xticklabels=names, yticklabels=names, ax=ax,
                cbar_kws={"shrink": 0.8})
    ax.set_title("核心变量 Pearson 相关系数矩阵")
    fig.tight_layout()
    path = out / "fig3_相关性热力图.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def keyword_bar_chart(keywords: pd.DataFrame, out: Path) -> Path | None:
    """开放题高频关键词条形图；无关键词时返回 None 而不是报错。"""
    if keywords.empty:
        return None
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)
    kw = keywords.iloc[::-1]  # 逆序让频次最高的在最上方
    ax.barh(kw["关键词"], kw["出现次数"], color=ACCENT)
    ax.set_xlabel("出现次数")
    ax.set_title("开放题高频关键词 TOP %d" % len(kw))
    fig.tight_layout()
    path = out / "fig4_开放题关键词.png"
    fig.savefig(path)
    plt.close(fig)
    return path
