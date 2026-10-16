# -*- coding: utf-8 -*-
"""配置读取、数据加载与路径管理。"""
from pathlib import Path

import pandas as pd
import yaml

# 仓库根目录（main.py 所在目录）
ROOT = Path(__file__).resolve().parents[1]


def load_config(path: str | Path | None = None) -> dict:
    """读取 YAML 配置文件，默认读取仓库根目录下的 config.yaml。"""
    cfg_path = Path(path) if path else ROOT / "config.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_raw(cfg: dict) -> pd.DataFrame:
    """按配置加载原始问卷 CSV。"""
    raw_path = ROOT / cfg["data"]["raw_path"]
    if not raw_path.exists():
        raise FileNotFoundError(
            f"原始数据不存在: {raw_path}\n"
            f"请先运行: python scripts/generate_sample_data.py"
        )
    return pd.read_csv(raw_path, encoding="utf-8-sig")


def output_dir(cfg: dict) -> Path:
    """返回输出目录并确保其存在。"""
    out = ROOT / cfg["data"]["output_dir"]
    out.mkdir(parents=True, exist_ok=True)
    return out
