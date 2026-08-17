# D2 + D3 进度报告：解析器优化 + CLI 入口

**日期**：2026-08-15
**状态**：✅ 100% 完成
**方向**：开发者工具（CLI + 库 + Docker）

## D2：解析器优化

| 优化项 | 状态 | 数据 |
|--------|------|------|
| bbox 上界用"下一题号 y" | ✅ | 1 张图 606 题（v2 是 407）|
| 解析题识别 | ✅ | essay 121 + essay_with_options 16 |
| 跨页题标记 | ✅ | cross_page 字段 |
| 内嵌选项切割 | ✅ | 题 23 修好（C/D 不再拼行）|
| 物理公式空选项 | ✅ | OPTION_RE 允许空值 |

### 关键 bug 修复
1. **选项行 C/D 拼一行**：原 PDF 把 `C．...重力D．触网时...力` 拼一行，v3 用正则 `r"([A-D])[．\.]\s*(...)$"` 切分
2. **物理公式换行**：`A．` 后面是空（公式换行），`OPTION_RE` 改成 `r"^([A-D])[．\.]\s*(.*)$"` 允许空

## D3：CLI 入口 + 库结构

### CLI 子命令
```bash
shuatipass parse <pdf> -o <json> [--images <dir>]
shuatipass stats <json>
shuatipass info <pdf>
```

### 库 API
```python
from shuatipass import XueKeWangParser
from pathlib import Path

parser = XueKeWangParser("input.pdf", image_dir=Path("./images"))
result = parser.parse()
# result.topics → 14 专题
# result.topics[0].questions → 48 道题
```

### 包结构（src layout）
```
src/shuatipass/
├── __init__.py      # 公开 API
├── parser.py        # 解析器核心
└── cli.py           # CLI 入口
```

### 安装
```bash
# 可编辑模式
pip install -e .

# 正式安装
pip install shuatipass
```

### 单元测试
```
tests/test_parser.py
- 5 个正则测试 ✅
- 2 个 dataclass 测试 ✅
- 6 个端到端测试 ✅
共 13/13 通过
```

## 当前可交付物

| 项 | 路径 | 说明 |
|----|------|------|
| 包代码 | `src/shuatipass/` | 库 + CLI |
| 解析结果 | `data/parsed/questions.json` | 821 题 / 1MB |
| 图片库 | `data/images/` | 1559 张 / 17MB |
| 示例 PDF | `data/input/物理-高考真题-学科网.pdf` | 学科网示例 |
| 测试 | `tests/test_parser.py` | 13 个测试 |
| 配置 | `pyproject.toml` | 包元数据 |
| 文档 | `README.md` + `docs/` | 使用说明 |

## 路线图（更新）

| 阶段 | 状态 | 目标 |
|------|------|------|
| D1 解析核心 | ✅ | PyMuPDF 解析 821 题 |
| D2 解析优化 | ✅ | bbox 切分 + 解析题 + 内嵌选项 |
| D3 CLI + 库 | ✅ | `shuatipass` 命令 + Python 库 |
| **D4 配置化** | ⏳ | YAML 配置（自定义解析规则）|
| **D5 文档** | ⏳ | API 文档 + 教程 + 示例 |
| **D6 Docker** | ⏳ | 一键 Docker 镜像 |
| **D7 CI/CD** | ⏳ | GitHub Actions + 覆盖率 |
| **D8 PyPI** | ⏳ | `pip install shuatipass` |
| **D9 多格式** | ⏳ | 组卷网 + Word 导出支持 |
| **D10 公式 OCR** | ⏳ | 物理公式 LaTeX 化（可选）|
