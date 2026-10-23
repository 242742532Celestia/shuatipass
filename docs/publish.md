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

### 3. 🔴 在 GitHub 上配置 PyPI Token（**必做，否则 PyPI 发布会被跳过**）

这一步是 2026-10-22 之前 v0.1.0 发布一直失败的原因。`release.yml` 现在从
**仓库 secret** 里读 token（不是环境变量）：

1. 打开仓库 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
2. Name: `PYPI_API_TOKEN`
3. Secret: 粘贴第 2 步生成的 token（形如 `pypi-AgEIcHlwaS5vcmc...`）
4. 保存

**没配会怎样**：`publish-pypi` 这个 job 会被**跳过（skipped）**，不是失败 ——
这样 Release workflow 不会常驻一个红叉，但**包也不会真的发到 PyPI**，
日志里会有一条明确告警。想真的发布就必须配这个 secret。

### 4.（可选）Trusted Publishing

更安全的方案 —— 不用存 token，让 GitHub Action 用 OIDC 身份认证：

1. PyPI 项目页 → Publishing → Add a new pending publisher
2. 填：
   - Owner: `your-pypi-username`
   - Repository: `shuatipass`
   - Workflow file: `release.yml`
   - Environment name: `pypi`
3. 然后把 `release.yml` 里的 `publish-pypi` job 改成用 OIDC（去掉 `password:` 输入、
   保留 `permissions: id-token: write`），并去掉 `if:` 条件

⚠️ 用信任发布的前提是 **PyPI 上已经存在 `shuatipass` 这个项目**。
项目还不存在时，OIDC 会直接失败 —— 这正是 v0.1.0 那次发布红掉的原因。
**首次发布建议走第 3 步的 token 方式**，等项目在 PyPI 上建好后再切信任发布。

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

1. **Build** —— 打包 sdist + wheel，跑 `twine check`，把产物存成 artifact
2. **Publish to PyPI** —— 需要 `PYPI_API_TOKEN` secret；没配则**跳过**（不是失败）
3. **Create GitHub Release** —— 把 wheel + sdist 贴到 Release 页上

> 2026-10-22 之前，第 3 步是坏的：它直接贴 `dist/*.whl`，但 `dist/` 是另一个 job 的产物，
> 而它自己从不 build ⇒ **workflow 一个附件都没贴上**。
> 更阴的是 `fail_on_unmatched_files` 默认 **false** —— 匹配不到文件也静默成功，
> 看起来"发布页建好了"，实际 **wheel 从来没上去**（v0.1.0 页面上那两个文件是手工传的）。
> 现在改成 build 一次 → artifact → 两个下游 job 各取所需，
> 并加 `fail_on_unmatched_files: true`：匹配不到就**失败**，不再静默。

## 发布后验证

```bash
# 1. 检查 PyPI 页面
open https://pypi.org/project/shuatipass/

# 2. 从 PyPI 安装
pip install shuatipass

# 3. 测试
shuatipass --version
shuatipass info your.pdf

# 4. 🔴 确认内置配置跟着包装上了（v0.1.0 的 wheel 就是死在这）
#    configs/ 以前靠 data-files 装到包外，而代码找的是包内路径
#    ⇒ 装完 get_builtin() 直接 FileNotFoundError，整个包解析不了任何 PDF
shuatipass configs          # 应该列出 generic / textbook / xuekewang / zujuan
```

## 版本号规则

按 [Semantic Versioning](https://semver.org/)：

- **主版本**（1.0.0）：不向后兼容的大改
- **次版本**（0.2.0）：向后兼容的新功能
- **修订号**（0.1.1）：向后兼容的 bug fix

**当前**：0.1.1（Alpha）

## 发布检查清单

发布前确认：

- [ ] 所有测试通过（117 个用例；数字由 `scripts/check_test_counts.py` 实跑盯着，别手抄）
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
