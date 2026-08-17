"""
shuatipass AI 出题 —— 基于种子题库或知识点生成新题

设计：
1. 学习种子题的风格/格式/难度
2. 生成结构化新题（与解析结果同 schema）
3. 支持按知识点/难度/题型过滤
4. 支持 MiniMax / OpenAI / Anthropic

用法：
    # 基于已有题生成（学习风格）
    shuatipass generate --seed questions.json --count 10

    # 按知识点生成
    shuatipass generate --topic "圆周运动" --difficulty hard --count 5

    # 按参考题生成（exam_mimic 风格）
    shuatipass generate --reference "01-001" --seed questions.json --count 3

    # 生成模拟卷
    shuatipass generate --mock-exam questions.json --count 20 -o mock.json

输出 JSON 字段（与解析结果同结构）：
    {
        "id": "GEN-001",
        "number": 1,
        "year": 2026,
        "province": "AI 生成",
        "type": "single_choice",
        "stem": "...",
        "options": {"A": "...", ...},
        "images": [],
        "ai_generated": true,
        "seed_ids": ["01-005", "01-012"],  # 参考的种子题
        "knowledge_point": "圆周运动",
        "difficulty": "hard",
        "source_page": 0,
    }
"""
from __future__ import annotations
import json
import os
import time
import random
from pathlib import Path
from typing import Optional
from dataclasses import asdict, dataclass, field


# 难度映射
DIFFICULTY_LEVELS = ["easy", "medium", "hard", "expert"]
DIFFICULTY_ZH = {
    "easy": "简单",
    "medium": "中等",
    "hard": "困难",
    "expert": "竞赛",
}


# Provider 配置（复用 examples/05_ai_answers.py 的逻辑）
PROVIDERS = {
    "minimax": {
        "base_url": "https://api.minimax.chat/v1",
        "default_model": "MiniMax-Text-01",
        "env_key": "MINIMAX_API_KEY",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
    },
    "anthropic": {
        "base_url": None,
        "default_model": "claude-3-5-sonnet-20241022",
        "env_key": "ANTHROPIC_API_KEY",
    },
}


@dataclass
class GeneratedQuestion:
    id: str
    number: int
    year: int = 2026
    province: str = "AI 生成"
    type: str = "single_choice"
    stem: str = ""
    options: dict = field(default_factory=dict)
    images: list = field(default_factory=list)
    answer: str = ""
    explanation: str = ""
    source_page: int = 0
    # AI 特有字段
    ai_generated: bool = True
    seed_ids: list = field(default_factory=list)
    knowledge_point: str = ""
    difficulty: str = "medium"
    formula_latex: str = ""
    formula_confidence: float = 0.0
    formula_ocr_engine: str = ""


# ======== LLM 调用 ========

def call_llm(provider: str, model: str, prompt: str, temperature: float = 0.7) -> str:
    """调用 LLM（统一接口）"""
    if provider == "anthropic":
        try:
            import anthropic
        except ImportError:
            raise RuntimeError("需要安装 anthropic: pip install anthropic")
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model=model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text

    # OpenAI 协议
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("需要安装 openai: pip install openai")

    cfg = PROVIDERS[provider]
    api_key = os.environ.get(cfg["env_key"])
    if not api_key:
        raise RuntimeError(f"需要环境变量 {cfg['env_key']}")

    client = OpenAI(api_key=api_key, base_url=cfg["base_url"])
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return resp.choices[0].message.content


# ======== Prompt 构造 ========

def build_prompt(
    topic: str = "",
    difficulty: str = "medium",
    count: int = 5,
    seed_questions: list = None,
    question_type: str = "single_choice",
    subject: str = "物理",
) -> str:
    """构造出题 prompt"""

    difficulty_zh = DIFFICULTY_ZH.get(difficulty, difficulty)

    prompt = f"""你是一个经验丰富的{subject}出题老师。请根据要求生成 {count} 道{subject}题。

## 要求
- 知识点范围：{topic or '根据种子题自动判断'}
- 难度：{difficulty_zh}
- 题型：{question_type}（{question_type == 'single_choice' and '单选题，4 个选项 A B C D' or '简答题' }）
"""

    if seed_questions:
        prompt += f"\n## 参考题目（共 {len(seed_questions)} 道）\n"
        prompt += "请学习这些题目的风格、难度、考点，并生成风格相似的新题：\n\n"
        for i, sq in enumerate(seed_questions[:5], 1):  # 最多给 5 道
            prompt += f"### 参考题 {i}\n"
            prompt += f"题干：{sq.get('stem', '')[:200]}\n"
            if sq.get("options"):
                for k, v in list(sq.get("options", {}).items())[:4]:
                    prompt += f"  {k}. {v[:80]}\n"
            if sq.get("year"):
                prompt += f"（{sq.get('year')}·{sq.get('province', '')}）\n"
            prompt += "\n"

    prompt += f"""
## 输出格式（严格 JSON，不要 markdown 包装）

{{
  "questions": [
    {{
      "stem": "题干内容",
      "options": {{
        "A": "选项 A",
        "B": "选项 B",
        "C": "选项 C",
        "D": "选项 D"
      }},
      "answer": "正确答案字母",
      "explanation": "详细解析（2-3 句话）",
      "knowledge_point": "具体知识点（如'匀速圆周运动'）",
      "difficulty": "{difficulty}"
    }}
  ]
}}

注意：
1. 题目要有区分度，不能太显然
2. 干扰项要有迷惑性（不是明显错误）
3. 题干表述要规范
4. 解析要给出解题关键步骤
5. 严格按 JSON 输出，不要加 markdown 标记
"""
    return prompt


def parse_llm_response(resp: str) -> list[dict]:
    """从 LLM 响应解析题目列表"""
    resp = resp.strip()

    # 去掉 markdown 包装
    if resp.startswith("```"):
        lines = resp.split("\n")
        # 找到第一个 ``` 后到最后一个 ``` 之间的内容
        in_block = False
        content_lines = []
        for line in lines:
            if line.strip().startswith("```"):
                in_block = not in_block
                continue
            if in_block:
                content_lines.append(line)
        resp = "\n".join(content_lines)

    # 尝试找 JSON 块
    if "{" in resp:
        start = resp.find("{")
        end = resp.rfind("}") + 1
        if start >= 0 and end > start:
            resp = resp[start:end]

    try:
        data = json.loads(resp)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM 返回不是有效 JSON: {e}\n原始: {resp[:500]}")

    questions = data.get("questions", [])
    if not questions:
        raise RuntimeError(f"LLM 返回的 JSON 里没有 questions 字段: {data}")

    return questions


# ======== 主出题函数 ========

def generate_questions(
    provider: str = "minimax",
    model: str = None,
    topic: str = "",
    difficulty: str = "medium",
    count: int = 5,
    seed_questions: list = None,
    question_type: str = "single_choice",
    subject: str = "物理",
    temperature: float = 0.7,
) -> list[GeneratedQuestion]:
    """
    生成题目

    Args:
        provider: LLM provider
        model: 模型名（None = 用 provider 默认）
        topic: 知识点（如"圆周运动"）
        difficulty: easy/medium/hard/expert
        count: 题目数量
        seed_questions: 种子题列表（用于学习风格）
        question_type: single_choice / multi_choice / essay
        subject: 学科
        temperature: 创造性（0=保守，1=发散）

    Returns:
        GeneratedQuestion 列表
    """
    if model is None:
        model = PROVIDERS.get(provider, {}).get("default_model", "gpt-4o-mini")

    if seed_questions and not topic:
        # 自动从种子题提取主题
        topic = auto_infer_topic(seed_questions)

    prompt = build_prompt(
        topic=topic,
        difficulty=difficulty,
        count=count,
        seed_questions=seed_questions,
        question_type=question_type,
        subject=subject,
    )

    print(f"🤖 调用 {provider}/{model} 生成 {count} 道题...")
    resp = call_llm(provider, model, prompt, temperature=temperature)

    questions_data = parse_llm_response(resp)

    # 转为 GeneratedQuestion
    result = []
    for i, q in enumerate(questions_data, 1):
        gq = GeneratedQuestion(
            id=f"GEN-{i:03d}",
            number=i,
            type=question_type,
            stem=q.get("stem", "").strip(),
            options=q.get("options", {}),
            answer=q.get("answer", "").strip(),
            explanation=q.get("explanation", "").strip(),
            knowledge_point=q.get("knowledge_point", topic),
            difficulty=q.get("difficulty", difficulty),
            seed_ids=[sq.get("id", "") for sq in (seed_questions or [])[:5]],
        )
        result.append(gq)

    return result


def auto_infer_topic(questions: list) -> str:
    """从种子题推断主题（用 LLM）"""
    if not questions:
        return ""

    # 简化版：直接用第一个种子题的 knowledge_point 字段
    for q in questions:
        if q.get("topic_title"):
            return q["topic_title"]
        if q.get("knowledge_point"):
            return q["knowledge_point"]

    # 否则用 prompt 让 LLM 推断
    # （这里简化：直接返回空，让 LLM 在 prompt 中自动判断）
    return ""


# ======== Mock 试卷生成 ========

def generate_mock_exam(
    seed_json: str | Path,
    count: int = 20,
    topic_ids: list = None,
    difficulty: str = "medium",
    provider: str = "minimax",
    model: str = None,
) -> dict:
    """
    基于已有题库生成模拟卷

    从 seed_json 选 count 道题（按 topic_ids 过滤），调 LLM 生成同结构新题。
    """
    src = Path(seed_json)
    with src.open() as f:
        data = json.load(f)

    # 收集所有题目（可选 topic_ids 过滤）
    pool = []
    for t in data.get("topics", []):
        if topic_ids and t.get("topic_id") not in topic_ids:
            continue
        for q in t.get("questions", []):
            pool.append({
                "id": q.get("id"),
                "topic_id": t.get("topic_id"),
                "topic_title": t.get("title"),
                "stem": q.get("stem"),
                "options": q.get("options"),
                "year": q.get("year"),
                "province": q.get("province"),
                "type": q.get("type"),
            })

    if not pool:
        raise ValueError(f"没找到符合的题目（topic_ids={topic_ids}）")

    print(f"📚 候选题库: {len(pool)} 道题")

    # 随机抽 count 道做种子（多样性）
    sample_size = min(count, len(pool))
    seed = random.sample(pool, sample_size)

    # 分批生成（避免单次 prompt 太大）
    batch_size = 5
    all_generated = []
    for i in range(0, count, batch_size):
        batch_count = min(batch_size, count - i)
        # 选最近的几道做种子
        batch_seeds = seed[max(0, i-batch_size):i+batch_size]
        try:
            batch_questions = generate_questions(
                provider=provider,
                model=model,
                topic=batch_seeds[0].get("topic_title", "") if batch_seeds else "",
                difficulty=difficulty,
                count=batch_count,
                seed_questions=batch_seeds,
            )
            all_generated.extend(batch_questions)
        except Exception as e:
            print(f"  ⚠️  第 {i+1}-{i+batch_count} 题生成失败: {e}")
        time.sleep(0.5)

    return {
        "source": "shuatipass generate",
        "seed_count": len(seed),
        "generated_count": len(all_generated),
        "questions": [asdict(q) for q in all_generated],
    }


# ======== 保存 ========

def save_to_json(
    questions: list[GeneratedQuestion],
    output_path: str | Path,
    append_to: str | Path = None,
):
    """
    保存生成的题到 JSON

    如果 append_to 指定，会把题目追加到原 JSON 的对应结构里
    """
    out_path = Path(output_path)

    if append_to:
        # 追加模式：读原 JSON，把生成题加到合适位置
        src = Path(append_to)
        with src.open() as f:
            data = json.load(f)

        # 加到第一个专题（或新建"AI 生成"专题）
        if data.get("topics"):
            gen_topic = {
                "topic_id": "GEN",
                "title": "AI 生成题",
                "page_start": 0,
                "page_end": 0,
                "questions": [asdict(q) for q in questions],
            }
            data["topics"].append(gen_topic)
            # 更新统计
            from dataclasses import asdict as _asdict
            existing = data.get("stats", {})
            existing["total_topics"] = len(data["topics"])
            existing["total_questions"] = sum(
                len(t.get("questions", [])) for t in data["topics"]
            )
            data["stats"] = existing

        with out_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        # 独立模式
        data = {
            "source": "shuatipass generate",
            "generated_count": len(questions),
            "questions": [asdict(q) for q in questions],
        }
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def make_ocr_from_env():  # 占位避免 import 错
    return None
