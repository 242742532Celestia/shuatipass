"""
shuatipass CLI 入口

用法:
  shuatipass parse <pdf> -o <json> [--images <dir>]
  shuatipass stats <json>
  shuatipass info <pdf>
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional


def cmd_parse(args):
    """解析 PDF → JSON"""
    from .parser import XueKeWangParser
    from .config import ParseConfig, get_builtin, list_builtins
    from .detect import detect_config, detect_with_details

    if not Path(args.pdf).exists():
        print(f"❌ PDF 不存在: {args.pdf}", file=sys.stderr)
        return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    images = Path(args.images) if args.images else out.parent / "images"
    images.mkdir(parents=True, exist_ok=True)

    # 加载配置
    if args.config:
        config = ParseConfig.load(args.config)
        config_name = config.name
        print(f"📄 解析: {args.pdf}")
        print(f"   配置: {args.config} ({config_name})")
    elif args.preset:
        try:
            config = get_builtin(args.preset)
            config_name = config.name
            print(f"📄 解析: {args.pdf}")
            print(f"   预设: {args.preset} ({config_name})")
        except FileNotFoundError:
            print(f"❌ 内置预设不存在: {args.preset}", file=sys.stderr)
            print(f"   可用预设: {list_builtins()}", file=sys.stderr)
            return 1
    elif args.auto:
        # 自动检测
        try:
            detected = detect_config(args.pdf)
        except ImportError:
            print("❌ 自动检测需要 pymupdf", file=sys.stderr)
            return 1
        try:
            config = get_builtin(detected)
        except FileNotFoundError:
            config = None
        config_name = detected
        print(f"📄 解析: {args.pdf}")
        print(f"   自动检测: {config_name}")
    else:
        config = None
        config_name = "xuekewang (默认)"
        print(f"📄 解析: {args.pdf}")
        print(f"   配置: 默认 (xuekewang)")

    print(f"   输出: {args.out}")
    print(f"   图片: {images}")

    parser = XueKeWangParser(args.pdf, images, config=config, config_name=config_name.split(" ")[0])
    result = parser.parse()

    from dataclasses import asdict
    data = asdict(result)
    with out.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    stats = result.stats
    print()
    print(f"✅ 解析完成")
    print(f"   专题: {stats['total_topics']} | 题目: {stats['total_questions']} | 跳过: {stats['skipped_pages']} 页")
    print(f"   题型: {stats['by_type']}")

    # 提示
    if stats["total_questions"] == 0 and not args.config:
        print()
        print("⚠️  没解析出题目。建议：")
        print("   1. 试试 --auto 自动检测")
        print("   2. 或指定 --preset generic / zujuan / textbook")
        print("   3. 或用 --config 写自己的 YAML")
    return 0


def cmd_stats(args):
    """查看 JSON 统计信息"""
    p = Path(args.json)
    if not p.exists():
        print(f"❌ JSON 不存在: {p}", file=sys.stderr)
        return 1
    with p.open() as f:
        data = json.load(f)

    print(f"📊 {p.name}")
    print(f"   来源: {data['source_file']}")
    print(f"   总页: {data['total_pages']}")
    print(f"   专题: {len(data['topics'])}")
    total = sum(len(t["questions"]) for t in data["topics"])
    print(f"   题目: {total}")

    # 题型统计
    by_type = {}
    for t in data["topics"]:
        for q in t["questions"]:
            by_type[q["type"]] = by_type.get(q["type"], 0) + 1
    print(f"   题型: {by_type}")

    # 年份统计
    by_year = {}
    for t in data["topics"]:
        for q in t["questions"]:
            y = q.get("year")
            if y:
                by_year[y] = by_year.get(y, 0) + 1
    if by_year:
        print(f"   年份: {sorted(by_year.items())}")

    print()
    print("   专题分布:")
    for t in data["topics"]:
        n = len(t["questions"])
        print(f"     专题 {t['topic_id']} {t['title']:<22} p{t['page_start']:>3}-{t['page_end']:<3}  {n} 题")
    return 0


def cmd_info(args):
    """查看 PDF 基础信息（不解析）"""
    try:
        import pymupdf
    except ImportError:
        print("❌ 需要安装 pymupdf: pip install PyMuPDF", file=sys.stderr)
        return 1

    p = Path(args.pdf)
    if not p.exists():
        print(f"❌ PDF 不存在: {p}", file=sys.stderr)
        return 1

    doc = pymupdf.open(str(p))
    print(f"📄 {p.name}")
    print(f"   路径: {p.absolute()}")
    print(f"   大小: {p.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"   页数: {len(doc)}")
    meta = doc.metadata
    if meta:
        for k, v in meta.items():
            if v:
                print(f"   {k}: {v}")
    doc.close()
    return 0


def cmd_configs(args):
    """列出可用配置"""
    from .config import list_builtins
    names = list_builtins()
    if not names:
        print("❌ 没有内置配置")
        return 1
    print(f"📋 内置配置 ({len(names)} 个):")
    for n in names:
        print(f"   - {n}")
    return 0


def cmd_ocr(args):
    """对已解析的 JSON 跑公式 OCR"""
    from .ocr import MathpixOCR, Pix2TexOCR, ocr_questions, OCRError, make_ocr_from_env

    if not Path(args.json).exists():
        print(f"❌ JSON 不存在: {args.json}", file=sys.stderr)
        return 1

    if not Path(args.images).exists():
        print(f"❌ 图片目录不存在: {args.images}", file=sys.stderr)
        return 1

    # 选 OCR 引擎
    try:
        if args.engine == "mathpix":
            ocr = MathpixOCR(
                app_id=args.app_id or os.environ.get("MATHPIX_APP_ID", ""),
                app_key=args.app_key or os.environ.get("MATHPIX_APP_KEY", ""),
            )
        elif args.engine == "pix2tex":
            try:
                ocr = Pix2TexOCR()
            except OCRError as e:
                print(f"❌ {e}", file=sys.stderr)
                return 1
        else:
            ocr = make_ocr_from_env()
            if ocr is None:
                print("❌ 未配置 OCR 引擎", file=sys.stderr)
                print("   1. 用 --engine mathpix + --app-id/--app-key", file=sys.stderr)
                print("   2. 或设置环境变量 MATHPIX_APP_ID / MATHPIX_APP_KEY", file=sys.stderr)
                print("   3. 或用 --engine pix2tex (需 pip install pix2tex[dev])", file=sys.stderr)
                return 1
    except OCRError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    print(f"🔍 OCR 引擎: {ocr.name}")
    print(f"   输入: {args.json}")
    print(f"   图片: {args.images}")
    print(f"   输出: {args.out}")
    print(f"   Rate limit: {args.rate_limit}s/次")

    stats = ocr_questions(
        ocr=ocr,
        questions_json=args.json,
        images_dir=args.images,
        output_json=args.out,
        rate_limit=args.rate_limit,
    )

    print()
    print(f"✅ OCR 完成")
    print(f"   总题目: {stats['total_questions']}")
    print(f"   总图片: {stats['total_images']}")
    print(f"   OCR 调用: {stats['ocr_called']}")
    print(f"   成功: {stats['ocr_success']}")
    print(f"   失败: {stats['ocr_failed']}")
    print(f"   跳过（无图）: {stats['ocr_skipped']}")
    return 0


def cmd_web(args):
    """启动 Web UI"""
    from .web import launch_web, is_available

    if not is_available():
        print("❌ 需要安装 gradio: pip install gradio", file=sys.stderr)
        print("   或: pip install shuatipass[web]", file=sys.stderr)
        return 1

    print(f"🌐 启动 Web UI")
    print(f"   地址: http://{args.host}:{args.port}")
    if args.share:
        print(f"   公网分享: 启动后会生成临时链接（72h 有效）")
    print(f"   按 Ctrl+C 停止")
    print()

    try:
        launch_web(
            host=args.host,
            port=args.port,
            share=args.share,
        )
    except KeyboardInterrupt:
        print("\n👋 Web UI 已停止")
        return 0
    except Exception as e:
        print(f"❌ 启动失败: {e}", file=sys.stderr)
        return 1

    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="shuatipass",
        description="中文题库 PDF 解析工具 - 把 PDF 一键转结构化 JSON",
    )
    sub = parser.add_subparsers(dest="cmd", help="子命令")

    # parse
    p_parse = sub.add_parser("parse", help="解析 PDF 为 JSON")
    p_parse.add_argument("pdf", help="输入 PDF 路径")
    p_parse.add_argument("-o", "--out", required=True, help="输出 JSON 路径")
    p_parse.add_argument("--images", help="图片输出目录（默认 <out_dir>/images）")
    p_parse.add_argument("--auto", action="store_true", help="自动检测 PDF 来源选择配置")
    p_parse.add_argument("--preset", help="使用内置预设（xuekewang / generic / zujuan / textbook）")
    p_parse.add_argument("--config", help="使用自定义 YAML 配置文件")
    p_parse.set_defaults(func=cmd_parse)

    # stats
    p_stats = sub.add_parser("stats", help="查看 JSON 统计")
    p_stats.add_argument("json", help="JSON 路径")
    p_stats.set_defaults(func=cmd_stats)

    # info
    p_info = sub.add_parser("info", help="查看 PDF 基础信息")
    p_info.add_argument("pdf", help="PDF 路径")
    p_info.set_defaults(func=cmd_info)

    # configs
    p_configs = sub.add_parser("configs", help="列出可用配置")
    p_configs.set_defaults(func=cmd_configs)

    # ocr
    p_ocr = sub.add_parser("ocr", help="对已解析的 JSON 跑公式 OCR")
    p_ocr.add_argument("json", help="输入 JSON 路径")
    p_ocr.add_argument("-o", "--out", default=None, help="输出 JSON 路径（默认 <input>.ocr.json）")
    p_ocr.add_argument("--images", required=True, help="图片目录")
    p_ocr.add_argument("--engine", choices=["mathpix", "pix2tex"], default="mathpix", help="OCR 引擎")
    p_ocr.add_argument("--app-id", help="Mathpix app_id（或环境变量 MATHPIX_APP_ID）")
    p_ocr.add_argument("--app-key", help="Mathpix app_key（或环境变量 MATHPIX_APP_KEY）")
    p_ocr.add_argument("--rate-limit", type=float, default=1.0, help="API 调用间隔（秒）")
    p_ocr.set_defaults(func=cmd_ocr)

    # web
    p_web = sub.add_parser("web", help="启动 Web UI（Gradio）")
    p_web.add_argument("--host", default="127.0.0.1", help="监听地址（默认 127.0.0.1）")
    p_web.add_argument("--port", type=int, default=7860, help="端口（默认 7860）")
    p_web.add_argument("--share", action="store_true", help="生成公网可访问链接（72h 有效）")
    p_web.set_defaults(func=cmd_web)

    # generate
    p_gen = sub.add_parser("generate", help="用 AI 生成新题（基于种子题/知识点）")
    p_gen.add_argument("-o", "--out", required=True, help="输出 JSON 路径")
    p_gen.add_argument("--seed", help="种子题 JSON（提供则学习其风格）")
    p_gen.add_argument("--topic", help="知识点（如'圆周运动'）")
    p_gen.add_argument("--difficulty", choices=["easy", "medium", "hard", "expert"],
                       default="medium", help="难度（默认 medium）")
    p_gen.add_argument("--count", type=int, default=5, help="生成题数（默认 5）")
    p_gen.add_argument("--type", choices=["single_choice", "multi_choice", "essay"],
                       default="single_choice", help="题型（默认 single_choice）")
    p_gen.add_argument("--subject", default="物理", help="学科（默认 物理）")
    p_gen.add_argument("--provider", choices=["minimax", "openai", "anthropic"],
                       default="minimax", help="LLM provider（默认 minimax）")
    p_gen.add_argument("--model", help="模型名（默认用 provider 默认）")
    p_gen.add_argument("--temperature", type=float, default=0.7, help="创造性 0-1")
    p_gen.add_argument("--mock-exam", action="store_true", help="生成模拟卷（从 seed 抽题学习）")
    p_gen.add_argument("--topic-ids", help="限定专题（逗号分隔，配合 --mock-exam）")
    p_gen.add_argument("--append", action="store_true", help="追加到 seed JSON（不覆盖）")
    p_gen.set_defaults(func=cmd_generate)

    # exam-mimic（完整版）
    p_mimic = sub.add_parser("exam-mimic", help="Exam Mimic —— 完整克隆试卷风格")
    p_mimic.add_argument("--seed", required=True, help="种子卷 JSON（必填）")
    p_mimic.add_argument("-o", "--out", required=True, help="输出 JSON 路径")
    p_mimic.add_argument("--count", type=int, help="目标题数（默认跟原卷一致）")
    p_mimic.add_argument("--subject", default="物理", help="学科（默认 物理）")
    p_mimic.add_argument("--provider", choices=["minimax", "openai", "anthropic"],
                         default="minimax", help="LLM provider")
    p_mimic.add_argument("--model", help="模型名")
    p_mimic.set_defaults(func=cmd_exam_mimic)

    # wrongbook（错题本）
    p_wb = sub.add_parser("wrongbook", help="错题本：标记/导出/打印")
    p_wb_sub = p_wb.add_subparsers(dest="wb_cmd", help="子命令")

    # mark
    p_wb_mark = p_wb_sub.add_parser("mark", help="标记/取消标记错题")
    p_wb_mark.add_argument("json", help="题库 JSON 路径")
    p_wb_mark.add_argument("--ids", required=True, help="题目 ID 列表（逗号分隔）")
    p_wb_mark.add_argument("--action", choices=["mark", "unmark"], default="mark", help="操作")
    p_wb_mark.add_argument("--tag", default="错题", help="标签名（默认 '错题'）")
    p_wb_mark.add_argument("-o", "--out", help="输出 JSON 路径（默认覆盖原文件）")
    p_wb_mark.set_defaults(func=cmd_wrongbook_mark)

    # export
    p_wb_export = p_wb_sub.add_parser("export", help="导出错题本")
    p_wb_export.add_argument("json", help="题库 JSON 路径")
    p_wb_export.add_argument("-o", "--out-json", help="输出 JSON 路径")
    p_wb_export.add_argument("--out-html", help="输出 HTML 路径")
    p_wb_export.add_argument("--ids", help="题目 ID 列表（逗号分隔）")
    p_wb_export.add_argument("--tag", default="错题", help="按 tag 过滤（默认 '错题'）")
    p_wb_export.add_argument("--group-by", default="knowledge_point",
                             choices=["knowledge_point", "topic", "year", "difficulty"],
                             help="分组方式")
    p_wb_export.add_argument("--title", default="错题本", help="HTML 标题")
    p_wb_export.set_defaults(func=cmd_wrongbook_export)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return 1

    # ocr 子命令：自动设置默认输出
    if args.cmd == "ocr" and args.out is None:
        args.out = str(Path(args.json).with_suffix(".ocr.json"))

    return args.func(args)


def cmd_generate(args):
    """AI 出题"""
    from .generator import (
        generate_questions,
        generate_mock_exam,
        save_to_json,
        PROVIDERS,
    )

    provider = args.provider
    model = args.model or PROVIDERS[provider]["default_model"]

    print(f"🤖 AI 出题")
    print(f"   Provider: {provider}/{model}")
    print(f"   难度: {args.difficulty}")
    print(f"   数量: {args.count}")
    print(f"   题型: {args.type}")

    # 检查 API key
    env_key = PROVIDERS[provider]["env_key"]
    if not os.environ.get(env_key):
        print(f"❌ 需要环境变量 {env_key}", file=sys.stderr)
        print(f"   1. 注册: {_provider_url(provider)}", file=sys.stderr)
        print(f"   2. export {env_key}='your_key'", file=sys.stderr)
        return 1

    # 模式 1: Mock Exam
    if args.mock_exam:
        if not args.seed:
            print("❌ --mock-exam 必须配合 --seed", file=sys.stderr)
            return 1
        topic_ids = args.topic_ids.split(",") if args.topic_ids else None
        try:
            data = generate_mock_exam(
                seed_json=args.seed,
                count=args.count,
                topic_ids=topic_ids,
                difficulty=args.difficulty,
                provider=provider,
                model=model,
            )
            out_path = Path(args.out)
            out_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"\n✅ 模拟卷生成完成: {len(data['questions'])} 题")
            print(f"   输出: {out_path}")
        except Exception as e:
            print(f"❌ 生成失败: {e}", file=sys.stderr)
            return 1
        return 0

    # 模式 2: 基础出题
    seed_questions = None
    if args.seed:
        seed_path = Path(args.seed)
        if not seed_path.exists():
            print(f"❌ seed JSON 不存在: {args.seed}", file=sys.stderr)
            return 1
        with seed_path.open() as f:
            seed_data = json.load(f)
        seed_questions = []
        for t in seed_data.get("topics", []):
            for q in t.get("questions", []):
                seed_questions.append({
                    "id": q.get("id"),
                    "topic_title": t.get("title"),
                    "stem": q.get("stem"),
                    "options": q.get("options"),
                    "year": q.get("year"),
                    "province": q.get("province"),
                })
        if not seed_questions:
            print(f"⚠️  seed JSON 里没找到题目")
        else:
            print(f"   种子题: {len(seed_questions)} 道")

    if not args.topic and not seed_questions:
        print("❌ 需要 --topic 或 --seed（至少一个）", file=sys.stderr)
        return 1

    # 生成
    try:
        questions = generate_questions(
            provider=provider,
            model=model,
            topic=args.topic or "",
            difficulty=args.difficulty,
            count=args.count,
            seed_questions=seed_questions,
            question_type=args.type,
            subject=args.subject,
            temperature=args.temperature,
        )

        # 保存
        if args.append and args.seed:
            save_to_json(questions, args.out, append_to=args.seed)
            print(f"\n✅ 追加 {len(questions)} 题到 {args.out}")
        else:
            save_to_json(questions, args.out)
            print(f"\n✅ 生成 {len(questions)} 题")

        # 展示前 2 道
        print()
        for q in questions[:2]:
            print(f"--- 题 {q.number} ({q.knowledge_point}) ---")
            print(f"题干: {q.stem[:80]}...")
            for k, v in list(q.options.items())[:4]:
                print(f"  {k}. {v[:60]}")
            if q.explanation:
                print(f"解析: {q.explanation[:80]}...")
            print()

        return 0
    except Exception as e:
        print(f"❌ 生成失败: {e}", file=sys.stderr)
        return 1


def _provider_url(provider: str) -> str:
    """获取 provider 注册地址（友好提示）"""
    return {
        "minimax": "https://api.minimax.chat/",
        "openai": "https://platform.openai.com/",
        "anthropic": "https://console.anthropic.com/",
    }.get(provider, "?")


def cmd_exam_mimic(args):
    """完整版 Exam Mimic"""
    from .exam_mimic import mimic_exam
    from .generator import PROVIDERS

    print("🎯 Exam Mimic —— 完整克隆试卷风格")
    print(f"   Seed: {args.seed}")
    print(f"   输出: {args.out}")
    print(f"   目标题数: {args.count or '跟原卷一致'}")
    print(f"   Provider: {args.provider}")

    provider = args.provider
    env_key = PROVIDERS[provider]["env_key"]
    if not os.environ.get(env_key):
        print(f"❌ 需要环境变量 {env_key}", file=sys.stderr)
        return 1

    try:
        result = mimic_exam(
            seed_json=args.seed,
            target_count=args.count,
            provider=provider,
            model=args.model,
            subject=args.subject,
            output=args.out,
        )

        # 打印风格报告
        style = result["style"]
        print(f"\n📊 风格分析报告:")
        print(f"   原卷总题: {style['total_questions']}")
        print(f"   估计时长: {style['estimated_duration']} 分钟")
        print(f"   估计总分: {style['estimated_score']} 分")
        print(f"   题型: {style['type_distribution']}")
        print(f"   难度: {style['difficulty_distribution']}")
        return 0
    except Exception as e:
        print(f"❌ 生成失败: {e}", file=sys.stderr)
        return 1


def cmd_wrongbook_mark(args):
    """标记/取消标记错题"""
    from .wrongbook import mark_questions

    ids = [i.strip() for i in args.ids.split(",") if i.strip()]
    if not ids:
        print("❌ --ids 不能为空")
        return 1

    try:
        result = mark_questions(
            json_path=args.json,
            question_ids=ids,
            action=args.action,
            tag=args.tag,
            output=args.out,
        )
        verb = "标记" if args.action == "mark" else "取消标记"
        n = result['marked'] if args.action == 'mark' else result['unmarked']
        print(f"🏷️  {verb}: {n} 道题")
        if result["not_found"]:
            print(f"⚠️  未找到: {result['not_found']}")
        print(f"📄 输出: {result['output']}")
        return 0
    except Exception as e:
        print(f"❌ 操作失败: {e}", file=sys.stderr)
        return 1


def cmd_wrongbook_export(args):
    """导出错题本"""
    from .wrongbook import export_wrongbook

    ids = None
    if args.ids:
        ids = [i.strip() for i in args.ids.split(",") if i.strip()]

    try:
        result = export_wrongbook(
            source_json=args.json,
            output_json=args.out_json,
            output_html=args.out_html,
            ids=ids,
            tag=args.tag,
            group_by=args.group_by,
            title=args.title,
        )
        return 0
    except Exception as e:
        print(f"❌ 导出失败: {e}", file=sys.stderr)
        return 1
