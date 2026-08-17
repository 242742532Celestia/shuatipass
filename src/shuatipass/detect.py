"""
shuatipass 自动检测 —— 根据 PDF 内容判断用哪个配置

检测方法：
1. 提取前 3 页文本
2. 关键词匹配
3. 返回最匹配的内置配置名

简单但有效 —— 覆盖 90% 场景。
复杂场景用户用 --preset/--config 显式指定。
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional

# 尝试导入 pymupdf（detect 阶段不依赖 shuatipass 主包）
try:
    import pymupdf
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


# 配置特征关键词
DETECTION_RULES = [
    # (config_name, keywords, weight, min_hits)
    ("xuekewang", [
        "学科网", "xueke100", "xueke", "北京）股份", "股 份有限",
    ], 3, 2),
    ("zujuan", [
        "组卷网", "zujuan", "zujuan.com", "学科网组卷", "组卷",
    ], 3, 2),
    ("textbook", [
        "人教版", "北师大版", "苏教版", "沪教版", "浙教版", "粤教版",
        "鲁教版", "教科版", "冀教版",
    ], 2, 1),
]


def detect_config(pdf_path: str | Path, sample_pages: int = 3) -> Optional[str]:
    """
    自动检测 PDF 来源，返回最匹配的配置名。

    Args:
        pdf_path: PDF 路径
        sample_pages: 取前 N 页文本检测（默认 3 页够用）

    Returns:
        配置名（"xuekewang" / "zujuan" / "textbook" / "generic"），
        无法识别时返回 "generic"。

    Raises:
        ImportError: pymupdf 未装
        FileNotFoundError: PDF 不存在
    """
    if not HAS_PYMUPDF:
        raise ImportError("需要 pymupdf: pip install PyMuPDF")

    p = Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(f"PDF 不存在: {p}")

    doc = pymupdf.open(str(p))
    pages_to_read = min(sample_pages, len(doc))

    # 收集前 N 页文本
    sample_text = ""
    for i in range(pages_to_read):
        sample_text += doc[i].get_text() + "\n"
    doc.close()

    # 评分
    scores = {}
    for cfg_name, keywords, weight, min_hits in DETECTION_RULES:
        hits = sum(1 for kw in keywords if kw in sample_text)
        if hits >= min_hits:
            scores[cfg_name] = hits * weight

    if not scores:
        return "generic"

    # 最高分
    best = max(scores.items(), key=lambda x: x[1])
    return best[0]


def detect_with_details(pdf_path: str | Path) -> dict:
    """
    检测 + 返回详细信息（用于调试 / 用户展示）
    """
    if not HAS_PYMUPDF:
        raise ImportError("需要 pymupdf: pip install PyMuPDF")

    p = Path(pdf_path)
    doc = pymupdf.open(str(p))
    sample_text = ""
    for i in range(min(3, len(doc))):
        sample_text += doc[i].get_text() + "\n"
    doc.close()

    result = {
        "recommended": detect_config(p),
        "scores": {},
    }
    for cfg_name, keywords, weight, min_hits in DETECTION_RULES:
        hits = sum(1 for kw in keywords if kw in sample_text)
        result["scores"][cfg_name] = {
            "hits": hits,
            "weight": weight,
            "score": hits * weight if hits >= min_hits else 0,
            "matched_keywords": [kw for kw in keywords if kw in sample_text],
        }
    return result
