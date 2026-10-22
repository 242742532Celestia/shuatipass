"""shuatipass 配置测试"""

import pytest

from shuatipass.config import ParseConfig, get_builtin, list_builtins


class TestParseConfig:
    def test_default(self):
        cfg = ParseConfig()
        cfg.compile()
        assert cfg.name == "学科网"
        assert cfg.question_re is not None

    def test_match_header(self):
        cfg = ParseConfig()
        cfg.compile()
        m = cfg.header_re.search("专题 01 直线运动\n1 / 20\n")
        assert m
        assert m.group(1) == "01"

    def test_match_question(self):
        cfg = ParseConfig()
        cfg.compile()
        m = cfg.question_re.match("1．（2025·黑吉辽蒙卷·高考真题）题干")
        assert m
        assert m.group(1) == "1"
        assert m.group(2) == "2025"
        assert m.group(3) == "黑吉辽蒙卷"

    def test_match_option(self):
        cfg = ParseConfig()
        cfg.compile()
        m = cfg.option_re.match("A．位移")
        assert m
        assert m.group(1) == "A"

    def test_should_skip(self):
        cfg = ParseConfig()
        cfg.compile()
        assert cfg.should_skip("学科 网（北京）股份 有限公司")
        assert cfg.should_skip("考点")
        assert not cfg.should_skip("正常的题干文字")

    def test_to_yaml(self):
        cfg = ParseConfig()
        cfg.compile()
        yaml_text = cfg.to_yaml()
        assert "name:" in yaml_text
        assert "question_pattern:" in yaml_text

    def test_from_yaml(self):
        cfg = ParseConfig()
        cfg.compile()
        yaml_text = cfg.to_yaml()
        cfg2 = ParseConfig.from_yaml(yaml_text)
        assert cfg2.name == cfg.name
        assert cfg2.question_pattern == cfg.question_pattern

    def test_invalid_regex_raises(self):
        cfg = ParseConfig(question_pattern="[invalid")
        with pytest.raises(ValueError):
            cfg.compile()


class TestBuiltinConfigs:
    def test_list_builtins(self):
        names = list_builtins()
        assert "xuekewang" in names
        assert "generic" in names

    def test_get_xuekewang(self):
        cfg = get_builtin("xuekewang")
        assert cfg.name == "学科网"
        assert cfg.compile() is True

    def test_get_generic(self):
        cfg = get_builtin("generic")
        assert cfg.name == "通用宽松"
        assert cfg.compile() is True

    def test_get_missing(self):
        with pytest.raises(FileNotFoundError):
            get_builtin("nonexistent")

    def test_xuekewang_matches_real(self):
        """学科网配置能识别真实 PDF 题目"""
        cfg = get_builtin("xuekewang")
        line = "1．（2025·黑吉辽蒙卷·高考真题）书法课上..."
        m = cfg.question_re.match(line)
        assert m
        assert m.group(1) == "1"

    def test_generic_loose_match(self):
        """通用配置能识别更宽松的格式"""
        cfg = get_builtin("generic")
        # 通用配置：只要"数字．" + 任何正文
        m = cfg.question_re.match("1. 下列说法正确的是：")
        assert m
        assert m.group(1) == "1"
