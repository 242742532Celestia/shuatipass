# D5 进度报告：完整文档

**日期**：2026-08-16
**状态**：✅ 100% 完成

## 交付物

| 文档 | 行数 | 目标读者 |
|------|------|----------|
| [tutorial.md](tutorial.md) | 238 | 第一次用 shuatipass 的新用户 |
| [api.md](api.md) | 245 | 库 + CLI 的完整 API 参考 |
| [config.md](config.md) | 242 | 写自定义 YAML 规则的人 |
| [examples.md](examples.md) | 323 | 想看真实用例的开发者 |
| [CHANGELOG.md](../CHANGELOG.md) | 50 | 关注版本变化的用户 |
| **合计** | **1098** | |

## 文档设计原则

1. **5 分钟上手** —— tutorial 极简，3 条命令跑通
2. **可抄可改** —— examples 全是可运行代码片段
3. **从浅到深** —— tutorial → examples → api → config
4. **故障排查** —— tutorial 末尾有常见问题解决
5. **可调试** —— config.md 给了"如何测试单个正则"的方法

## 关键章节速览

### tutorial.md
- 安装
- 3 步上手（CP 命令 + 解析 + stats）
- 用法 1/2/3（Markdown / Excel / RAG）
- 进阶：自定义配置 / 故障排查

### api.md
- CLI 4 个子命令
- Python 库 4 个数据类
- 10 个 YAML 字段
- 正则规则详解
- 异常 / 版本兼容

### config.md
- 最小配置（2 字段）vs 完整配置（10 字段）
- 写配置的 4 步流程
- 3 个真实案例（组卷网/纯文字/英文）
- 调试技巧

### examples.md
- 12 个真实场景：
  1. Markdown 试卷
  2. 按年份/省份筛选
  3. Anki 卡片
  4. RAG 文档块
  5. 按题型分组
  6. 找最难题
  7. 批量处理
  8. 自定义配置示例
  9. Jupyter 探索
  10. 跨页题合并
  11. 质量检查
  12. LLM 加答案（用 MINIMAX_API_KEY）

## README 更新

更新了：
- 项目状态表（D5 标为完成）
- 文档索引（4 篇新文档链接）
- 路线图（保留 v0.1 详细时间表）

## 路线图（更新）

| 阶段 | 状态 | 目标 |
|------|------|------|
| D1 解析核心 | ✅ | PyMuPDF 解析 821 题 |
| D2 解析优化 | ✅ | bbox + 解析题 + 内嵌选项 |
| D3 CLI + 库 | ✅ | `shuatipass` 命令 + Python 库 |
| D4 配置化 | ✅ | YAML + 2 个内置预设 |
| **D5 文档** | ✅ | 4 篇核心文档 + CHANGELOG + README 更新 |
| **D6 Docker** | ⏳ | 一键 Docker 镜像 |
| **D7 CI/CD** | ⏳ | GitHub Actions + 覆盖率 |
| **D8 PyPI** | ⏳ | `pip install shuatipass` |
| **D9 多格式** | ⏳ | 组卷网 + Word 导出 |
| **D10 公式 OCR** | ⏳ | 物理公式 LaTeX 化 |
