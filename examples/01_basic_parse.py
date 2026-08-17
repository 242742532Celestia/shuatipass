"""
Example 01: 最简解析 —— 把 PDF 一行变 JSON

用法:
    python examples/01_basic_parse.py data/input/物理-高考真题-学科网.pdf
"""
import sys
from pathlib import Path
from shuatipass import XueKeWangParser, get_builtin


def main():
    if len(sys.argv) < 2:
        print("用法: python 01_basic_parse.py <pdf_path> [output_json]")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else pdf_path.with_suffix(".json")

    if not pdf_path.exists():
        print(f"❌ PDF 不存在: {pdf_path}")
        sys.exit(1)

    print(f"📄 解析: {pdf_path}")
    print(f"   输出: {out_path}")

    # 一行解析 —— 用默认（学科网）配置
    parser = XueKeWangParser(
        pdf_path,
        image_dir=out_path.parent / "images",
        config=get_builtin("xuekewang"),
    )
    result = parser.parse()

    # 写 JSON
    import json
    from dataclasses import asdict
    out_path.write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 统计
    s = result.stats
    print(f"\n✅ 解析完成")
    print(f"   专题: {s['total_topics']} | 题目: {s['total_questions']} | 跳过: {s['skipped_pages']} 页")
    print(f"   题型: {s['by_type']}")
    print(f"   JSON: {out_path}")


if __name__ == "__main__":
    main()
