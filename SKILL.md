---
name: interest-radar
description: "相关性判断引擎（兴趣雷达/Interest Radar/Personal Radar）：接收外部内容，利用用户的个人上下文判断内容与用户的相关程度。触发场景：(1) 用户转发/粘贴链接/消息并询问相关性（如\"你看看这条\"、\"这个跟我有关吗\"、\"解读一下\"、\"这条重要吗\"、\"分析一下\"、\"值得看吗\"、\"跟我有关系吗\"、\"影响我的项目吗\"）；(2) 用户要求分析某条内容与项目的关联；(3) 用户提到\"兴趣雷达\"、\"personal radar\"、\"相关性判断\"；(4) 其他 Skill 调用 batch_judge 增强推送质量。"
---

# 兴趣雷达 / Interest Radar

## 一句话

**给内容，还判断。** 兴趣雷达不采集、不推送、不存储，只做一件事：告诉你一段外部内容和你有多相关、为什么、该不该看。

## 产品形态

兴趣雷达是一个 **Hermes Skill**。它通过本 SKILL.md 指导 Agent 的行为。核心判断逻辑由 Agent 的推理能力 + 上下文工具完成，不需要外部 Python 运行时。

---

## MVP 1：转发即用

### 触发条件

当用户的消息满足以下任一条件时，**自动执行 judge 流程**：

1. 消息包含 URL + 询问意图（"你看看"、"解读一下"、"这个怎么样"、"分析一下"）
2. 消息包含 URL + 相关性询问（"跟我有关吗"、"重要吗"、"值得关注吗"）
3. 消息包含 URL + 项目关联询问（"影响我的项目吗"、"跟 XR 有关吗"）
4. 用户直接把链接贴过来，没有明确问题但上下文暗示想了解

**不需要用户显式说"用兴趣雷达"。** 只要内容 + 意图匹配，Agent 自动触发。

### Judge 执行流程

收到触发后，Agent 按以下步骤执行。**不要跳过步骤。**

#### Step 1：获取内容

优先级 1：如果消息包含 URL
  → 先尝试 web_extract([url])
  → 如果 web_extract 失败（订阅限制/网站不支持）→ fallback 到 browser_navigate(url) + browser_snapshot
  → 提取：标题、摘要/正文前800字、来源域名

优先级 2：如果消息只有文字描述（无 URL）
  → 直接使用用户提供的文字作为内容

优先级 3：如果消息包含 URL + 用户补充的描述
  → 获取页面内容 + 合并用户描述

⚠️ **web_extract 经常因 Nous 订阅限制而失败。** 此时必须 fallback 到 browser，不要因为获取失败就跳过判断。

#### Step 2：实体抽取

从获取的内容中识别以下实体类型：

| 实体类型 | 示例 | 用途 |
|---------|------|------|
| 技术词 | OpenXR, scene understanding, MCP, GGUF | 兴趣匹配 |
| 产品/项目名 | Android XR, Vision Pro, Ollama, Hermes | 项目关联 |
| 公司/组织 | Google, Meta, NousResearch, Khronos | 来源可信度 |
| 事件类型 | release, breaking change, SDK update, paper | 变化幅度评分 |

#### Step 3：上下文系统探测与召回

**这是核心步骤。不要跳过。**

##### 3a. 主召回：Hindsight

始终先调用 hindsight_recall(query=entities中的关键词, limit=5) 作为基础上下文。

- 如果返回有效结果 → 记录，继续 3b
- 如果报错/不可用 → 记录，继续 3b

##### 3b. 补充召回：Obsidian 活跃项目

**无论 Hindsight 是否成功，都执行此步骤。**

检查路径 ~/Documents/ObsidianVault/ 是否存在。
如果存在 → 搜索 1-Projects/ 下的活跃项目笔记（关键词：项目名、产品名、技术栈）。

目的：Hindsight 记忆可能缺少项目级别的上下文（如 PRD 细节、技术决策），Obsidian 笔记可以补充。

##### 3c. 补充召回：Hermes Memory（按需）

如果 Hindsight + Obsidian 的召回结果仍然不足（< 3 条相关上下文），
尝试调用 memory 工具搜索相关记忆作为补充。

##### 3d. 回退到种子兴趣

如果以上所有源都不可用或返回空结果，使用以下种子兴趣作为最小上下文：

- XR / spatial computing: Android XR, OpenXR, Vision Pro, spatial computing, AR, VR, MR
- AI agents: Claude Code, Codex, MCP, agent, tool calling, browser automation
- Personal context / memory: Hindsight, knowledge graph, personal knowledge management
- HomeLab / local inference: Ollama, llama.cpp, Docker, PVE, GPU, CUDA

告知用户："⚠️ 未检测到个人上下文系统，使用最小种子兴趣判断。配置 Hindsight 或 Obsidian 可获得更准确结果。"

##### 3e. Top 档位强制多源召回

**如果初步评分达到 top 档位（≥ 80 分），必须执行额外召回：**

1. 用不同的关键词组合再做一次 hindsight_recall（扩大查询范围）
2. 尝试 hindsight_reflect 对召回结果做深度综合（慢思考）— **如果失败则跳过，不阻塞流程**
3. 搜索 Obsidian 中相关的项目笔记和技术笔记

目的：高相关度内容的判断质量要求更高，不能只靠单一召回源。
⚠️ hindsight_reflect 可能因预算/权限限制失败，此时用步骤 1 + 3 的结果继续，不要等待或重试。

#### Step 4：相关性评分

基于 Step 2 的实体 + Step 3 的上下文，按以下维度打分：

| 维度 | 权重 | 评分标准 |
|------|------|---------|
| 项目影响 | 35% | 是否直接影响 active project？高=正在做的项目；中=相关但非核心；低=无直接关联 |
| 兴趣匹配 | 20% | 是否匹配用户 hot/durable 兴趣？高=核心兴趣；中=边缘兴趣；低=不匹配 |
| 变化幅度 | 15% | release/breaking change=高；SDK/API update=中；观点/讨论=低 |
| 可行动性 | 15% | 是否能触发具体行动（更新PRD、测试、学习）？ |
| 来源可信度 | 10% | 官方发布=高；一手报道=中；二手转载=低 |
| 时效性 | 5% | 24h内=高；一周内=中；更早=低 |

综合评分 = 加权求和，映射到 0-100

分桶规则：
- 80-100 → top（强烈建议阅读）
- 60-79 → watch（值得关注）
- 30-59 → silent（有关联但不需要立即行动）
- 0-29 → ignore（不相关）

#### Step 5：生成 why_it_matters

基于评分维度，用 1-2 句话解释为什么这条内容与用户相关。

要求：
- 必须关联到具体的项目/兴趣/决策
- 不要泛泛而谈（避免"因为你对 XR 感兴趣"这种废话）
- 要指出具体的影响点（如"新增的 scene understanding API 可能影响你 PRD 中空间控制面板的技术假设"）

#### Step 6：输出结果

微信端输出格式（注意微信不支持 markdown 表格，用列表格式）：

📡 兴趣雷达

🔗 [内容标题]
来源：[来源域名]

📊 相关度：[score]/100（[bucket中文]）
🎯 关联：[项目名/兴趣名]

💡 为什么相关：
[why_it_matters]

📋 建议行动：[read/watch/save/ignore]
   具体建议：[如"更新 PRD 技术风险部分"]

📎 判断依据：
• [依据1：来自Hindsight/Memory/Obsidian的具体内容]
• [依据2]

置信度：High/Medium/Low

---

## MVP 2：已有推送 Skill 的增强器（暂不实现）

见 MVP 2 文档。当前聚焦 MVP 1。

---

## 边界

- ❌ 不做内容采集（不维护 sources、不 RSS scraping）
- ❌ 不负责推送（不发送微信/邮件、不维护 cronjob）
- ❌ 不存储事件历史
- ❌ 不管理订阅列表
- ✅ 只做判断：给内容 → 返回相关性

---

## 常见情况处理

### 内容获取失败
如果 web_extract 失败（页面需要登录、内容过短等）：
"⚠️ 无法自动获取页面内容。请粘贴文章标题和摘要，我来帮你判断。"

### 内容过短/信息不足
如果获取到的内容少于 100 字：
"⚠️ 获取到的内容较少，判断可能不够准确。" [继续基于已有信息判断，但标注置信度为 Low]

### 多个链接
如果用户一次发了多个链接：逐条判断，分别输出结果。最后给一个综合排序。

### 用户追问
如果用户问"为什么这么说"或"详细解释"：展开 evidence 部分，详细说明判断依据。

---

## 工具可靠性说明（必读）

以下工具在实际使用中**不可靠**，必须有 fallback：

| 工具 | 问题 | Fallback |
|------|------|---------|
| `web_extract` | 需要 Nous 订阅，经常返回 SUBSCRIPTION_REQUIRED | `browser_navigate` + `browser_snapshot` |
| `hindsight_reflect` | 预算/权限限制，经常失败 | 跳过，仅用 hindsight_recall + Obsidian |
| `memory` (Hermes) | 返回结果可能不完整 | 作为补充，不依赖 |

**核心原则：**
- 内容获取：web_extract 失败 → 立即 fallback 到 browser，不要放弃
- 上下文召回：hindsight_recall 是主力，Obsidian 是补充，hindsight_reflect 是锦上添花（失败就跳过）
- 不要因为工具失败就降低判断质量，用已有信息继续执行

---

## 项目文档

项目文档位于 Obsidian 1-Projects/兴趣雷达/兴趣雷达.md。每次架构变更后同步更新。

---

*最后更新：2026-05-15 — 工具可靠性说明，hindsight_reflect 非阻塞*