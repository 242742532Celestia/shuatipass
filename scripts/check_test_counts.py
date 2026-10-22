"""校验「文档里写的测试数」和「pytest 实际收集到的用例数」一致。

🔴 为什么要这个守卫：
文档里的测试数以前是手抄的。仓库从 51 个用例长到 110 个之后，
``docs/publish.md`` 还写着「所有测试通过（51 个）」—— 数字早就过期了，
但没有任何东西会报错，因为没人会去数。

这里把「数字」改成**实跑出来的**，并且加一条 CI 检查盯着它：
  ① ``docs/test-counts.json`` 里的每文件计数 == pytest 实际收集数；
  ② 清单里的文件集合 == 实际收集的文件集合（新增/删除测试文件必须同步清单）；
  ③ 清单总数 == 各文件之和；
  ④ 文档里几处「N 个测试 / N 个用例」的说法 == 清单里对应的数字。

口径说明（很重要，别改错）：
  * 断言的是**收集到的用例总数**（``pytest --collect-only``），它与环境无关；
  * **不**断言 passed / skipped 的拆分 —— 跳过数取决于本机有没有
    docker / gradio / 示例 PDF，各环境不一样，断言它只会制造假红。

用法：
    python scripts/check_test_counts.py            # 检查
    python scripts/check_test_counts.py --write    # 按实跑结果重写清单
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "docs" / "test-counts.json"

# Windows 控制台默认 GBK，编码不了 ✅/❌ → 只放宽错误字符，**不改码页**
# （改成 utf-8 会让整篇中文在控制台里乱码）。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(errors="replace")

# 文档里"测试数"的说法 → 对应清单里的哪一项
#   (文档相对路径, 正则（含一个捕获组 = 数字）, 清单里的 key)
DOC_CLAIMS: list[tuple[str, str, str]] = [
    ("docs/publish.md", r"（(\d+) 个用例", "total"),
    ("docs/web.md", r"(\d+) 个测试", "tests/test_web.py"),
    ("docs/generate.md", r"(\d+) 个测试", "tests/test_generator.py"),
    ("docs/exam-mimic-wrongbook.md", r"(\d+) 个测试", "tests/test_exam_mimic.py"),
    ("README.md", r"YAML \+ 内置预设 \+ (\d+) 个测试", "tests/test_config.py"),
]


def collect_counts() -> dict[str, int]:
    """跑 pytest --collect-only，解析出每个测试文件的用例数。

    兼容两种 pytest 输出格式：
      * pytest >= 9：``tests/test_x.py: 14``（每文件一行计数）
      * pytest 7/8：``tests/test_x.py::TestFoo::test_bar``（每个用例一行）
    """
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-qq",
            "-o",
            "addopts=",
            "-p",
            "no:cacheprovider",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        print(proc.stdout[-3000:])
        print(proc.stderr[-3000:], file=sys.stderr)
        raise SystemExit("❌ pytest --collect-only 失败（收集阶段就有错，先修那个）")

    counts: dict[str, int] = {}
    for raw in proc.stdout.splitlines():
        line = raw.strip()
        m = re.match(r"^(tests[\\/][^:]+\.py):\s*(\d+)\s*$", line)
        if m:
            counts[m.group(1).replace("\\", "/")] = int(m.group(2))
            continue
        m = re.match(r"^(tests[\\/][^:]+\.py)::", line)
        if m:
            key = m.group(1).replace("\\", "/")
            counts[key] = counts.get(key, 0) + 1

    if not counts:
        print(proc.stdout[-3000:])
        raise SystemExit("❌ 没解析到 pytest 的收集结果（pytest 输出格式变了？）")
    return counts


def load_manifest() -> dict:
    if not MANIFEST.exists():
        raise SystemExit(f"❌ 清单不存在: {MANIFEST}")
    # utf-8-sig：容忍带 BOM 的文件（Windows 编辑器 / PowerShell Set-Content -Encoding UTF8 会写 BOM）
    raw = MANIFEST.read_text(encoding="utf-8-sig")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise SystemExit(f"❌ {MANIFEST} 不是合法 JSON: {e}") from e


def check(manifest: dict, actual: dict[str, int]) -> list[str]:
    """返回问题列表（空列表 = 全过）。"""
    problems: list[str] = []
    expected: dict[str, int] = manifest.get("counts", {})

    for key in sorted(set(expected) - set(actual)):
        problems.append(f"清单里有 {key}，但 pytest 没收集到（文件被删了？清单没同步？）")
    for key in sorted(set(actual) - set(expected)):
        problems.append(
            f"pytest 收集到 {key}（{actual[key]} 个），但清单里没有 —— 请同步 docs/test-counts.json"
        )
    for key in sorted(set(expected) & set(actual)):
        if expected[key] != actual[key]:
            problems.append(f"{key}: 清单写 {expected[key]}，实跑是 {actual[key]}")

    real_total = sum(actual.values())
    if manifest.get("total") != real_total:
        problems.append(f"总数: 清单写 {manifest.get('total')}，实跑是 {real_total}")

    return problems


def check_docs(manifest: dict) -> list[str]:
    """文档里写的测试数必须和清单一致。"""
    problems: list[str] = []
    expected: dict[str, int] = manifest.get("counts", {})
    total = manifest.get("total", 0)

    for rel, pattern, key in DOC_CLAIMS:
        path = ROOT / rel
        if not path.exists():
            problems.append(f"{rel}: 文件不存在")
            continue
        text = path.read_text(encoding="utf-8-sig")
        want = total if key == "total" else expected.get(key)
        if want is None:
            problems.append(f"{rel}: 清单里没有 {key}")
            continue
        found = re.search(pattern, text)
        if not found:
            problems.append(f"{rel}: 找不到「测试数」的说法（正则 {pattern}）—— 文档结构变了？")
        elif int(found.group(1)) != want:
            problems.append(f"{rel}: 文档写 {found.group(1)} 个，清单是 {want} 个（{key}）")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description="校验文档里的测试数 == pytest 实跑收集数")
    ap.add_argument("--write", action="store_true", help="按实跑结果重写 docs/test-counts.json")
    args = ap.parse_args()

    actual = collect_counts()

    if args.write:
        payload = {
            "_comment": (
                "pytest 实际收集到的用例数（由 scripts/check_test_counts.py 实跑生成，不是手抄的）。"
                "只记收集数，不记 passed/skipped —— 跳过数取决于本机有没有 docker / gradio / 示例 PDF，"
                "各环境不一样，断言它只会制造假红。"
            ),
            "counts": dict(sorted(actual.items())),
            "total": sum(actual.values()),
        }
        MANIFEST.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"✅ 已按实跑结果重写 {MANIFEST.relative_to(ROOT)}（total={sum(actual.values())}）")
        return 0

    manifest = load_manifest()
    problems = check(manifest, actual) + check_docs(manifest)
    if problems:
        print("❌ 测试数校验失败：")
        for p in problems:
            print(f"   - {p}")
        print()
        print("如果这些数字确实变了（真的加了/删了用例），跑：")
        print("   python scripts/check_test_counts.py --write")
        print("然后**同步改掉上面列出的文档**，别只改清单。")
        return 1

    print(
        f"✅ 测试数一致：{len(actual)} 个测试文件 / {sum(actual.values())} 个用例，"
        f"文档里的 {len(DOC_CLAIMS)} 处说法也都对得上"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
