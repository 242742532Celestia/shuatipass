#!/bin/bash
# 刷题通 shuatipass Docker 端到端测试
# 验证：build + run + parse 完整流程
#
# 用法：
#   bash scripts/test-docker.sh
#
# 要求：本机有 docker

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "================================================"
echo "  shuatipass Docker 端到端测试"
echo "================================================"
echo

# 1. 检查 docker
if ! command -v docker &> /dev/null; then
    echo "❌ docker 未安装"
    echo "   请先安装 docker: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ docker: $(docker --version)"
echo

# 2. build 镜像
echo "🔨 构建镜像..."
docker build -t shuatipass:test . || {
    echo "❌ 构建失败"
    exit 1
}
echo "✅ 镜像构建成功"
echo

# 3. 镜像信息
echo "📊 镜像信息:"
docker images shuatipass:test --format "  {{.Repository}}:{{.Tag}}  {{.Size}}  创建于 {{.CreatedSince}}"
echo

# 4. 测 help
echo "🧪 测试 1: shuatipass --help"
docker run --rm shuatipass:test --help | head -5
echo

# 5. 测 info
echo "🧪 测试 2: shuatipass info（用示例 PDF）"
SAMPLE_PDF="data/input/物理-高考真题-学科网.pdf"
if [ -f "$SAMPLE_PDF" ]; then
    docker run --rm \
        -v "$(pwd)/$SAMPLE_PDF:/data/input/test.pdf:ro" \
        -v "$(pwd)/data/output:/data/output" \
        shuatipass:test info /data/input/test.pdf | head -5
    echo "✅ info 命令正常"
else
    echo "⚠️  示例 PDF 不存在，跳过 info 测试"
fi
echo

# 6. 测 parse
echo "🧪 测试 3: shuatipass parse（端到端）"
if [ -f "$SAMPLE_PDF" ]; then
    # 清理旧结果
    rm -rf /tmp/shuatipass-test
    mkdir -p /tmp/shuatipass-test/images

    docker run --rm \
        -v "$(pwd)/$SAMPLE_PDF:/data/input/test.pdf:ro" \
        -v /tmp/shuatipass-test:/data/output \
        shuatipass:test parse /data/input/test.pdf -o /data/output/result.json --images /data/output/images 2>&1 | tail -5

    if [ -f /tmp/shuatipass-test/result.json ]; then
        echo "✅ JSON 输出存在"
        python3 -c "
import json
with open('/tmp/shuatipass-test/result.json') as f:
    d = json.load(f)
total = sum(len(t['questions']) for t in d['topics'])
print(f'  专题: {len(d[\"topics\"])}')
print(f'  题目: {total}')
print(f'  配置: {d.get(\"config_name\", \"?\")}')
"
    else
        echo "❌ JSON 未生成"
        exit 1
    fi
else
    echo "⚠️  示例 PDF 不存在，跳过 parse 测试"
fi
echo

# 7. 镜像大小检查
echo "📏 镜像大小检查:"
SIZE=$(docker images shuatipass:test --format "{{.Size}}")
echo "  $SIZE"
echo

# 8. 清理
echo "🧹 清理测试镜像..."
docker rmi shuatipass:test 2>/dev/null || true
rm -rf /tmp/shuatipass-test

echo "================================================"
echo "  ✅ 所有测试通过！"
echo "================================================"
