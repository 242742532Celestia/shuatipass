"""
shuatipass 公式 OCR —— 把 PDF 里的公式图片转 LaTeX

设计：
1. 默认不集成（保持轻量）
2. 可选安装: pip install shuatipass[ocr]
3. 支持 Mathpix API（主推，准确率高，需 API key）
4. 预留 pix2tex 接口（本地，免费，依赖 PyTorch）

用法：
    from shuatipass.ocr import MathpixOCR, ocr_questions

    # 1. 初始化（用户需要先去 https://mathpix.com/ 申请 API key）
    ocr = MathpixOCR(app_id="xxx", app_key="yyy")

    # 2. 批量识别
    results = ocr_questions(ocr, "questions.json", "images/", "output.json")

JSON 字段扩展：
    question.formula_latex: "F = ma"  # 公式对应的 LaTeX
    question.formula_confidence: 0.95   # 置信度
"""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from typing import Protocol

# 顶层 import（方便 patch 测试）
try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class OCRError(Exception):
    """OCR 基础异常"""

    pass


class FormulaOCR(Protocol):
    """公式 OCR 接口协议（duck typing）"""

    def recognize(self, image_path: str | Path) -> tuple[str, float]:
        """
        识别一张图片里的公式。

        Args:
            image_path: 图片路径

        Returns:
            (latex, confidence) 元组
        """
        ...

    @property
    def name(self) -> str:
        """OCR 引擎名（用于显示）"""
        ...


class MathpixOCR:
    """
    Mathpix API 客户端

    注册: https://mathpix.com/
    计费: 免费 1000 次/月，学生包 $4.99/月 = 5000 次

    文档: https://docs.mathpix.com/
    """

    API_URL = "https://api.mathpix.com/v3/text"

    def __init__(self, app_id: str, app_key: str, timeout: int = 30):
        if not app_id or not app_key:
            raise OCRError("Mathpix 需要 app_id 和 app_key")
        self.app_id = app_id
        self.app_key = app_key
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "mathpix"

    def recognize(self, image_path: str | Path) -> tuple[str, float]:
        """
        调用 Mathpix API 识别图片里的公式

        返回 (latex, confidence)
        """
        if not HAS_REQUESTS:
            raise OCRError("需要安装 requests: pip install requests")

        p = Path(image_path)
        if not p.exists():
            raise OCRError(f"图片不存在: {p}")

        # base64 编码图片
        image_b64 = base64.b64encode(p.read_bytes()).decode()

        headers = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "Content-Type": "application/json",
        }
        payload = {
            "src": f"data:image/{p.suffix.lstrip('.')};base64,{image_b64}",
            "formats": ["latex_styled"],
            "data_options": {
                "include_asciimath": False,
                "include_latex": True,
            },
        }

        resp = requests.post(
            self.API_URL,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            raise OCRError(f"Mathpix API 错误 {resp.status_code}: {resp.text}")

        data = resp.json()
        latex = data.get("latex_styled") or data.get("latex", "")
        confidence = float(data.get("confidence", 0.0))
        return latex, confidence


class Pix2TexOCR:
    """
    pix2tex 本地公式识别（占位实现，需要 PyTorch）

    安装: pip install pix2tex[dev]
    注意: 会装 PyTorch (~500MB)，仅推荐本地 GPU 推理
    """

    def __init__(self):
        try:
            from pix2tex.cli import LatexOCR

            self.model = LatexOCR()
        except ImportError:
            raise OCRError("需要安装 pix2tex: pip install pix2tex[dev]") from None

    @property
    def name(self) -> str:
        return "pix2tex"

    def recognize(self, image_path: str | Path) -> tuple[str, float]:
        try:
            from PIL import Image
        except ImportError:
            raise OCRError("需要安装 Pillow: pip install Pillow") from None
        img = Image.open(image_path)
        latex = self.model(img)
        # pix2tex 不返回 confidence，简单用空字符串占位
        return latex, 0.8


def ocr_questions(
    ocr: FormulaOCR,
    questions_json: str | Path,
    images_dir: str | Path,
    output_json: str | Path,
    rate_limit: float = 1.0,
) -> dict:
    """
    批量识别 questions.json 里的公式图片，输出新 JSON。

    Args:
        ocr: FormulaOCR 实例
        questions_json: 输入 JSON 路径
        images_dir: 图片目录
        output_json: 输出 JSON 路径
        rate_limit: API 调用间隔（秒），防 rate limit

    Returns:
        统计信息
    """
    q_path = Path(questions_json)
    out_path = Path(output_json)
    img_dir = Path(images_dir)

    with q_path.open(encoding="utf-8") as f:
        data = json.load(f)

    stats = {
        "total_questions": 0,
        "total_images": 0,
        "ocr_called": 0,
        "ocr_success": 0,
        "ocr_failed": 0,
        "ocr_skipped": 0,
    }

    for topic in data.get("topics", []):
        for q in topic.get("questions", []):
            stats["total_questions"] += 1
            images = q.get("images", [])
            if not images:
                stats["ocr_skipped"] += 1
                continue

            # 每题只 OCR 第一张图（公式通常在第一张）
            # 多图题只 OCR 第一个，避免重复扣费
            first_img = images[0]
            img_path = img_dir / first_img
            stats["total_images"] += 1

            if not img_path.exists():
                stats["ocr_skipped"] += 1
                continue

            # 调用 OCR
            try:
                latex, conf = ocr.recognize(img_path)
                q["formula_latex"] = latex
                q["formula_confidence"] = conf
                q["formula_ocr_engine"] = ocr.name
                stats["ocr_success"] += 1
            except OCRError as e:
                q["formula_latex"] = None
                q["formula_confidence"] = 0.0
                q["formula_ocr_error"] = str(e)
                stats["ocr_failed"] += 1

            stats["ocr_called"] += 1

            # Rate limit
            if rate_limit > 0:
                time.sleep(rate_limit)

    # 保存
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return stats


# === CLI 集成辅助 ===


def make_ocr_from_env() -> FormulaOCR | None:
    """
    从环境变量创建 OCR 实例

    需要:
      MATHPIX_APP_ID
      MATHPIX_APP_KEY
    """
    import os

    app_id = os.environ.get("MATHPIX_APP_ID")
    app_key = os.environ.get("MATHPIX_APP_KEY")
    if app_id and app_key:
        return MathpixOCR(app_id=app_id, app_key=app_key)
    return None
