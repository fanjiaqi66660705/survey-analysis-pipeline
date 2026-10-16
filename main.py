# -*- coding: utf-8 -*-
"""
问卷数据分析管线 · 一键入口
============================

使用方式：
    python main.py                 # 使用 config.yaml 跑完整流程
    python main.py --config x.yaml # 指定其他配置

流程：原始数据 → 质量控制清洗 → 信度 → 描述统计 → 卡方 → Logistic 回归
      → 开放题文本 → 图表 → Word 三线表报告
所有结果输出到 outputs/ 目录。
"""
import argparse
import logging
import sys

from src import charts, crosstab_analysis as crosstab_mod
from src import descriptives, reliability, report, text_analysis
from src.cleaning import clean
from src.io_utils import load_config, load_raw, output_dir
from src.regression_mod import logistic_regression

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("pipeline")


def run(config_path: str | None = None) -> None:
    cfg = load_config(config_path)
    out = output_dir(cfg)

    # 1. 读取与清洗
    log.info("1/8 读取原始数据 ...")
    raw = load_raw(cfg)
    log.info("    原始样本量 N=%d，字段数=%d", len(raw), raw.shape[1])

    log.info("2/8 数据质量控制与清洗 ...")
    analytic, clean_report = clean(raw, cfg)
    for k, v in clean_report.items():
        log.info("    %s: %s", k, v)
    analytic.to_csv(out / "cleaned_data.csv", index=False, encoding="utf-8-sig")

    # 3. 信度
    log.info("3/8 信度分析 ...")
    rel = reliability.reliability_table(cfg["scales"], analytic)
    rel.to_csv(out / "01_信度分析.csv", index=False, encoding="utf-8-sig")
    log.info("\n%s", rel.to_string(index=False))

    # 4. 描述统计
    log.info("4/8 描述统计 ...")
    labels = cfg.get("value_labels", {})
    for col in cfg["descriptives"]["categorical"]:
        freq = descriptives.frequency_table(analytic, col, labels.get(col))
        fname = f"02_频数_{col}.csv"
        freq.to_csv(out / fname, index=False, encoding="utf-8-sig")
    freq_edu = descriptives.frequency_table(analytic, "Q2_学历", labels.get("Q2_学历"))

    numeric_cols = {c: c for c in cfg["descriptives"]["numeric"]}
    numeric_cols.update({name: f"{name}得分" for name in cfg["scales"]})
    desc = descriptives.describe_numeric(analytic, numeric_cols)
    desc.to_csv(out / "03_描述统计.csv", index=False, encoding="utf-8-sig")

    # 5. 交叉分析 + 卡方
    log.info("5/8 交叉分析与卡方检验 ...")
    ct_cfg = cfg["crosstabs"][0]
    cross = crosstab_mod.crosstab_analysis(
        analytic, ct_cfg["row"], ct_cfg["col"],
        labels.get(ct_cfg["row"]), labels.get(ct_cfg["col"]),
    )
    cross["table"].to_csv(out / "04_列联表.csv", encoding="utf-8-sig")
    cross["row_pct"].to_csv(out / "04_行百分比表.csv", encoding="utf-8-sig")
    cross["result"].to_csv(out / "04_卡方检验.csv", index=False, encoding="utf-8-sig")
    log.info("    %s", cross["conclusion"])

    # 6. Logistic 回归
    log.info("6/8 Logistic 回归 ...")
    reg_cfg = cfg["regression"]
    reg_table, reg_meta = logistic_regression(
        analytic, reg_cfg["dependent"], reg_cfg["predictors"],
        reg_cfg.get("predictor_labels"),
    )
    reg_table.to_csv(out / "05_logistic回归.csv", index=False, encoding="utf-8-sig")
    log.info("    %s", reg_meta)

    # 7. 开放题文本
    log.info("7/8 开放题文本分词 ...")
    ot_cfg = cfg["open_text"]
    keywords = text_analysis.keyword_frequency(analytic, ot_cfg["item"], ot_cfg["top_n"])
    keywords.to_csv(out / "06_开放题关键词.csv", index=False, encoding="utf-8-sig")

    # 8. 图表
    log.info("8/8 生成图表与 Word 报告 ...")
    fig_rate = charts.purchase_rate_chart(
        analytic, "Q2_学历", "Q6_购买", labels.get("Q2_学历", {}), out)
    fig_box = charts.scale_box_chart(analytic, list(cfg["scales"].keys()), out)
    fig_corr = charts.corr_heatmap(analytic, list(cfg["scales"].keys()), out)
    fig_kw = charts.keyword_bar_chart(keywords, out)

    context = {
        "clean_report": clean_report,
        "reliability": rel,
        "freq_edu": freq_edu,
        "describe": desc,
        "crosstab": cross,
        "regression_table": reg_table,
        "regression_meta": reg_meta,
        "keywords": keywords,
        "fig_purchase_rate": fig_rate,
        "fig_scale_box": fig_box,
        "fig_corr": fig_corr,
        "fig_keywords": fig_kw,
    }
    docx_path = report.build_report(context, out)

    log.info("全部完成 ✅  共 %d 个有效样本，结果目录: %s", len(analytic), out)
    log.info("Word 报告: %s", docx_path.name)


def main() -> int:
    parser = argparse.ArgumentParser(description="问卷数据自动分析管线")
    parser.add_argument("--config", default=None, help="配置文件路径（默认 config.yaml）")
    args = parser.parse_args()
    try:
        run(args.config)
    except Exception as exc:  # 顶层兜底：把错误打印清楚，方便定位
        log.error("管线运行失败: %s", exc, exc_info=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
