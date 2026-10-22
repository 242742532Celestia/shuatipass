"""pytest 公共夹具。"""

import os
import subprocess
import sys

import pytest


@pytest.fixture
def run_cli():
    """用当前解释器跑 shuatipass CLI。

    🔴 原来直接调 ``["shuatipass", ...]``，依赖 console script 在 PATH 上。
    在"包没装成 console script"的环境里（本地 venv 的 Scripts 目录没进 PATH、
    或从源码树直接跑 pytest）→ 子进程直接 FileNotFoundError，
    用例是红的，但和被测功能无关 —— 属于**环境问题伪装成功能失败**。

    改用 ``python -m shuatipass``，任何环境都能跑。

    同时显式固定编码：``encoding="utf-8"`` + 子进程 ``PYTHONIOENCODING=utf-8``。
    不然父子进程各按各的 locale 编码走（Windows 是 GBK、Linux 是 UTF-8），
    中文输出在 Windows 上会解码错乱。
    """

    def _run(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        child_env = dict(os.environ, PYTHONIOENCODING="utf-8")
        if env:
            child_env.update(env)
        return subprocess.run(
            [sys.executable, "-m", "shuatipass", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=child_env,
        )

    return _run
