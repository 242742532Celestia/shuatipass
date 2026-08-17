"""
Example 04: JSON → RAG 文档块（喂给 LangChain / LlamaIndex）

用法:
    pip install langchain
    python examples/04_rag_chunks.py questions.json rag_docs.json
"""
import sys
import json
from pathlib import Path


def main():
    if len(sys.argv) < 3:
        print("用法: python 04_rag_chunks.py <questions.json> <output.json>")
        sys.exit(1)

    src = Path(sys.argv[1])
    out = Path(sys.argv[2])

    if not src.exists():
        print(f"❌ JSON 不存在: {src}")
        sys.exit(1)

    with src.open() as f:
        data = json.load(f)

    # 转 RAG 友好的文本块
    chunks = []
    for t in data["topics"]:
        for q in t["questions"]:
            text = f"【专题】{t['title']}\n"
            text += f"【题号】{q['number']}\n"
            if q.get("year"):
                text += f"【年份】{q['year']}\n"
            if q.get("province"):
                text += f"【省份】{q['province']}\n"
            text += f"【题型】{q.get('type', '?')}\n"
            text += f"【题干】{q['stem']}\n"
            for k, v in q.get("options", {}).items():
                text += f"【选项{k}】{v}\n"
            if q.get("formula_latex"):
                text += f"【公式】{q['formula_latex']}\n"

            chunks.append({
                "text": text.strip(),
                "metadata": {
                    "topic": t["title"],
                    "topic_id": t["topic_id"],
                    "year": q.get("year"),
                    "province": q.get("province"),
                    "type": q.get("type"),
                    "question_id": q.get("id"),
                },
            })

    # 保存
    with out.open("w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"✅ 已生成 {len(chunks)} 个 RAG 文档块到 {out}")
    print()
    print("接下来可以：")
    print("  # 用 LangChain 向量化")
    print("  from langchain.schema import Document")
    print("  from langchain.embeddings import OpenAIEmbeddings")
    print("  from langchain.vectorstores import FAISS")
    print()
    print("  docs = [Document(page_content=c['text'], metadata=c['metadata']) for c in chunks]")
    print("  embeddings = OpenAIEmbeddings()")
    print("  db = FAISS.from_documents(docs, embeddings)")
    print("  db.save_local('my_exam_db')")


if __name__ == "__main__":
    main()
