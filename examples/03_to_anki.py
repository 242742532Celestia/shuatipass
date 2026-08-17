"""
Example 03: JSON → Anki 卡片（TSV 格式）

Anki 导入: File → Import → 选这个 .tsv → 设置字段映射

用法:
    python examples/03_to_anki.py questions.json anki_cards.tsv
"""
import sys
import json
import csv
from pathlib import Path


def main():
    if len(sys.argv) < 3:
        print("用法: python 03_to_anki.py <questions.json> <output.tsv>")
        sys.exit(1)

    src = Path(sys.argv[1])
    out = Path(sys.argv[2])

    if not src.exists():
        print(f"❌ JSON 不存在: {src}")
        sys.exit(1)

    with src.open() as f:
        data = json.load(f)

    # Anki TSV 格式: 正面<TAB>背面<TAB>标签
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        # 第一行是字段名（Anki 用）
        writer.writerow(["题干", "选项", "答案", "来源"])

        for t in data["topics"]:
            for q in t["questions"]:
                if not q.get("options"):
                    continue
                # 正面: 题干 + 选项
                front = q["stem"]
                # 背面: 4 个选项
                opts = q.get("options", {})
                back = "\n".join(f"{k}. {v}" for k, v in sorted(opts.items()))
                # 答案（如果有）
                answer = q.get("answer") or "?"
                # 来源
                source = f"{t['title']} | {q.get('year','')}·{q.get('province','')} | 题{q['number']}"
                writer.writerow([front, back, answer, source])

    count = sum(1 for t in data["topics"] for q in t["questions"] if q.get("options"))
    print(f"✅ 已导出 {count} 张 Anki 卡片到 {out}")
    print(f"   Anki 导入: File → Import → 选 TSV → Separator: Tab")


if __name__ == "__main__":
    main()
