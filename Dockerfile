# 刷题通 shuatipass —— 极简 Docker 镜像
# 多阶段构建：builder 装依赖，runtime 只留 wheel
# PyMuPDF 1.23+ wheel 自带 mupdf，**无需**系统 libmupdf-dev

# ========== Stage 1: builder ==========
FROM python:3.11-slim AS builder

WORKDIR /build

# 只装 build 阶段需要的（wheel 安装不需要 gcc，但 setuptools 装包需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制包元数据
COPY pyproject.toml README.md ./
COPY src/ ./src/

# 装包到 /install
RUN pip install --no-cache-dir --prefix=/install .


# ========== Stage 2: runtime ==========
FROM python:3.11-slim

# 极简基础镜像
# - 无 gcc
# - 无 dev headers
# - PyMuPDF wheel 自带 mupdf

# 安全：non-root 用户
RUN groupadd -r shuatipass && useradd -r -g shuatipass shuatipass

# 复制装好的包
COPY --from=builder /install /usr/local

# 数据目录（用户挂载点）
RUN mkdir -p /data/input /data/output /data/images \
    && chown -R shuatipass:shuatipass /data

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD shuatipass --help || exit 1

USER shuatipass
WORKDIR /data

# 入口：shuatipass 命令
ENTRYPOINT ["shuatipass"]
CMD ["--help"]

# Labels
LABEL org.opencontainers.image.title="shuatipass"
LABEL org.opencontainers.image.description="中文题库 PDF 解析工具 - 把 PDF 一键转结构化 JSON"
LABEL org.opencontainers.image.source="https://github.com/242742532Celestia/shuatipass"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.version="0.1.1"
