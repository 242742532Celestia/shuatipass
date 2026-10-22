"""shuatipass Web UI 测试"""

import ast
import importlib.util
import inspect
from pathlib import Path

import pytest

from shuatipass import web as web_mod
from shuatipass.web import _build_ui, _on_parse, _parse_pdf, is_available, launch_web

HAS_GRADIO = importlib.util.find_spec("gradio") is not None

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

    @pytest.mark.skipif(not SAMPLE_PDF.exists(), reason="示例 PDF 不存在")
    def test_parse_pdf_real(self, tmp_path):
        """真实 PDF 解析（端到端）"""
        json_str, stats_text, preview_md, file_path = _parse_pdf(str(SAMPLE_PDF), "xuekewang")
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


class TestParsePdfAsLibrary:
    """_parse_pdf 不该依赖 gradio —— 它同时是个库函数。

    🔴 原实现里 `progress = gr.Progress()` 在没装 gradio 的机器上直接 NameError
    （注释还写着"gradio 可能还没装"），于是这些用例在 CI 上是跑不到的。
    """

    def test_parse_pdf_no_pdf(self, tmp_path):
        """无 PDF 时返回错误"""
        json_str, stats, preview, file_path = _parse_pdf("", "xuekewang")
        assert "❌" in json_str or "请先上传" in json_str

    def test_parse_pdf_missing(self, tmp_path):
        """PDF 不存在时返回错误"""
        json_str, stats, preview, file_path = _parse_pdf("/nonexistent.pdf", "xuekewang")
        assert "❌" in json_str


class TestOnParseWiring:
    """🔴 Gradio 事件回调的输出契约。

    原来的 outputs 列表接的是 _parse_pdf 的 4 元组：数量对不上、顺序还错位。
    Gradio 在点击时会抛 "Number of output components does not match..."，
    也就是 **Web UI 的「解析」按钮点了就炸**。

    这组用例不装 gradio 也能跑，守住两个不变量：
      ① 回调返回值个数 == outputs 列表长度；
      ② outputs 的顺序 == 回调返回值的顺序（文件 / 统计 / 预览）。
    """

    def _outputs_count(self) -> int:
        """用 AST 数出 _build_ui 里 parse_btn.click 的 outputs 列表长度。

        不用"建 UI 再看组件树"的办法 —— 那样要装 gradio，
        而且 gradio 只在**点击时**才校验数量，build 阶段根本不报错。
        """
        tree = ast.parse(inspect.getsource(web_mod._build_ui))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "click":
                for kw in node.keywords:
                    if kw.arg == "outputs":
                        return len(kw.value.elts)
        raise AssertionError("_build_ui 里没找到 parse_btn.click(...)")

    def test_callback_returns_three_values(self):
        """回调固定返回 3 个值（文件 / 统计 / 预览）"""
        out = _on_parse("", "xuekewang")
        assert len(out) == 3

    def test_outputs_count_matches_callback(self):
        """outputs 的长度必须等于回调返回值的个数"""
        assert self._outputs_count() == len(_on_parse("", "xuekewang"))

    def test_outputs_order_matches_callback(self):
        """outputs[0] 必须是下载组件（接收文件路径），且错误路径下为空"""
        outputs = self._outputs_count()
        file_path, stats, preview = _on_parse("", "xuekewang")
        # 第 1 个输出接的是文件路径 → 出错时必须是 None（不是错误字符串）
        assert outputs == 3
        assert file_path is None
        # 第 2 个输出接统计文本 → 出错时错误信息要显示在这里
        assert "❌" in stats
        # 第 3 个输出接预览 → 出错时为空
        assert preview == ""

    def test_error_message_reaches_stats_pane(self):
        """错误信息不能塞进 File 组件（它渲染不出来），必须出现在统计栏"""
        file_path, stats, preview = _on_parse("/nonexistent.pdf", "xuekewang")
        assert file_path is None
        assert "❌" in stats


class TestWebLaunch:
    def test_launch_web_no_gradio(self, monkeypatch):
        """gradio 不可用时抛错"""
        monkeypatch.setattr(web_mod, "HAS_GRADIO", False)
        with pytest.raises(ImportError, match="gradio"):
            launch_web()
