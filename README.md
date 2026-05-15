# Personal Radar / 兴趣雷达

一个 Hermes Agent Skill：接收外部内容，利用用户的个人上下文判断内容与用户的相关程度。

**给内容，还判断。** 不采集、不推送、不存储，只做一件事：告诉你一段外部内容和你有多相关、为什么、该不该看。

## 安装

将 `SKILL.md` 和 `references/` 目录复制到你的 Hermes skills 目录：

```bash
cp -r personal-radar ~/.hermes/skills/research/
```

## 使用方式

在聊天中转发/粘贴一条内容：

```
你看看这条 https://example.com/some-article
```

Agent 会自动触发兴趣雷达，返回相关性判断结果。

## 功能

- **MVP 1：转发即用** — 聊天中粘贴链接，自动判断相关性
- **MVP 2：推送增强器** — 其他 Skill 调用 `batch_judge` 增强推送质量（开发中）

## 依赖

- Hermes Agent
- Hindsight（可选，用于个性化上下文召回）
- Obsidian（可选，用于项目笔记补充）

## 许可证

MIT
