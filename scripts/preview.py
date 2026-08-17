"""简单 HTML 预览 —— 把解析结果的前 N 题渲染成 HTML"""
import json
import base64
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
JSON_PATH = WORKSPACE / "data/parsed/questions.json"
IMG_DIR = WORKSPACE / "data/images"
OUT_PATH = WORKSPACE / "data/output/preview.html"

with JSON_PATH.open() as f:
    data = json.load(f)

def img_to_data_url(fname: str) -> str:
    p = IMG_DIR / fname
    if not p.exists():
        return ""
    ext = p.suffix.lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    b64 = base64.b64encode(p.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"

html = ['<!DOCTYPE html><html><head><meta charset="utf-8"><title>刷题通 - 解析预览</title>']
html.append('''<style>
body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;max-width:900px;margin:24px auto;padding:0 20px;color:#222;background:#fafafa}
h1{border-bottom:2px solid #333;padding-bottom:8px}
h2{background:#e3f2fd;padding:10px 16px;border-left:4px solid #1976d2;margin-top:32px}
.q{background:white;padding:16px 20px;margin:12px 0;border:1px solid #ddd;border-radius:6px;box-shadow:0 1px 2px rgba(0,0,0,.05)}
.q .meta{color:#666;font-size:13px;margin-bottom:8px}
.q .meta .badge{display:inline-block;background:#1976d2;color:white;font-size:12px;padding:2px 8px;border-radius:10px;margin-right:6px}
.q .meta .topic{background:#9c27b0}
.q .meta .year{background:#43a047}
.q .meta .type{background:#fb8c00}
.q .stem{line-height:1.7;margin:8px 0}
.q .options{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:8px}
.q .opt{background:#f5f5f5;padding:6px 10px;border-radius:4px;font-size:14px}
.q .imgs{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.q .imgs img{max-width:280px;max-height:200px;border:1px solid #eee;background:white;padding:4px}
.summary{background:#fff3e0;padding:12px 20px;border-radius:6px;margin:16px 0}
</style></head><body>''')

html.append('<h1>📚 刷题通 shuatipass · 解析预览</h1>')
html.append('<div class="summary">')
total_q = sum(len(t["questions"]) for t in data["topics"])
total_img = sum(len(q["images"]) for t in data["topics"] for q in t["questions"])
html.append(f'<b>{data["source_file"]}</b> · {data["total_pages"]} 页 · {len(data["topics"])} 专题 · {total_q} 题 · {total_img} 张图')
html.append('</div>')

# 选 3 个专题的前 2 题预览
show_topics = data["topics"][:3]
for t in show_topics:
    html.append(f'<h2>专题 {t["topic_id"]} · {t["title"]}（共 {len(t["questions"])} 题）</h2>')
    for q in t["questions"][:2]:
        html.append('<div class="q">')
        html.append('<div class="meta">')
        html.append(f'<span class="badge topic">专题 {t["topic_id"]}</span>')
        html.append(f'<span class="badge year">{q.get("year","-")}</span>')
        html.append(f'<span class="badge">{q.get("province","-")}</span>')
        html.append(f'<span class="badge type">{q.get("type","-")}</span>')
        html.append(f'<span style="color:#999">题号 {q["number"]} · p{q["source_page"]}</span>')
        html.append('</div>')
        html.append(f'<div class="stem">{q["stem"]}</div>')
        if q["options"]:
            html.append('<div class="options">')
            for k, v in q["options"].items():
                html.append(f'<div class="opt"><b>{k}.</b> {v}</div>')
            html.append('</div>')
        if q["images"]:
            html.append('<div class="imgs">')
            for fname in q["images"]:
                url = img_to_data_url(fname)
                if url:
                    html.append(f'<img src="{url}" title="{fname}"/>')
            html.append('</div>')
        html.append('</div>')

html.append('</body></html>')

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUT_PATH.write_text("\n".join(html), encoding="utf-8")
print(f"✅ 预览 HTML: {OUT_PATH}")
print(f"   大小: {OUT_PATH.stat().st_size / 1024:.1f} KB")
