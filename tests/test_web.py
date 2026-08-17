"""shuatipass Web UI 测试"""
import pytest
from pathlib import Path

try:
    import gradio as gr
    HAS_GRADIO = True
except ImportError:
    HAS_GRADIO = False

from shuatipass.web import is_available, launch_web, _build_ui, _parse_pdf


SAMPLE_PDF = Path(__file__).parent.parent / "data" / "input" / "物理-高考真题-学科网.pdf"


@pytest.mark.skipif(not HAS_GRADIO, reason="gradio 未装")
class TestWeb:
    def test_is_available(self):
        assert is_available() is True

    def test_build_ui(self):
        demo = _build_ui()
        assert demo is not None
        # Gradio Blocks 有 .blocks 属性
        assert hasattr(demo, "launch")

    def test_parse_pdf_no_pdf(self, tmp_path):
        """无 PDF 时返回错误"""
        json_str, stats, preview, file_path = _parse_pdf("", "xuekewang")
        assert "❌" in json_str or "请先上传" in json_str

    def test_parse_pdf_missing(self, tmp_path):
        """PDF 不存在时返回错误"""
        json_str, stats, preview, file_path = _parse_pdf("/nonexistent.pdf", "xuekewang")
        assert "❌" in json_str

    @pytest.mark.skipif(not SAMPLE_PDF.exists(), reason="示例 PDF 不存在")
    def test_parse_pdf_real(self, tmp_path):
        """真实 PDF 解析（端到端）"""
        json_str, stats_text, preview_md, file_path = _parse_pdf(
            str(SAMPLE_PDF), "xuekewang"
        )
        # JSON 字符串
        assert "解析完成" not in json_str  # 是 JSON，不是错误
        import json
        data = json.loads(json_str)
        total = sum(len(t["questions"]) for t in data["topics"])
        assert total > 500
        # 统计文本
        assert "统计" in stats_text
        assert "题目数" in stats_text
        # 预览
        assert "shuatipass" in preview_md or "题" in preview_md
        # JSON 文件
        assert file_path is not None
        assert Path(file_path).exists()


class TestWebLaunch:
    def test_launch_web_no_gradio(self, monkeypatch):
        """gradio 不可用时抛错"""
        from shuatipass import web as web_mod
        monkeypatch.setattr(web_mod, "HAS_GRADIO", False)
        with pytest.raises(ImportError, match="gradio"):
            launch_web()
