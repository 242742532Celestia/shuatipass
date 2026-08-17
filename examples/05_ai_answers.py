"""
Example 05: 用 LLM 给题目加答案和解析

支持:
  - MiniMax (env: MINIMAX_API_KEY)
  - OpenAI (env: OPENAI_API_KEY)
  - Anthropic (env: ANTHROPIC_API_KEY)
  - 任意 OpenAI 协议兼容服务

用法:
    export MINIMAX_API_KEY="your_key"
    python examples/05_ai_answers.py questions.json questions-with-answers.json
    # 默认 MiniMax 模型

    # 或者:
    python examples/05_ai_answers.py questions.json out.json --provider openai --model gpt-4
"""
import sys
import json
import os
import time
from pathlib import Path


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
        # Anthropic 协议不同，特殊处理
        "base_url": None,
        "default_model": "claude-3-5-sonnet-20241022",
        "env_key": "ANTHROPIC_API_KEY",
    },
}


def ask_ai(provider: str, model: str, prompt: str) -> str:
    """调用 LLM"""
    if provider == "anthropic":
        # 用 anthropic SDK
        try:
            import anthropic
        except ImportError:
            raise RuntimeError("需要安装 anthropic: pip install anthropic")
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model=model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text

    # OpenAI 协议（minimax/openai/其他）
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
        temperature=0.3,
    )
    return resp.choices[0].message.content


def build_prompt(q: dict) -> str:
    """构造 prompt"""
    p = f"请回答这道物理题，给出答案字母和详细解析。\n\n"
    p += f"【题干】{q['stem']}\n\n"
    for k, v in q.get("options", {}).items():
        p += f"{k}. {v}\n"
    p += f"\n请用 JSON 格式返回：\n"
    p += '{"answer": "字母", "explanation": "详细解析"}'
    return p


def main():
    if len(sys.argv) < 3:
        print("用法: python 05_ai_answers.py <questions.json> <out.json> [--provider minimax] [--model ...] [--limit N]")
        sys.exit(1)

    src = Path(sys.argv[1])
    out = Path(sys.argv[2])
    provider = "minimax"
    model = None
    limit = 0  # 0 = 全部

    # 简单参数解析
    args = sys.argv[3:]
    i = 0
    while i < len(args):
        if args[i] == "--provider":
            provider = args[i+1]
            i += 2
        elif args[i] == "--model":
            model = args[i+1]
            i += 2
        elif args[i] == "--limit":
            limit = int(args[i+1])
            i += 2
        else:
            i += 1

    if model is None:
        model = PROVIDERS[provider]["default_model"]

    print(f"🤖 引擎: {provider} / {model}")
    print(f"   输入: {src}")
    print(f"   输出: {out}")
    if limit > 0:
        print(f"   限制: 前 {limit} 道题")

    with src.open() as f:
        data = json.load(f)

    # 选题
    to_answer = []
    for t in data["topics"]:
        for q in t["questions"]:
            if q.get("type") == "single_choice" and not q.get("answer"):
                to_answer.append(q)
                if limit > 0 and len(to_answer) >= limit:
                    break
        if limit > 0 and len(to_answer) >= limit:
            break

    print(f"   待答题: {len(to_answer)}")
    print()

    # 调 LLM
    success = 0
    failed = 0
    for i, q in enumerate(to_answer, 1):
        try:
            prompt = build_prompt(q)
            resp = ask_ai(provider, model, prompt)
            # 解析 JSON 响应（可能含 markdown ```json 包装）
            resp = resp.strip()
            if resp.startswith("```"):
                resp = resp.split("```")[1]
                if resp.startswith("json"):
                    resp = resp[4:]
            result = json.loads(resp)
            q["answer"] = result.get("answer", "?")
            q["explanation"] = result.get("explanation", "")
            success += 1
            print(f"  [{i}/{len(to_answer)}] {q['id']}: {q['answer']}")
        except Exception as e:
            failed += 1
            q["answer_error"] = str(e)
            print(f"  [{i}/{len(to_answer)}] {q['id']}: ❌ {e}")

        # Rate limit
        time.sleep(0.5)

    # 保存
    with out.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print()
    print(f"✅ 完成：成功 {success}, 失败 {failed}")
    print(f"   输出: {out}")


if __name__ == "__main__":
    main()
