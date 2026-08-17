# shuatipass Exam Mimic + 错题本

> 借鉴自港大 DEEPTUTOR 项目的两个核心能力：
> - **Authenticate Exam Simulation** → `exam-mimic` 子命令
> - **Personal Notebook** → `wrongbook` 子命令

## Exam Mimic（完整克隆试卷风格）

### 快速上手

```bash
shuatipass exam-mimic \
  --seed data/parsed/questions.json \
  -o mock.json
```

会自动：
1. 分析原卷风格（题量/题型/难度/专题/分值）
2. 把风格特征喂给 LLM
3. 按风格生成完整新卷

### 与 `--mock-exam` 区别

| 特性 | `--mock-exam`（generate） | `exam-mimic`（独立子命令）|
|------|---------------------------|---------------------------|
| 风格分析 | ❌ 简单抽 5 道 | ✅ 完整特征化（题量/题型/难度比例）|
| 输出 | 新题（追加）| 完整新卷 + 风格报告 |
| 适用 | 补充少量新题 | 整张新卷 |

### 参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `--seed` | 必填 | 种子卷 JSON |
| `-o` | 必填 | 输出 JSON |
| `--count` | None | 目标题数（None = 跟原卷一致）|
| `--subject` | 物理 | 学科 |
| `--provider` | minimax | LLM provider |
| `--model` | None | 自定义模型 |

### 输出格式

```json
{
  "source": "shuatipass exam-mimic",
  "style": {
    "total_questions": 821,
    "estimated_duration": 2122,
    "estimated_score": 4380,
    "type_distribution": {"single_choice": 684, "essay": 121, ...},
    "difficulty_distribution": {"hard": 394, "medium": 154, "easy": 273},
    "topic_distribution": {"直线运动": 48, ...},
    "year_range": [2021, 2025],
    "provinces": ["山东", "广东", ...]
  },
  "questions": [...],
  "stats": {
    "seed_count": 821,
    "generated_count": 5,
    "type_dist": {"single_choice": 3, ...},
    "difficulty_dist": {"medium": 2, ...}
  }
}
```

## 错题本

### 3 个子命令

#### 1. 标记错题

```bash
# 标记 3 道题为错题
shuatipass wrongbook mark questions.json \
  --ids "01-001,01-002,02-001" \
  --action mark

# 取消标记
shuatipass wrongbook mark questions.json \
  --ids "01-001" \
  --action unmark

# 自定义标签
shuatipass wrongbook mark questions.json \
  --ids "01-001" --tag "难题"
```

#### 2. 导出错题本（JSON）

```bash
shuatipass wrongbook export questions.json \
  -o wrongbook.json \
  --tag "错题"
```

#### 3. 导出错题本（HTML / 打印友好）

```bash
shuatipass wrongbook export questions.json \
  --out-html wrongbook.html \
  --group-by knowledge_point
```

可选 `--group-by`：
- `knowledge_point`（按知识点，默认）
- `topic`（按专题）
- `year`（按年份）
- `difficulty`（按难度）

#### 4. 灵活组合：手动指定题目

```bash
# 不按 tag 过滤，手动指定 ID
shuatipass wrongbook export questions.json \
  --ids "01-001,01-005,02-003" \
  --out-html my-wrongbook.html
```

### 输出 HTML 样式

错题本 HTML 自带：
- 📊 顶部统计（总题数/分组数/题型分布/年份分布）
- 🏷️ 彩色徽章（专题/年份/省份/题型）
- 📝 每题完整题干 + 选项
- ✅ 答案 + 解析（绿色高亮）
- 🖨️ 适合打印（A4 友好）

## Python API

```python
from shuatipass import (
    # Exam Mimic
    analyze_exam_style,
    mimic_exam,
    ExamStyle,
    # 错题本
    load_questions,
    find_by_ids,
    find_by_tag,
    mark_questions,
    build_wrongbook,
    export_wrongbook,
    render_wrongbook_html,
)

# 分析风格
style = analyze_exam_style("questions.json")
print(style.type_distribution)
print(style.estimated_score)

# 生成模拟卷
result = mimic_exam(
    seed_json="questions.json",
    target_count=20,
    output="mock.json",
)

# 错题本
questions = load_questions("questions.json")
wrong = find_by_tag(questions, "错题")
wb = build_wrongbook(wrong, group_by="knowledge_point")
html = render_wrongbook_html(wb, title="我的错题本")
```

## 借鉴自 DEEPTUTOR

| DEEPTUTOR 能力 | shuatipass 对应 |
|----------------|-----------------|
| Authenticate Exam Simulation | `shuatipass exam-mimic` |
| Personal Notebook | `shuatipass wrongbook` |
| Knowledge Reinforcement & Practice Exercise Generator | `shuatipass generate`（D11）|

**shuatipass 的差异化**：
- shuatipass 专注"题库工具链"（解析 → 出题 → 模拟卷 → 错题本）
- DEEPTUTOR 是完整学习平台（多 Agent + 知识图谱 + 长期记忆）
- 上下游：shuatipass 解析的 JSON 可直接喂给 DEEPTUTOR 做长期学习

## 故障排查

### `wrongbook mark` 报"未找到: ['ghost']"

说明 ID 不在题库里。检查：
```bash
shuatipass stats questions.json
# 看所有 ID
```

### `exam-mimic` 报"LLM 返回不是有效 JSON"

LLM 偶尔返回非严格 JSON。可：
1. 调低 temperature（默认 0.7，可降到 0.3）
2. 换更大的模型
3. 重试

## 测试

```bash
python3 -m pytest tests/test_exam_mimic.py -v
```

30 个测试覆盖：
- 风格分析（7）
- prompt 构造（1）
- 响应解析（4）
- 完整端到端（1）
- 题库加载（2）
- ID/tag 查找（3）
- 标记/取消标记（4）
- 错题本构建（3）
- 导出（4）
- HTML 渲染（1）
