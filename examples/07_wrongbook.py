"""
Example 07: 错题本使用示例

用法:
    # 1. 标记错题
    python examples/07_wrongbook.py mark data/parsed/q-xk.json \\
        --ids "01-001,01-002,02-001" --action mark

    # 2. 导出 JSON
    python examples/07_wrongbook.py export data/parsed/q-xk.json \\
        -o /tmp/wb.json --tag 错题

    # 3. 导出 HTML（打印友好）
    python examples/07_wrongbook.py export data/parsed/q-xk.json \\
        --out-html /tmp/wb.html --tag 错题

    # 4. 按知识点分组的错题本
    python examples/07_wrongbook.py export data/parsed/q-xk.json \\
        --out-html /tmp/wb-topic.html --group-by topic

    # 5. 手动指定题目 ID
    python examples/07_wrongbook.py export data/parsed/q-xk.json \\
        --ids "01-001,01-005" \\
        --out-html /tmp/wb-selected.html
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))


def cmd_mark(args):
    from shuatipass.wrongbook import mark_questions
    ids = [i.strip() for i in args.ids.split(",") if i.strip()]
    result = mark_questions(
        json_path=args.json,
        question_ids=ids,
        action=args.action,
        tag=args.tag,
    )
    verb = "标记" if args.action == "mark" else "取消标记"
    n = result['marked'] if args.action == 'mark' else result['unmarked']
    print(f"🏷️  {verb}: {n} 道题")
    if result["not_found"]:
        print(f"⚠️  未找到: {result['not_found']}")


def cmd_export(args):
    from shuatipass.wrongbook import export_wrongbook
    ids = None
    if args.ids:
        ids = [i.strip() for i in args.ids.split(",") if i.strip()]
    export_wrongbook(
        source_json=args.json,
        output_json=args.out,
        output_html=args.out_html,
        ids=ids,
        tag=args.tag,
        group_by=args.group_by,
        title=args.title,
    )


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    sub = sys.argv[1]
    args = sys.argv[2:]

    if sub == "mark":
        # parse: json --ids X --action Y --tag Z
        json_path = args[0]
        ids = None
        action = "mark"
        tag = "错题"
        for i, a in enumerate(args):
            if a == "--ids": ids = args[i+1]
            elif a == "--action": action = args[i+1]
            elif a == "--tag": tag = args[i+1]
        class A: pass
        a = A()
        a.json = json_path
        a.ids = ids
        a.action = action
        a.tag = tag
        cmd_mark(a)
    elif sub == "export":
        json_path = args[0]
        out = None
        out_html = None
        ids = None
        tag = "错题"
        group_by = "knowledge_point"
        title = "错题本"
        for i, a in enumerate(args):
            if a in ("-o", "--out"): out = args[i+1]
            elif a == "--out-html": out_html = args[i+1]
            elif a == "--ids": ids = args[i+1]
            elif a == "--tag": tag = args[i+1]
            elif a == "--group-by": group_by = args[i+1]
            elif a == "--title": title = args[i+1]
        class A: pass
        a = A()
        a.json = json_path
        a.out = out
        a.out_html = out_html
        a.ids = ids
        a.tag = tag
        a.group_by = group_by
        a.title = title
        cmd_export(a)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
