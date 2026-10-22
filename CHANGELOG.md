# Changelog

All notable changes to shuatipass will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-10-22

这一轮的目标是「让 CI 真的绿」，但修 CI 的过程里挖出了 5 个**真 bug** ——
它们在 CI 上看不见，却会让装好的包完全不能用。

### Fixed

- **Web UI 的「解析」按钮点了就炸**
  `_parse_pdf` 返回 4 元组，而 `outputs` 只接了 3 个、顺序还错位
  ⇒ Gradio 在点击时抛 `Number of output components does not match...`。
  新增 `_on_parse` 适配层（文件 / 统计 / 预览），并补 4 个**接线契约**测试
  —— 它们不装 gradio 也能跑，而且用 AST 数 `_build_ui` 里 outputs 的长度，
  不靠"点一下看看"。
  （gradio 只在**点击时**才校验数量，build 阶段根本不报错 —— 这就是它藏这么久的原因。）

- **装成 wheel 后找不到自己的内置配置**
  `configs/` 靠 `[tool.setuptools.data-files]` 装到**包外**（`<prefix>/configs`），
  而代码找的是包内路径 ⇒ `get_builtin()` 直接 `FileNotFoundError`，
  **整个包解析不了任何 PDF**（Docker 镜像同样中招）。
  现在 `configs/` 移进 `src/shuatipass/configs/`，跟着包走；
  `_builtin_dir()` 按「包内 → 源码树 → 安装前缀」顺序找，兼容旧的已装版本。

- **Windows GBK 控制台打印 emoji 直接崩**
  `shuatipass configs > out.txt` 一律 `UnicodeEncodeError`。
  新增 `shuatipass/_console.py`：只放宽**错误字符**（`errors="replace"`），
  **不改码页** —— 改成 `encoding="utf-8"` 会让整篇中文在控制台里变乱码，
  那是把一个 bug 换成另一个。

- **库写 UTF-8 却用 locale 编码读回**
  错题本 / 仿卷 / 生成 / OCR 在中文 Windows 上读自己写出的 JSON 会 `UnicodeDecodeError`。
  8 处 `open()` 全部显式 `encoding="utf-8"`（写的地方本来就有）。

- **测试自己把被测对象删了**
  `test_docker.py` 在 `finally` 里 `docker rmi` 删掉刚 build 的镜像，
  后面的 `test_help_command` 必然报 "No such image" ⇒ 改成模块级 fixture。

- **fixture 先跑、skip 后跑**
  `test_detect.py::test_xuekewang_works` 把 `pytest.skip()` 写在测试体里，
  但 fixture 先执行、已经炸了（ERROR 而不是 SKIPPED）⇒ skip 移进 fixture。

- **CI 的 build job 缺 twine**
  只装了 `build` 却跑 `python -m twine check` ⇒ `ModuleNotFoundError`。
  这个 job 一直被 `needs: [test, lint]` 挡着从没跑过，test/lint 一绿就炸。

- **PyPI 发布会永远红**
  OIDC 信任发布要求项目**已在 PyPI 注册**，首次发布必挂 ⇒ 改成
  token secret + 没配就**跳过**（skipped ≠ 失败），并在日志里明确告警。

- **GitHub Release 的附件数是 0**
  `github-release` job 直接贴 `dist/*.whl`，可那是**另一个 job** 的产物，
  它自己从不 build ⇒ v0.1.0 的发布页是个空壳。
  改成 `build → artifact → 下游消费`，`fail_on_unmatched_files: true`。

- **占位符**
  16 处 `yourname`（GitHub 地址 11 / Docker Hub 4 / PyPI owner 1）+ CHANGELOG 里的 `<owner>`。
  GitHub 地址填真实 handle；Docker Hub / PyPI 这种**用户账号未知**的改成
  一眼可辨的填写提示（`your-docker-id` / `your-pypi-username`），不造假。

- **文档里的测试数是手抄的**
  `docs/publish.md` 还写着「所有测试通过（51 个）」，实跑已经 117 个 ——
  而且没有任何东西会报错，因为没人会去数。
  现在数字来自实跑，并加了 `scripts/check_test_counts.py` 机械校验
  （清单 ↔ pytest 收集数 ↔ 文档说法，三方一致才算过）。

### Changed

- ruff：96 项告警 → 0（CI 的 lint job 之前必红）
- black：18 个文件重新格式化
- `requires-python`：`>=3.10,<3.13` → `>=3.10,<3.14`
  （3.13 上本机实跑 117 个用例全绿；原来的上界让包**装不上**当前主流 Python）
- CI matrix 加 3.13；新增独立的 `web` job（装 gradio）——
  主 matrix 不装 gradio 是为了快，但**Web UI 的接线只有装上 gradio 才测得到**
- lint 覆盖到 `scripts/`
- `py.typed` 补齐（pyproject 声明了，但文件从来不存在）

### Added

- `scripts/check_test_counts.py` + `docs/test-counts.json`
  —— 盯住"文档里的测试数 == pytest 实跑收集数"
- `tests/conftest.py` 的 `run_cli` fixture
  —— 用 `python -m shuatipass` 调 CLI，不再依赖 console script 在 PATH 上
- `src/shuatipass/__main__.py` —— `python -m shuatipass` 入口
- `src/shuatipass/_console.py` —— 控制台 emoji 兼容层

### Verified

本机（Windows / Python 3.13.9）实跑：**117 个用例，99 passed / 18 skipped**
（跳过的是缺示例 PDF、缺 docker 的用例，各环境不一样）。
wheel 装进干净 venv 后 `shuatipass configs` / `get_builtin()` 正常。

## [0.1.0] - 2026-08-17

### Added
- **D1**: PDF parser core (PyMuPDF) with 4 built-in question types
- **D2**: bbox cutting, essay detection, embedded option splitting
- **D3**: CLI + Python library (parse / stats / info / configs)
- **D4**: YAML config system with 4 built-in presets (xuekewang / generic / zujuan / textbook)
- **D5**: Documentation (tutorial / api / config / examples / docker / publish / web)
- **D6**: Docker multi-stage build + docker-compose
- **D7**: GitHub Actions CI (Python 3.10/3.11/3.12 + lint + build)
- **D8**: PyPI publish prep + wheel built
- **D9**: Auto-detect PDF source + 2 new configs
- **D10**: Formula OCR (Mathpix API + pix2tex)
- **D11**: AI question generator (3 providers: MiniMax / OpenAI / Anthropic)
- **D12**: Exam Mimic 完整版 + 错题本 (mark / export / HTML)

### Features
- 9 CLI subcommands: `parse`, `stats`, `info`, `configs`, `ocr`, `web`, `generate`, `exam-mimic`, `wrongbook`
- 100 unit tests + 6 skipped (with gradio)
- 7 documentation files in `docs/`
- 7 example scripts in `examples/`
- Gradio Web UI with one-click parse
- MIT License
- PyPI-ready packaging

[Unreleased]: https://github.com/242742532Celestia/shuatipass/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/242742532Celestia/shuatipass/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/242742532Celestia/shuatipass/releases/tag/v0.1.0
