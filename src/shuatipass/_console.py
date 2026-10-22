"""控制台输出兼容层。

🔴 为什么需要这个：
本项目大量使用 emoji 做输出标识（📋 📊 ✅ ❌ 📒 …）。中文 Windows 的
控制台代码页是 **cp936 (GBK)**，编码不了这些字符。而 Python 在
**stdout 被重定向**（管道、> file、被 CI/工具捕获）时用的是
locale 编码 + ``errors='strict'`` ⇒ 遇到一个 emoji 直接
``UnicodeEncodeError`` 崩掉。

    shuatipass configs > out.txt     # ← 崩
    shuatipass configs               # ← 交互式终端里通常没事

修法：只放宽**错误字符**（``errors="replace"``），**不改码页**。
如果改成 ``encoding="utf-8"``，整篇中文在控制台里都会变成乱码 ——
那是把一个 bug 换成另一个。

幂等：可以反复调用。
"""

from __future__ import annotations

import sys


def enable_console_compat() -> None:
    """让 stdout / stderr 能承受 emoji 等 GBK 编不了的字符。

    幂等；流不支持 reconfigure 时静默跳过（某些嵌入式环境会替换掉 sys.stdout）。
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(errors="replace")
        except (ValueError, OSError):  # pragma: no cover - 取决于宿主环境
            pass
