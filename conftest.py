# -*- coding: utf-8 -*-
"""pytest 全局配置：把仓库根目录加入 sys.path，使测试可以 import src 包。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
