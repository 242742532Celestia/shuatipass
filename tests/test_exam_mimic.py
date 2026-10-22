"""
shuatipass Exam Mimic + Wrongbook 测试
"""

import json
from unittest.mock import patch

import pytest

from shuatipass.exam_mimic import (
    analyze_exam_style,
    build_mimic_prompt,
    parse_exam_mimic_response,
)
from shuatipass.wrongbook import (
    build_wrongbook,
    export_wrongbook,
    find_by_ids,
    find_by_tag,
    load_questions,
    mark_questions,
    render_wrongbook_html,
)

# ==========================
# Exam Mimic 测试
# ==========================

SAMPLE_SEED = {
    "topics": [
        {
            "topic_id": "01",
            "title": "直线运动",
            "questions": [
                {
                    "id": "01-001",
                    "type": "single_choice",
                    "stem": "一辆汽车做匀加速直线运动...",
                    "options": {"A": "10", "B": "20", "C": "30", "D": "40"},
                    "answer": "B",
                    "explanation": "由 v = at",
                    "year": 2022,
                    "province": "山东",
                },
                {
                    "id": "01-002",
                    "type": "single_choice",
                    "stem": "小球做自由落体...",
                    "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
                    "answer": "C",
                    "explanation": "h = 1/2 gt^2",
                    "year": 2024,
                    "province": "广东",
                },
            ],
        },
        {
            "topic_id": "02",
            "title": "圆周运动",
            "questions": [
                {
                    "id": "02-001",
                    "type": "essay",
                    "stem": "一质点做匀速圆周运动...",
                    "options": {},
                    "answer": "见解析",
                    "explanation": "F = mv²/r",
                    "year": 2025,
                    "province": "北京",
                },
            ],
        },
    ]
}


class TestExamStyleAnalysis:
    def test_basic_features(self, tmp_path):
        p = tmp_path / "seed.json"
        p.write_text(json.dumps(SAMPLE_SEED), encoding="utf-8")
        style = analyze_exam_style(p)
        assert style.total_questions == 3
        assert "直线运动" in style.topic_distribution
        assert style.topic_distribution["直线运动"] == 2
        assert "圆周运动" in style.topic_distribution
        assert style.topic_distribution["圆周运动"] == 1

    def test_type_distribution(self, tmp_path):
        p = tmp_path / "seed.json"
        p.write_text(json.dumps(SAMPLE_SEED), encoding="utf-8")
        style = analyze_exam_style(p)
        assert style.type_distribution["single_choice"] == 2
        assert style.type_distribution["essay"] == 1
        # 比例
        assert abs(style.type_ratio["single_choice"] - 66.7) < 1.0

    def test_year_range(self, tmp_path):
        p = tmp_path / "seed.json"
        p.write_text(json.dumps(SAMPLE_SEED), encoding="utf-8")
        style = analyze_exam_style(p)
        assert style.year_range == (2022, 2025)

    def test_provinces(self, tmp_path):
        p = tmp_path / "seed.json"
        p.write_text(json.dumps(SAMPLE_SEED), encoding="utf-8")
        style = analyze_exam_style(p)
        assert "山东" in style.provinces
        assert "广东" in style.provinces

    def test_difficulty_estimation(self, tmp_path):
        p = tmp_path / "seed.json"
        p.write_text(json.dumps(SAMPLE_SEED), encoding="utf-8")
        style = analyze_exam_style(p)
        # 2022=easy, 2024=hard, 2025=hard
        assert style.difficulty_distribution.get("easy", 0) >= 1
        assert style.difficulty_distribution.get("hard", 0) >= 1

    def test_estimated_score(self, tmp_path):
        p = tmp_path / "seed.json"
        p.write_text(json.dumps(SAMPLE_SEED), encoding="utf-8")
        style = analyze_exam_style(p)
        # 2 单选 (4×2=8) + 1 解析 (12) = 20
        assert style.estimated_score == 20

    def test_missing_file(self):
        with pytest.raises(FileNotFoundError):
            analyze_exam_style("/tmp/nonexistent.json")


class TestMimicPrompt:
    def test_contains_style(self, tmp_path):
        p = tmp_path / "seed.json"
        p.write_text(json.dumps(SAMPLE_SEED), encoding="utf-8")
        style = analyze_exam_style(p)
        prompt = build_mimic_prompt(style, target_count=10, subject="物理")
        assert "物理" in prompt
        assert "10" in prompt
        assert "题型分布" in prompt
        assert "难度分布" in prompt


class TestParseExamMimicResponse:
    def test_parse_pure_json(self):
        resp = json.dumps(
            {
                "questions": [
                    {
                        "type": "single_choice",
                        "stem": "测试题",
                        "options": {"A": "1", "B": "2"},
                        "answer": "A",
                        "explanation": "因为...",
                        "knowledge_point": "力学",
                        "difficulty": "easy",
                    }
                ]
            }
        )
        questions = parse_exam_mimic_response(resp)
        assert len(questions) == 1
        assert questions[0]["stem"] == "测试题"

    def test_parse_markdown_wrapped(self):
        resp = "```json\n" + json.dumps({"questions": [{"type": "essay", "stem": "题1"}]}) + "\n```"
        questions = parse_exam_mimic_response(resp)
        assert len(questions) == 1

    def test_parse_invalid_json(self):
        with pytest.raises(RuntimeError):
            parse_exam_mimic_response("not json at all")

    def test_parse_no_questions(self):
        with pytest.raises(RuntimeError):
            parse_exam_mimic_response('{"other": "stuff"}')


class TestMimicExamE2E:
    def test_mimic_with_mock(self, tmp_path):
        """端到端：mock LLM 响应，跑完整流程"""
        seed_path = tmp_path / "seed.json"
        seed_path.write_text(json.dumps(SAMPLE_SEED), encoding="utf-8")
        out_path = tmp_path / "mock.json"

        mock_resp = json.dumps(
            {
                "questions": [
                    {
                        "type": "single_choice",
                        "stem": "测试题1",
                        "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
                        "answer": "A",
                        "explanation": "解析",
                        "knowledge_point": "测试",
                        "difficulty": "easy",
                    }
                ]
            }
        )

        with patch("shuatipass.exam_mimic.call_llm", return_value=mock_resp):
            from shuatipass.exam_mimic import mimic_exam

            result = mimic_exam(
                seed_json=seed_path,
                target_count=1,
                output=out_path,
            )
            assert result is not None

        assert out_path.exists()
        saved = json.loads(out_path.read_text(encoding="utf-8"))
        assert saved["source"] == "shuatipass exam-mimic"
        assert "style" in saved
        assert "questions" in saved
        assert "stats" in saved


# ==========================
# Wrongbook 测试
# ==========================


class TestWrongbookLoad:
    def test_load_basic(self, tmp_path):
        p = tmp_path / "q.json"
        p.write_text(json.dumps(SAMPLE_SEED), encoding="utf-8")
        questions = load_questions(p)
        assert len(questions) == 3
        # 每题带 _topic_id
        assert all("_topic_id" in q for q in questions)
        assert all("_topic_title" in q for q in questions)

    def test_load_missing(self):
        with pytest.raises(FileNotFoundError):
            load_questions("/tmp/nonexistent.json")


class TestWrongbookFind:
    def test_find_by_ids(self, tmp_path):
        p = tmp_path / "q.json"
        p.write_text(json.dumps(SAMPLE_SEED), encoding="utf-8")
        questions = load_questions(p)
        result = find_by_ids(questions, ["01-001", "02-001"])
        assert len(result) == 2
        ids = {r["id"] for r in result}
        assert ids == {"01-001", "02-001"}

    def test_find_by_ids_no_match(self, tmp_path):
        p = tmp_path / "q.json"
        p.write_text(json.dumps(SAMPLE_SEED), encoding="utf-8")
        questions = load_questions(p)
        result = find_by_ids(questions, ["nonexistent"])
        assert len(result) == 0

    def test_find_by_tag(self, tmp_path):
        # 加 tag
        seed = json.loads(json.dumps(SAMPLE_SEED))
        seed["topics"][0]["questions"][0]["tags"] = ["错题", "重要"]
        p = tmp_path / "q.json"
        p.write_text(json.dumps(seed), encoding="utf-8")
        questions = load_questions(p)
        result = find_by_tag(questions, "错题")
        assert len(result) == 1
        assert result[0]["id"] == "01-001"


class TestMarkQuestions:
    def test_mark_basic(self, tmp_path):
        p = tmp_path / "q.json"
        p.write_text(json.dumps(SAMPLE_SEED), encoding="utf-8")
        result = mark_questions(
            json_path=p,
            question_ids=["01-001", "01-002"],
            action="mark",
            tag="错题",
        )
        assert result["marked"] == 2
        assert result["not_found"] == []

        # 重新读，确认 tag 加上
        data = json.loads(p.read_text(encoding="utf-8"))
        for t in data["topics"]:
            for q in t["questions"]:
                if q["id"] in ["01-001", "01-002"]:
                    assert "错题" in q.get("tags", [])

    def test_mark_not_found(self, tmp_path):
        p = tmp_path / "q.json"
        p.write_text(json.dumps(SAMPLE_SEED), encoding="utf-8")
        result = mark_questions(
            json_path=p,
            question_ids=["01-001", "ghost"],
            action="mark",
        )
        assert result["marked"] == 1
        assert "ghost" in result["not_found"]

    def test_unmark(self, tmp_path):
        seed = json.loads(json.dumps(SAMPLE_SEED))
        seed["topics"][0]["questions"][0]["tags"] = ["错题"]
        p = tmp_path / "q.json"
        p.write_text(json.dumps(seed), encoding="utf-8")
        result = mark_questions(
            json_path=p,
            question_ids=["01-001"],
            action="unmark",
        )
        assert result["unmarked"] == 1
        data = json.loads(p.read_text(encoding="utf-8"))
        assert "错题" not in data["topics"][0]["questions"][0].get("tags", [])

    def test_mark_to_output(self, tmp_path):
        src = tmp_path / "src.json"
        out = tmp_path / "out.json"
        src.write_text(json.dumps(SAMPLE_SEED), encoding="utf-8")
        mark_questions(
            json_path=src,
            question_ids=["01-001"],
            action="mark",
            output=out,
        )
        # 原文件不变
        src_data = json.loads(src.read_text(encoding="utf-8"))
        assert "tags" not in src_data["topics"][0]["questions"][0]
        # 输出文件有 tag
        out_data = json.loads(out.read_text(encoding="utf-8"))
        assert "错题" in out_data["topics"][0]["questions"][0].get("tags", [])


class TestBuildWrongbook:
    def test_group_by_knowledge_point(self):
        questions = [
            {"id": "1", "knowledge_point": "力学", "type": "single_choice", "year": 2022},
            {"id": "2", "knowledge_point": "力学", "type": "essay", "year": 2023},
            {"id": "3", "knowledge_point": "光学", "type": "single_choice", "year": 2024},
        ]
        wb = build_wrongbook(questions, group_by="knowledge_point")
        assert wb["total"] == 3
        assert wb["groups_count"] == 2
        assert len(wb["groups"]["力学"]) == 2
        assert len(wb["groups"]["光学"]) == 1

    def test_group_by_year(self):
        questions = [
            {"id": "1", "type": "single_choice", "year": 2022},
            {"id": "2", "type": "essay", "year": 2022},
            {"id": "3", "type": "single_choice", "year": 2023},
        ]
        wb = build_wrongbook(questions, group_by="year")
        assert wb["groups_count"] == 2
        assert len(wb["groups"]["2022"]) == 2

    def test_stats(self):
        questions = [
            {"id": "1", "type": "single_choice", "year": 2022},
            {"id": "2", "type": "essay", "year": 2022},
        ]
        wb = build_wrongbook(questions)
        assert wb["stats"]["total"] == 2
        assert wb["stats"]["by_type"]["single_choice"] == 1
        assert wb["stats"]["by_type"]["essay"] == 1
        assert wb["stats"]["by_year"]["2022"] == 2


class TestExportWrongbook:
    def test_export_json(self, tmp_path):
        src = tmp_path / "src.json"
        out = tmp_path / "wb.json"
        # 标错题
        mark_questions(
            src.write_text(json.dumps(SAMPLE_SEED), encoding="utf-8") and src,  # write first
            question_ids=["01-001"],
            action="mark",
        )
        # 导出
        wb = export_wrongbook(
            source_json=src,
            output_json=out,
            tag="错题",
        )
        assert wb["total"] == 1
        assert out.exists()

    def test_export_html(self, tmp_path):
        src = tmp_path / "src.json"
        out_html = tmp_path / "wb.html"
        # 标错题
        src.write_text(json.dumps(SAMPLE_SEED), encoding="utf-8")
        mark_questions(src, question_ids=["01-001"], action="mark")
        export_wrongbook(
            source_json=src,
            output_html=out_html,
            tag="错题",
        )
        assert out_html.exists()
        content = out_html.read_text(encoding="utf-8")
        assert "错题本" in content
        assert "直线运动" in content
        assert "解析" in content

    def test_export_by_ids(self, tmp_path):
        src = tmp_path / "src.json"
        src.write_text(json.dumps(SAMPLE_SEED), encoding="utf-8")
        wb = export_wrongbook(
            source_json=src,
            ids=["01-001", "02-001"],
        )
        assert wb["total"] == 2

    def test_export_empty(self, tmp_path):
        src = tmp_path / "src.json"
        src.write_text(json.dumps(SAMPLE_SEED), encoding="utf-8")
        wb = export_wrongbook(
            source_json=src,
            tag="错题",  # 没标过任何错题
        )
        assert wb["total"] == 0


class TestRenderHtml:
    def test_html_structure(self):
        wb = {
            "total": 2,
            "groups_count": 1,
            "group_by": "knowledge_point",
            "groups": {
                "力学": [
                    {
                        "id": "1",
                        "_topic_title": "直线运动",
                        "type": "single_choice",
                        "year": 2022,
                        "province": "山东",
                        "number": 1,
                        "stem": "测试题",
                        "options": {"A": "1", "B": "2"},
                        "answer": "A",
                        "explanation": "因为...",
                    }
                ]
            },
            "stats": {"total": 2, "by_type": {"single_choice": 2}, "by_year": {"2022": 2}},
        }
        html = render_wrongbook_html(wb, title="我的错题本")
        assert "<!DOCTYPE html>" in html
        assert "我的错题本" in html
        assert "力学" in html
        assert "测试题" in html
        assert "因为" in html
