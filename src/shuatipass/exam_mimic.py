"""
shuatipass Exam Mimic —— 完整版"克隆试卷风格"

借鉴自 DEEPTUTOR 的 exam_mimic.py + auth-exam-simulation

设计：
1. 深度分析种子卷（题量/题型/难度/知识点/分值/时间）
2. 把分析结果喂给 LLM
3. LLM 按风格特征生成完整新卷（题量、题型分布、难度分布都跟原卷一致）
4. 输出：卷子 JSON（带答案+解析）

vs 简化版（generate --mock-exam）：
- 简化版：随机抽种子 + 单 prompt
- 完整版：风格特征化 + 多 prompt（按章节/题型分批）
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ._console import enable_console_compat
from .generator import PROVIDERS, call_llm


@dataclass
class ExamStyle:
    """试卷风格特征"""

    # 基础
    total_questions: int = 0
    topic_distribution: dict = field(default_factory=dict)  # {"直线运动": 48, ...}
    # 题型
    type_distribution: dict = field(
        default_factory=dict
    )  # {"single_choice": 684, "essay": 121, ...}
    type_ratio: dict = field(default_factory=dict)  # 各题型占比（百分比）
    # 难度
    difficulty_distribution: dict = field(default_factory=dict)  # {"hard": 200, ...}
    # 年份/省份
    year_range: tuple = (2021, 2025)  # (最早, 最晚)
    provinces: list = field(default_factory=list)  # 高频省份
    # 时长/分值（估算）
    estimated_duration: int = 120  # 分钟
    estimated_score: int = 100


def analyze_exam_style(seed_json: str | Path) -> ExamStyle:
    """
    分析种子卷的风格特征。

    从 questions.json 提取：
    - 题目总数
    - 各专题题目数
    - 各题型数量 + 占比
    - 各难度分布（用 year 反推：2025=hard, 2021=easy, 中间=medium）
    - 年份范围
    - 高频省份
    """
    enable_console_compat()  # Windows GBK 控制台扛不住 emoji
    p = Path(seed_json)
    if not p.exists():
        raise FileNotFoundError(f"seed JSON 不存在: {p}")

    with p.open(encoding="utf-8") as f:
        data = json.load(f)

    style = ExamStyle()

    # 收集所有题
    all_questions = []
    for t in data.get("topics", []):
        topic_title = t.get("title", "未知")
        for q in t.get("questions", []):
            q["_topic_title"] = topic_title
            q["_topic_id"] = t.get("topic_id", "")
            all_questions.append(q)

    style.total_questions = len(all_questions)

    # 专题分布
    topic_counter = Counter()
    for q in all_questions:
        topic_counter[q.get("_topic_title", "未知")] += 1
    style.topic_distribution = dict(topic_counter)

    # 题型分布
    type_counter = Counter()
    for q in all_questions:
        type_counter[q.get("type", "unknown")] += 1
    style.type_distribution = dict(type_counter)
    total = sum(type_counter.values()) or 1
    style.type_ratio = {k: round(v / total * 100, 1) for k, v in type_counter.items()}

    # 难度分布（用年份估算）
    diff_counter = Counter()
    for q in all_questions:
        year = q.get("year")
        if year is None:
            diff_counter["unknown"] += 1
            continue
        # 2021 = easy, 2022 = medium, 2023 = medium, 2024 = hard, 2025 = hard
        # 简化映射
        if year <= 2022:
            diff_counter["easy"] += 1
        elif year <= 2023:
            diff_counter["medium"] += 1
        elif year <= 2024:
            diff_counter["hard"] += 1
        else:
            diff_counter["hard"] += 1
    style.difficulty_distribution = dict(diff_counter)

    # 年份范围
    years = [q.get("year") for q in all_questions if q.get("year")]
    if years:
        style.year_range = (min(years), max(years))

    # 高频省份
    prov_counter = Counter()
    for q in all_questions:
        prov = q.get("province")
        if prov:
            prov_counter[prov] += 1
    style.provinces = [p for p, _ in prov_counter.most_common(10)]

    # 估算时长/分值
    # 简化：单选 1 分×30 秒，解析 5 分×5 分钟
    score = 0
    duration = 0
    for q in all_questions:
        if q.get("type") == "single_choice":
            score += 4
            duration += 1.5
        elif q.get("type") == "multi_choice":
            score += 5
            duration += 2
        elif q.get("type") in ("essay", "essay_with_options"):
            score += 12
            duration += 8
        else:
            score += 4
            duration += 1.5
    style.estimated_score = int(score)
    style.estimated_duration = int(duration)

    return style


def build_mimic_prompt(style: ExamStyle, target_count: int, subject: str = "物理") -> str:
    """构造"风格学习 + 整卷生成"prompt"""
    # 风格特征摘要
    style_summary = f"""## 原卷风格特征（请严格按此风格生成新卷）

- 总题数：{style.total_questions}
- 估计时长：{style.estimated_duration} 分钟
- 估计总分：{style.estimated_score} 分
- 年份范围：{style.year_range[0]} - {style.year_range[1]}

### 题型分布
"""
    for t, c in style.type_distribution.items():
        ratio = style.type_ratio.get(t, 0)
        style_summary += f"- {t}: {c} 题 ({ratio}%)\n"

    style_summary += "\n### 难度分布\n"
    for d, c in style.difficulty_distribution.items():
        style_summary += f"- {d}: {c} 题\n"

    style_summary += "\n### 专题分布\n"
    for topic, c in style.topic_distribution.items():
        style_summary += f"- {topic}: {c} 题\n"

    style_summary += "\n### 高频省份（卷风风格）\n"
    style_summary += ", ".join(style.provinces[:5]) if style.provinces else "无"

    # 计算目标题数对应的分布
    target_type = {}
    for t, ratio in style.type_ratio.items():
        target_type[t] = max(1, int(target_count * ratio / 100))
    # 补齐
    diff = target_count - sum(target_type.values())
    if diff > 0:
        # 加到最大占比的题型
        max_t = max(target_type, key=target_type.get)
        target_type[max_t] += diff

    target_summary = f"\n## 目标生成参数\n- 总题数：{target_count}\n- 题型分配：{target_type}\n"

    prompt = f"""你是一位经验丰富的{subject}出题老师。现在给你一份"参考卷"风格特征，请你按照这个风格生成一份新卷。

{style_summary}

{target_summary}

## 要求

1. **题量**：生成 {target_count} 道题
2. **题型分布**：严格按照目标分配
3. **难度分布**：按参考卷比例（{style.difficulty_distribution}）
4. **风格**：每道题都要"看起来像"原卷的真实题目（考点、命题方式、难度）
5. **省份标注**：可以混合原卷出现过的省份风格（{', '.join(style.provinces[:3])}）
6. **每题必含**：题干预设干扰项 + 标准答案 + 详细解析 + 知识点

## 输出格式（严格 JSON）

{{
  "questions": [
    {{
      "type": "single_choice",
      "stem": "题干",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "answer": "A",
      "explanation": "解析（2-3 句）",
      "knowledge_point": "具体知识点",
      "difficulty": "medium",
      "province_style": "山东卷风格"
    }}
  ]
}}

注意：
- 题目要有区分度，干扰项有迷惑性
- 解析必须给出解题关键步骤
- 严格按 JSON 输出，不要 markdown 包装
"""
    return prompt


def parse_exam_mimic_response(resp: str) -> list[dict]:
    """解析整卷生成结果"""
    resp = resp.strip()

    # 去 markdown 包装
    if resp.startswith("```"):
        lines = resp.split("\n")
        in_block = False
        content_lines = []
        for line in lines:
            if line.strip().startswith("```"):
                in_block = not in_block
                continue
            if in_block:
                content_lines.append(line)
        resp = "\n".join(content_lines)

    if "{" in resp:
        start = resp.find("{")
        end = resp.rfind("}") + 1
        if start >= 0 and end > start:
            resp = resp[start:end]

    try:
        data = json.loads(resp)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM 返回不是有效 JSON: {e}\n原始: {resp[:500]}") from e

    questions = data.get("questions", [])
    if not questions:
        raise RuntimeError(f"LLM 返回的 JSON 里没有 questions 字段: {data}")

    return questions


def mimic_exam(
    seed_json: str | Path,
    target_count: int = None,
    provider: str = "minimax",
    model: str = None,
    subject: str = "物理",
    output: str | Path = None,
) -> dict:
    """
    完整版 Exam Mimic

    Args:
        seed_json: 种子卷 JSON 路径
        target_count: 目标题数（None = 跟原卷一致）
        provider: LLM provider
        model: 模型名
        subject: 学科
        output: 输出 JSON 路径（None = 不保存）

    Returns:
        {
            "style": ExamStyle,
            "questions": [GeneratedQuestion, ...],
            "stats": {...}
        }
    """
    enable_console_compat()  # Windows GBK 控制台扛不住 emoji
    if model is None:
        model = PROVIDERS.get(provider, {}).get("default_model", "gpt-4o-mini")

    # 1. 分析风格
    print("📊 分析原卷风格...")
    style = analyze_exam_style(seed_json)
    print(f"   总题数: {style.total_questions}")
    print(f"   题型: {style.type_distribution}")
    print(f"   难度: {style.difficulty_distribution}")
    print(f"   专题数: {len(style.topic_distribution)}")
    print(f"   估计: {style.estimated_duration} 分钟 / {style.estimated_score} 分")

    # 2. 目标题数
    if target_count is None:
        target_count = style.total_questions
    print(f"\n🎯 目标生成: {target_count} 道")

    # 3. 构造 prompt
    prompt = build_mimic_prompt(style, target_count, subject)

    # 4. 调 LLM
    print(f"\n🤖 调用 {provider}/{model}...")
    resp = call_llm(provider, model, prompt, temperature=0.7)

    # 5. 解析
    questions_data = parse_exam_response(resp)

    # 6. 包装
    from .generator import GeneratedQuestion

    questions = []
    for i, q in enumerate(questions_data, 1):
        gq = GeneratedQuestion(
            id=f"MOCK-{i:03d}",
            number=i,
            type=q.get("type", "single_choice"),
            stem=q.get("stem", "").strip(),
            options=q.get("options", {}),
            answer=q.get("answer", "").strip(),
            explanation=q.get("explanation", "").strip(),
            knowledge_point=q.get("knowledge_point", ""),
            difficulty=q.get("difficulty", "medium"),
            province=q.get("province_style", "AI 生成"),
            seed_ids=[],
        )
        questions.append(gq)

    # 7. 统计
    stats = {
        "seed_count": style.total_questions,
        "generated_count": len(questions),
        "type_dist": dict(Counter(q.type for q in questions)),
        "difficulty_dist": dict(Counter(q.difficulty for q in questions)),
    }

    result = {
        "source": "shuatipass exam-mimic",
        "style": asdict(style),
        "questions": [asdict(q) for q in questions],
        "stats": stats,
    }

    # 8. 保存
    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n✅ 模拟卷生成: {len(questions)} 题")
        print(f"   输出: {out_path}")
        print(f"\n   题型分布: {stats['type_dist']}")
        print(f"   难度分布: {stats['difficulty_dist']}")

    return result


# 兼容别名
def parse_exam_response(resp: str) -> list[dict]:
    return parse_exam_mimic_response(resp)
