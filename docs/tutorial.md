# shuatipass 新用户教程

> 5 分钟上手 shuatipass —— 从 0 到把第一份 PDF 转成结构化 JSON。

## 你能用 shuatipass 做什么

把"PDF 题库"（学科网/组卷网/教辅资料）一键转成结构化 JSON，附带图片库。然后你就可以：
- 拿 JSON 搭在线题库系统
- 用 JSON 喂给 AI 做 RAG / 微调
- 拿 JSON 生成 A4 试卷、答题卡、错题本
- 自己写脚本批量处理任意题库

## 安装

```bash
# 推荐：Python 3.10+ 
pip install shuatipass
```

或从 GitHub 安装最新版：

```bash
pip install git+https://github.com/yourname/shuatipass.git
```

## 最快上手：3 条命令

### 第 1 步：把 PDF 放好

```bash
mkdir my-paper
cp ~/Downloads/物理-高考真题.pdf my-paper/
cd my-paper
```

### 第 2 步：解析

```bash
shuatipass parse 物理-高考真题.pdf -o questions.json
```

输出：
```
📄 解析: 物理-高考真题.pdf
   配置: 默认 (xuekewang)
   输出: questions.json
   图片: questions.json所在目录/images

✅ 解析完成
   专题: 14 | 题目: 821 | 跳过: 14 页
   题型: {'single_choice': 684, 'essay': 121, 'essay_with_options': 16}
```

产物：
- `questions.json` —— 结构化题库（~1MB）
- `images/` —— 1559 张图，按 `t01-p001-i01.jpeg` 命名（17MB）

### 第 3 步：看效果

```bash
shuatipass stats questions.json
```

输出：
```
📊 questions.json
   来源: 物理-高考真题.pdf
   总页: 423
   专题: 14
   题目: 821
   题型: {'single_choice': 684, 'essay': 121, 'essay_with_options': 16}
   年份: [(2021, 143), (2022, 123), (2023, 154), (2024, 201), (2025, 193)]

   专题分布:
     专题 01 直线运动                   p  1-20   48 题
     专题 02 相互作用                   p 21-37   42 题
     ...
```

## 接下来怎么用 JSON

最常见的几种用法：

### 用法 1：把题目转成 Markdown 给 AI

```python
import json

with open("questions.json") as f:
    data = json.load(f)

# 输出第 1 道题
q = data["topics"][0]["questions"][0]
md = f"""
# 题 {q['number']}（{q['year']}·{q['province']}）

{q['stem']}

"""
for k, v in q["options"].items():
    md += f"- **{k}**. {v}\n"

print(md)
```

输出：
```
# 题 1（2025·黑吉辽蒙卷）

书法课上，某同学临摹"力"字时，笔尖的轨迹如图中带箭头的实线所示。
笔尖由a点经b点回到a点，则（ ）

- **A**. 该过程位移为0
- **B**. 该过程路程为0
- **C**. 两次过a点时速度方向相同
- **D**. 两次过a点时摩擦力方向相同
```

### 用法 2：导出为 Excel

```python
import json
import openpyxl

wb = openpyxl.Workbook()
ws = wb.active
ws.append(["专题", "题号", "年份", "省份", "题型", "题干", "A", "B", "C", "D", "答案"])

with open("questions.json") as f:
    data = json.load(f)

for t in data["topics"]:
    for q in t["questions"]:
        opts = q["options"]
        ws.append([
            t["title"], q["number"], q.get("year"), q.get("province"),
            q["type"], q["stem"],
            opts.get("A", ""), opts.get("B", ""), opts.get("C", ""), opts.get("D", ""),
            q.get("answer", ""),
        ])

wb.save("题库.xlsx")
```

### 用法 3：喂给大模型做 RAG

```python
import json

with open("questions.json") as f:
    data = json.load(f)

# 转成 RAG 友好的文本
docs = []
for t in data["topics"]:
    for q in t["questions"]:
        text = f"【专题】{t['title']}\n【题号】{q['number']}\n【年份】{q.get('year')}\n【省份】{q.get('province')}\n【题干】{q['stem']}\n"
        for k, v in q["options"].items():
            text += f"【选项{k}】{v}\n"
        docs.append(text)

# 把 docs 喂给 LangChain / LlamaIndex 做向量化
from langchain.schema import Document
lc_docs = [Document(page_content=d) for d in docs]
```

## 如果你的 PDF 不是学科网格式

shuatipass 有 3 个内置预设：

| 预设 | 适用 |
|------|------|
| `xuekewang` | 学科网（默认）|
| `generic` | 通用宽松（不知道格式时用）|
| 自定义 | 写自己的 YAML |

试用通用模式：

```bash
shuatipass parse input.pdf -o out.json --preset generic
```

通用模式识别更激进（可能多识别一些"假题目"），但兼容更多格式。

## 写自己的 YAML 规则

如果你的 PDF 是其他来源（组卷网/某教辅/自出版），可以写一个 YAML：

```bash
shuatipass parse input.pdf -o out.json --config my-rules.yaml
```

最简配置（参考 `configs/generic.yaml`）：

```yaml
name: 我的教辅
question_pattern: '^(\d+)\s*[．\.、]\s*(.{10,})'
option_pattern: '^([A-D])[．\.]\s*(.*)$'
option_keys: [A, B, C, D]
essay_keywords: [求, 证明, 计算]
```

完整字段说明见 [API 参考](api.md#配置字段)。

## 进阶

- 想看完整的 API：[api.md](api.md)
- 想看更多用例：[examples.md](examples.md)
- 想自定义解析规则：[config.md](config.md)

## 故障排查

### 问题：解析出 0 题

**原因**：PDF 格式与默认配置不匹配

**解决**：
```bash
# 1. 先用通用模式试试
shuatipass parse input.pdf -o out.json --preset generic

# 2. 通用模式有题但默认没有 → 写自定义 YAML
# 3. 通用也没题 → 你的 PDF 可能是扫描版，需要先 OCR
```

### 问题：图片归错题（多题图堆一起）

**已知问题**：D2 已优化大部分场景。极少数题仍有图归错。
**临时方案**：用 JSON 的 `bbox` 字段手动调整，或提 issue。

### 问题：选项没识别（"C．...D．..."拼一行）

**已修复**（D2）。如果你的 PDF 也有这类问题，检查 YAML 的 `option_pattern` 是否支持内嵌。

### 问题：YAML 加载报错

常见原因：YAML 里的 `:` 字符被解析为 mapping。
解决：用引号包起来，例如 `"解:"` 而不是 `解:`。
