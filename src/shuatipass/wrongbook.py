"""
shuatipass 错题本 —— 借鉴 DEEPTUTOR 的 Personal Notebook

功能：
1. 从题库中按 ID 提取错题
2. 按 tag 过滤（"错题"/"难题"）
3. 按知识点分类汇总
4. 输出错题本 JSON + HTML 报告
5. 支持"标记错题"和"取消标记"
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from ._console import enable_console_compat


def load_questions(json_path: str | Path) -> list[dict]:
    """从 JSON 加载所有题目（展平）"""
    p = Path(json_path)
    if not p.exists():
        raise FileNotFoundError(f"JSON 不存在: {p}")

    with p.open(encoding="utf-8") as f:
        data = json.load(f)

    questions = []
    for t in data.get("topics", []):
        for q in t.get("questions", []):
            q["_topic_id"] = t.get("topic_id", "")
            q["_topic_title"] = t.get("title", "未知")
            questions.append(q)

    return questions


def find_by_ids(questions: list, ids: list[str]) -> list[dict]:
    """按 ID 查找题目（支持精确匹配和模糊匹配）"""
    id_set = set(ids)
    result = []
    for q in questions:
        if q.get("id") in id_set:
            result.append(q)
    return result


def find_by_tag(questions: list, tag: str) -> list[dict]:
    """按 tag 过滤"""
    return [q for q in questions if tag in q.get("tags", [])]


def mark_questions(
    json_path: str | Path,
    question_ids: list[str],
    action: str = "mark",  # mark / unmark
    tag: str = "错题",
    output: str | Path | None = None,
) -> dict:
    """
    标记/取消标记错题

    Args:
        json_path: 题库 JSON
        question_ids: 要标记的题目 ID 列表
        action: "mark" 或 "unmark"
        tag: 标签名（默认 "错题"）
        output: 输出路径（None = 覆盖原文件）

    Returns:
        {"marked": N, "unmarked": N, "not_found": [...]}
    """
    p = Path(json_path)
    with p.open(encoding="utf-8") as f:
        data = json.load(f)

    marked_count = 0
    not_found = []

    for t in data.get("topics", []):
        for q in t.get("questions", []):
            if q.get("id") in question_ids:
                tags = q.setdefault("tags", [])
                if action == "mark":
                    if tag not in tags:
                        tags.append(tag)
                        marked_count += 1
                elif action == "unmark":
                    if tag in tags:
                        tags.remove(tag)
                        marked_count += 1
                # 标记已处理
                if q.get("id") in question_ids:
                    question_ids = [x for x in question_ids if x != q.get("id")]

    not_found = question_ids  # 剩下的就是没找到的

    # 保存
    out_path = Path(output) if output else p
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "marked": marked_count if action == "mark" else 0,
        "unmarked": marked_count if action == "unmark" else 0,
        "not_found": not_found,
        "output": str(out_path),
    }


def build_wrongbook(
    questions: list[dict],
    group_by: str = "knowledge_point",  # knowledge_point / topic / year / difficulty
) -> dict:
    """
    构建错题本

    Returns:
        {
            "total": int,
            "groups": {
                "知识点1": [q1, q2, ...],
                "知识点2": [...],
            },
            "stats": {...}
        }
    """
    # 分组
    groups = defaultdict(list)
    for q in questions:
        if group_by == "knowledge_point":
            key = q.get("knowledge_point") or q.get("_topic_title", "未知")
        elif group_by == "topic":
            key = q.get("_topic_title", "未知")
        elif group_by == "year":
            key = str(q.get("year", "未知"))
        elif group_by == "difficulty":
            key = q.get("difficulty", "未知")
        else:
            key = "未分组"
        groups[key].append(q)

    # 统计
    stats = {
        "total": len(questions),
        "groups_count": len(groups),
        "by_type": {},
        "by_year": {},
    }
    for q in questions:
        t = q.get("type", "unknown")
        stats["by_type"][t] = stats["by_type"].get(t, 0) + 1
        y = str(q.get("year", "未知"))
        stats["by_year"][y] = stats["by_year"].get(y, 0) + 1

    return {
        "total": len(questions),
        "group_by": group_by,
        "groups": dict(groups),
        "groups_count": len(groups),
        "stats": stats,
    }


def render_wrongbook_html(wrongbook: dict, title: str = "错题本") -> str:
    """渲染错题本为 HTML（适合打印）"""
    html = [f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{title}</title>"]
    html.append("""<style>
body { font-family: -apple-system, sans-serif; max-width: 900px; margin: 24px auto; padding: 0 20px; color: #222; }
h1 { border-bottom: 2px solid #333; padding-bottom: 8px; }
h2 { background: #fff3e0; padding: 10px 16px; border-left: 4px solid #ff9800; margin-top: 32px; }
.q { background: white; padding: 16px 20px; margin: 12px 0; border: 1px solid #ddd; border-radius: 6px; }
.q .meta { color: #666; font-size: 13px; margin-bottom: 8px; }
.q .badge { display: inline-block; background: #1976d2; color: white; font-size: 12px; padding: 2px 8px; border-radius: 10px; margin-right: 6px; }
.q .badge.topic { background: #9c27b0; }
.q .badge.year { background: #43a047; }
.q .badge.type { background: #fb8c00; }
.q .stem { line-height: 1.7; margin: 8px 0; }
.q .options { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 8px; }
.q .opt { background: #f5f5f5; padding: 6px 10px; border-radius: 4px; font-size: 14px; }
.q .answer { background: #e8f5e9; padding: 8px 12px; border-left: 3px solid #4caf50; margin-top: 12px; font-size: 14px; }
.summary { background: #f3e5f5; padding: 12px 20px; border-radius: 6px; margin: 16px 0; }
</style></head><body>""")
    html.append(f"<h1>📒 {title}</h1>")
    html.append('<div class="summary">')
    html.append(f'<b>总题数</b>: {wrongbook["total"]} | ')
    html.append(f'<b>分组数</b>: {wrongbook["groups_count"]} | ')
    html.append(f'<b>分组方式</b>: {wrongbook["group_by"]}<br>')
    html.append(f'<b>题型分布</b>: {wrongbook["stats"]["by_type"]} | ')
    html.append(f'<b>年份分布</b>: {wrongbook["stats"]["by_year"]}')
    html.append("</div>")

    for group_name, qs in wrongbook["groups"].items():
        html.append(f"<h2>{group_name}（{len(qs)} 题）</h2>")
        for q in qs:
            html.append('<div class="q">')
            html.append('<div class="meta">')
            html.append(f'<span class="badge topic">{q.get("_topic_title", "")}</span>')
            if q.get("year"):
                html.append(f'<span class="badge year">{q.get("year")}</span>')
            if q.get("province"):
                html.append(f'<span class="badge">{q.get("province")}</span>')
            html.append(f'<span class="badge type">{q.get("type", "")}</span>')
            html.append(
                f'<span style="color:#999">题号 {q.get("number", "")} · p{q.get("source_page", "")}</span>'
            )
            html.append("</div>")
            html.append(f'<div class="stem">{q.get("stem", "")}</div>')
            if q.get("options"):
                html.append('<div class="options">')
                for k, v in q["options"].items():
                    html.append(f'<div class="opt"><b>{k}.</b> {v}</div>')
                html.append("</div>")
            # 答案
            answer = q.get("answer", "")
            explanation = q.get("explanation", "")
            if answer or explanation:
                html.append('<div class="answer">')
                if answer:
                    html.append(f"<b>答案</b>: {answer}<br>")
                if explanation:
                    html.append(f"<b>解析</b>: {explanation}")
                html.append("</div>")
            html.append("</div>")

    html.append("</body></html>")
    return "\n".join(html)


def export_wrongbook(
    source_json: str | Path,
    output_json: str | Path = None,
    output_html: str | Path = None,
    ids: list[str] = None,
    tag: str = "错题",
    group_by: str = "knowledge_point",
    title: str = "错题本",
) -> dict:
    """
    导出错题本

    Args:
        source_json: 题库 JSON
        output_json: 错题本 JSON 路径（None = 不输出）
        output_html: 错题本 HTML 路径（None = 不输出）
        ids: 指定题目 ID 列表（None = 用 tag 过滤）
        tag: 用 tag 过滤时的标签名
        group_by: 分组方式
        title: HTML 标题

    Returns:
        wrongbook dict
    """
    enable_console_compat()  # Windows GBK 控制台扛不住 emoji
    all_questions = load_questions(source_json)

    if ids:
        questions = find_by_ids(all_questions, ids)
    else:
        questions = find_by_tag(all_questions, tag)

    if not questions:
        print("⚠️  没找到符合条件的题目")
        return {"total": 0, "groups": {}, "stats": {}}

    wrongbook = build_wrongbook(questions, group_by=group_by)

    print(f"📒 错题本: {wrongbook['total']} 题，分 {wrongbook['groups_count']} 组")

    if output_json:
        out = Path(output_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(wrongbook, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"   JSON: {out}")

    if output_html:
        out = Path(output_html)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            render_wrongbook_html(wrongbook, title=title),
            encoding="utf-8",
        )
        print(f"   HTML: {out}")

    return wrongbook
