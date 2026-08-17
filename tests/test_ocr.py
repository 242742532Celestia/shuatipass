"""shuatipass OCR 测试（不需要真实 API key）"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

from shuatipass.ocr import (
    OCRError,
    MathpixOCR,
    Pix2TexOCR,
    ocr_questions,
    make_ocr_from_env,
)


SAMPLE_PDF = Path(__file__).parent.parent / "data" / "input" / "物理-高考真题-学科网.pdf"


class TestMathpixOCR:
    def test_missing_credentials(self):
        with pytest.raises(OCRError, match="app_id"):
            MathpixOCR(app_id="", app_key="")

    def test_recognize_success(self, tmp_path):
        """用 mock 模拟 API 成功响应"""
        # 准备假图片
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n")  # fake PNG

        # Mock requests.post
        with patch("shuatipass.ocr.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "latex_styled": "F = ma",
                "confidence": 0.95,
            }
            mock_post.return_value = mock_resp

            ocr = MathpixOCR("test_id", "test_key")
            latex, conf = ocr.recognize(img)
            assert latex == "F = ma"
            assert conf == 0.95
            assert ocr.name == "mathpix"

    def test_recognize_api_error(self, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG")
        with patch("shuatipass.ocr.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 401
            mock_resp.text = "Unauthorized"
            mock_post.return_value = mock_resp

            ocr = MathpixOCR("bad_id", "bad_key")
            with pytest.raises(OCRError, match="401"):
                ocr.recognize(img)

    def test_recognize_no_requests(self, tmp_path):
        """requests 没装时的错误处理"""
        from shuatipass import ocr as ocr_mod
        with patch.object(ocr_mod, "HAS_REQUESTS", False):
            with pytest.raises(OCRError, match="requests"):
                ocr = MathpixOCR("id", "key")
                ocr.recognize(tmp_path / "x.png")

    def test_missing_image(self, tmp_path):
        ocr = MathpixOCR("id", "key")
        with pytest.raises(OCRError, match="不存在"):
            ocr.recognize(tmp_path / "nonexistent.png")


class TestMakeOCRFromEnv:
    def test_returns_none_when_no_env(self, monkeypatch):
        monkeypatch.delenv("MATHPIX_APP_ID", raising=False)
        monkeypatch.delenv("MATHPIX_APP_KEY", raising=False)
        assert make_ocr_from_env() is None

    def test_returns_ocr_when_env_set(self, monkeypatch):
        monkeypatch.setenv("MATHPIX_APP_ID", "id")
        monkeypatch.setenv("MATHPIX_APP_KEY", "key")
        ocr = make_ocr_from_env()
        assert ocr is not None
        assert ocr.name == "mathpix"


class TestOCRQuestions:
    def test_ocr_questions_with_mock(self, tmp_path):
        """端到端：JSON + 图片 → OCR → 新 JSON"""
        # 准备输入 JSON
        q_data = {
            "topics": [
                {
                    "topic_id": "01",
                    "title": "测试",
                    "questions": [
                        {
                            "id": "01-001",
                            "number": 1,
                            "stem": "F = ?",
                            "options": {"A": "ma", "B": "mg"},
                            "images": ["01-001.png"],
                            "source_page": 1,
                        },
                        {
                            "id": "01-002",
                            "number": 2,
                            "stem": "无图题",
                            "options": {"A": "1", "B": "2"},
                            "images": [],
                            "source_page": 1,
                        },
                    ],
                }
            ]
        }
        input_json = tmp_path / "in.json"
        input_json.write_text(json.dumps(q_data), encoding="utf-8")

        # 准备图片
        img_dir = tmp_path / "imgs"
        img_dir.mkdir()
        (img_dir / "01-001.png").write_bytes(b"\x89PNG")

        output_json = tmp_path / "out.json"

        # Mock OCR
        mock_ocr = MagicMock()
        mock_ocr.name = "mock"
        mock_ocr.recognize.return_value = ("F = ma", 0.95)

        stats = ocr_questions(
            mock_ocr,
            input_json,
            img_dir,
            output_json,
            rate_limit=0,  # 测速
        )

        # 验证统计
        assert stats["total_questions"] == 2
        assert stats["total_images"] == 1
        assert stats["ocr_called"] == 1
        assert stats["ocr_success"] == 1
        assert stats["ocr_skipped"] == 1  # 无图题

        # 验证输出
        result = json.loads(output_json.read_text(encoding="utf-8"))
        q1 = result["topics"][0]["questions"][0]
        assert q1["formula_latex"] == "F = ma"
        assert q1["formula_confidence"] == 0.95
        assert q1["formula_ocr_engine"] == "mock"

    def test_ocr_questions_missing_image(self, tmp_path):
        """图片不存在时跳过"""
        q_data = {
            "topics": [
                {
                    "questions": [
                        {"id": "01-001", "number": 1, "stem": "题", "images": ["missing.png"]}
                    ]
                }
            ]
        }
        input_json = tmp_path / "in.json"
        input_json.write_text(json.dumps(q_data), encoding="utf-8")

        img_dir = tmp_path / "imgs"
        img_dir.mkdir()
        # 不创建图片

        mock_ocr = MagicMock()
        stats = ocr_questions(mock_ocr, input_json, img_dir, tmp_path / "out.json", rate_limit=0)
        assert stats["ocr_skipped"] == 1
        assert stats["ocr_called"] == 0


class TestOCRCLI:
    """CLI 集成测试"""

    def test_ocr_help(self):
        import subprocess
        result = subprocess.run(
            ["shuatipass", "ocr", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "ocr" in result.stdout
        assert "mathpix" in result.stdout

    def test_ocr_no_credentials(self, tmp_path, monkeypatch):
        """没 key 时给出友好提示"""
        monkeypatch.delenv("MATHPIX_APP_ID", raising=False)
        monkeypatch.delenv("MATHPIX_APP_KEY", raising=False)
        import subprocess
        # 创建 JSON + 图片目录（都存在，但 topics 为空）
        (tmp_path / "q.json").write_text('{"topics":[]}', encoding="utf-8")
        img_dir = tmp_path / "imgs"
        img_dir.mkdir()
        result = subprocess.run(
            ["shuatipass", "ocr", str(tmp_path / "q.json"), "--images", str(img_dir)],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
        output = result.stdout + result.stderr
        # 应该报"未配置 OCR 引擎"或"Mathpix 需要 app_id"
        assert any(kw in output for kw in ["OCR 引擎", "未配置", "app_id"]), \
            f"Unexpected output: {output}"
