"""``python -m shuatipass`` 入口。

🔴 没有这个文件时，只有装了 console script（``shuatipass``）才能从命令行启动；
在"源码树 + venv 没进 PATH"的环境里（比如本地跑测试、或从 git clone 直接跑），
子进程调 ``shuatipass`` 会直接 FileNotFoundError。
加上它之后，``python -m shuatipass`` 在任何环境都能用 —— 测试也改用它。

🔴 ``main()`` 返回的是退出码，必须 ``sys.exit(main())``：
直接调 ``main()`` 会让退出码恒为 0，"失败路径返回非 0"的用例就全假绿了。
（console script 那条路由 setuptools 生成的 wrapper 负责 sys.exit。）
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
