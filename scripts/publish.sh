#!/bin/bash
# 刷题通 shuatipass 发布到 PyPI
#
# 用法：
#   bash scripts/publish.sh test   # 发布到 TestPyPI
#   bash scripts/publish.sh prod   # 发布到正式 PyPI
#
# 要求：
#   1. pip install build twine
#   2. 设置环境变量 TWINE_USERNAME / TWINE_PASSWORD
#      - TestPyPI: https://test.pypi.org/account/register/
#      - PyPI: https://pypi.org/account/register/
#   3. 或者用 trusted publishing（推荐）—— 在 GitHub 配 PYPI_API_TOKEN

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

ENV="${1:-prod}"

case "$ENV" in
    test)
        REPO_URL="https://test.pypi.org/legacy/"
        REPO_DESC="TestPyPI"
        ;;
    prod)
        REPO_URL="https://upload.pypi.org/legacy/"
        REPO_DESC="PyPI"
        ;;
    *)
        echo "❌ 未知环境: $ENV（用 test 或 prod）"
        exit 1
        ;;
esac

echo "================================================"
echo "  发布到 $REPO_DESC"
echo "================================================"

# 1. 清理旧 build
echo "🧹 清理旧 build..."
rm -rf build/ dist/ *.egg-info src/*.egg-info

# 2. 装 build 工具
echo "📦 确保 build 工具已装..."
pip install --quiet --upgrade build twine

# 3. 跑测试
echo "🧪 跑测试..."
python3 -m pytest tests/ -x --ignore=tests/test_docker.py -q || {
    echo "❌ 测试失败，不发布"
    exit 1
}

# 4. 跑 lint
echo "🔍 跑 lint (black + ruff)..."
if command -v black &> /dev/null; then
    black --check src/ tests/ || {
        echo "❌ black 检查失败"
        echo "   跑: black src/ tests/"
        exit 1
    }
fi
if command -v ruff &> /dev/null; then
    ruff check src/ tests/ || {
        echo "❌ ruff 检查失败"
        exit 1
    }
fi

# 5. Build
echo "🔨 构建分发包..."
python3 -m build

# 6. 检查
echo "✅ 检查分发包..."
twine check dist/*

# 7. 显示构建产物
echo ""
echo "📦 构建产物："
ls -la dist/

# 8. 确认
echo ""
if [ "$ENV" = "prod" ]; then
    echo "⚠️  即将发布到正式 PyPI！"
    read -p "确认? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "❌ 取消发布"
        exit 1
    fi
fi

# 9. 上传
echo "🚀 上传到 $REPO_DESC..."
twine upload --repository-url "$REPO_URL" dist/* || {
    echo "❌ 上传失败"
    echo "   提示: 检查 TWINE_USERNAME / TWINE_PASSWORD 环境变量"
    exit 1
}

echo ""
echo "================================================"
echo "  ✅ 发布成功！"
echo "================================================"
echo ""
if [ "$ENV" = "test" ]; then
    echo "测试包地址: https://test.pypi.org/project/shuatipass/"
    echo ""
    echo "试装: pip install -i https://test.pypi.org/simple/ shuatipass"
else
    echo "正式包地址: https://pypi.org/project/shuatipass/"
    echo ""
    echo "现在可以: pip install shuatipass"
fi
