"""shuatipass 解析器测试"""
import pytest
import json
from pathlib import Path
from dataclasses import asdict

from shuatipass.parser import XueKeWangParserV3, Question, Topic, ParsedDocument
from shuatipass.parser import HEADER_RE, QUESTION_RE, OPTION_RE


# === 正则测试 ===

class TestRegex:
    def test_header(self):
        m = HEADER_RE.search("专题 01 直线运动\n1 / 20\n")
        assert m
        assert m.group(1) == "01"
        assert m.group(2) == "直线运动"
        assert m.group(3) == "1"
        assert m.group(4) == "20"

    def test_question_standard(self):
        m = QUESTION_RE.match("1．（2025·黑吉辽蒙卷·高考真题）题干")
        assert m
        assert m.group(1) == "1"
        assert m.group(2) == "2025"
        assert m.group(3) == "黑吉辽蒙卷"

    def test_question_no_source(self):
        m = QUESTION_RE.match("10．（2024·江西·高考真题）题干")
        assert m
        assert m.group(1) == "10"

    def test_option_with_value(self):
        m = OPTION_RE.match("A．位移")
        assert m
        assert m.group(1) == "A"
        assert m.group(2) == "位移"

    def test_option_with_empty_value(self):
        """物理公式题：A． 后面紧接换行（公式），允许空值"""
        m = OPTION_RE.match("A．")
        assert m
        assert m.group(1) == "A"
        assert m.group(2) == ""


# === 数据类测试 ===

class TestDataclasses:
    def test_question_defaults(self):
        q = Question(id="01-001", number=1)
        assert q.stem == ""
        assert q.options == {}
        assert q.images == []
        assert q.year is None
        assert q.type == "single_choice"

    def test_question_serializable(self):
        q = Question(id="01-001", number=1, year=2025, province="黑吉辽")
        d = asdict(q)
        assert d["id"] == "01-001"
        assert d["year"] == 2025


# === 解析器集成测试（需要 PDF）===

SAMPLE_PDF = Path(__file__).parent.parent / "data" / "input" / "物理-高考真题-学科网.pdf"


@pytest.mark.skipif(not SAMPLE_PDF.exists(), reason="示例 PDF 不存在")
class TestParserIntegration:
    """端到端测试 — 需要示例 PDF"""

    def test_parse_returns_structure(self, tmp_path):
        parser = XueKeWangParserV3(SAMPLE_PDF, tmp_path / "images")
        result = parser.parse()
        assert isinstance(result, ParsedDocument)
        assert result.source_file == SAMPLE_PDF.name
        assert result.total_pages == 423

    def test_topics_not_empty(self, tmp_path):
        parser = XueKeWangParserV3(SAMPLE_PDF, tmp_path / "images")
        result = parser.parse()
        assert len(result.topics) >= 10
        # 空专题被跳过
        for t in result.topics:
            assert len(t.questions) > 0, f"专题 {t.topic_id} 应该有题"

    def test_questions_have_required_fields(self, tmp_path):
        parser = XueKeWangParserV3(SAMPLE_PDF, tmp_path / "images")
        result = parser.parse()
        for t in result.topics:
            for q in t.questions:
                assert q.id
                assert q.number > 0
                assert q.stem
                assert q.source_page > 0

    def test_choices_have_4_options(self, tmp_path):
        """选择题应该有 A/B/C/D 4 个选项"""
        parser = XueKeWangParserV3(SAMPLE_PDF, tmp_path / "images")
        result = parser.parse()
        single_choice_count = 0
        for t in result.topics:
            for q in t.questions:
                if q.type == "single_choice":
                    single_choice_count += 1
                    assert len(q.options) == 4, f"题 {q.id} 选择题应该 4 个选项，实测 {len(q.options)}"
        assert single_choice_count > 100

    def test_images_extracted(self, tmp_path):
        parser = XueKeWangParserV3(SAMPLE_PDF, tmp_path / "images")
        result = parser.parse()
        # 至少有一些题有图片
        has_image_count = sum(1 for t in result.topics for q in t.questions if q.images)
        assert has_image_count > 100

    def test_stats(self, tmp_path):
        parser = XueKeWangParserV3(SAMPLE_PDF, tmp_path / "images")
        result = parser.parse()
        assert result.stats["total_questions"] > 500
        assert "single_choice" in result.stats["by_type"]
