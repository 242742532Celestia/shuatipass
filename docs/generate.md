# shuatipass AI 出题指南

> 基于 LLM 的智能出题 —— 借鉴 DEEPTUTOR 的"Knowledge Reinforcement"模块。

## 功能

- 📚 **基于种子题风格生成**：从已有题库学风格，生成相似新题
- 🎯 **按知识点生成**：指定知识点 + 难度，AI 出新题
- 📝 **模拟卷（Exam Mimic）**：从大题库抽题，AI 模仿出整张卷
- 💾 **支持追加到原 JSON**：新题并入原题库，作为"AI 生成题"专题
- 🔌 **多 LLM 支持**：MiniMax / OpenAI / Anthropic

## 快速上手

### 前置：配 API key

```bash
# MiniMax（推荐）
export MINIMAX_API_KEY="your_key"

# 或 OpenAI
export OPENAI_API_KEY="your_key"

# 或 Anthropic
export ANTHROPIC_API_KEY="your_key"
```

### 模式 1：按知识点生成

```bash
shuatipass generate \
  -o new-questions.json \
  --topic "圆周运动" \
  --difficulty medium \
  --count 5
```

输出：
```
🤖 AI 出题
   Provider: minimax/MiniMax-Text-01
   难度: medium
   数量: 5
   题型: single_choice
🤖 调用 minimax/MiniMax-Text-01 生成 5 道题...

✅ 生成 5 题

--- 题 1 (匀速圆周运动) ---
题干: 一个质量为m的小球，以速度v在光滑水平面上做半径为r的匀速圆周运动...
  A. 向心力大小为mv²/r
  B. 向心力大小为mv/r
  ...
```

### 模式 2：基于种子题风格

```bash
shuatipass generate \
  -o new-questions.json \
  --seed data/parsed/questions.json \
  --topic "圆周运动" \
  --difficulty hard \
  --count 3
```

AI 会从 `questions.json` 里学 5 道样题的风格（命题方式、难度、考点），再生成新题。

### 模式 3：模拟卷（Exam Mimic）

```bash
shuatipass generate \
  -o mock-exam.json \
  --seed data/parsed/questions.json \
  --mock-exam \
  --topic-ids "01" \
  --count 20
```

- 从专题 01 抽 5 道做种子
- AI 学风格后生成 20 道新题
- 整张卷子"看起来像"原题

### 模式 4：追加到原题库

```bash
shuatipass generate \
  -o data/parsed/questions.json \
  --seed data/parsed/questions.json \
  --append \
  --count 10
```

把生成的题作为"AI 生成题"专题追加到原 JSON。

## 参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `-o` | 必填 | 输出 JSON 路径 |
| `--seed` | - | 种子题 JSON 路径 |
| `--topic` | - | 知识点（如"圆周运动"）|
| `--difficulty` | medium | easy/medium/hard/expert |
| `--count` | 5 | 生成题数 |
| `--type` | single_choice | single_choice/multi_choice/essay |
| `--subject` | 物理 | 学科 |
| `--provider` | minimax | minimax/openai/anthropic |
| `--model` | provider 默认 | 自定义模型 |
| `--temperature` | 0.7 | 创造性 0-1 |
| `--mock-exam` | false | 模拟卷模式 |
| `--topic-ids` | - | 限定专题（逗号分隔）|
| `--append` | false | 追加到 seed |

## Python API

```python
from shuatipass import generate_questions, generate_mock_exam, save_to_json

# 基础生成
questions = generate_questions(
    provider="minimax",
    topic="圆周运动",
    difficulty="hard",
    count=5,
    seed_questions=[...],  # 可选
)
save_to_json(questions, "out.json")

# 模拟卷
data = generate_mock_exam(
    seed_json="questions.json",
    count=20,
    difficulty="medium",
)
```

## 输出格式

```json
{
  "id": "GEN-001",
  "number": 1,
  "year": 2026,
  "province": "AI 生成",
  "type": "single_choice",
  "stem": "题干...",
  "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "answer": "A",
  "explanation": "解析...",
  "knowledge_point": "匀速圆周运动",
  "difficulty": "hard",
  "ai_generated": true,
  "seed_ids": ["01-005", "01-012"]
}
```

## 借鉴自 DEEPTUTOR

DEEPTUTOR 港大项目（17.8k stars）的"Knowledge Reinforcement & Practice Exercise Generator"是这个功能的灵感来源。

shuatipass 的差异化：
- shuatipass 专注"PDF 解析 + AI 出题"的工具链
- DEEPTUTOR 是完整学习平台（多 Agent + 知识图谱 + 记忆系统）
- 两者上下游关系：shuatipass 解析的 JSON 可直接喂给 DEEPTUTOR

## 故障排查

### 问题 1：没 API key

```
❌ 需要环境变量 MINIMAX_API_KEY
   1. 注册: https://api.minimax.chat/
   2. export MINIMAX_API_KEY='your_key'
```

### 问题 2：openai 没装

```
❌ 生成失败: 需要安装 openai: pip install openai
```

解决：
```bash
pip install openai
# 或
pip install shuatipass
```

### 问题 3：JSON 解析失败

LLM 偶尔会返回非严格 JSON。脚本会报"不是有效 JSON"。可：
1. 调低 `--temperature`（如 0.3）
2. 换更大的模型
3. 重试

## 测试

```bash
python3 -m pytest tests/test_generator.py -v
```

19 个测试（用 mock 模拟 LLM 响应）：
- 4 个 prompt 构造测试
- 5 个响应解析测试
- 2 个端到端 mock 测试
- 2 个保存测试
- 2 个模拟卷测试
- 2 个 provider 配置测试
- 3 个 CLI 测试

## 路线图

- [x] 基础出题（按知识点）
- [x] 种子题风格学习
- [x] 模拟卷
- [x] 追加到原 JSON
- [x] 多 provider 支持
- [ ] 公式自动 LaTeX 化（生成后用 OCR 跑）
- [ ] 出题质量自动评分
- [ ] 人工反馈学习（标记好/坏题）
