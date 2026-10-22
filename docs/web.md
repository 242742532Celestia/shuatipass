# shuatipass Web UI 指南

> Gradio 实现的轻量 Web 界面 —— 无需写代码就能用 shuatipass。

## 启动

### 命令行

```bash
# 安装
pip install shuatipass[web]   # 或 pip install gradio

# 启动
shuatipass web
# 默认: http://127.0.0.1:7860
```

### 自定义参数

```bash
# 改端口
shuatipass web --port 8888

# 监听所有网络（容器/远程访问）
shuatipass web --host 0.0.0.0 --port 7860

# 生成公网分享链接（Gradio 内置，72h 有效）
shuatipass web --share
```

### Python 启动

```python
from shuatipass import launch_web
launch_web(host="0.0.0.0", port=7860, share=False)
```

## 界面

### Tab 1: 解析 PDF

- **左栏**：上传 PDF + 选配置 + 解析按钮
- **右栏**：统计信息（题目数/年份分布/专题列表）
- **下方**：题目预览（前 5 专题 × 2 题，含图片）
- **下载**：解析完成的 JSON

### Tab 2: 使用说明

新手教学 —— 三步上手

### Tab 3: 关于

项目信息、链接、路线图

## 用法截图

启动后浏览器访问 `http://127.0.0.1:7860`：

```
┌────────────────────────────────────────────────────────────┐
│  📚 shuatipass · 中文题库 PDF 解析工具                       │
├────────────────────────────────────────────────────────────┤
│  [📤 解析 PDF]  [📖 使用说明]  [🔧 关于]                     │
├────────────────────────────────────────────────────────────┤
│  上传 PDF:    [选择文件]                  配置: ◉ auto       │
│                                          ○ xuekewang       │
│                                          ○ generic         │
│                                          ○ zujuan          │
│                                          ○ textbook        │
│                                                              │
│              [🚀 解析]                                        │
├────────────────────────────────────────────────────────────┤
│  ## 📊 统计                                                  │
│  - 文件: 物理-高考真题-学科网.pdf                            │
│  - 题目: 821                                                 │
│  - 题型: single_choice: 684 / essay: 121 / ...              │
└────────────────────────────────────────────────────────────┘
```

## 部署

### 本地开发

```bash
shuatipass web --host 127.0.0.1 --port 7860
```

### Docker

更新 Dockerfile，加 gradio 依赖：

```dockerfile
# 安装 web 依赖
RUN pip install --no-cache-dir --prefix=/install .[web]
```

然后：

```bash
docker build -t shuatipass-web .
docker run -p 7860:7860 shuatipass-web shuatipass web --host 0.0.0.0
```

### 远程服务器

```bash
# 在服务器上
shuatipass web --host 0.0.0.0 --port 7860

# 本地访问
ssh -L 7860:localhost:7860 user@server
# 浏览器: http://localhost:7860
```

### 公网分享

```bash
shuatipass web --share
# 输出: Running on public URL: https://xxxxx.gradio.live
```

72 小时内任何人可访问（Gradio 内置 ngrok 隧道）。

## API 端点

Gradio 自动暴露 REST API：

```bash
# 解析端点
curl -X POST http://127.0.0.1:7860/gradio_api/call/parse \
  -H "Content-Type: application/json" \
  -d '{"data": ["/path/to/test.pdf", "xuekewang"]}'
```

或用 Gradio Python client：

```python
from gradio_client import Client
client = Client("http://127.0.0.1:7860")
result = client.predict("/path/to/test.pdf", "xuekewang", api_name="/parse")
```

## 故障排查

### 端口被占

```bash
shuatipass web --port 8888  # 换端口
```

### gradio 没装

```bash
pip install gradio
# 或
pip install shuatipass[web]
```

### 浏览器打不开

```bash
# 1. 看服务是否真的起来
shuatipass web --host 127.0.0.1 --port 7860
# 输出: Running on local URL: http://127.0.0.1:7860

# 2. 防火墙检查
sudo ufw allow 7860  # Ubuntu
```

### 解析慢

- 大 PDF（>500 页）需要 1-2 分钟
- 默认会显示 Gradio 进度条

## 测试

```bash
# 跑 web 测试
python3 -m pytest tests/test_web.py -v
```

10 个测试：
- `test_is_available` —— gradio 装了
- `test_build_ui` —— UI 能构建
- `test_parse_pdf_no_pdf` —— 无 PDF 错误处理
- `test_parse_pdf_missing` —— PDF 不存在
- `test_parse_pdf_real` —— 真实 PDF 端到端
- `test_launch_web_no_gradio` —— gradio 不可用报错
- `test_callback_returns_three_values` —— 事件回调返回值个数 == outputs 个数
- `test_outputs_count_matches_callback` —— outputs 列表长度和回调返回值对得上
- `test_outputs_order_matches_callback` —— outputs 顺序（文件/统计/预览）和返回值对得上
- `test_error_message_reaches_stats_pane` —— 出错时错误信息显示在统计栏（不是 File 组件）

> 🔴 后 4 个是**接线契约**测试，不装 gradio 也能跑。
> 之前 Web UI 的「解析」按钮点了就炸（outputs 接的是 4 元组、还错位），
> 就是因为这类断言根本不存在 —— 而且 gradio 只在**点击时**才校验数量，
> build 阶段根本不报错。
