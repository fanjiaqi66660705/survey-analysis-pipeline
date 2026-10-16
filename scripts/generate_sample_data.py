# -*- coding: utf-8 -*-
"""
生成一份带典型质量问题的仿真问卷数据（固定随机种子，可复现）。

运行方式：
    python scripts/generate_sample_data.py

输出：
    data/raw/sample_survey.csv （N=320）

重要声明：
    本数据为算法生成的仿真数据，仅用于演示分析管线能否跑通，
    不代表任何真实调研结论。接入真实问卷后，由同一套代码重算即可。

仿真数据中故意埋入的“脏数据”类型：
    1) 量表题缺失（空值）
    2) 越界值（五级量表出现 9）
    3) 直线作答（8 道量表题全部选同一个选项）
    4) 注意力检验题答错
    5) 数值型题项缺失（月支出）
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20261016
N = 320

# 开放题候选回答（用于文本分词与关键词统计演示）
OPEN_ANSWERS = [
    "绿色农产品价格比普通的贵不少，我只会偶尔购买",
    "最担心买到假冒认证的产品，现在标识太多看不懂",
    "包装上认证标识太多了，分不清有机和绿色的区别",
    "平时买菜的渠道很少看到卖绿色农产品的",
    "总体比较信任大品牌的绿色产品，小牌子不敢买",
    "希望政府能加强监管，查得更严一些",
    "物流配送太慢，到手的时候已经不新鲜了",
    "不知道怎么辨别真假认证，只能看价格猜",
    "只要能保证安全，愿意为绿色农产品多付一点钱",
    "感觉概念炒作的成分居多，实际差别可能不大",
    "担心造假，溯源二维码扫了也不一定是真的",
    "商超里的绿色蔬菜价格太贵，希望多一些补贴",
]


def likert_from_latent(latent: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """把潜在态度变量映射为 1-5 级量表作答，并加入随机作答噪声。"""
    score = 3 + np.round(latent * 0.9 + rng.normal(0, 0.4, size=len(latent)))
    return np.clip(score, 1, 5).astype(int)


def main() -> None:
    rng = np.random.default_rng(SEED)

    # ---- 1. 人口学变量 ----
    gender = rng.integers(1, 3, size=N)                                   # 1 男 / 2 女
    edu = rng.choice([1, 2, 3, 4], size=N, p=[0.18, 0.22, 0.42, 0.18])   # 学历 1-4
    age = np.clip(rng.normal(29, 8, size=N).round(), 17, 60).astype(int)

    # ---- 2. 潜在态度 → 各量表作答（学历越高环保态度略强）----
    attitude = rng.normal(0, 1, size=N) + 0.28 * (edu - 2.5)
    trust = 0.55 * attitude + rng.normal(0, 0.85, size=N)
    intent = 0.55 * attitude + 0.45 * trust + rng.normal(0, 0.7, size=N)

    q3_1 = likert_from_latent(attitude, rng)
    q3_2 = likert_from_latent(-attitude, rng)   # 反向表述题：态度越积极越不认同
    q3_3 = likert_from_latent(attitude, rng)
    q4_1 = likert_from_latent(trust, rng)
    q4_2 = likert_from_latent(trust, rng)
    q4_3 = likert_from_latent(trust, rng)
    q5_1 = likert_from_latent(intent, rng)
    q5_2 = likert_from_latent(intent, rng)

    # ---- 3. 购买行为（0/1），意愿越强购买概率越高 ----
    prob = 1.0 / (1.0 + np.exp(-(0.85 * intent - 0.2)))
    purchase = (rng.random(N) < prob).astype(int)

    # ---- 4. 月支出（部分缺失）----
    spend = (1200 + 8 * (age - 25) + rng.normal(0, 300, size=N)).round(-1)

    # ---- 5. 注意力检验题（正确答案为 3，少数人答错）----
    attention = np.full(N, 3, dtype=int)
    wrong_idx = rng.choice(N, size=30, replace=False)
    attention[wrong_idx] = rng.choice([1, 2, 4, 5], size=30)

    df = pd.DataFrame({
        "id": [f"S{idx:04d}" for idx in range(1, N + 1)],
        "Q1_性别": gender,
        "Q2_学历": edu,
        "Q3_1": q3_1,
        "Q3_2": q3_2,
        "Q3_3": q3_3,
        "Q4_1": q4_1,
        "Q4_2": q4_2,
        "Q4_3": q4_3,
        "Q5_1": q5_1,
        "Q5_2": q5_2,
        "Q6_购买": purchase,
        "Q7_年龄": age,
        "Q8_月支出": spend,
        "Q9_attn": attention,
        "Q10_open": rng.choice(OPEN_ANSWERS, size=N),
    })

    likert_cols = ["Q3_1", "Q3_2", "Q3_3", "Q4_1", "Q4_2", "Q4_3", "Q5_1", "Q5_2"]

    # ---- 6. 注入脏数据 ----
    # (a) 量表题随机缺失
    for _ in range(18):
        i, col = rng.integers(0, N), likert_cols[rng.integers(0, len(likert_cols))]
        df.loc[i, col] = np.nan
    # (b) 越界值
    bad_idx = rng.choice(N, size=8, replace=False)
    df.loc[bad_idx, "Q3_1"] = 9
    # (c) 直线作答：8 道量表题全部相同
    straight_idx = rng.choice(N, size=12, replace=False)
    for i in straight_idx:
        df.loc[i, likert_cols] = rng.integers(1, 6)
    # (d) 月支出缺失
    miss_spend = rng.choice(N, size=28, replace=False)
    df.loc[miss_spend, "Q8_月支出"] = np.nan

    out = Path(__file__).resolve().parents[1] / "data" / "raw"
    out.mkdir(parents=True, exist_ok=True)
    target = out / "sample_survey.csv"
    df.to_csv(target, index=False, encoding="utf-8-sig")
    print(f"[OK] 仿真问卷已生成: {target}  (N={N}, 含缺失/越界/直线作答/注意力失败)")


if __name__ == "__main__":
    main()
