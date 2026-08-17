# shuatipass 发布到 PyPI 指南

> 完整发布流程：从代码到 `pip install shuatipass`。

## 前置准备

### 1. 注册账号

- **PyPI**：https://pypi.org/account/register/
- **TestPyPI**：https://test.pypi.org/account/register/

### 2. 申请 API Token

在账号设置里生成 API Token：
- PyPI：https://pypi.org/manage/account/token/
- TestPyPI：https://test.pypi.org/manage/account/token/

设环境变量：
```bash
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="pypi-xxxxxxxxxxxxxxxxxxxx"  # 你的 token
```

### 3. （推荐）Trusted Publishing

更安全的方案 —— 在 GitHub 上配 trusted publishing：

1. PyPI 项目页 → Publishing → Add a new pending publisher
2. 填：
   - Owner: `yourname`
   - Repository: `shuatipass`
   - Workflow file: `release.yml`
   - Environment name: `pypi`
3. 这样不用 token，GitHub Action 自动认证

## 发布流程

### 第一次发布

```bash
# 1. 改版本号
# 编辑 pyproject.toml: version = "0.1.0"

# 2. 更新 CHANGELOG.md
# 加 v0.1.0 段落

# 3. 提交
git add -A
git commit -m "Release v0.1.0"
git tag v0.1.0
git push origin main --tags

# 4. 自动触发 release workflow
# GitHub Action 自动 build + publish to PyPI
```

### 手动发布（调试用）

```bash
# 发布到 TestPyPI（先试试）
bash scripts/publish.sh test

# 发布到正式 PyPI
bash scripts/publish.sh prod
```

## GitHub Actions 自动发布

`release.yml` 监听 `v*.*.*` 标签。推标签即触发：

```bash
git tag v0.1.0
git push origin v0.1.0
```

会自动：
1. Build sdist + wheel
2. 推送到 PyPI
3. 创建 GitHub Release

## 发布后验证

```bash
# 1. 检查 PyPI 页面
open https://pypi.org/project/shuatipass/

# 2. 从 PyPI 安装
pip install shuatipass

# 3. 测试
shuatipass --version
shuatipass info your.pdf
```

## 版本号规则

按 [Semantic Versioning](https://semver.org/)：

- **主版本**（1.0.0）：不向后兼容的大改
- **次版本**（0.2.0）：向后兼容的新功能
- **修订号**（0.1.1）：向后兼容的 bug fix

**当前**：0.1.0（Alpha）

## 发布检查清单

发布前确认：

- [ ] 所有测试通过（51 个）
- [ ] 文档已更新
- [ ] CHANGELOG.md 加了版本段
- [ ] pyproject.toml 版本号更新
- [ ] 没遗留调试代码
- [ ] 依赖版本在 requirements.txt / pyproject.toml 都对
- [ ] README 链接到 GitHub
- [ ] 跑过 `python3 -m build` 成功
- [ ] 跑过 `twine check dist/*` 成功

## 常见问题

### 问题 1：包名被占用

PyPI 包名全网唯一。如果 `shuatipass` 已被占：

```toml
# pyproject.toml
[project]
name = "shuatipass-edu"  # 加后缀
```

### 问题 2：版本已存在

PyPI 不允许覆盖已有版本。只能升版本号：

```toml
version = "0.1.1"  # 从 0.1.0 升到 0.1.1
```

### 问题 3：依赖装不上

常见于 sandbox 限速。用清华源：

```bash
PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple python3 -m build
```

或在 pyproject.toml 里固定：

```toml
[build-system]
requires = [
    "setuptools>=69",
    "wheel",
    "PyMuPDF>=1.28.0",  # build 阶段也要
]
```

### 问题 4：trusted publishing 配错

检查 GitHub Action 配的 environment name 必须和 PyPI 配的一致。

## 文件位置

- 发布脚本：`scripts/publish.sh`
- GitHub Actions：`.github/workflows/{ci,release}.yml`
- 包元数据：`pyproject.toml`
- 更新日志：`CHANGELOG.md`
