"""
Example 02: JSON → Excel

用法:
    pip install openpyxl
    python examples/02_to_excel.py questions.json 题库.xlsx
"""
import sys
import json
from pathlib import Path


def main():
    if len(sys.argv) < 3:
        print("用法: python 02_to_excel.py <questions.json> <output.xlsx>")
        sys.exit(1)

    src = Path(sys.argv[1])
    out = Path(sys.argv[2])

    if not src.exists():
        print(f"❌ JSON 不存在: {src}")
        sys.exit(1)

    try:
        import openpyxl
    except ImportError:
        print("❌ 需要安装 openpyxl: pip install openpyxl")
        sys.exit(1)

    with src.open() as f:
        data = json.load(f)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "题库"

    # 表头
    ws.append([
        "专题", "题号", "年份", "省份", "题型", "题干",
        "A", "B", "C", "D", "E",
        "图片数", "来源页", "公式LaTeX", "公式置信度",
    ])

    # 调列宽
    ws.column_dimensions["F"].width = 60  # 题干
    for col in "ABCDE":
        ws.column_dimensions[col].width = 30

    # 数据
    for t in data["topics"]:
        for q in t["questions"]:
            opts = q.get("options", {})
            ws.append([
                t["title"],
                q["number"],
                q.get("year", ""),
                q.get("province", ""),
                q.get("type", ""),
                q.get("stem", ""),
                opts.get("A", ""),
                opts.get("B", ""),
                opts.get("C", ""),
                opts.get("D", ""),
                opts.get("E", ""),
                len(q.get("images", [])),
                q.get("source_page", ""),
                q.get("formula_latex", ""),
                q.get("formula_confidence", ""),
            ])

    wb.save(out)
    total = sum(len(t["questions"]) for t in data["topics"])
    print(f"✅ 已导出 {total} 题到 {out}")


if __name__ == "__main__":
    main()
