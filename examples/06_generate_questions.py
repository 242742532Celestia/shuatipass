"""
Example 06: 用 AI 生成新题

用法:
    export MINIMAX_API_KEY="your_key"

    # 基础出题
    python examples/06_generate_questions.py \
      --topic "圆周运动" --count 5

    # 种子题风格
    python examples/06_generate_questions.py \
      --seed data/parsed/questions.json \
      --topic "圆周运动" --count 3

    # 模拟卷
    python examples/06_generate_questions.py \
      --seed data/parsed/questions.json \
      --mock-exam --topic-ids "01" --count 20
"""
import sys
import json
import os
from pathlib import Path

# 加 shuatipass 到路径
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from shuatipass.generator import (
    generate_questions,
    generate_mock_exam,
    save_to_json,
    PROVIDERS,
)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    # 简单参数解析
    args = sys.argv[1:]
    config = {
        "topic": None,
        "seed": None,
        "count": 5,
        "difficulty": "medium",
        "type": "single_choice",
        "subject": "物理",
        "provider": "minimax",
        "model": None,
        "mock_exam": False,
        "topic_ids": None,
        "output": "generated.json",
    }
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--topic":
            config["topic"] = args[i+1]; i += 2
        elif a == "--seed":
            config["seed"] = args[i+1]; i += 2
        elif a == "--count":
            config["count"] = int(args[i+1]); i += 2
        elif a == "--difficulty":
            config["difficulty"] = args[i+1]; i += 2
        elif a == "--type":
            config["type"] = args[i+1]; i += 2
        elif a == "--subject":
            config["subject"] = args[i+1]; i += 2
        elif a == "--provider":
            config["provider"] = args[i+1]; i += 2
        elif a == "--model":
            config["model"] = args[i+1]; i += 2
        elif a == "--mock-exam":
            config["mock_exam"] = True; i += 1
        elif a == "--topic-ids":
            config["topic_ids"] = args[i+1].split(","); i += 2
        elif a == "-o":
            config["output"] = args[i+1]; i += 2
        else:
            i += 1

    # 模拟卷模式
    if config["mock_exam"]:
        if not config["seed"]:
            print("❌ --mock-exam 需要 --seed")
            sys.exit(1)
        data = generate_mock_exam(
            seed_json=config["seed"],
            count=config["count"],
            topic_ids=config["topic_ids"],
            difficulty=config["difficulty"],
            provider=config["provider"],
            model=config["model"],
        )
        Path(config["output"]).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"✅ 模拟卷: {data['generated_count']} 题 → {config['output']}")
        return

    # 基础模式
    seed_questions = None
    if config["seed"]:
        with open(config["seed"]) as f:
            seed_data = json.load(f)
        seed_questions = []
        for t in seed_data.get("topics", []):
            for q in t.get("questions", []):
                seed_questions.append({
                    "id": q.get("id"),
                    "topic_title": t.get("title"),
                    "stem": q.get("stem"),
                    "options": q.get("options"),
                })

    questions = generate_questions(
        provider=config["provider"],
        model=config["model"],
        topic=config["topic"] or "",
        difficulty=config["difficulty"],
        count=config["count"],
        seed_questions=seed_questions,
        question_type=config["type"],
        subject=config["subject"],
    )
    save_to_json(questions, config["output"])
    print(f"✅ 生成 {len(questions)} 题 → {config['output']}")


if __name__ == "__main__":
    main()
