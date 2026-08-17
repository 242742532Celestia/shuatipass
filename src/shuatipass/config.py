"""
shuatipass 配置 —— 让用户自定义"什么样的 PDF 算一道题"

通过 YAML 配置文件，用户可以为不同来源/格式的题库 PDF 定义解析规则。
"""
from __future__ import annotations
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def _coerce_str(item) -> str:
    """把任意类型转字符串（修复 YAML mapping 简写 bug: `解:` -> {解: None}）"""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        # {解: None} → "解:"
        return ":".join(str(k) for k in item.keys()) + ":"
    return str(item)


@dataclass
class ParseConfig:
    """解析配置"""
    name: str = "学科网"
    description: str = ""

    # 必填：4 个核心正则
    header_pattern: str = r"专题\s*(\d+)\s+(\S+?)\s*\n\s*(\d+)\s*/\s*(\d+)\s*\n"
    question_pattern: str = r"^(\d+)\s*[．\.]\s*[（(]\s*(\d{4})\s*[·\.]\s*([^·）\)]+?)\s*[·\.]\s*(?:高考真题|高考|真题|模拟)?\s*[）)]\s*"
    option_pattern: str = r"^([A-D])[．\.]\s*(.*)$"
    has_question_pattern: str = r"\d+\s*[．\.]\s*[（(]\s*\d{4}\s*[·\.]"
    topic_title_pattern: str = r"专题\s*(\d+)\s+(\S+?)\s*$"

    # 可选：行为配置
    option_keys: list = field(default_factory=lambda: ["A", "B", "C", "D"])
    essay_keywords: list = field(default_factory=lambda: ["求", "证明", "计算", "（1）", "(1)"])
    skip_patterns: list = field(default_factory=lambda: [
        "学科 网", "股 份", "有限公司", "考点", "命题趋势",
    ])
    skip_exact_lines: list = field(default_factory=lambda: [
        "考点", "五年考情（2021-2025）", "命题趋势",
    ])

    # 编译后的正则（运行时填充）
    _header_re: Optional[re.Pattern] = field(default=None, repr=False, compare=False)
    _question_re: Optional[re.Pattern] = field(default=None, repr=False, compare=False)
    _option_re: Optional[re.Pattern] = field(default=None, repr=False, compare=False)
    _has_question_re: Optional[re.Pattern] = field(default=None, repr=False, compare=False)
    _topic_title_re: Optional[re.Pattern] = field(default=None, repr=False, compare=False)
    _skip_res: list = field(default_factory=list, repr=False, compare=False)

    def compile(self):
        """编译所有正则"""
        try:
            self._header_re = re.compile(self.header_pattern, re.MULTILINE)
            self._question_re = re.compile(self.question_pattern, re.MULTILINE)
            self._option_re = re.compile(self.option_pattern, re.MULTILINE)
            self._has_question_re = re.compile(self.has_question_pattern, re.MULTILINE)
            self._topic_title_re = re.compile(self.topic_title_pattern, re.MULTILINE)
            self._skip_res = [re.compile(p, re.MULTILINE) for p in self.skip_patterns]
            return True
        except re.error as e:
            raise ValueError(f"配置 {self.name} 正则编译失败: {e}")

    @property
    def header_re(self) -> re.Pattern:
        if self._header_re is None:
            self.compile()
        return self._header_re

    @property
    def question_re(self) -> re.Pattern:
        if self._question_re is None:
            self.compile()
        return self._question_re

    @property
    def option_re(self) -> re.Pattern:
        if self._option_re is None:
            self.compile()
        return self._option_re

    @property
    def has_question_re(self) -> re.Pattern:
        if self._has_question_re is None:
            self.compile()
        return self._has_question_re

    @property
    def topic_title_re(self) -> re.Pattern:
        if self._topic_title_re is None:
            self.compile()
        return self._topic_title_re

    @property
    def skip_res(self) -> list:
        if not self._skip_res:
            self.compile()
        return self._skip_res

    def should_skip(self, line: str) -> bool:
        """判断这行是否要跳过"""
        if line in self.skip_exact_lines:
            return True
        for p in self._skip_res:
            if p.search(line):
                return True
        return False

    def to_yaml(self) -> str:
        """导出为 YAML"""
        d = asdict(self)
        # 移除编译后字段
        for k in list(d.keys()):
            if k.startswith("_"):
                d.pop(k)
        return yaml.safe_dump(d, allow_unicode=True, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_text: str) -> "ParseConfig":
        """从 YAML 文本加载"""
        if not HAS_YAML:
            raise ImportError("需要安装 pyyaml: pip install pyyaml")
        d = yaml.safe_load(yaml_text) or {}
        # 过滤掉 _ 开头字段
        d = {k: v for k, v in d.items() if not k.startswith("_")}
        # 强制 list[str] 字段：dict 元素（YAML mapping 简写）转字符串
        for k in ["essay_keywords", "option_keys", "skip_patterns", "skip_exact_lines"]:
            if k in d and isinstance(d[k], list):
                d[k] = [_coerce_str(item) for item in d[k]]
        cfg = cls(**d)
        cfg.compile()
        return cfg

    @classmethod
    def load(cls, path: str | Path) -> "ParseConfig":
        """从 YAML 文件加载"""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"配置文件不存在: {p}")
        return cls.from_yaml(p.read_text(encoding="utf-8"))


# === 内置预设 ===

def get_builtin(name: str) -> ParseConfig:
    """获取内置预设配置"""
    builtin_dir = Path(__file__).parent.parent.parent / "configs"
    path = builtin_dir / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"内置配置不存在: {name}（{path}）")
    return ParseConfig.load(path)


def list_builtins() -> list[str]:
    """列出所有内置预设"""
    builtin_dir = Path(__file__).parent.parent.parent / "configs"
    if not builtin_dir.exists():
        return []
    return [p.stem for p in builtin_dir.glob("*.yaml")]
