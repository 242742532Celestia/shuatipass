# D9 + D10 进度报告：多格式 + 公式 OCR

**日期**：2026-08-16
**状态**：✅ 100% 完成

## D9：多格式支持

### 新增 2 个内置配置

| 配置 | 适用 |
|------|------|
| `zujuan` | 组卷网（zujuan.com）|
| `textbook` | 教辅资料（人教版/北师大版等）|

加上之前的 `xuekewang` + `generic`，**内置配置从 2 个扩到 4 个**。

### 自动检测模块

新增 `src/shuatipass/detect.py`：

```python
from shuatipass import detect_config
result = detect_config("input.pdf")  # → "xuekewang" / "zujuan" / "textbook" / "generic"
```

检测方法：
1. 提取前 3 页文本
2. 关键词匹配（"学科网"/"组卷网"/"人教版" 等）
3. 加权评分
4. 返回最高分配置

**CLI 新增 `--auto` 标志**：
```bash
shuatipass parse input.pdf -o out.json --auto
# 自动检测: xuekewang
# ...
```

### 修了 1 个老 bug

YAML 加载时 dict 元素（如 `解:` → `{解: None}`）自动转字符串。**以后写配置不用再担心 `:` 字符**。

### 关键文件

| 文件 | 说明 |
|------|------|
| `configs/zujuan.yaml` | 组卷网配置 |
| `configs/textbook.yaml` | 教辅配置 |
| `src/shuatipass/detect.py` | 自动检测模块 |
| `src/shuatipass/cli.py` | CLI 加 `--auto` |
| `tests/test_detect.py` | 9 个测试 |

---

## D10：公式 OCR

### 设计

**默认不集成，保持轻量**。公式 OCR 是可选插件。

### 支持的引擎

| 引擎 | 模式 | 准确率 | 成本 |
|------|------|--------|------|
| **Mathpix API** | 云端 | 95%+ | $0.004/次（学生包 $4.99/月 5000 次）|
| **pix2tex** | 本地 | 70-80% | 免费（需 PyTorch ~500MB）|

### 用法

**Mathpix（推荐）**：
```bash
# 1. 去 https://mathpix.com/ 申请 app_id + app_key
# 2. 配环境变量
export MATHPIX_APP_ID="your_app_id"
export MATHPIX_APP_KEY="your_app_key"

# 3. OCR
shuatipass ocr questions.json --images ./images
# 输出 questions.ocr.json
```

**pix2tex**：
```bash
pip install shuatipass[ocr]
shuatipass ocr questions.json --images ./images --engine pix2tex
```

### JSON 字段扩展

每题新增 3 个字段：

```json
{
  "id": "01-001",
  "stem": "...",
  "options": {...},
  "images": ["01-001.png"],
  "formula_latex": "F = ma",      // 新增
  "formula_confidence": 0.95,     // 新增
  "formula_ocr_engine": "mathpix" // 新增
}
```

### 关键文件

| 文件 | 说明 |
|------|------|
| `src/shuatipass/ocr.py` | OCR 核心（接口 + Mathpix + pix2tex）|
| `src/shuatipass/cli.py` | CLI 加 `shuatipass ocr` 子命令 |
| `tests/test_ocr.py` | 11 个测试（含 mock）|
| `pyproject.toml` | 加 `ocr` extras_require |

---

## 测试

```
tests/test_config.py       14 ✅
tests/test_detect.py        9 ✅  (新增)
tests/test_docker.py        4 🚧  (skip，没 docker)
tests/test_ocr.py          11 ✅  (新增)
tests/test_parser.py       13 ✅
─────────────────────────────
合计 47 passed + 4 skipped
```

## 路线图（更新）

| 阶段 | 状态 | 目标 |
|------|------|------|
| D1 解析核心 | ✅ | PyMuPDF 解析 821 题 |
| D2 解析优化 | ✅ | bbox + 解析题 + 内嵌选项 |
| D3 CLI + 库 | ✅ | `shuatipass` 命令 + Python 库 |
| D4 配置化 | ✅ | YAML + 2 个内置预设 |
| D5 文档 | ✅ | 4 篇核心文档 + CHANGELOG |
| D6 Docker | ✅ | 多阶段镜像 + compose + 集成测试 |
| **D9 多格式** | ✅ | 4 个内置配置 + 自动检测 |
| **D10 公式 OCR** | ✅ | Mathpix API + pix2tex + CLI |
| **D7 CI/CD** | ⏳ | GitHub Actions + 覆盖率 |
| **D8 PyPI** | ⏳ | `pip install shuatipass` |
