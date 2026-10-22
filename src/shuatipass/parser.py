"""
shuatipass 解析器 —— 把 PDF 转结构化 JSON

v4 改动：
1. 接受 config 参数（默认用 xuekewang 预设）
2. 把硬编码正则改成从 config 读
3. 适配不同 PDF 来源
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

from .config import ParseConfig, get_builtin

# 兼容老代码：导出原正则
HEADER_RE = re.compile(r"专题\s*(\d+)\s+(\S+?)\s*\n\s*(\d+)\s*/\s*(\d+)\s*\n")
QUESTION_RE = re.compile(
    r"^(\d+)\s*[．\.]\s*[（(]\s*(\d{4})\s*[·\.]\s*([^·）\)]+?)\s*[·\.]\s*(?:高考真题|高考|真题|模拟)?\s*[）)]\s*"
)
OPTION_RE = re.compile(r"^([A-D])[．\.]\s*(.*)$")
TOPIC_TITLE_LINE_RE = re.compile(r"专题\s*(\d+)\s+(\S+?)\s*$")
HAS_QUESTION_RE = re.compile(r"\d+\s*[．\.]\s*[（(]\s*\d{4}\s*[·\.]")

ESSAY_KEYWORDS = [
    "求",
    "证明",
    "试求",
    "试证明",
    "计算",
    "解:",
    "解：",
    "（1）",
    "(1)",
    "①",
    "②",
    "③",
]


@dataclass
class Question:
    id: str
    number: int
    year: int | None = None
    province: str | None = None
    type: str = "single_choice"
    stem: str = ""
    options: dict = field(default_factory=dict)
    images: list = field(default_factory=list)
    image_bboxes: list = field(default_factory=list)
    answer: str | None = None
    explanation: str | None = None
    source_page: int = 0
    bbox: list | None = None
    cross_page: bool = False


@dataclass
class Topic:
    topic_id: str
    title: str
    page_start: int = 0
    page_end: int = 0
    questions: list = field(default_factory=list)


@dataclass
class ParsedDocument:
    source_file: str
    total_pages: int
    topics: list = field(default_factory=list)
    skipped_pages: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    config_name: str = "default"


class XueKeWangParser:
    """通用 PDF 题库解析器（兼容老 API）"""

    def __init__(
        self,
        pdf_path: str | Path,
        image_dir: str | Path,
        config: ParseConfig | None = None,
        config_name: str = "xuekewang",
    ):
        self.pdf_path = Path(pdf_path)
        self.image_dir = Path(image_dir)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.doc = pymupdf.open(str(self.pdf_path))

        # 加载配置
        if config is not None:
            self.config = config
        else:
            try:
                self.config = get_builtin(config_name)
            except FileNotFoundError:
                # fallback: 用默认
                self.config = ParseConfig()
                self.config.compile()

    def parse(self) -> ParsedDocument:
        result = ParsedDocument(
            source_file=self.pdf_path.name,
            total_pages=len(self.doc),
            config_name=self.config.name,
        )

        cfg = self.config

        # 第一遍：识别每个页面的"专题归属"
        page_topic_map = {}
        for page_idx in range(len(self.doc)):
            page = self.doc[page_idx]
            page_text = page.get_text()
            page_num = page_idx + 1
            header_match = cfg.header_re.search(page_text) if cfg.header_pattern else None
            if not header_match:
                # 没有 header 配置（通用模式）：所有有题的页归到默认专题
                if cfg.has_question_pattern and cfg.has_question_re.search(page_text):
                    page_topic_map[page_num] = "00"
                else:
                    page_topic_map[page_num] = None
                continue
            # header_groups 定义：[topic_id, topic_title, page_in_topic, total_in_topic]
            header_topic_id = header_match.group(1).zfill(2)
            if not cfg.has_question_re.search(page_text):
                # 考点分析页：检查是否内嵌另一个专题名
                lines = [raw_line.strip() for raw_line in page_text.split("\n")]
                reassigned = False
                if cfg.topic_title_pattern:
                    for line in lines:
                        m = cfg.topic_title_re.match(line)
                        if m and m.group(1).zfill(2) != header_topic_id:
                            page_topic_map[page_num] = m.group(1).zfill(2)
                            reassigned = True
                            break
                if not reassigned:
                    page_topic_map[page_num] = None
                    result.skipped_pages.append(
                        {"page": page_num, "reason": "考点分析页", "header_topic": header_topic_id}
                    )
                continue
            page_topic_map[page_num] = header_topic_id

        # 第二遍：按专题归类
        topic_pages = {}
        for page_idx in range(len(self.doc)):
            page = self.doc[page_idx]
            page_text = page.get_text()
            page_num = page_idx + 1
            tid = page_topic_map.get(page_num)
            if not tid:
                continue
            header_match = cfg.header_re.search(page_text) if cfg.header_pattern else None
            title = header_match.group(2).strip() if header_match else ""
            topic_pages.setdefault(tid, {"title": title, "pages": []})
            topic_pages[tid]["pages"].append(page_num)
            if title and not topic_pages[tid]["title"]:
                topic_pages[tid]["title"] = title

        # 第三遍：每个专题内逐页解析
        for tid in sorted(topic_pages.keys()):
            info = topic_pages[tid]
            topic = Topic(
                topic_id=tid,
                title=info["title"],
                page_start=info["pages"][0] if info["pages"] else 0,
                page_end=info["pages"][-1] if info["pages"] else 0,
            )
            for page_num in info["pages"]:
                self._parse_page(page_num, topic)
            if not topic.questions:
                result.skipped_pages.append(
                    {"topic_id": tid, "title": info["title"], "reason": "空专题（仅有考点分析页）"}
                )
                continue
            result.topics.append(topic)

        # 4. 题型推断
        for topic in result.topics:
            for q in topic.questions:
                q.type = self._infer_type(q)

        # 5. 统计
        result.stats = self._compute_stats(result)
        return result

    def _parse_page(self, page_num: int, topic: Topic):
        page = self.doc[page_num - 1]
        page_text = page.get_text()
        lines = page_text.split("\n")
        page_height = page.rect.height

        cfg = self.config
        page_images = self._extract_page_images(page, page_num, topic.topic_id)

        d = page.get_text("dict")
        blocks = []
        for block in d.get("blocks", []):
            if block.get("type") != 0:
                continue
            x0, y0, x1, y1 = block["bbox"]
            text = "".join(
                span["text"] for line in block.get("lines", []) for span in line.get("spans", [])
            )
            blocks.append((x0, y0, x1, y1, text))

        # 找本页所有题号 + y 坐标
        question_ys = {}
        for b in blocks:
            bx0, by0, bx1, by1, btext = b
            btext_stripped = btext.strip()
            m = cfg.question_re.match(btext_stripped)
            if m:
                q_num = int(m.group(1))
                if q_num not in question_ys:
                    question_ys[q_num] = by0

        current_q: Question | None = None
        current_stem_lines: list[str] = []
        current_options: dict[str, str] = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 配置化跳过规则
            if cfg.should_skip(line):
                continue
            if cfg.header_pattern and re.match(r"^\d+\s*/\s*\d+$", line):
                continue

            q_match = cfg.question_re.match(line)
            if q_match:
                # 收尾上一题
                if current_q is not None:
                    current_q.stem = self._finalize_stem(current_stem_lines)
                    current_q.options = current_options
                    current_q.bbox = self._calc_bbox(current_q.number, question_ys, page_height)
                    if current_q.bbox:
                        current_q.images, current_q.image_bboxes = self._assign_images(
                            page_images, current_q.bbox
                        )
                    topic.questions.append(current_q)

                # 新题
                groups = q_match.groups()
                q_num = int(groups[0])
                # year/province 可选（学科网配置有 3 组，宽松配置只 1 组）
                q_year = None
                q_province = None
                if len(groups) >= 3:
                    try:
                        q_year = int(groups[1])
                    except (ValueError, TypeError):
                        q_year = None
                    q_province = groups[2].strip() if groups[2] else None
                elif len(groups) >= 2:
                    try:
                        q_year = int(groups[1])
                    except (ValueError, TypeError):
                        q_year = None

                # 题干起始：去掉题目识别部分
                rest = line[q_match.end() :].strip()
                qid = f"{topic.topic_id}-{q_num:03d}"
                current_q = Question(
                    id=qid,
                    number=q_num,
                    year=q_year,
                    province=q_province,
                    source_page=page_num,
                    images=[],
                    image_bboxes=[],
                )
                current_stem_lines = [rest] if rest else []
                current_options = {}
                continue

            if current_q is None:
                continue

            opt_match = cfg.option_re.match(line)
            if opt_match:
                key = opt_match.group(1)
                val = opt_match.group(2).strip()
                if key in cfg.option_keys:
                    current_options[key] = val
                    # 检查行内嵌入新选项
                    while True:
                        m = re.search(r"([A-D])[．\.]\s*([^\sA-D][^A-D]*?)$", val)
                        if not m:
                            break
                        embedded_key = m.group(1)
                        embedded_val = m.group(2).strip()
                        if embedded_key == key or embedded_key in current_options:
                            break
                        if embedded_key not in cfg.option_keys:
                            break
                        val = val[: m.start()].strip()
                        current_options[key] = val
                        current_options[embedded_key] = embedded_val
                        key = embedded_key
                        val = embedded_val
                    continue

            if not current_options:
                current_stem_lines.append(line)
            else:
                # 新选项开头
                m_embedded = re.match(r"^([A-D])[．\.]\s*(.+)$", line)
                if m_embedded and m_embedded.group(1) in cfg.option_keys:
                    new_key = m_embedded.group(1)
                    if new_key not in current_options:
                        current_options[new_key] = m_embedded.group(2).strip()
                        continue
                # 续行
                last_key = list(current_options.keys())[-1]
                if current_options[last_key]:
                    current_options[last_key] += " " + line
                else:
                    current_options[last_key] = line

        if current_q is not None:
            current_q.stem = self._finalize_stem(current_stem_lines)
            current_q.options = current_options
            current_q.bbox = self._calc_bbox(current_q.number, question_ys, page_height)
            if current_q.bbox:
                current_q.images, current_q.image_bboxes = self._assign_images(
                    page_images, current_q.bbox
                )
            topic.questions.append(current_q)

    @staticmethod
    def _calc_bbox(q_num, question_ys, page_height):
        y_top = question_ys.get(q_num, 100)
        next_y = None
        for n, y in sorted(question_ys.items(), key=lambda x: x[1]):
            if n > q_num:
                next_y = y
                break
        y_bottom = next_y - 5 if next_y else page_height - 50
        return [40, y_top, 555, y_bottom]

    def _extract_page_images(self, page, page_num, topic_id):
        images = []
        for img_idx, img_info in enumerate(page.get_images(full=True)):
            xref = img_info[0]
            try:
                base_image = self.doc.extract_image(xref)
                ext = base_image["ext"]
                fname = f"t{topic_id}-p{page_num:03d}-i{img_idx+1:02d}.{ext}"
                fpath = self.image_dir / fname
                fpath.write_bytes(base_image["image"])
                rects = page.get_image_rects(xref)
                bbox = list(rects[0]) if rects else None
                images.append({"fname": fname, "bbox": bbox, "xref": xref})
            except Exception as e:
                print(f"[warn] p{page_num} img{img_idx} fail: {e}")
        return images

    @staticmethod
    def _assign_images(images, q_bbox):
        qx0, qy0, qx1, qy1 = q_bbox
        fnames, bboxes = [], []
        for img in images:
            if not img["bbox"]:
                continue
            ix0, iy0, ix1, iy1 = img["bbox"]
            cx, cy = (ix0 + ix1) / 2, (iy0 + iy1) / 2
            if qx0 <= cx <= qx1 and qy0 - 5 <= cy <= qy1:
                fnames.append(img["fname"])
                bboxes.append(img["bbox"])
        return fnames, bboxes

    @staticmethod
    def _finalize_stem(lines):
        text = " ".join(lines).strip()
        # 残留清理
        text = re.sub(r"学科\s*网[（(]?北\s*京[）)]?\s*股\s*份?\s*有\s*限\s*公\s*司?", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _infer_type(self, q: Question) -> str:
        cfg = self.config
        has_options = bool(q.options)
        has_essay_kw = any(kw in q.stem for kw in cfg.essay_keywords)
        if not has_options:
            return "essay"
        if has_essay_kw and len(q.options) >= 2:
            return "essay_with_options"
        if len(q.options) > len(cfg.option_keys):
            return "multi_choice"
        return "single_choice"

    @staticmethod
    def _compute_stats(result: ParsedDocument) -> dict:
        type_counter = {}
        for t in result.topics:
            for q in t.questions:
                type_counter[q.type] = type_counter.get(q.type, 0) + 1
        total = sum(len(t.questions) for t in result.topics)
        return {
            "total_topics": len(result.topics),
            "total_questions": total,
            "by_type": type_counter,
            "skipped_pages": len(result.skipped_pages),
        }


# 兼容老 API：XueKeWangParserV3 = XueKeWangParser
XueKeWangParserV3 = XueKeWangParser
