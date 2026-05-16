# 兴趣雷达 / Interest Radar

**给内容，还判断。** 兴趣雷达是一个通用相关性判断引擎，不采集、不推送、不存储，只做一件事：告诉你一段外部内容和你有多相关、为什么、该不该看。

## 特性

- **平台无关** — 不绑定任何 Agent 平台，可在 Hermes、Claude Code、Codex、Cursor、ChatGPT 等任何 Agent 上运行
- **零代码依赖** — 纯 SKILL.md 定义的工作流，不依赖 Python 脚本或外部运行时
- **自适应上下文召回** — 运行时自动探测可用的记忆/搜索工具，不预设任何特定工具
- **反馈闭环** — 用户对判断结果的反馈（confirm/dismiss）自动影响后续判断，越用越准

## 三个 MVP 能力

| 能力 | 触发方式 | 说明 |
|------|---------|------|
| MVP 1：转发即用 | 用户发链接 + 询问意图 | 自动触发 judge，返回相关性判断 |
| MVP 2：batch_judge | 其他推送 Skill 调用 | 批量过滤，只推送高相关内容 |
| MVP 3：反馈闭环 | 用户回复 confirm/dismiss | 自动调整后续评分 |

## 安装

将 `SKILL.md` 和 `references/` 复制到你的 Agent skills 目录：

```bash
# Hermes
cp -r interest-radar ~/.hermes/skills/research/interest-radar

# Claude Code — 在 CLAUDE.md 中引用
# Codex/Cursor — 在 .codex/rules/ 或 .cursorrules 中引用
```

## 使用

转发任何链接或内容，说"帮我看看这个相不相关"，Agent 就会用兴趣雷达帮你判断。

## 文档

- `SKILL.md` — 完整工作流定义
- `references/batch-interface.md` — batch_judge 接口参考
- `references/feedback-loop.md` — 反馈闭环参考
- `references/output-format.md` — 输出格式参考
- `references/snapshot-cache.md` — 快照缓存方案

## 仓库

https://github.com/Igloo302/interest-radar
