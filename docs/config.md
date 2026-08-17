# shuatipass 自定义配置指南

> 给非学科网格式的 PDF 写自己的解析规则。

## 什么时候需要自定义

- 你的 PDF 来自非学科网来源（组卷网/教辅资料/Word 导出）
- 默认配置识别不出题目（解析出 0 题 或 题目数过少）
- 想精确控制"什么算一道题"

## 最小配置

最少只需要 2 个字段就能跑：

```yaml
name: 我的教辅
question_pattern: '^(\d+)\s*[．\.、]\s*(.{10,})'
option_pattern: '^([A-D])[．\.]\s*(.*)$'
```

其他字段会用合理默认值。

## 完整配置（10 个字段）

```yaml
name: 我的教辅
description: 一句话描述

# 1. 必填 - 题目识别
question_pattern: '^(\d+)\s*[．\.]\s*[（(]\s*(\d{4})\s*[·\.]\s*([^·）\)]+?)\s*[·\.]\s*(?:高考真题)?\s*[）)]\s*'

# 2. 必填 - 选项识别
option_pattern: '^([A-D])[．\.]\s*(.*)$'

# 3. 选填 - 页眉（识别专题）
#   - 留空 = 所有页归一个通用专题
#   - 不留空 = 按页眉分组
header_pattern: '专题\s*(\d+)\s+(\S+?)\s*\n\s*(\d+)\s*/\s*(\d+)\s*\n'

# 4. 选填 - "有题目页"判断（过滤空白页/考点分析页）
#   - 留空 = 不过滤
has_question_pattern: '\d+\s*[．\.]\s*[（(]\s*\d{4}\s*[·\.]'

# 5. 选填 - 从考点分析页提取真实专题名
topic_title_pattern: '专题\s*(\d+)\s+(\S+?)\s*$'

# 6. 选填 - 选项字母列表
option_keys: [A, B, C, D]    # 默认
# 也支持 E, F, G...（多选题）

# 7. 选填 - 解析题关键词
essay_keywords:
  - 求
  - 证明
  - 试求
  - 计算
  - "解:"
  - "解："
  - "（1）"
  - "(1)"

# 8. 选填 - 跳过的行（正则）
skip_patterns:
  - '学科\s*网'
  - '股\s*份'
  - '有限公司'
  - '考点'
  - '命题趋势'

# 9. 选填 - 跳过的行（完全匹配）
skip_exact_lines:
  - 考点
  - 命题趋势
  - 五年考情
```

## 正则规则

### 题目正则 `question_pattern`

**关键**：第 1 个捕获组必须是**题号**（数字）。

捕获组数 = 1：只识别题号
```yaml
question_pattern: '^(\d+)\s*[．\.、]\s*(.{10,})'
# 1：题号
# 2：题干开头（忽略）
```

捕获组数 = 3：识别题号 + 年份 + 省份
```yaml
question_pattern: '^(\d+)\s*[．\.]\s*[（(]\s*(\d{4})\s*[·\.]\s*([^·）\)]+?)\s*[·\.]\s*(?:高考真题)?\s*[）)]\s*'
# 1：题号
# 2：年份
# 3：省份
```

### 选项正则 `option_pattern`

**关键**：第 1 个捕获组是**选项 key**（字母）。

```yaml
# 标准 A/B/C/D
option_pattern: '^([A-D])[．\.]\s*(.*)$'

# 支持 E, F, G
option_pattern: '^([A-G])[．\.]\s*(.*)$'
```

### `re.MULTILINE` 自动启用

所有正则都自动带 `re.MULTILINE` flag，`^` 匹配每行开头。不用手动加。

## 写配置的步骤

### 第 1 步：先看 PDF 文本格式

```bash
python3 -c "
import pymupdf
doc = pymupdf.open('your.pdf')
print(doc[0].get_text()[:1000])
"
```

输出示例：
```
高三物理练习题 第1页
1．下列说法正确的是（ ）
A．...
B．...
2．关于 X 的说法，错误的是（ ）
A．...
```

### 第 2 步：写正则

基于看到的格式写：

```yaml
name: 我的教辅
question_pattern: '^(\d+)\s*[．\.]\s*'
option_pattern: '^([A-D])[．\.]\s*(.*)$'
```

### 第 3 步：试跑

```bash
shuatipass parse your.pdf -o out.json --config my-rules.yaml
```

### 第 4 步：调试

如果题目数不对：

1. 用 `--preset generic` 对比，看是规则太严还是太松
2. 加 `print` 看具体哪行没匹配：
   ```python
   from shuatipass.config import ParseConfig
   cfg = ParseConfig.load("my-rules.yaml")
   test_line = "1．下列说法正确的是"
   print(cfg.question_re.match(test_line))
   ```
3. 在 regex101.com 测试你的正则

## 真实案例

### 案例 1：组卷网

```yaml
name: 组卷网
question_pattern: '^(\d+)\s*[．\.]\s*(.{20,})'
option_pattern: '^([A-D])[．\.]\s*(.*)$'
header_pattern: ''
has_question_pattern: '^\d+\s*[．\.、]'
essay_keywords: [求, 证明, 计算, 解答]
```

### 案例 2：纯文字试卷（无选项）

```yaml
name: 纯文字试卷
question_pattern: '^(\d+)\s*[．\.]\s*(.{10,})'
option_pattern: '^([A-Z])[．\.]\s*(.*)$'  # A-Z 因为可能不只 A-D
essay_keywords: [求, 证明, 解, 答]
```

### 案例 3：英文题库

```yaml
name: English SAT
question_pattern: '^(\d+)\.\s+(.{20,})'
option_pattern: '^([A-E])\.\s+(.+)$'
option_keys: [A, B, C, D, E]
skip_patterns: ['Page \d+', 'www\.']
```

## 调试技巧

### 单独测试 YAML

```python
from shuatipass.config import ParseConfig

cfg = ParseConfig.load("my-rules.yaml")
print(cfg.question_re.pattern)

# 测试某行
line = "1．这是一道题"
m = cfg.question_re.match(line)
print(m)
if m:
    print(m.group(1))  # 题号
```

### 找 PDF 里所有"看起来像题目"的行

```python
import pymupdf
from shuatipass.config import ParseConfig

cfg = ParseConfig.load("my-rules.yaml")
doc = pymupdf.open("input.pdf")

for page_idx in range(min(5, len(doc))):
    text = doc[page_idx].get_text()
    for line in text.split("\n"):
        line = line.strip()
        if cfg.question_re.match(line):
            print(f"  p{page_idx+1}: {line[:60]}")
```

## 限制

shuatipass v0.1 不支持：

- **扫描版 PDF** —— 需要先 OCR（Tesseract / PaddleOCR）
- **多列排版** —— 当前按行扫描
- **图片内嵌题号** —— 图片里的题目不会被识别
- **嵌套题型**（如"第 1 大题 (1) (2) (3)"）—— 大题会被识别为独立题

这些限制会在后续版本改进。
