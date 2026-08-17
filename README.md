# 刷题通 shuatipass

> **把"PDF 题库"一键变成"结构化 JSON"。**
> 中文圈首个面向开发者的题库 PDF 解析工具。开源、可下载、可部署、可二次开发。

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green)]()
[![Tests](https://img.shields.io/badge/tests-100%20passed-brightgreen)]()
[![Status: v0.1.0](https://img.shields.io/badge/status-v0.1.0-blue)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-orange)]()

## 它解决什么

教师/教培/学生手里有大量"扫描版真题集 PDF"（学科网/组卷网/教辅资料），想做：
- 在线题库系统
- 班级错题本
- 智能组卷
- AI 出题
- 学情分析

但这些 PDF 是非结构化的，没法直接用。**shuatipass 把它们一键转成 JSON，附带图片库**。

## 9 个 CLI 子命令

```bash
# 1. parse —— 解析 PDF
shuatipass parse input.pdf -o questions.json --preset xuekewang

# 2. stats —— 统计 JSON
shuatipass stats questions.json

# 3. info —— 看 PDF 元信息
shuatipass info input.pdf

# 4. configs —— 列出可用配置
shuatipass configs

# 5. ocr —— 公式 OCR（Mathpix/pix2tex）
shuatipass ocr questions.json --provider mathpix

# 6. web —— 启动 Web UI
shuatipass web

# 7. generate —— AI 出题
shuatipass generate -o out.json --topic "圆周运动" --count 5

# 8. exam-mimic —— 完整克隆试卷风格
shuatipass exam-mimic --seed questions.json -o mock.json --count 10

# 9. wrongbook —— 错题本
shuatipass wrongbook mark questions.json --ids "01-001" --action mark
shuatipass wrongbook export questions.json --out-html wrongbook.html
```

## 安装

```bash
pip install shuatipass

# Web UI 依赖
pip install shuatipass[web]

# 公式 OCR 依赖
pip install shuatipass[ocr]
```

## 它解决什么

教师/教培/学生手里有大量"扫描版真题集 PDF"（学科网/组卷网/教辅资料），想做：
- 在线题库系统
- 班级错题本
- 智能组卷
- AI 出题
- 学情分析

但这些 PDF 是非结构化的，没法直接用。**shuatipass 把它们一键转成 JSON，附带图片库**。

## 三种用法

### 1. 命令行（最简单）

看上面的 9 个子命令一览。

### 2. Python 库

```python
from shuatipass import (
    XueKeWangParser, ParseConfig, get_builtin,
    # AI 出题
    generate_questions, mimic_exam,
    # 错题本
    find_by_tag, build_wrongbook, render_wrongbook_html,
)
from pathlib import Path

# 解析 PDF
parser = XueKeWangParser("input.pdf", image_dir=Path("./images"))
result = parser.parse()

for q in result.topics[0].questions:
    print(f"题{q.number} ({q.year}·{q.province}): {q.stem[:50]}...")

# AI 出题
qs = generate_questions(topic="圆周运动", count=5)

# 错题本
import json
with open("questions.json") as f: data = json.load(f)
all_qs = [q for t in data["topics"] for q in t["questions"]]
wrong = find_by_tag(all_qs, "错题")
wb = build_wrongbook(wrong, group_by="knowledge_point")
html = render_wrongbook_html(wb, title="我的错题本")
```

### 3. Web UI

```bash
pip install shuatipass[web]
shuatipass web  # 浏览器打开 http://127.0.0.1:7860
```

界面：上传 PDF → 选配置 → 解析 → 看统计/预览/下载 JSON。

### 4. Docker

```bash
docker run -v $(pwd)/data:/data shuatipass/cli parse /data/input.pdf -o /data/out.json
```

## 支持的 PDF 格式

| 来源 | 状态 | 说明 |
|------|------|------|
| 学科网（五年真题/三年真题/专题汇编）| ✅ 完整支持 | 排版规则统一 |
| 组卷网 | 🚧 计划中 | 排版略有差异 |
| WPS/Word 导出 | 🚧 计划中 | 通用格式 |
| 扫描版 | ❌ 不支持 | 需先 OCR |

## 解析输出（JSON 格式）

```json
{
  "source_file": "物理-高考真题-学科网.pdf",
  "total_pages": 423,
  "topics": [
    {
      "topic_id": "01",
      "title": "直线运动",
      "page_start": 1,
      "page_end": 20,
      "questions": [
        {
          "id": "01-001",
          "number": 1,
          "year": 2025,
          "province": "黑吉辽蒙卷",
          "type": "single_choice",
          "stem": "书法课上...",
          "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
          "images": ["t01-p001-i05.jpeg"],
          "image_bboxes": [[40, 100, 200, 250]],
          "source_page": 1,
          "bbox": [40, 542, 555, 791]
        }
      ]
    }
  ],
  "skipped_pages": [{"page": 290, "reason": "考点分析页"}]
}
```

## 项目状态

| 阶段 | 状态 | 交付物 |
|------|------|--------|
| **D1** 解析器核心 | ✅ 完成 | PyMuPDF 解析器，821 题实测 |
| **D2** 解析器优化 | ✅ 完成 | bbox 切分 + 解析题 + 内嵌选项 |
| **D3** CLI + 库 | ✅ 完成 | `shuatipass` 命令 + Python 库 |
| **D4** 配置化 | ✅ 完成 | YAML + 内置预设 + 14 个测试 |
| **D5** 文档 | ✅ 完成 | tutorial + api + config + examples |
| **D6** Docker 镜像 | ✅ 完成 | 多阶段镜像 + compose + 集成测试 |
| **D7** CI/CD | ✅ 完成 | GitHub Actions + 3 Python 版本 + lint + build |
| **D8** PyPI 发布 | ✅ 完成 | `pip install shuatipass`（待你推 tag）|
| **D9** 多格式 | ✅ 完成 | 4 个内置配置 + 自动检测 |
| **D10** 公式 OCR | ✅ 完成 | Mathpix API + pix2tex + CLI 子命令 |
| **D11** AI 出题 | ✅ 完成 | generate 子命令 + 3 个 LLM provider |
| **D12** Exam Mimic + 错题本 | ✅ 完成 | exam-mimic + wrongbook 子命令 |

## 文档

- 📘 [新用户教程](docs/tutorial.md) —— 5 分钟上手
- 📖 [API 参考](docs/api.md) —— CLI + 库完整接口
- ⚙️ [自定义配置指南](docs/config.md) —— 写自己的 YAML 规则
- 💡 [实战示例](docs/examples.md) —— 12 个真实场景（Excel/Anki/RAG/LLM 加答案）
- 🤖 [AI 出题指南](docs/generate.md) —— generate 子命令
- 🎯 [Exam Mimic + 错题本](docs/exam-mimic-wrongbook.md) —— D12 完整文档
- 🌐 [Web UI 指南](docs/web.md) —— Gradio 界面使用
- 🐳 [Docker 部署](docs/docker.md) —— 一键容器化
- 📦 [发布到 PyPI](docs/publish.md) —— 从代码到 `pip install shuatipass`
- 📊 [进度报告](docs/progress-*.md) —— D1-D12 阶段性产出

## 路线图

| 阶段 | 时间 | 目标 |
|------|------|------|
| v0.1 MVP | ✅ 完成 | 解析器 + CLI + 库 + 文档 + Docker + Web + PyPI |

## 适用人群

- 🧑‍💻 **开发者**：想用题库数据做应用（在线题库、刷题 APP、学情分析）
- 🏫 **教师/教培**：手里有大量 PDF 资料想数字化
- 🤖 **AI 工程师**：用题库微调 LLM / 做 RAG
- 📚 **自媒体**：做教辅内容需要题目数据

## 许可证

MIT License —— 随便用、商用、修改都行。

## 贡献

欢迎 PR！特别欢迎：
- 新 PDF 格式适配器
- 公式 OCR 集成
- 文档改进
- Bug 修复
