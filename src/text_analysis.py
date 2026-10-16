# -*- coding: utf-8 -*-
"""开放题文本分析：jieba 分词 + 停用词过滤 + 关键词频次。"""
from __future__ import annotations

from collections import Counter
import logging

import pandas as pd
import jieba

jieba.setLogLevel(logging.WARNING)  # 避免分词库的 DEBUG 构建日志刷屏

# 小型内置停用词表（演示用，真实项目可替换为外部停用词文件）
STOPWORDS = set("的 了 和 是 我 就 都 而 而且 也 在 有 不 没 很 太 更 能 会 要 个 "
                "一些 一点 一个 这种 这个 那个 什么 怎么 因为 所以 但是 如果 还是 "
                "可能 应该 已经 比较 觉得 现在 自己 我们 你们 他们 产品 绿色 农产品".split())


def keyword_frequency(df: pd.DataFrame, text_col: str, top_n: int = 15) -> pd.DataFrame:
    """对开放题文本分词，返回前 top_n 个有效关键词的频次表。"""
    counter: Counter[str] = Counter()
    n_answers = 0
    for text in df[text_col].dropna():
        text = str(text).strip()
        if not text:
            continue
        n_answers += 1
        for word in jieba.lcut(text):
            word = word.strip()
            if len(word) >= 2 and word not in STOPWORDS:
                counter[word] += 1

    rows = [{"关键词": w, "出现次数": c} for w, c in counter.most_common(top_n)]
    result = pd.DataFrame(rows)
    result.attrs["n_answers"] = n_answers
    return result
