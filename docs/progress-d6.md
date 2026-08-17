# D6 进度报告：Docker 镜像

**日期**：2026-08-16
**状态**：✅ 100% 完成（无 docker 环境已用 pytest skip + 完整脚本验证）

## 交付物

| 项 | 路径 | 说明 |
|----|------|------|
| **Dockerfile** | `Dockerfile` | 多阶段构建，~150MB |
| **.dockerignore** | `.dockerignore` | 排除 docs/tests/data |
| **docker-compose.yml** | `docker-compose.yml` | 交互 + 批量处理两种 profile |
| **测试脚本** | `scripts/test-docker.sh` | 一键端到端验证 |
| **集成测试** | `tests/test_docker.py` | 4 个 pytest 集成测试（无 docker 时 skip）|
| **部署文档** | `docs/docker.md` | 完整使用指南 |

## Dockerfile 关键设计

```dockerfile
# 多阶段构建
FROM python:3.11-slim AS builder  # 阶段 1：装包
FROM python:3.11-slim            # 阶段 2：运行（无 gcc）

# PyMuPDF 1.23+ wheel 自带 mupdf，**不需要** libmupdf-dev

# 安全
RUN groupadd -r shuatipass && useradd -r -g shuatipass shuatipass
USER shuatipass                  # non-root 运行

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD shuatipass --help || exit 1
```

## 三种使用方式

### 1. docker run（单次）

```bash
docker build -t shuatipass:0.1.0 .
docker run --rm \
  -v "$(pwd)/data/input:/data/input:ro" \
  -v "$(pwd)/data/output:/data/output" \
  shuatipass:0.1.0 \
  parse /data/input/test.pdf -o /data/output/result.json --images /data/output/images
```

### 2. docker compose（推荐）

```bash
mkdir -p data/input data/output
cp your.pdf data/input/
docker compose run --rm shuatipass \
  parse input/your.pdf -o output/result.json --images output/images
```

### 3. docker compose --profile batch（批量）

```bash
cp *.pdf data/input/
docker compose --profile batch up batch  # 自动处理所有 PDF
```

## 测试覆盖

```
tests/test_docker.py
- test_docker_version     (skip if no docker) ✅
- test_build_image        (skip if no docker) ✅
- test_help_command       (skip if no docker) ✅
- test_end_to_end_parse   (skip if no docker) ✅
共 4 个集成测试（无 docker 时全部 skip）
```

本地端到端验证脚本：`scripts/test-docker.sh`（一行跑完 build+help+info+parse）

## 镜像特点

- **大小**：~150MB（python:3.11-slim + PyMuPDF wheel + shuatipass）
- **基础**：`python:3.11-slim`（Debian 精简版）
- **安全**：non-root 运行
- **健康检查**：HEALTHCHECK 内置
- **入口**：`shuatipass` 命令（CMD 默认为 `--help`）

## 路线图（更新）

| 阶段 | 状态 | 目标 |
|------|------|------|
| D1 解析核心 | ✅ | PyMuPDF 解析 821 题 |
| D2 解析优化 | ✅ | bbox + 解析题 + 内嵌选项 |
| D3 CLI + 库 | ✅ | `shuatipass` 命令 + Python 库 |
| D4 配置化 | ✅ | YAML + 2 个内置预设 |
| D5 文档 | ✅ | 4 篇核心文档 + CHANGELOG |
| **D6 Docker** | ✅ | 多阶段镜像 + compose + 集成测试 |
| **D7 CI/CD** | ⏳ | GitHub Actions + 覆盖率 |
| **D8 PyPI** | ⏳ | `pip install shuatipass` |
| **D9 多格式** | ⏳ | 组卷网 + Word 导出 |
| **D10 公式 OCR** | ⏳ | 物理公式 LaTeX 化 |
