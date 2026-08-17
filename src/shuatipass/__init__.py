"""shuatipass - 中文题库 PDF 解析工具"""
__version__ = "0.1.0"
__author__ = "Mavis / shuatipass contributors"

from .parser import XueKeWangParser
from .parser import Question, Topic, ParsedDocument
from .config import ParseConfig, get_builtin, list_builtins
from .detect import detect_config, detect_with_details
from .generator import (
    GeneratedQuestion,
    generate_questions,
    generate_mock_exam,
    save_to_json,
    PROVIDERS as GENERATOR_PROVIDERS,
)
from .exam_mimic import (
    ExamStyle,
    analyze_exam_style,
    mimic_exam,
    build_mimic_prompt,
)
from .wrongbook import (
    load_questions,
    find_by_ids,
    find_by_tag,
    mark_questions,
    build_wrongbook,
    export_wrongbook,
    render_wrongbook_html,
)

__all__ = [
    "XueKeWangParser",
    "Question",
    "Topic",
    "ParsedDocument",
    "ParseConfig",
    "get_builtin",
    "list_builtins",
    "detect_config",
    "detect_with_details",
    "GeneratedQuestion",
    "generate_questions",
    "generate_mock_exam",
    "save_to_json",
    "GENERATOR_PROVIDERS",
    "ExamStyle",
    "analyze_exam_style",
    "mimic_exam",
    "load_questions",
    "find_by_ids",
    "find_by_tag",
    "mark_questions",
    "build_wrongbook",
    "export_wrongbook",
    "render_wrongbook_html",
    "__version__",
]


def launch_web(host="127.0.0.1", port=7860, share=False, **kwargs):
    """启动 Web UI（便捷函数）"""
    from .web import launch_web as _launch_web
    return _launch_web(host=host, port=port, share=share, **kwargs)
