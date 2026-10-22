"""控制台输出兼容层测试。

🔴 背景：本项目到处用 emoji 做输出标识（📋 📊 ✅ ❌ 📒）。中文 Windows 的
控制台代码页是 cp936 (GBK)，编码不了这些字符；而 stdout 被重定向时
（管道、> file、被 CI/工具捕获）Python 用的是 locale 编码 + errors='strict'
⇒ 遇到第一个 emoji 就 UnicodeEncodeError 崩掉。

    shuatipass configs > out.txt     # ← 崩
"""

import io

import pytest

from shuatipass._console import enable_console_compat


def _gbk_stream() -> io.TextIOWrapper:
    """造一个 GBK + strict 的文本流，模拟中文 Windows 的 stdout。"""
    return io.TextIOWrapper(io.BytesIO(), encoding="gbk", errors="strict")


def test_gbk_stream_raises_without_compat():
    """不做处理的话，遇到 emoji 直接 UnicodeEncodeError —— 这就是线上那个 bug。"""
    stream = _gbk_stream()
    with pytest.raises(UnicodeEncodeError):
        stream.write("📋 内置配置\n")


def test_compat_makes_gbk_stream_tolerate_emoji(monkeypatch):
    """enable_console_compat() 之后，GBK 流也能输出 emoji（编不出来的降级成 ?）。"""
    stream = _gbk_stream()
    monkeypatch.setattr("sys.stdout", stream)

    enable_console_compat()

    print("📋 内置配置")
    stream.flush()

    out = stream.buffer.getvalue().decode("gbk", errors="replace")
    assert "内置配置" in out


def test_compat_keeps_chinese_readable(monkeypatch):
    """🔴 关键：**不能**把 encoding 改成 utf-8 —— 那会让整篇中文在控制台里变乱码。
    这里断言码页没被改（中文仍按 GBK 存）。"""
    stream = _gbk_stream()
    monkeypatch.setattr("sys.stdout", stream)

    enable_console_compat()

    print("中文标题")
    stream.flush()

    raw = stream.buffer.getvalue()
    assert "中文标题".encode("gbk") in raw


def test_compat_is_idempotent(monkeypatch):
    """反复调用不能炸（reconfigure 同一流两次是可以的，但要有护栏）。"""
    stream = _gbk_stream()
    monkeypatch.setattr("sys.stdout", stream)

    enable_console_compat()
    enable_console_compat()

    print("📋 再来一次")
    stream.flush()


def test_compat_tolerates_missing_reconfigure(monkeypatch):
    """某些嵌入式环境会把 sys.stdout 换成没有 reconfigure 的对象 —— 不能因此抛异常。"""

    class Dummy:
        pass

    monkeypatch.setattr("sys.stdout", Dummy())
    enable_console_compat()  # 不抛异常就算过


class TestCliSmoke:
    """CLI 冒烟：这几个命令以前在 Windows 重定向输出时会直接崩。"""

    def test_configs_command(self, run_cli):
        result = run_cli("configs")
        assert result.returncode == 0, result.stderr
        assert "内置配置" in result.stdout

    def test_stats_missing_file(self, run_cli, tmp_path):
        """文件不存在 → 走错误分支（错误信息带 ❌，也必须能输出）"""
        result = run_cli("stats", str(tmp_path / "nope.json"))
        assert result.returncode != 0
