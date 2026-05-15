# Context 适配参考

## 核心原则

兴趣雷达不定义 Python ContextProvider 接口。它是 Hermes Skill，不是 Python 库。

上下文获取由 Agent 在运行时通过可用工具完成：

| 工具 | 用途 |
|------|------|
| `hindsight_recall(query, limit)` | 从 Hindsight 记忆系统召回相关记忆 |
| `hindsight_reflect(query)` | 从 Hindsight 获取综合推理结果（兴趣快照、项目状态） |
| `memory` | 从 Hermes 原生记忆搜索 |
| `read_file` / `search_files` | 读取 Obsidian 笔记 |

## 探测顺序

1. 尝试 `hindsight_recall` → 成功则用 Hindsight
2. 尝试 `memory` → 成功则用 Hermes Memory
3. 检查 Obsidian Vault 路径 → 存在则扫描笔记
4. 都没有 → 回退到 SKILL.md 内置种子兴趣

## 示例：Hindsight 可用时的上下文获取

```
# Agent 执行
memories = hindsight_recall(query="Android XR OpenXR spatial computing", limit=5)
snapshot = hindsight_reflect(query="用户当前活跃项目和兴趣快照")

# 从 memories 中提取：活跃项目、历史决策、兴趣信号
# 从 snapshot 中提取：hot/durable 兴趣分类
# 用于相关性评分
```

## 示例：只有 Obsidian 时

```
# Agent 执行
vault = "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/ObsidianVault"
projects = search_files(path=f"{vault}/1-Projects", query="active", file_glob="*.md")
# 解析项目笔记内容，提取项目名、关键词、状态
# 用于相关性评分
```

## 种子兴趣（回退）

当所有上下文系统都不可用时：

- XR / spatial computing: Android XR, OpenXR, Vision Pro, spatial computing, AR, VR, MR
- AI agents: Claude Code, Codex, MCP, agent, tool calling, browser automation
- Personal context / memory: Hindsight, knowledge graph, personal knowledge management
- HomeLab / local inference: Ollama, llama.cpp, Docker, PVE, GPU, CUDA
