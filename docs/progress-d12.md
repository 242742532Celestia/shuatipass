# D12 进度报告：Exam Mimic 完整版 + 错题本

> 完成时间：2026-08-17
> 借鉴自：港大 DEEPTUTOR 项目的"Authenticate Exam Simulation"和"Personal Notebook"

## 交付物

### 1. Exam Mimic 完整版

**文件**：
- `src/shuatipass/exam_mimic.py` (12.4 KB)
- `docs/exam-mimic-wrongbook.md`
- `tests/test_exam_mimic.py` 中 13 个相关测试

**核心能力**：
- ✅ 深度风格分析（题量/题型/难度/专题/分值/时长/省份）
- ✅ 风格特征 prompt 化（喂给 LLM）
- ✅ 完整新卷生成（按风格克隆）
- ✅ 风格分析报告输出

**与之前 `--mock-exam` 区别**：

| 特性 | `--mock-exam`（D11）| `exam-mimic`（D12）|
|------|---------------------|---------------------|
| 风格分析 | 简单抽 5 道种子 | 完整特征化（题量/题型/难度比例）|
| 输出 | 新题（追加到原题库）| 完整新卷 + 风格报告 |
| 适用场景 | 补充少量新题 | 整张新卷克隆 |
| LLM 调用 | 1 次 | 1 次（但 prompt 复杂得多）|

**实测**（用 `data/parsed/q-xk.json` 821 题黑吉辽蒙物理卷做种子）：

```
📊 风格分析报告:
   原卷总题: 821
   估计时长: 2122 分钟
   估计总分: 4380 分
   题型: {'single_choice': 684, 'essay': 121, 'essay_with_options': 16}
   难度: {'hard': 394, 'medium': 154, 'easy': 273}

🎯 目标生成: 5 道
🤖 调用 minimax/MiniMax-Text-01...

✅ 模拟卷生成: 5 题
   题型分布: {'single_choice': 3, 'essay': 1, 'essay_with_options': 1}
   难度分布: {'medium': 2, 'hard': 2, 'easy': 1}
```

### 2. 错题本

**文件**：
- `src/shuatipass/wrongbook.py` (10.5 KB)
- `examples/07_wrongbook.py`
- `tests/test_exam_mimic.py` 中 17 个相关测试

**3 个子命令**：

```bash
# 1. mark：标记/取消错题
shuatipass wrongbook mark questions.json --ids "01-001,01-002" --action mark
shuatipass wrongbook mark questions.json --ids "01-001" --action unmark

# 2. export：导出错题本（JSON + HTML）
shuatipass wrongbook export questions.json \
  -o wrongbook.json \
  --out-html wrongbook.html \
  --tag "错题" \
  --group-by knowledge_point

# 3. 灵活组合：按 ID 列表、tag、知识点/年份/难度 分组
shuatipass wrongbook export questions.json --ids "01-001,01-005" --out-html selected.html
```

**HTML 错题本特性**：
- 📊 顶部统计面板（总题数、分组数、题型/年份分布）
- 🏷️ 彩色徽章（专题紫/年份绿/省份蓝/题型橙）
- 📝 每题完整题干 + 4 选项网格 + 答案解析（绿色高亮）
- 🖨️ A4 打印友好（900px 最大宽度，无图片依赖）

**实测**：

```
🏷️  标记: 1 道题
📒 错题本: 3 题，分 2 组
   HTML: /tmp/wb-out.html
```

## 测试覆盖

| 模块 | 测试数 | 状态 |
|------|--------|------|
| exam-mimic 风格分析 | 7 | ✅ |
| exam-mimic prompt 构造 | 1 | ✅ |
| exam-mimic 响应解析 | 4 | ✅ |
| exam-mimic 端到端 | 1 | ✅ |
| 错题本加载 | 2 | ✅ |
| 错题本查找（by_id / by_tag）| 3 | ✅ |
| 错题本标记（mark / unmark / to_output）| 4 | ✅ |
| 错题本构建（分组 / 统计）| 3 | ✅ |
| 错题本导出（JSON / HTML / by_ids / empty）| 4 | ✅ |
| HTML 渲染 | 1 | ✅ |
| **新增测试** | **30** | **✅** |
| D11 已有（generator）| 17 | ✅ |
| 旧测试（parser / config / etc）| 53 | ✅ |
| **总测试** | **100** | **✅** |

## CLI 现状（9 个子命令）

| 子命令 | 功能 | 阶段 |
|--------|------|------|
| `parse` | PDF → JSON | D1 |
| `stats` | JSON 统计 | D1 |
| `info` | PDF 元信息 | D1 |
| `configs` | 列出配置 | D4 |
| `ocr` | 公式 OCR | D10 |
| `web` | 启动 Web UI | D10 |
| `generate` | AI 出题（基础 + 模拟卷简版）| D11 |
| **`exam-mimic`** | **Exam Mimic 完整版** | **D12** ⭐ |
| **`wrongbook`** | **错题本（mark / export）** | **D12** ⭐ |

## 借鉴 DEEPTUTOR 完成度

| DEEPTUTOR 能力 | shuatipass 对应 | 阶段 |
|----------------|----------------|------|
| Knowledge Reinforcement & Practice Exercise Generator | `generate` | D11 ✅ |
| Authenticate Exam Simulation | `exam-mimic` | D12 ✅ |
| Personal Notebook | `wrongbook` | D12 ✅ |
| Multi-Agent 解题 | 暂不 | - |
| 知识图谱 | 暂不 | - |
| 长期记忆/个性化 | 暂不 | - |

**3 个核心 AI 能力已全部借鉴完成**。

## 路线图（下一步）

shuatipass 已经到了"功能完整"的状态：
- 解析：PDF → JSON
- 出题：AI 生成新题
- 模拟卷：完整克隆风格
- 错题本：标记/导出
- OCR：公式识别
- Web：Gradio UI

**候选下一步**：
1. **PyPI 发布 v0.1.0** —— 收尾，发布给社区
2. **多 PDF 批量解析** —— 一次解析一个文件夹的 PDF
3. **公式 OCR 集成到出题** —— 自动 LaTeX 化公式
4. **题目查重** —— 跨卷查重，AI 评估相似度
5. **Excel 导入/导出** —— 老师常用 Excel 管理题库

## 真实 API 验证

| 测试 | 工具 | 状态 |
|------|------|------|
| 基础出题 | `shuatipass generate` | ✅ |
| 种子题风格 | `shuatipass generate --seed` | ✅ |
| 模拟卷（简版）| `shuatipass generate --mock-exam` | ✅ |
| 模拟卷（完整）| `shuatipass exam-mimic` | ✅ |
| 标记错题 | `shuatipass wrongbook mark` | ✅ |
| 导出 JSON | `shuatipass wrongbook export` | ✅ |
| 导出 HTML | `shuatipass wrongbook export --out-html` | ✅ |

## 文件清单（D12 新增/修改）

```
新增：
  src/shuatipass/exam_mimic.py            (12,419 bytes)
  src/shuatipass/wrongbook.py             (10,541 bytes)
  tests/test_exam_mimic.py                (14,856 bytes)
  examples/07_wrongbook.py                (3,361 bytes)
  docs/exam-mimic-wrongbook.md            (5,114 bytes)
  docs/progress-d12.md                    (this file)

修改：
  src/shuatipass/__init__.py              (新增 9 个 export)
  src/shuatipass/cli.py                   (新增 3 个子命令)
```

## 总结

D11 + D12 完成 shuatipass 的 **3 个 AI 核心能力**（出题、模拟卷、错题本），借鉴自港大 DEEPTUTOR 项目的核心 AI 模块。

shuatipass 现在的定位：
> **中文题库 PDF 解析 + AI 出题工具链** —— 从 PDF 到 AI 错题本，一条龙

**100 tests + 6 skipped** 全部通过，真实 MiniMax API 端到端验证。
