# D7 + D8 进度报告：CI/CD + PyPI 发布

**日期**：2026-08-16
**状态**：✅ 100% 完成

## D7：CI/CD

### GitHub Actions

| 文件 | 触发 | 工作 |
|------|------|------|
| `.github/workflows/ci.yml` | push / PR | 测试（3 个 Python 版本）+ lint + build |
| `.github/workflows/release.yml` | tag `v*.*.*` | 自动发 PyPI + 创建 GitHub Release |

### CI 做的事

- **3 个 Python 版本**（3.10 / 3.11 / 3.12）跑 47 个测试
- **Lint**：black + ruff
- **Build**：sdist + wheel，twine check
- **Coverage**：上传到 Codecov（需配 `CODECOV_TOKEN` secret）

### Release 做的事

- 推 `v*.*.*` 标签自动触发
- Build 分发包
- 发布到 PyPI（trusted publishing）
- 创建 GitHub Release

### Issue 模板

- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`

## D8：PyPI 发布

### 包元数据（pyproject.toml）

- **包名**：`shuatipass`
- **版本**：0.1.0
- **License**：MIT
- **Python**：3.10 - 3.12
- **依赖**：PyMuPDF, Pillow, PyYAML, requests
- **可选依赖**：`dev` / `web` / `ocr` / `all`
- **入口**：`shuatipass` 命令

### 包含的文件

```
shuatipass/
├── __init__.py
├── cli.py
├── config.py
├── detect.py
├── ocr.py
└── parser.py

data/configs/
├── generic.yaml
├── textbook.yaml
├── xuekewang.yaml
└── zujuan.yaml
```

### 发布流程

**方式 1：自动（推标签）**
```bash
git tag v0.1.0
git push origin v0.1.0
# → GitHub Action 自动 build + publish + release
```

**方式 2：手动（脚本）**
```bash
bash scripts/publish.sh test   # TestPyPI
bash scripts/publish.sh prod   # 正式 PyPI
```

**方式 3：手动（命令）**
```bash
python3 -m build
twine upload dist/*
```

### 当前已构建（本地测试通过）

```
dist/
├── shuatipass-0.1.0-py3-none-any.whl  (37KB)
└── shuatipass-0.1.0.tar.gz            (35KB)
```

包内文件验证：
- ✅ 4 个核心模块（__init__, cli, config, detect, ocr, parser）
- ✅ 4 个 YAML 配置
- ✅ entry_points（shuatipass 命令）
- ✅ METADATA（含完整 classifiers）

### 发布前清单

- [x] 47 个测试通过
- [x] 文档完整（tutorial/api/config/examples/docker/publish）
- [x] CHANGELOG.md
- [x] Dockerfile
- [x] pyproject.toml 完整
- [ ] **需要你：**
  - [ ] 注册 PyPI 账号
  - [ ] 创建 GitHub 仓库
  - [ ] 配 trusted publishing（或用 token）
  - [ ] 推 `v0.1.0` 标签
  - [ ] 自动发布

## 完整项目交付清单

### 核心代码（4 个模块 + 4 个配置 + 4 个测试文件）
```
src/shuatipass/
├── __init__.py      # 公开 API
├── cli.py           # CLI 入口
├── config.py        # 配置系统
├── detect.py        # 自动检测
├── ocr.py           # 公式 OCR
└── parser.py        # 解析器
```

### 配置（4 个内置）
```
configs/
├── generic.yaml     # 通用宽松
├── textbook.yaml    # 教辅资料
├── xuekewang.yaml   # 学科网（默认）
└── zujuan.yaml      # 组卷网
```

### 文档（7 篇）
```
docs/
├── api.md           # API 参考
├── config.md        # 自定义配置
├── docker.md        # Docker 部署
├── examples.md      # 12 个实战示例
├── progress-*.md    # 7 份进度报告
├── publish.md       # 发布指南
└── tutorial.md      # 新用户教程
```

### 测试（51 个）
- 5 个正则
- 2 个 dataclass
- 6 个端到端
- 5 个配置
- 9 个自动检测
- 11 个 OCR（含 mock）
- 4 个 CLI
- 4 个 Docker（skip）
- 5 个 config + builtin

### 部署
- `Dockerfile`（多阶段 ~150MB）
- `docker-compose.yml`（交互+批量两 profile）
- `.github/workflows/ci.yml`（3 Python 版本）
- `.github/workflows/release.yml`（自动发 PyPI）
- `pyproject.toml`（PyPI 元数据 + 4 extras）

### 示例数据
- `data/input/物理-高考真题-学科网.pdf`（示例）
- `data/parsed/questions.json`（示例输出 821 题）

## 最终统计

| 类别 | 数量 |
|------|------|
| 代码行数 | ~2500 |
| 文档行数 | ~2000 |
| 测试数 | 47 + 4 skipped |
| 内置配置 | 4 |
| CLI 子命令 | 5（parse/stats/info/configs/ocr）|
| Python 模块 | 6 |

## 路线图（全部完成）

| 阶段 | 状态 |
|------|------|
| D1 解析核心 | ✅ |
| D2 解析优化 | ✅ |
| D3 CLI + 库 | ✅ |
| D4 配置化 | ✅ |
| D5 文档 | ✅ |
| D6 Docker | ✅ |
| D9 多格式 | ✅ |
| D10 公式 OCR | ✅ |
| D7 CI/CD | ✅ |
| D8 PyPI | ✅ |

**v0.1.0 完整发布准备就绪。**
