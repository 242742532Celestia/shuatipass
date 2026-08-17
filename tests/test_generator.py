"""shuatipass AI 出题测试"""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from dataclasses import asdict

from shuatipass.generator import (
    GeneratedQuestion,
    build_prompt,
    parse_llm_response,
    generate_questions,
    generate_mock_exam,
    save_to_json,
    PROVIDERS,
    DIFFICULTY_LEVELS,
)


SAMPLE_JSON = Path(__file__).parent.parent / "data" / "parsed" / "questions.json"


class TestPromptBuilder:
    def test_basic_prompt(self):
        prompt = build_prompt(
            topic="圆周运动",
            difficulty="hard",
            count=5,
        )
        assert "圆周运动" in prompt
        assert "困难" in prompt
        assert "5" in prompt
        assert "JSON" in prompt

    def test_prompt_with_seed(self):
        seeds = [
            {"stem": "题1...", "options": {"A": "a", "B": "b"}},
            {"stem": "题2...", "options": {"A": "c", "B": "d"}},
        ]
        prompt = build_prompt(
            topic="物理",
            difficulty="medium",
            count=3,
            seed_questions=seeds,
        )
        assert "题1" in prompt
        assert "题2" in prompt
        assert "参考题" in prompt

    def test_difficulty_translation(self):
        for level in DIFFICULTY_LEVELS:
            prompt = build_prompt(topic="x", difficulty=level, count=1)
            assert "参考题目" in prompt or "题目" in prompt  # 中文


class TestResponseParser:
    def test_parse_clean_json(self):
        resp = '{"questions": [{"stem": "题1", "options": {"A": "1", "B": "2"}}]}'
        result = parse_llm_response(resp)
        assert len(result) == 1
        assert result[0]["stem"] == "题1"

    def test_parse_markdown_wrapped(self):
        resp = """```json
        {"questions": [{"stem": "题1", "options": {}}]}
        ```"""
        result = parse_llm_response(resp)
        assert len(result) == 1
        assert result[0]["stem"] == "题1"

    def test_parse_with_explanation(self):
        resp = '{"questions": [{"stem": "s", "options": {}, "answer": "A", "explanation": "e"}]}'
        result = parse_llm_response(resp)
        assert result[0]["answer"] == "A"
        assert result[0]["explanation"] == "e"

    def test_parse_no_questions_field(self):
        resp = '{"foo": "bar"}'
        with pytest.raises(RuntimeError, match="没有 questions 字段"):
            parse_llm_response(resp)

    def test_parse_invalid_json(self):
        with pytest.raises(RuntimeError, match="不是有效 JSON"):
            parse_llm_response("not json at all")


class TestGenerateWithMock:
    """端到端：用 mock LLM 测 generate_questions"""

    def test_generate_questions_minimax(self):
        mock_resp = json.dumps({
            "questions": [
                {
                    "stem": "测试题干",
                    "options": {"A": "A", "B": "B", "C": "C", "D": "D"},
                    "answer": "A",
                    "explanation": "测试解析",
                    "knowledge_point": "测试知识点",
                    "difficulty": "medium",
                }
            ]
        })

        with patch("shuatipass.generator.call_llm", return_value=mock_resp):
            questions = generate_questions(
                provider="minimax",
                topic="测试",
                difficulty="medium",
                count=1,
            )
            assert len(questions) == 1
            assert questions[0].stem == "测试题干"
            assert questions[0].answer == "A"
            assert questions[0].id == "GEN-001"
            assert questions[0].ai_generated is True
            assert questions[0].knowledge_point == "测试知识点"

    def test_generate_questions_with_seed(self):
        mock_resp = '{"questions": [{"stem": "s", "options": {}, "answer": "B"}]}'

        seeds = [{"id": "01-001", "stem": "原题", "options": {"A": "a"}}]

        with patch("shuatipass.generator.call_llm", return_value=mock_resp) as m:
            questions = generate_questions(
                provider="openai",
                topic="",
                difficulty="hard",
                count=1,
                seed_questions=seeds,
            )
            # 验证 prompt 包含种子题
            call_args = m.call_args
            prompt = call_args[0][2]  # 第 3 个位置参数
            assert "原题" in prompt
            assert "困难" in prompt
            assert questions[0].seed_ids == ["01-001"]


class TestSaveToJson:
    def test_save_independent(self, tmp_path):
        qs = [
            GeneratedQuestion(id="GEN-001", number=1, stem="题1", options={"A": "1"}),
            GeneratedQuestion(id="GEN-002", number=2, stem="题2", options={"A": "2"}),
        ]
        out = tmp_path / "out.json"
        save_to_json(qs, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["generated_count"] == 2
        assert len(data["questions"]) == 2
        assert data["questions"][0]["stem"] == "题1"

    def test_save_append(self, tmp_path):
        # 准备 seed JSON
        seed = {
            "topics": [
                {
                    "topic_id": "01",
                    "title": "原专题",
                    "questions": [
                        {"id": "01-001", "number": 1, "stem": "原题", "options": {"A": "1"}}
                    ],
                }
            ],
            "stats": {"total_questions": 1, "total_topics": 1},
        }
        seed_path = tmp_path / "seed.json"
        seed_path.write_text(json.dumps(seed), encoding="utf-8")

        # 生成题
        new_qs = [
            GeneratedQuestion(id="GEN-001", number=1, stem="新题", options={"A": "2"})
        ]
        out = tmp_path / "out.json"
        save_to_json(new_qs, out, append_to=seed_path)

        data = json.loads(out.read_text(encoding="utf-8"))
        # 应该有 2 个专题
        assert len(data["topics"]) == 2
        # 最后一个是 "AI 生成题"
        assert data["topics"][-1]["title"] == "AI 生成题"
        # 统计更新
        assert data["stats"]["total_questions"] == 2
        assert data["stats"]["total_topics"] == 2


class TestMockExam:
    @pytest.mark.skipif(not SAMPLE_JSON.exists(), reason="示例 JSON 不存在")
    def test_mock_exam_basic(self):
        mock_resp = json.dumps({
            "questions": [
                {"stem": "题1", "options": {"A": "1"}, "answer": "A", "explanation": "e"},
                {"stem": "题2", "options": {"A": "1"}, "answer": "B"},
            ]
        })

        with patch("shuatipass.generator.call_llm", return_value=mock_resp):
            data = generate_mock_exam(
                seed_json=SAMPLE_JSON,
                count=2,
                difficulty="medium",
            )
            assert data["generated_count"] == 2
            assert data["seed_count"] > 0
            assert len(data["questions"]) == 2

    @pytest.mark.skipif(not SAMPLE_JSON.exists(), reason="示例 JSON 不存在")
    def test_mock_exam_with_topic_filter(self):
        mock_resp = '{"questions": [{"stem": "s", "options": {}}]}'

        with patch("shuatipass.generator.call_llm", return_value=mock_resp):
            data = generate_mock_exam(
                seed_json=SAMPLE_JSON,
                count=1,
                topic_ids=["01"],  # 只用专题 01
            )
            assert data["generated_count"] >= 1


class TestProviders:
    def test_all_providers_have_config(self):
        for name in ["minimax", "openai", "anthropic"]:
            assert name in PROVIDERS
            assert "env_key" in PROVIDERS[name]
            assert "default_model" in PROVIDERS[name]

    def test_minimax_config(self):
        cfg = PROVIDERS["minimax"]
        assert cfg["env_key"] == "MINIMAX_API_KEY"
        assert "api.minimax.chat" in cfg["base_url"]


class TestCLI:
    """CLI 集成测试"""

    def test_generate_help(self):
        import subprocess
        result = subprocess.run(
            ["shuatipass", "generate", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "--seed" in result.stdout
        assert "--topic" in result.stdout
        assert "--mock-exam" in result.stdout

    def test_generate_no_key(self, tmp_path, monkeypatch):
        """没 API key 时友好提示"""
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        import subprocess
        result = subprocess.run(
            ["shuatipass", "generate", "-o", str(tmp_path / "out.json"),
             "--topic", "test"],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
        output = result.stdout + result.stderr
        assert "API_KEY" in output or "环境变量" in output

    def test_generate_no_seed_no_topic(self, tmp_path, monkeypatch):
        """--seed 和 --topic 都没给时报错"""
        monkeypatch.setenv("MINIMAX_API_KEY", "fake_key")
        import subprocess
        result = subprocess.run(
            ["shuatipass", "generate", "-o", str(tmp_path / "out.json")],
            capture_output=True, text=True,
        )
        # 因为没真 key，会先报"需要环境变量"或"需要 --topic"
        assert result.returncode != 0
