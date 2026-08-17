# shuatipass API 参考

> 完整的库 + CLI + 配置 API 文档。

## CLI

### `shuatipass parse`

把 PDF 解析为 JSON。

```bash
shuatipass parse <pdf> -o <json> [options]
```

**位置参数**：
- `pdf` —— 输入 PDF 路径

**选项**：
- `-o, --out <path>` —— **必填**，输出 JSON 路径
- `--images <dir>` —— 图片输出目录（默认 `<out_dir>/images`）
- `--preset <name>` —— 使用内置预设（`xuekewang` / `generic`）
- `--config <path>` —— 使用自定义 YAML 配置

**示例**：
```bash
# 默认
shuatipass parse input.pdf -o out.json

# 用通用模式
shuatipass parse input.pdf -o out.json --preset generic

# 用自定义 YAML
shuatipass parse input.pdf -o out.json --config rules.yaml

# 指定图片目录
shuatipass parse input.pdf -o out.json --images /tmp/imgs
```

### `shuatipass stats`

查看 JSON 统计信息。

```bash
shuatipass stats <json>
```

**输出**：
```
📊 questions.json
   来源: 物理-高考真题-学科网.pdf
   总页: 423
   专题: 14
   题目: 821
   题型: {'single_choice': 684, 'essay': 121, 'essay_with_options': 16}
   年份: [(2021, 143), (2022, 123), ...]
   
   专题分布:
     专题 01 直线运动  p  1-20   48 题
     ...
```

### `shuatipass info`

查看 PDF 基础信息（不解析）。

```bash
shuatipass info <pdf>
```

**输出**：
```
📄 input.pdf
   路径: /path/to/input.pdf
   大小: 13.49 MB
   页数: 423
   format: PDF 1.7
   author: ...
   creator: WPS 文字
   ...
```

### `shuatipass configs`

列出所有内置配置。

```bash
shuatipass configs
```

## Python 库

### `XueKeWangParser`

主解析器类（兼容学科网 + 自定义配置）。

```python
from shuatipass import XueKeWangParser
from pathlib import Path

parser = XueKeWangParser(
    pdf_path="input.pdf",       # 必填
    image_dir=Path("./images"), # 必填
    config=None,                 # 可选：ParseConfig 实例
    config_name="xuekewang",    # 可选：内置预设名（config 优先）
)
result = parser.parse()         # → ParsedDocument
```

**参数**：
- `pdf_path: str | Path` —— PDF 文件路径
- `image_dir: str | Path` —— 图片输出目录（自动创建）
- `config: ParseConfig | None` —— 自定义配置
- `config_name: str` —— 内置预设名（仅在 `config=None` 时生效）

**返回**：`ParsedDocument` 实例

### `ParseConfig`

解析配置数据类。

```python
from shuatipass import ParseConfig

# 从 YAML 加载
cfg = ParseConfig.load("rules.yaml")

# 直接构造
cfg = ParseConfig(
    name="我的配置",
    question_pattern=r'^(\d+)\s*[．\.]\s*...',
    option_pattern=r'^([A-D])[．\.]\s*(.*)$',
    ...
)
cfg.compile()  # 必须调用才能用
```

### `ParsedDocument`

解析结果。

**字段**：
- `source_file: str` —— 源 PDF 文件名
- `total_pages: int` —— PDF 总页数
- `topics: list[Topic]` —— 专题列表
- `skipped_pages: list[dict]` —— 跳过的页（含原因）
- `stats: dict` —— 统计信息
- `config_name: str` —— 使用的配置名

**方法**：
- (无) —— 数据类，结果通过属性访问

### `Topic`

专题数据类。

**字段**：
- `topic_id: str` —— 专题编号（"01" / "00" 通用）
- `title: str` —— 专题名
- `page_start: int` —— 起始页
- `page_end: int` —— 结束页
- `questions: list[Question]` —— 题目列表

### `Question`

题目数据类。

**字段**：
- `id: str` —— 唯一 ID（"01-001"）
- `number: int` —— 专题内题号
- `year: int | None` —— 年份（学科网可识别）
- `province: str | None` —— 省份
- `type: str` —— 题型（`single_choice` / `multi_choice` / `essay` / `essay_with_options`）
- `stem: str` —— 题干
- `options: dict[str, str]` —— 选项 `{"A": "...", ...}`
- `images: list[str]` —— 图片文件名列表
- `image_bboxes: list[list]` —— 图片在 PDF 中的位置
- `source_page: int` —— 来源页码
- `bbox: list | None` —— 题干在 PDF 中的 bbox `[x0, y0, x1, y1]`
- `cross_page: bool` —— 是否跨页题
- `answer: str | None` —— 答案（默认 None，需要用户补充或 AI 生成）
- `explanation: str | None` —— 解析（同上）

## 配置字段

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `name` | str | ✅ | - | 配置名（显示用）|
| `description` | str | ❌ | "" | 描述 |
| `header_pattern` | str | ❌ | 学科网 | 页眉正则（识别专题）|
| `question_pattern` | str | ✅ | - | 题目正则 |
| `option_pattern` | str | ✅ | - | 选项正则 |
| `has_question_pattern` | str | ❌ | 学科网 | 判断"有题页"用 |
| `topic_title_pattern` | str | ❌ | 学科网 | 考点页提取专题名 |
| `option_keys` | list[str] | ❌ | [A,B,C,D] | 选项字母 |
| `essay_keywords` | list[str] | ❌ | [求,证明,...] | 解析题关键词 |
| `skip_patterns` | list[str] | ❌ | [...] | 跳过的行（regex）|
| `skip_exact_lines` | list[str] | ❌ | [...] | 跳过的行（完全匹配）|

### 题目正则 `question_pattern` 必须满足

- 有 **1 个或 3 个** 捕获组
  - 1 组：`[number, ...rest]`
  - 3 组：`[number, year, province]`
- 第 1 组必须是题号（数字）
- **所有正则默认带 `re.MULTILINE` flag**（`^` 匹配每行开头）

### 选项正则 `option_pattern` 必须满足

- 至少 1 个捕获组
- 第 1 组是选项 key（字母）
- 第 2 组（可选）是选项值

### 完整 YAML 模板

```yaml
name: 我的教辅
description: 组卷网格式 PDF

# 必填
question_pattern: '^(\d+)\s*[．\.]\s*[（(]\s*(\d{4})\s*[·\.]\s*([^·）\)]+?)\s*[）)]\s*'
option_pattern: '^([A-D])[．\.]\s*(.*)$'

# 选填（有合理默认）
header_pattern: '第\s*(\d+)\s*卷\s*(\S+?)\s*\n'
has_question_pattern: '\d+\s*[．\.]\s*[（(]\s*\d{4}\s*[·\.]'
topic_title_pattern: '第\s*(\d+)\s*卷\s*(\S+?)\s*$'
option_keys: [A, B, C, D]
essay_keywords: [求, 证明, 计算]
skip_patterns: ['组\s*卷\s*网']
skip_exact_lines: []
```

## 异常

| 异常 | 触发条件 |
|------|----------|
| `FileNotFoundError` | PDF 或配置文件不存在 |
| `ValueError("配置 X 正则编译失败")` | YAML 中有非法正则 |
| `ImportError` | 缺 pyyaml（解析 YAML 配置时）|

## 版本兼容

- Python: 3.10 / 3.11 / 3.12
- PyMuPDF: >= 1.28
- PyYAML: >= 5.0（用 `--config` 时需要）
