# shuatipass Docker 部署指南

> 无需装 Python 也能用 shuatipass —— Docker 一行跑起来。

## 镜像特性

- **基础镜像**：`python:3.11-slim`（Debian 精简版）
- **多阶段构建**：builder 装依赖 + runtime 只留 wheel
- **最终大小**：~150MB（含 PyMuPDF + 必要库）
- **non-root 运行**：默认 shuatipass 用户
- **HEALTHCHECK**：自动检测镜像健康

## 快速开始

### 1. 拉镜像（首次）

```bash
docker pull shuatipass:0.1.0
```

> 现在还没发布到 Docker Hub，先用 build。

### 2. Build 镜像

```bash
cd /path/to/shuatipass
docker build -t shuatipass:0.1.0 .
```

输出：
```
[+] Building 45.2s (12/12) FINISHED
 => [builder 4/5] RUN pip install --no-cache-dir --prefix=/install .
 => [runtime 3/4] COPY --from=builder /install /usr/local
 => exporting to image
 => => naming to docker.io/library/shuatipass:0.1.0
```

### 3. 看版本

```bash
docker run --rm shuatipass:0.1.0 --help
```

### 4. 解析一份 PDF

```bash
# 准备目录
mkdir -p mydata/input mydata/output

# 复制 PDF
cp ~/Downloads/物理题.pdf mydata/input/

# 跑解析
docker run --rm \
  -v "$(pwd)/mydata/input:/data/input:ro" \
  -v "$(pwd)/mydata/output:/data/output" \
  shuatipass:0.1.0 \
  parse /data/input/物理题.pdf -o /data/output/result.json --images /data/output/images
```

产物在 `mydata/output/`：
- `result.json` —— 结构化题库
- `images/` —— 提取的图片

### 5. 查看统计

```bash
docker run --rm \
  -v "$(pwd)/mydata/output:/data/output:ro" \
  shuatipass:0.1.0 \
  stats /data/output/result.json
```

## Docker Compose 方式

### 一次性解析

```bash
# 1. 准备
mkdir -p data/input data/output
cp your.pdf data/input/

# 2. 启动（用 compose）
docker compose run --rm shuatipass \
  parse input/your.pdf -o output/result.json --images output/images

# 3. 看结果
docker compose run --rm shuatipass stats output/result.json
```

### 批量处理

```bash
# 把所有 PDF 放到 data/input/
cp *.pdf data/input/

# 用 batch profile 一次性处理
docker compose --profile batch up batch

# 自动跑完退出
```

## 常用模式

### 模式 1：交互解析（最常用）

```bash
docker run --rm -it \
  -v "$(pwd)/data:/data" \
  shuatipass:0.1.0 \
  parse /data/input/test.pdf -o /data/output/result.json
```

### 模式 2：自定义配置

```bash
docker run --rm \
  -v "$(pwd)/data:/data" \
  -v "$(pwd)/my-rules.yaml:/data/my-rules.yaml:ro" \
  shuatipass:0.1.0 \
  parse /data/input/test.pdf -o /data/output/result.json --config /data/my-rules.yaml
```

### 模式 3：CI/CD 用

```yaml
# GitHub Actions 示例
- name: 解析 PDF
  run: |
    docker build -t shuatipass:ci .
    docker run --rm \
      -v ${{ github.workspace }}/pdfs:/data/input:ro \
      -v ${{ github.workspace }}/output:/data/output \
      shuatipass:ci \
      parse /data/input/exam.pdf -o /data/output/result.json
```

### 模式 4：开发模式（挂载源码）

```bash
docker run --rm -it \
  -v "$(pwd):/app" \
  -v "$(pwd)/data:/data" \
  --entrypoint bash \
  shuatipass:0.1.0
```

## 故障排查

### 问题 1：镜像 build 失败

**最常见原因**：网络问题，pip 装不上。

**解决**：
```dockerfile
# 用国内镜像源（在 Dockerfile 里）
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple .
```

### 问题 2：docker run 时找不到 PDF

**原因**：挂载路径不对。

**检查**：
```bash
# 1. 确认挂载的 PDF 存在
ls -la data/input/

# 2. 用 docker run 的绝对路径
docker run --rm -v "$(pwd)/data:/data" shuatipass:0.1.0 \
  parse /data/input/test.pdf -o /data/output/result.json
```

### 问题 3：图片未生成

**原因**：图片目录权限或路径。

**解决**：
```bash
# 1. 确认 --images 路径在挂载目录内
docker run --rm -v "$(pwd)/data:/data" shuatipass:0.1.0 \
  parse /data/input/test.pdf -o /data/output/result.json --images /data/output/images
#                                            ↑ 必须 /data/output 下 ↑
```

### 问题 4：内存不够

shuatipass 解析大 PDF（>500 页）可能需要 1-2GB 内存。

**解决**：
```bash
docker run --rm -m 2g \
  -v "$(pwd)/data:/data" \
  shuatipass:0.1.0 \
  parse /data/input/big.pdf -o /data/output/result.json
```

## 镜像优化

### 当前镜像大小

```bash
docker images shuatipass:0.1.0 --format "{{.Size}}"
```

典型 ~150MB（python:3.11-slim + PyMuPDF wheel + shuatipass）。

### 进一步优化（可选）

如需更小的镜像，可改用 `python:3.11-alpine`：

```dockerfile
FROM python:3.11-alpine
# 注：Alpine 需要额外装 musl 兼容的 PyMuPDF
# 实际可能不节省（PyMuPDF wheel 自带 mupdf 二进制）
```

## 测试

### 自动化测试

```bash
# 跑全部测试（含 docker 集成测试，前提是本机有 docker）
python3 -m pytest tests/

# 仅 docker 测试
python3 -m pytest tests/test_docker.py -v
```

### 手动端到端测试

```bash
# 项目根目录
bash scripts/test-docker.sh
```

测试会：
1. 检查 docker 可用
2. build 镜像
3. 跑 `--help` 命令
4. 跑 `info` 命令
5. 跑端到端 `parse`（用示例 PDF）
6. 验证 JSON 输出
7. 清理

## 发布到 Docker Hub（待办）

```bash
# 1. 登录
docker login

# 2. 标记镜像
docker tag shuatipass:0.1.0 yourname/shuatipass:0.1.0
docker tag shuatipass:0.1.0 yourname/shuatipass:latest

# 3. 推送
docker push yourname/shuatipass:0.1.0
docker push yourname/shuatipass:latest
```

## 镜像信息

```dockerfile
LABEL org.opencontainers.image.title="shuatipass"
LABEL org.opencontainers.image.description="中文题库 PDF 解析工具 - 把 PDF 一键转结构化 JSON"
LABEL org.opencontainers.image.source="https://github.com/yourname/shuatipass"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.version="0.1.0"
```

可以这样查：

```bash
docker inspect shuatipass:0.1.0 | grep -A 5 Labels
```
