"""
shuatipass Web UI —— Gradio 实现

启动: shuatipass web [--port 7860] [--host 0.0.0.0]
浏览器访问: http://localhost:7860
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

try:
    import gradio as gr

    HAS_GRADIO = True
except ImportError:
    HAS_GRADIO = False

from .config import get_builtin
from .detect import detect_config
from .parser import XueKeWangParser

PRESETS = ["auto", "xuekewang", "generic", "zujuan", "textbook"]


class _NoopProgress:
    """gradio 不可用时的空进度回调。

    🔴 没有它，`_parse_pdf` 在没装 gradio 的机器上会直接 NameError
    （原注释写"gradio 可能还没装"，但代码却直接用了 gr.Progress()），
    于是这个函数没法当纯库函数调用，也没法被不依赖 gradio 的测试覆盖。
    """

    def __call__(self, *args, **kwargs) -> None:
        return None


def _parse_pdf(
    pdf_path: str,
    preset: str,
    progress: gr.Progress | _NoopProgress | None = None,
) -> tuple[str, str, str, str | None]:
    """
    Gradio 调用的解析函数（也可当纯库函数用）

    Returns: (json_str, stats_text, preview_md, json_file_path)
    """
    if progress is None:
        # 🔴 这里**不**自己造 gr.Progress()：
        #   ① gradio 没装时那会直接 NameError；
        #   ② 自己造的进度条在非请求上下文里也不生效。
        # 真正的 UI 路径是 _build_ui → _on_parse，gradio 会把 progress
        # 按参数名注入给 _on_parse（SPECIAL_ARGS = {"progress", ...}），
        # 由它透传下来。所以走到这里就说明不是 gradio 调的 → 用空实现。
        progress = _NoopProgress()

    if not pdf_path:
        return "❌ 请先上传 PDF", "", "", None

    pdf = Path(pdf_path)
    if not pdf.exists():
        return f"❌ PDF 不存在: {pdf}", "", "", None

    # 选配置
    try:
        if preset == "auto":
            detected = detect_config(pdf)
            config = get_builtin(detected)
            preset_name = f"auto ({detected})"
        else:
            config = get_builtin(preset)
            preset_name = preset
    except Exception as e:
        return f"❌ 配置加载失败: {e}", "", "", None

    # 准备输出目录
    out_dir = Path(tempfile.mkdtemp(prefix="shuatipass-"))
    img_dir = out_dir / "images"
    img_dir.mkdir()

    progress(0.1, desc=f"开始解析（{preset_name}）...")

    try:
        parser = XueKeWangParser(pdf, img_dir, config=config, config_name=preset_name)
        result = parser.parse()
    except Exception as e:
        return f"❌ 解析失败: {e}", "", "", None

    progress(0.7, desc="生成输出...")

    # 写 JSON
    from dataclasses import asdict

    json_path = out_dir / "questions.json"
    json_path.write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 统计文本
    s = result.stats
    stats_text = "## 📊 统计\n\n"
    stats_text += f"- **文件**: {pdf.name}\n"
    stats_text += f"- **总页数**: {result.total_pages}\n"
    stats_text += f"- **专题数**: {s['total_topics']}\n"
    stats_text += f"- **题目数**: {s['total_questions']}\n"
    stats_text += f"- **跳过页**: {s['skipped_pages']}（考点分析页）\n"
    stats_text += f"- **使用配置**: {preset_name}\n"
    stats_text += "\n### 题型分布\n\n"
    for t, c in s["by_type"].items():
        stats_text += f"- `{t}`: {c} 题\n"

    # 专题列表
    stats_text += "\n### 专题列表\n\n"
    for t in asdict(result)["topics"]:
        n = len(t["questions"])
        stats_text += (
            f"- {t['topic_id']} **{t['title']}**: p{t['page_start']}-{t['page_end']} ({n} 题)\n"
        )

    # 题目预览（Markdown）
    progress(0.9, desc="生成预览...")
    preview_md = f"# 📄 {pdf.name}\n\n"
    preview_md += f"**配置**: {preset_name}  \n"
    preview_md += f"**题目**: {s['total_questions']}  \n"
    preview_md += f"**生成时间**: {json_path.stat().st_mtime}\n\n"
    preview_md += "---\n\n"

    # 预览前 5 专题 × 前 2 题
    for t in asdict(result)["topics"][:5]:
        preview_md += f"## 专题 {t['topic_id']} · {t['title']}\n\n"
        for q in t["questions"][:2]:
            preview_md += f"### 题 {q['number']} ({q.get('year', '')}·{q.get('province', '')})\n\n"
            preview_md += f"{q['stem']}\n\n"
            for k, v in q.get("options", {}).items():
                preview_md += f"- **{k}**. {v}\n"
            if q.get("images"):
                # 显示第一张图（base64）
                img_name = q["images"][0]
                img_path = img_dir / img_name
                if img_path.exists():
                    import base64

                    b64 = base64.b64encode(img_path.read_bytes()).decode()
                    ext = img_path.suffix.lstrip(".")
                    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
                    preview_md += f'\n<img src="data:{mime};base64,{b64}" width="300"/>\n\n'
            preview_md += "\n---\n\n"

    progress(1.0, desc="✅ 完成")

    return (
        json.dumps(asdict(result), ensure_ascii=False, indent=2),
        stats_text,
        preview_md,
        str(json_path),
    )


def _on_parse(
    pdf_path: str,
    preset: str,
    progress: gr.Progress | None = None,
) -> tuple[str | None, str, str]:
    """
    Gradio 事件回调：把 _parse_pdf 的 4 元组适配成 3 个 UI 输出。

    ⚠️ 返回顺序必须和 _build_ui 里 outputs 的顺序严格一一对应：
        outputs = [json_download, stats_output, preview_output]
        即（下载文件 / 统计 / 预览）。

    🔴 原来写的是 outputs=[gr.File(...), stats_output, preview_output] 去接 4 元组
    —— 数量对不上、顺序还错位。Gradio 在点击时会抛
    "Number of output components does not match..."，也就是说
    **Web UI 的「解析」按钮点了就炸**。这里做显式适配把它修掉。
    """
    json_str, stats_text, preview_md, file_path = _parse_pdf(pdf_path, preset, progress)
    if file_path is None:
        # 出错时 _parse_pdf 把错误信息放在第一个返回值里，
        # 而 File 组件显示不了错误字符串 → 改显示到统计栏
        return None, json_str, ""
    return file_path, stats_text, preview_md


def _build_ui():
    """构建 Gradio 界面"""
    with gr.Blocks(
        title="shuatipass · 中文题库 PDF 解析",
    ) as demo:
        gr.Markdown("""
            # 📚 shuatipass · 中文题库 PDF 解析工具

            把 PDF 题库（学科网/组卷网/教辅资料）一键转结构化 JSON。

            ---
            """)

        with gr.Tab("📤 解析 PDF"):
            with gr.Row():
                with gr.Column(scale=1):
                    pdf_input = gr.File(
                        label="上传 PDF",
                        file_types=[".pdf"],
                        type="filepath",
                    )
                    preset_input = gr.Radio(
                        choices=PRESETS,
                        value="auto",
                        label="配置选择",
                        info="auto = 自动检测；其他 = 内置预设",
                    )
                    parse_btn = gr.Button("🚀 解析", variant="primary", size="lg")

                with gr.Column(scale=2):
                    stats_output = gr.Markdown(label="统计信息")

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 题目预览（前 10 题）")
                    preview_output = gr.Markdown()

            with gr.Row():
                json_download = gr.File(
                    label="下载 JSON",
                    interactive=False,
                )

            # 事件
            parse_btn.click(
                fn=_on_parse,
                inputs=[pdf_input, preset_input],
                outputs=[
                    json_download,
                    stats_output,
                    preview_output,
                ],
            )

        with gr.Tab("📖 使用说明"):
            gr.Markdown("""
                ## 三步上手

                ### 1. 上传 PDF
                点击 "上传 PDF"，选你的题库文件（学科网/组卷网/教辅）。

                ### 2. 选配置
                - **auto**（推荐）：自动检测来源
                - **xuekewang**：学科网格式（严格）
                - **generic**：通用宽松
                - **zujuan**：组卷网
                - **textbook**：教辅资料

                ### 3. 点 "解析"
                几秒到几分钟后，右侧会显示：
                - 统计信息（专题数/题目数/年份分布）
                - 题目预览（带图片）
                - JSON 下载链接

                ## 高级用法（命令行）

                ```bash
                # 命令行模式
                shuatipass parse input.pdf -o out.json --auto

                # Python 库
                from shuatipass import XueKeWangParser, get_builtin
                parser = XueKeWangParser("input.pdf", "./images", config=get_builtin("auto"))
                result = parser.parse()
                ```

                ## 安装

                ```bash
                pip install shuatipass
                ```

                或从 GitHub 安装最新版：
                ```bash
                pip install git+https://github.com/242742532Celestia/shuatipass.git
                ```
                """)

        with gr.Tab("🔧 关于"):
            gr.Markdown("""
                ## shuatipass

                中文圈首个面向开发者的题库 PDF 解析工具。

                - 🐙 GitHub: https://github.com/242742532Celestia/shuatipass
                - 📦 PyPI: https://pypi.org/project/shuatipass/
                - 📖 文档: https://github.com/242742532Celestia/shuatipass#readme
                - 📜 License: MIT

                ## 路线图

                - [x] 学科网格式解析
                - [x] 通用宽松模式
                - [x] 自动检测
                - [x] 组卷网/教辅格式
                - [x] 公式 OCR（Mathpix/pix2tex）
                - [x] Docker 镜像
                - [x] CI/CD
                - [x] PyPI 发布
                - [x] Gradio Web UI ✅

                ## 反馈

                Bug / Feature Request：https://github.com/242742532Celestia/shuatipass/issues
                """)

    return demo


def launch_web(
    host: str = "127.0.0.1",
    port: int = 7860,
    share: bool = False,
    server_name: str | None = None,
    server_port: int | None = None,
    **kwargs,
):
    """启动 Web UI"""
    if not HAS_GRADIO:
        raise ImportError("需要安装 gradio: pip install gradio\n" "或: pip install shuatipass[web]")

    demo = _build_ui()
    demo.launch(
        server_name=host,
        server_port=port,
        share=share,
        theme=gr.themes.Soft(),
        **kwargs,
    )


def is_available() -> bool:
    """检查 Gradio 是否可用"""
    return HAS_GRADIO
