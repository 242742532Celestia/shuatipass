# 发布到 GitHub 指南

> 这份文档是给维护者用的 —— 怎么把 shuatipass 推到 GitHub + 发 v0.1.0 tag

## 准备工作（已完成 ✅）

- [x] `LICENSE`（MIT）
- [x] `README.md`（9 个子命令 + 安装 + 用法 + 状态表）
- [x] `CHANGELOG.md`（D1-D12 完整记录）
- [x] `.gitignore`（不含 PDF/API key/dist）
- [x] `pyproject.toml`（PyPI 配置）
- [x] `.github/workflows/ci.yml`（CI 测试）
- [x] `.github/workflows/release.yml`（PyPI + GitHub Release）

## 步骤

### 1. 在 GitHub 上创建空 repo

1. 打开 https://github.com/new
2. Repository name: `shuatipass`
3. Description: `中文题库 PDF 解析 + AI 出题工具链`
4. 选择 **Public**（开源）
5. **不要**勾选 "Initialize with README"（我们要 push 自己的）
6. 点击 "Create repository"

### 2. 把代码推上去

#### 方法 A：用 sandbox 里的 .git 目录（最快）

sandbox 里已经 `git init` 并 commit 完毕。把 `/workspace/shuatipass` 整个文件夹（含 .git）下载到本地：

1. 下载 `shuatipass/` 文件夹（沙箱快照或 tarball）
2. 在本地解压/放到一个目录
3. 添加 remote + push：

```bash
cd shuatipass
git remote add origin https://github.com/<你的用户名>/shuatipass.git
git branch -M main
git push -u origin main
```

#### 方法 B：用 tarball 重新 commit

下载 `shuatipass-v0.1.0.tar.gz`（87 KB），本地解压后：

```bash
tar -xzf shuatipass-v0.1.0.tar.gz
cd shuatipass
git init -b main
git add -A
git commit -m "v0.1.0: initial release"
git remote add origin https://github.com/<你的用户名>/shuatipass.git
git push -u origin main
```

### 3. 推 v0.1.0 tag（触发 PyPI + GitHub Release）

```bash
cd shuatipass
git tag -a v0.1.0 -m "v0.1.0: initial release"
git push origin v0.1.0
```

### 4. 配置 PyPI Trusted Publishing（首次发布需要）

因为 release.yml 用了 [PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/)（无需手动 token），需要先在 PyPI 后台配：

1. 打开 https://pypi.org/manage/account/publishing/
2. 点击 "Add a new pending publisher"
3. 填：
   - **PyPI Project Name**: `shuatipass`
   - **Owner**: `<你的 GitHub 用户名>`
   - **Repository name**: `shuatipass`
   - **Workflow filename**: `release.yml`
   - **Environment name**: 留空
4. 点 "Add"

如果还没在 PyPI 创建 `shuatipass` 项目，第一次需要手动：

```bash
# 在本地：
python -m pip install --upgrade build twine
python -m build
python -m twine upload dist/*
# 第一次会让你输 PyPI 账号密码（或 token）
```

之后所有 v*.*.* tag 都会自动发布到 PyPI + 创建 GitHub Release。

### 5. （可选）完善 GitHub repo 设置

推完代码后，到 GitHub repo 设置页：

- [ ] **About**: 写一句简介，加 topic: `pdf`, `chinese`, `education`, `parser`, `llm`
- [ ] **Website**: 留空或填文档地址
- [ ] **Releases**: 推 tag 后会自动出现 v0.1.0
- [ ] **Issues**: 启用（默认开）
- [ ] **Discussions**: 可选 —— 想跟用户互动就开
- [ ] **Branch protection**: 给 main 分支加保护（maintainer 才能 push）

### 6. 推完后验证

```bash
# 验证 PyPI
pip install shuatipass
shuatipass --version
shuatipass --help

# 验证 GitHub
# 打开 https://github.com/<你的用户名>/shuatipass
# 看 README / LICENSE / Actions / Releases
```

## 发布清单

| 任务 | 状态 | 备注 |
|------|------|------|
| LICENSE (MIT) | ✅ | |
| README.md | ✅ | 9 个子命令 + 文档链接 |
| CHANGELOG.md | ✅ | v0.1.0 |
| .gitignore | ✅ | 不含 PDF / API key |
| Git 初始 commit | ✅ | 64 个文件，干净 |
| CI (3 Python 版本) | ✅ | `.github/workflows/ci.yml` |
| Release workflow | ✅ | `release.yml` 配 trusted publishing |
| Issue 模板 | ✅ | bug + feature request |
| PyPI 配置 | ✅ | `pyproject.toml` |
| Docker 镜像 | ✅ | `Dockerfile` + `docker-compose.yml` |
| **推到 GitHub** | ⏳ | **等你执行** |
| **打 v0.1.0 tag** | ⏳ | **等你执行** |
| **PyPI trusted publisher 配置** | ⏳ | **首次需要配** |

## 完成后

- 🐙 GitHub: `https://github.com/<你的用户名>/shuatipass`
- 📦 PyPI: `pip install shuatipass`
- 🐳 Docker: `docker pull <你的用户名>/shuatipass`（需要 push docker hub）

## 后续

- **每次发布新版本**：
  1. 改 `CHANGELOG.md` + `pyproject.toml` 的 `version`
  2. `git tag -a v0.1.1 -m "..."`
  3. `git push origin v0.1.1`
  4. CI 自动 build + publish + release
- **接受 PR**：开 issue 讨论 → 接受 → merge
- **社区**：开 Discussions / 写 blog / 录 demo 视频
