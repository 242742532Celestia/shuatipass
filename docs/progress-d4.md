# D4 进度报告：YAML 配置化

**日期**：2026-08-15
**状态**：✅ 100% 完成
**目标**：让用户自定义"什么样的 PDF 算一道题"，不限于学科网格式

## 交付物

| 项 | 路径 | 说明 |
|----|------|------|
| **配置模块** | `src/shuatipass/config.py` | ParseConfig 数据类 + YAML 加载/导出 |
| **内置配置 1** | `configs/xuekewang.yaml` | 学科网严格模式（默认）|
| **内置配置 2** | `configs/generic.yaml` | 通用宽松模式 |
| **CLI 集成** | `shuatipass parse --preset/--config` | 三种使用方式 |
| **配置测试** | `tests/test_config.py` | 14 个测试，全通过 |

## CLI 三种用法

```bash
# 1. 默认（学科网）
shuatipass parse input.pdf -o out.json

# 2. 内置预设
shuatipass parse input.pdf -o out.json --preset generic
shuatipass parse input.pdf -o out.json --preset xuekewang

# 3. 自定义 YAML
shuatipass parse input.pdf -o out.json --config my-rules.yaml

# 列出可用预设
shuatipass configs
```

## 库 API 三种用法

```python
from shuatipass import XueKeWangParser, ParseConfig, get_builtin

# 1. 默认
parser = XueKeWangParser("input.pdf", "./images")

# 2. 内置预设
parser = XueKeWangParser("input.pdf", "./images", config=get_builtin("generic"))

# 3. 自定义 YAML
parser = XueKeWangParser("input.pdf", "./images", config=ParseConfig.load("my-rules.yaml"))
```

## YAML 配置字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | ✅ | 配置名（显示用）|
| `header_pattern` | 选 | 页眉正则（识别专题）；空 = 不分组 |
| `question_pattern` | ✅ | 题目正则（必须有 1 个数字捕获组）|
| `option_pattern` | ✅ | 选项正则（捕获 key）|
| `has_question_pattern` | 选 | 用于判断"是否有题目页"（过滤考点分析页）|
| `topic_title_pattern` | 选 | 用于从考点分析页提取真实专题名 |
| `option_keys` | 选 | 选项字母列表，默认 [A,B,C,D] |
| `essay_keywords` | 选 | 解析题关键词 |
| `skip_patterns` | 选 | 跳过行的正则 |
| `skip_exact_lines` | 选 | 完全匹配才跳过的行 |

## 三种配置实测对比（同一份物理 PDF）

| 配置 | 专题 | 题目 | 题型 | 适用 |
|------|------|------|------|------|
| xuekewang（默认）| 14 | 821 | 684 单选 + 121 解析 + 16 带选项 | 学科网 PDF |
| generic（宽松）| 1 | 848 | 702 单选 + 132 解析 + 14 带选项 | 不知道格式时用 |
| 自定义 YAML | 14 | 821 | 同 xuekewang | 你的特殊格式 |

## 关键 bug 修复

1. **YAML mapping 简写 bug**：`解:` 被解析成 `{"解": null}`，加引号 `"解:"` 修复
2. **MULTILINE flag 缺失**：`^` 之前只匹配字符串开头，加 `re.MULTILINE` 才能匹配每行开头
3. **无 header 模式 0 题**：generic 配置没 header 时所有页都被丢掉，加 fallback 把所有有题页归到"00"专题

## 测试

```
tests/test_config.py       14 个测试 ✅
tests/test_parser.py       13 个测试 ✅
─────────────────────────
合计 27/27 通过
```

## 路线图（更新）

| 阶段 | 状态 | 目标 |
|------|------|------|
| D1 解析核心 | ✅ | PyMuPDF 解析 821 题 |
| D2 解析优化 | ✅ | bbox + 解析题 + 内嵌选项 |
| D3 CLI + 库 | ✅ | `shuatipass` 命令 + Python 库 |
| **D4 配置化** | ✅ | YAML + 内置预设 + 14 个测试 |
| **D5 文档** | ⏳ | API 文档 + 教程 + 示例 |
| **D6 Docker** | ⏳ | 一键 Docker 镜像 |
| **D7 CI/CD** | ⏳ | GitHub Actions + 覆盖率 |
| **D8 PyPI** | ⏳ | `pip install shuatipass` |
| **D9 多格式** | ⏳ | 组卷网 + Word 导出支持 |
| **D10 公式 OCR** | ⏳ | 物理公式 LaTeX 化（可选）|
