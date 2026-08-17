"""shuatipass 自动检测测试"""
import pytest
from pathlib import Path
from shuatipass.detect import detect_config, detect_with_details, HAS_PYMUPDF

SAMPLE_PDF = Path(__file__).parent.parent / "data" / "input" / "物理-高考真题-学科网.pdf"


@pytest.mark.skipif(not HAS_PYMUPDF, reason="pymupdf 未装")
class TestDetect:
    def test_detect_xuekewang(self):
        """示例 PDF 是学科网格式，应检测为 xuekewang"""
        if not SAMPLE_PDF.exists():
            pytest.skip("示例 PDF 不存在")
        result = detect_config(SAMPLE_PDF)
        assert result == "xuekewang"

    def test_detect_with_details(self):
        """详细检测应返回分数信息"""
        if not SAMPLE_PDF.exists():
            pytest.skip("示例 PDF 不存在")
        result = detect_with_details(SAMPLE_PDF)
        assert "recommended" in result
        assert "scores" in result
        assert result["recommended"] == "xuekewang"
        # xuekewang 应该有命中
        assert result["scores"]["xuekewang"]["hits"] > 0

    def test_detect_missing_file(self):
        """文件不存在应抛错"""
        with pytest.raises(FileNotFoundError):
            detect_config("/nonexistent.pdf")

    def test_detect_returns_string(self):
        """返回值是字符串"""
        if not SAMPLE_PDF.exists():
            pytest.skip("示例 PDF 不存在")
        result = detect_config(SAMPLE_PDF)
        assert isinstance(result, str)
        assert result in ["xuekewang", "zujuan", "textbook", "generic"]


class TestBuiltinConfigs:
    """所有内置配置加载测试"""

    def test_zujuan_loaded(self):
        from shuatipass.config import get_builtin
        cfg = get_builtin("zujuan")
        assert cfg.name == "组卷网"
        assert cfg.compile() is True

    def test_textbook_loaded(self):
        from shuatipass.config import get_builtin
        cfg = get_builtin("textbook")
        assert cfg.name == "教辅资料"
        assert cfg.compile() is True

    def test_list_4_builtins(self):
        from shuatipass.config import list_builtins
        names = list_builtins()
        assert "xuekewang" in names
        assert "generic" in names
        assert "zujuan" in names
        assert "textbook" in names


class TestMultiFormatIntegration:
    """用不同预设解析同一 PDF（验证 fallback 工作）"""

    @pytest.fixture
    def result_xk(self, tmp_path):
        from shuatipass import XueKeWangParser, get_builtin
        parser = XueKeWangParser(
            SAMPLE_PDF, tmp_path / "imgs", config=get_builtin("xuekewang"),
        )
        return parser.parse()

    def test_xuekewang_works(self, result_xk):
        if not SAMPLE_PDF.exists():
            pytest.skip()
        assert result_xk.stats["total_questions"] > 500

    def test_zujuan_works_on_xk_pdf(self, tmp_path):
        """用 zujuan 解析学科网 PDF（fallback 应该也工作）"""
        if not SAMPLE_PDF.exists():
            pytest.skip()
        from shuatipass import XueKeWangParser, get_builtin
        parser = XueKeWangParser(
            SAMPLE_PDF, tmp_path / "imgs", config=get_builtin("zujuan"),
        )
        result = parser.parse()
        # zujuan 配置会更多识别（不过滤考点分析页），所以题数可能更多
        assert result.stats["total_questions"] > 0
