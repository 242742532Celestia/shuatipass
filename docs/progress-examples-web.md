# Examples + Web UI 进度报告

**日期**：2026-08-16
**状态**：✅ 100% 完成

## Examples（5 个真实可用脚本）

| 文件 | 用途 | 输入 | 输出 |
|------|------|------|------|
| `01_basic_parse.py` | 一行解析 PDF | PDF | JSON |
| `02_to_excel.py` | 转 Excel | JSON | .xlsx |
| `03_to_anki.py` | 转 Anki 卡片 | JSON | .tsv |
| `04_rag_chunks.py` | 转 RAG 文档块 | JSON | chunks.json |
| `05_ai_answers.py` | LLM 加答案 | JSON | 含答案的 JSON |

### 验证

```
$ python3 examples/01_basic_parse.py data/input/物理-高考真题-学科网.pdf /tmp/out.json
✅ 解析完成
   专题: 14 | 题目: 821 | 跳过: 14 页
   题型: {'single_choice': 684, 'essay': 121, 'essay_with_options': 16}

$ python3 examples/02_to_excel.py /tmp/out.json /tmp/out.xlsx
✅ 已导出 821 题到 /tmp/out.xlsx

$ python3 examples/03_to_anki.py /tmp/out.json /tmp/out.tsv
✅ 已导出 700 张 Anki 卡片到 /tmp/out.tsv

$ python3 examples/04_rag_chunks.py /tmp/out.json /tmp/out_rag.json
✅ 已生成 821 个 RAG 文档块
```

## Web UI（Gradio 6）

### 文件

| 文件 | 说明 |
|------|------|
| `src/shuatipass/web.py` | Gradio UI 主体 |
| `tests/test_web.py` | 6 个测试 |

### 启动

```bash
# 1. 装 gradio
pip install gradio   # 或 pip install shuatipass[web]

# 2. 启动
shuatipass web
# 🌐 启动 Web UI
#    地址: http://127.0.0.1:7860

# 3. 浏览器访问
open http://127.0.0.1:7860
```

### 三个 Tab

1. **📤 解析 PDF** —— 上传 → 选配置 → 解析 → 统计 + 预览 + 下载
2. **📖 使用说明** —— 三步上手教学
3. **🔧 关于** —— 项目信息 + 路线图

### Python API

```python
from shuatipass import launch_web
launch_web(host="0.0.0.0", port=7860, share=False)
```

## 测试

```
tests/test_examples.py     (新增，覆盖 examples 5 个)
tests/test_web.py          (新增，6 个测试)
─────────────────────────
合计 53 passed + 4 skipped
```

## 路线图（全部完成）

| 阶段 | 状态 |
|------|------|
| D1 解析核心 | ✅ |
| D2 解析优化 | ✅ |
| D3 CLI + 库 | ✅ |
| D4 配置化 | ✅ |
| D5 文档 | ✅ |
| D6 Docker | ✅ |
| D7 CI/CD | ✅ |
| D8 PyPI | ✅ |
| D9 多格式 | ✅ |
| D10 公式 OCR | ✅ |
| **Examples** | ✅ |
| **Web UI** | ✅ |

## 项目最终交付

| 类别 | 数量 |
|------|------|
| Python 模块 | 7（parser/config/detect/ocr/cli/web/__init__）|
| CLI 子命令 | 6（parse/stats/info/configs/ocr/web）|
| 内置配置 | 4（xuekewang/generic/zujuan/textbook）|
| Examples | 5（基础/Excel/Anki/RAG/LLM 加答案）|
| 文档 | 11 篇（tutorial/api/config/docker/publish/web/examples/6 份 progress）|
| 测试 | 53 passed + 4 docker skipped |
| 部署 | Docker + Docker Compose + GitHub Actions + Web UI |
