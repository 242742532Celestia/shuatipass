# shuatipass 实战示例

> 9 个真实场景示例 —— 从基础到高级。

## 1. 把题库转成 Markdown 试卷

```python
import json
from pathlib import Path

with open("questions.json") as f:
    data = json.load(f)

lines = ["# 物理练习册\n"]
for t in data["topics"]:
    lines.append(f"\n## {t['title']}\n")
    for q in t["questions"]:
        lines.append(f"\n### 题 {q['number']}（{q.get('year','')}·{q.get('province','')}）\n")
        lines.append(f"{q['stem']}\n")
        for k, v in q["options"].items():
            lines.append(f"- **{k}**. {v}\n")

Path("物理练习册.md").write_text("\n".join(lines), encoding="utf-8")
```

## 2. 按年份/省份筛选题目

```python
import json

with open("questions.json") as f:
    data = json.load(f)

# 找 2025 年所有黑吉辽的题
selected = []
for t in data["topics"]:
    for q in t["questions"]:
        if q.get("year") == 2025 and "黑吉辽" in (q.get("province") or ""):
            selected.append(q)

print(f"找到 {len(selected)} 道题")
for q in selected[:3]:
    print(f"  题 {q['number']}: {q['stem'][:50]}...")
```

## 3. 导出为 Anki 卡片

```python
import json
import csv

with open("questions.json") as f:
    data = json.load(f)

# Anki 用 TSV 导入
with open("anki-import.tsv", "w", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter="\t")
    for t in data["topics"]:
        for q in t["questions"]:
            if not q["options"]:
                continue
            # 正面: 题干 + 选项
            front = f"{q['stem']}\n"
            for k, v in q["options"].items():
                front += f"\n{k}. {v}"
            # 背面: 留空（用户自己填答案）
            back = ""
            writer.writerow([front, back, t["title"], f"{q.get('year','')}"])
```

## 4. 生成 RAG 用的文本块

```python
import json
from langchain.schema import Document

with open("questions.json") as f:
    data = json.load(f)

docs = []
for t in data["topics"]:
    for q in t["questions"]:
        text = f"【专题】{t['title']}\n【题号】{q['number']}\n【年份】{q.get('year')}\n【省份】{q.get('province')}\n"
        text += f"【题型】{q['type']}\n【题干】{q['stem']}\n"
        for k, v in q["options"].items():
            text += f"【{k}】{v}\n"
        docs.append(Document(page_content=text, metadata={
            "topic": t["title"],
            "year": q.get("year"),
            "province": q.get("province"),
        }))

print(f"生成 {len(docs)} 个 RAG 文档块")
# 然后用 FAISS / Chroma / Pinecone 向量化
```

## 5. 按题型分组输出

```python
import json
from collections import defaultdict

with open("questions.json") as f:
    data = json.load(f)

by_type = defaultdict(list)
for t in data["topics"]:
    for q in t["questions"]:
        by_type[q["type"]].append(q)

for qtype, qs in by_type.items():
    print(f"\n=== {qtype} ({len(qs)} 题) ===")
    for q in qs[:2]:
        print(f"  题 {q['number']}: {q['stem'][:50]}...")
```

## 6. 找出最难的题（题干最长）

```python
import json

with open("questions.json") as f:
    data = json.load(f)

all_q = [(t, q) for t in data["topics"] for q in t["questions"]]
all_q.sort(key=lambda x: len(x[1]["stem"]), reverse=True)

print("题干最长的 5 道题：")
for t, q in all_q[:5]:
    print(f"\n  [{t['title']}] 题 {q['number']}（{len(q['stem'])}字）")
    print(f"  {q['stem'][:80]}...")
```

## 7. 批量处理多个 PDF

```bash
# 批量解析某目录下所有 PDF
for pdf in *.pdf; do
  echo "处理: $pdf"
  shuatipass parse "$pdf" -o "${pdf%.pdf}.json" --images "./images/${pdf%.pdf}"
done
```

Python 版本：

```python
from pathlib import Path
from shuatipass import XueKeWangParser

for pdf_path in Path(".").glob("*.pdf"):
    out_dir = Path("output") / pdf_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    
    parser = XueKeWangParser(pdf_path, out_dir / "images")
    result = parser.parse()
    
    import json
    from dataclasses import asdict
    out_json = out_dir / "questions.json"
    out_json.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    
    print(f"✅ {pdf_path.name}: {result.stats['total_questions']} 题")
```

## 8. 自定义配置：组卷网格式

组卷网（zujuan.com）的 PDF 格式和学科网略有不同。写一个 YAML：

```yaml
# src/shuatipass/configs/zujuan.yaml
name: 组卷网
description: 组卷网题库 PDF 解析

question_pattern: '^(\d+)\s*[．\.]\s*(.{20,})'
option_pattern: '^([A-D])[．\.]\s*(.*)$'

# 组卷网没有标准页眉
header_pattern: ''
has_question_pattern: '^\d+\s*[．\.、]'

option_keys: [A, B, C, D]
essay_keywords: [求, 证明, 计算, 解答]
skip_patterns: ['组\s*卷\s*网', '学科网']
skip_exact_lines: []
```

使用：

```bash
shuatipass parse 组卷网-数学.pdf -o out.json --config src/shuatipass/configs/zujuan.yaml
```

## 9. 在 Jupyter Notebook 里交互探索

```python
import json
import pandas as pd
from pathlib import Path

with open("questions.json") as f:
    data = json.load(f)

# 转成 DataFrame 探索
rows = []
for t in data["topics"]:
    for q in t["questions"]:
        rows.append({
            "专题": t["title"],
            "题号": q["number"],
            "年份": q.get("year"),
            "省份": q.get("province"),
            "题型": q["type"],
            "题长": len(q["stem"]),
            "选项数": len(q["options"]),
            "图片数": len(q["images"]),
            "页码": q["source_page"],
        })

df = pd.DataFrame(rows)
df.head()

# 统计
print("题型分布：")
print(df["题型"].value_counts())

print("\n按年份统计：")
print(df.groupby("年份").size())

# 找没有图片的选择题（可能是不完整的）
print("\n没有图片的选择题：")
print(df[(df["题型"]=="single_choice") & (df["图片数"]==0)].head())
```

## 10. 跨页题合并（高级）

shuatipass 当前默认不自动合并跨页题，需要手动处理：

```python
import json

with open("questions.json") as f:
    data = json.load(f)

# 找题号连续但跨页的题对
for t in data["topics"]:
    qs = t["questions"]
    for i in range(len(qs) - 1):
        if qs[i]["number"] + 1 == qs[i+1]["number"] and qs[i]["source_page"] != qs[i+1]["source_page"]:
            print(f"专题 {t['topic_id']} 题 {qs[i]['number']}-{qs[i+1]['number']} 跨页 (p{qs[i]['source_page']} → p{qs[i+1]['source_page']})")
```

## 11. 检查解析质量

```python
import json
from collections import Counter

with open("questions.json") as f:
    data = json.load(f)

issues = []

for t in data["topics"]:
    for q in t["questions"]:
        # 选择题必须有 4 个选项
        if q["type"] == "single_choice" and len(q["options"]) != 4:
            issues.append(f"题 {q['id']}: 单选但选项 {len(q['options'])} 个")
        # 题干不能太短
        if len(q["stem"]) < 10:
            issues.append(f"题 {q['id']}: 题干太短（{len(q['stem'])}字）")
        # 题号应该连续
        # （略）

print(f"发现 {len(issues)} 个问题：")
for issue in issues[:10]:
    print(f"  - {issue}")
```

## 12. 用 LLM 给题目加答案和解析

```python
import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["MINIMAX_API_KEY"], base_url="https://api.minimax.chat/v1")

with open("questions.json") as f:
    data = json.load(f)

# 选前 3 道没有答案的题
to_answer = []
for t in data["topics"]:
    for q in t["questions"]:
        if q["type"] == "single_choice" and not q.get("answer"):
            to_answer.append(q)
            if len(to_answer) >= 3:
                break
    if len(to_answer) >= 3:
        break

for q in to_answer:
    prompt = f"请回答这道物理选择题，给出答案和详细解析：\n\n{q['stem']}\n"
    for k, v in q["options"].items():
        prompt += f"{k}. {v}\n"
    prompt += "\n请用 JSON 格式返回：{\"answer\": \"X\", \"explanation\": \"...\"}"

    resp = client.chat.completions.create(
        model="MiniMax-Text-01",
        messages=[{"role": "user", "content": prompt}],
    )
    result = json.loads(resp.choices[0].message.content)
    q["answer"] = result["answer"]
    q["explanation"] = result["explanation"]
    print(f"题 {q['id']}: 答案 = {q['answer']}")

# 保存
from dataclasses import asdict
with open("questions-with-answers.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

> 提示：用了 `MINIMAX_API_KEY` 环境变量（项目已有的 secret）。换成 OpenAI/Claude 也一样。
