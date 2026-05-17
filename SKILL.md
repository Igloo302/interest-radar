---
name: interest-radar
description: "通用相关性判断引擎（兴趣雷达/Interest Radar/Personal Radar）：接收外部内容，利用用户的个人上下文判断内容与用户的相关程度。平台无关，可在各种 Agent 平台上运行。触发场景：(1) 用户转发/粘贴链接/消息并询问相关性；(2) 用户要求分析某条内容与项目的关联；(3) 用户提到\"兴趣雷达\"、\"personal radar\"、\"相关性判断\"；(4) 其他推送 Skill 调用 batch_judge 增强推送质量。"
---

# 兴趣雷达 / Interest Radar

## 一句话

**给内容，还判断。** 兴趣雷达不采集、不推送、不存储，只做一件事：告诉你一段外部内容和你有多相关、为什么、该不该看。

---

## 🚀 首次使用 — Onboarding

**这是 SKILL.md 内置的 onboarding。** 当用户首次触发兴趣雷达时（或 Agent 检测到快照文件不存在时），Agent 必须先执行以下流程：

### Step 1：欢迎 + 展示用法

向用户展示以下内容：

---

**📡 兴趣雷达已就绪！**

你装了这个 skill，你的 Agent 就从「什么都推」变成了「只推值得看的」。

装了这个 skill，有 **三种用法**：

**1️⃣ 聊天中随手用（最直接）**

看到一篇文章、一条消息、一个链接，直接转发给 Agent：

> 「帮我看看这条跟我相关吗」
> 「这条内容值得看吗」
> 「分析一下这个」

Agent 自动调兴趣雷达，返回评分 + 为什么相关 + 建议动作（必看/可看/忽略）。

**2️⃣ 注入到已有推送里（最实用）**

如果你已经有定时推送（比如 AI 周刊、XR 动态、GitHub 趋势），一句话就能加上雷达过滤：

> 「把兴趣雷达加到 AI 周刊的推送里」

之后每次推送完，自动附上一份雷达扫描报告——从几十条信息里捞出 top 档位的内容，告诉你哪些值得看、为什么。

**3️⃣ 批量扫描（主动排查）**

> 「帮我扫描一下最近有什么值得关注的」
> 「雷达扫一下」

Agent 会从你最近的推送/消息里批量跑 `batch_judge`，按分数排序给你一份精选清单。

---

### Step 2：生成初始快照

Agent 自动生成初始兴趣快照（写入 `~/.hermes/cache/interest-snapshot.json`），以便后续判断有上下文可用。

生成方式：按以下优先级探测可用的上下文工具（详见后文「自适应上下文召回」章节）：
1. 快照缓存文件（首次不存在，跳过）
2. 记忆系统召回（如 hindsight_recall、neuDrive search_memory）
3. 项目笔记扫描（如 Obsidian Vault）
4. 回退到种子兴趣（内置默认兴趣列表）

**fallback 路径：**
- 有记忆/搜索工具 → 实时召回生成快照
- 无记忆/搜索工具但有文件系统 → 用种子兴趣生成初始快照，标记 `source: seed`
- 无文件系统（如 ChatGPT）→ 跳过快照生成，后续每次判断都走实时上下文探测
- 全部不可用 → 直接展示用法指南，跳过快照生成，告知用户「后续使用时我会逐步了解你的兴趣」

### Step 2.5：用户确认

生成快照后，向用户展示快照摘要（兴趣列表 + 项目列表），并询问：

> 「以上是我对你兴趣和项目的初步了解，准确吗？你可以补充或修改。」

等待用户确认后再继续。如果用户说"不对"或"修改"，根据反馈调整快照内容，然后重新展示确认。

### Step 3：标记 onboarding 完成

将 `onboarding_complete: true` 写入配置文件（或快照文件中），确保下次不再重复展示。

---

## 架构

### 三层架构

兴趣雷达采用三层架构，每层职责明确，上层依赖下层接口，不跨层调用：

```
┌──────────────────────────────────────────────────────────┐
│                    编排层 (Orchestration)                  │
│                                                          │
│  judge() — 单条判断流程编排                              │
│  batch_judge() — 批量判断流程编排                        │
│  inject_into_cron() — 注入已有推送                        │
│  remove_from_cron() — 从推送移除                          │
│  onboarding() — 首次使用流程                             │
│                                                          │
│  职责：流程编排、用户交互、错误处理、状态管理             │
│  依赖：推理层接口                                         │
├──────────────────────────────────────────────────────────┤
│                    推理层 (Reasoning)                      │
│                                                          │
│  extract_entities(content) → entities[]                   │
│  score_relevance(entities, context) → score + reasoning   │
│  generate_why_it_matters(score, entities, context) → text │
│  format_output(result, platform) → formatted_text          │
│                                                          │
│  职责：评分推理、内容理解、输出格式化                     │
│  依赖：数据层接口                                         │
├──────────────────────────────────────────────────────────┤
│                    数据层 (Context)                        │
│                                                          │
│  load_snapshot() → context                               │
│  refresh_context(current_context) → new_context           │
│  save_snapshot(context)                                   │
│  store_feedback(feedback)                                 │
│                                                          │
│  职责：上下文管理、快照缓存、反馈持久化                   │
│  实现：运行时自适应探测可用工具                            │
└──────────────────────────────────────────────────────────┘
```

### 调用关系

- **编排层**调用**推理层**的接口，编排层**不直接访问**数据层
- **推理层**调用**数据层**获取上下文，推理层**不直接与用户交互**
- **数据层**不感知上层业务逻辑，只提供 get/save/refresh 能力

### 流程状态机

每个 judge/batch_judge 请求经历以下状态：

```
IDLE → CONTENT_FETCHING ──→ ENTITY_EXTRACTING ──→ SCORING ──→ OUTPUT → DONE
        CONTEXT_LOADING ──→                          ↑
                                                    │
                                  (两路在 SCORING 前汇合)

状态说明：
- IDLE：空闲，可接受新请求
- CONTENT_FETCHING：正在获取内容（路径 A）
- CONTEXT_LOADING：正在加载上下文（路径 B）
- ENTITY_EXTRACTING：内容已获取，正在抽取实体
- SCORING：两路汇合，正在评分
- OUTPUT：正在格式化输出
- DONE：完成

错误状态：
- FAILED_CONTENT：内容获取失败，可重试
- FAILED_CONTEXT：上下文加载失败，降级使用种子兴趣
- FAILED_SCORING：评分异常，返回 ERR_INTERNAL
```

### 并行执行规则

Step 1（获取内容）与 Step 3（上下文召回）并行执行：

| 场景 | 路径 A（内容） | 路径 B（上下文） | 结果 |
|------|---------------|-----------------|------|
| 正常 | 成功 | 成功 | 正常评分 |
| 内容失败 | 失败 | 成功 | 返回 ERR_CONTENT_FETCH |
| 上下文失败 | 成功 | 全部不可用 | 使用种子兴趣，置信度 Low |
| 双双失败 | 失败 | 全部不可用 | 返回 ERR_CONTENT_FETCH（优先报内容错误） |

**超时策略：**
- 内容获取：单个 URL 最长等待 30 秒，超时视为失败
- 上下文召回：单个工具最长等待 15 秒，超时跳过该工具
- 两路最晚汇合时间：45 秒，超时后未返回的路径标记失败

**同步机制：**
- 两路各有一个 `ready` 标记，两路都就绪后进入 SCORING
- 先完成的路径等待另一路（最长 45 秒），超时后走错误处理

## 配置

兴趣雷达通过配置文件驱动（默认路径 `~/.hermes/config.yaml` 或同级 `interest-radar.json`），不内置任何平台假设。

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| snapshot_path | 快照缓存文件路径 | `~/.hermes/cache/interest-snapshot.json` |
| snapshot_ttl_hours | 快照缓存有效期 | 6 |
| seed_interests | 回退用种子兴趣 | 内置 |
| output_format | 输出格式（weixin / telegram / feishu / plain） | plain |

用户在 onboarding 时配置，Agent 运行时读配置。

## 接口规范

**API 版本：** `v1`

所有接口遵循统一响应信封：

```json
成功响应：
{
  "api_version": "v1",
  "success": true,
  "data": { ... },
  "processing_info": {
    "context_source": "cache|memory|notes|seed",
    "context_source_detail": "使用的具体工具名（如 hindsight_recall）",
    "duration_ms": 1234
  }
}

错误响应：
{
  "api_version": "v1",
  "success": false,
  "error": {
    "code": "ERR_xxx",
    "message": "人可读的错误描述"
  },
  "data": null
}
```

### 错误码表

| 错误码 | 含义 | 触发条件 |
|--------|------|---------|
| ERR_CONTENT_FETCH | 内容获取失败 | URL 不可达、超时 |
| ERR_CONTENT_TOO_LARGE | 内容超过大小限制 | content > 50KB |
| ERR_CONTEXT_FAILURE | 上下文召回全部失败 | 所有上下文源不可用 |
| ERR_BATCH_EMPTY | 批量输入为空 | items 数组长度为 0 |
| ERR_BATCH_TOO_LARGE | 批量超过上限 | items > 50 |
| ERR_PARAM_INVALID | 参数校验失败 | 缺少必填字段 |
| ERR_INTERNAL | 内部错误 | 未预期的执行异常 |

### judge（单条判断）

```json
输入：
{
  "title": string,            // 必填。内容标题
  "summary": string,          // 必填。内容摘要，最长 2000 字符，超出截断
  "url": string | null,       // 可选。原文链接
  "content": string | null,   // 可选。全文内容，最长 50KB，超出截断
  "source": string | null     // 可选。来源标识（如 "hackernews"、"arxiv"）
}

输出（成功时 data 字段）：
{
  "relevance_score": 0-100,
  "bucket": "top|watch|silent|ignore",
  "why_it_matters": string,
  "confidence": "High|Medium|Low",
  "action": "read|watch|save|ignore",
  "dimension_scores": {
    "project_impact": 0-10,
    "interest_match": 0-10,
    "change_magnitude": 0-10,
    "actionability": 0-10,
    "source_credibility": 0-10,
    "timeliness": 0-10
  },
  "interests_hit": [
    {"label": "AI agents", "score": 7}
  ]
}
```

### batch_judge（批量判断）

```json
输入：
{
  "items": [
    {
      "title": string,
      "url": string | null,
      "content": string | null,
      "source": string | null,
      "event_type": string | null
    }
  ],
  "top_k": number | null,     // 可选。推送档位上限，默认 3，范围 1-10
  "page": number | null,      // 可选。分页页码，从 1 开始，默认 1
  "page_size": number | null  // 可选。每页条数，默认 10，最大 50
}
```

**限制：**
- items 长度：1-50 条
- items > 15 时自动执行初筛（基于 title 关键词匹配），取 top_k × 3 条进入完整评分
- 单条 content > 50KB 时截断，截断部分标记到 processing_info 中

```json
输出（成功时 data 字段）：
{
  "results": [
    {
      "index": 0,
      "relevance_score": 0-100,
      "bucket": "top|watch|silent|ignore",
      "why_it_matters": string,
      "confidence": "High|Medium|Low",
      "action": "read|watch|save|ignore"
    }
  ],
  "summary": {
    "total_items": number,
    "scored_items": number,
    "push_count": number,
    "watch_count": number,
    "top_score": number,
    "avg_score": number,
    "prescreened": boolean
  },
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_pages": 1
  },
  "context": {
    "source": "cache|memory|notes|seed",
    "interests_hit": [string]
  }
}
```

## 判断流程（编排层）

编排层按以下流程执行 judge/batch_judge。每一步的职责和产出物在注释中标注。

### Phase 1：内容获取（路径 A — 编排层 → 推理层）

**输入：** 用户提供的 URL 或内容文本
**产出：** `raw_content`（原始文本）+ `entities`（结构化实体列表）

#### 1a. 获取原始内容

由 Agent 自身能力处理。对 URL 先用网页提取工具，失败则用浏览器工具回退。
超时 30 秒，超时视为失败，进入 `FAILED_CONTENT` 状态。

#### 1b. 实体抽取（推理层）

从内容中识别以下实体类型：
- **技术词**：框架、语言、协议（如 MCP、OpenXR、MoE）
- **产品/项目名**：具体产品或开源项目（如 Llama 4、Claude Code）
- **公司/组织**：发布方或涉及方（如 Meta、OpenAI）
- **事件类型**：release / breaking change / SDK update / paper / opinion

### Phase 2：上下文加载（路径 B — 编排层 → 数据层）

**输入：** 无（从数据层自发现）
**产出：** `context`（包含 interests、active_projects、keywords、dismissed_topics）

#### 2a. 快照缓存（数据层 — 优先）

检查本地缓存文件（默认 `~/.hermes/cache/interest-snapshot.json`）。

```
读文件 → 解析 JSON → 校验 schema_version → 取 updated_at → 判断是否超过 TTL
```

- 文件存在、schema_version 匹配、未过期 → 直接使用，**跳过 2b/2c**
- 文件不存在、过期或 schema_version 不匹配 → 执行实时召回

#### 2b. 实时召回（数据层 — 快照过期时）

用 Agent 可用的记忆/搜索工具召回上下文。不预设具体工具，按以下优先级尝试：
每个工具最长等待 15 秒，超时跳过。

1. 高阶记忆工具（如 hindsight_recall、hindsight_reflect）
2. neuDrive MCP 工具（search_memory, read_profile, list_projects）
3. 原生记忆工具（memory）
4. 项目笔记扫描（如 Obsidian Vault）

#### 2c. 回退到种子兴趣（数据层 — 全部不可用时）

使用以下最小种子兴趣，标记 `source: seed`，置信度 Low：
- XR / spatial computing
- AI agents / Agent 产品
- Personal context / memory systems
- HomeLab / local inference

#### 2d. 更新快照（数据层）

实时召回完成后，将最新上下文写入快照文件：

```json
{
  "schema_version": "v1",
  "updated_at": 1715760000,
  "source": "memory|seed|hybrid",

  "interests": [
    {
      "label": "AI agents",
      "keywords": ["Claude Code", "MCP", "Codex"],
      "source": "memory|seed|user_confirmed",
      "confidence": "High|Medium|Low",
      "last_matched_at": 1715760000,
      "match_count": 12
    }
  ],

  "active_projects": [
    {
      "name": "兴趣雷达",
      "status": "active",
      "source": "memory|user_input",
      "last_mentioned_at": 1715760000
    }
  ],

  "keywords": [
    {"word": "OpenXR", "weight": 3},
    {"word": "MCP", "weight": 2},
    {"word": "agent", "weight": 1}
  ],

  "dismissed_topics": [
    {
      "keywords": ["奶茶AI"],
      "reason": "user_dismissed",
      "count": 2,
      "expires_at": 1747260000,
      "created_at": 1715760000
    }
  ],

  "feedback": [
    {
      "type": "confirm|dismiss",
      "context_id": "judge_20260517_001",
      "content_title": "文章标题",
      "relevance_score": 82,
      "raw_input": "这个不准",
      "scope": {
        "keywords": ["AI agents", "Claude Code"],
        "effect": "global|keyword_specific"
      },
      "created_at": 1715760000
    }
  ]
}
```

**字段说明：**

| 字段 | 说明 |
|------|------|
| `schema_version` | 快照结构版本号，用于未来迁移兼容。当前 v1 |
| `interfaces[].source` | 来源标记：memory（从记忆系统召回）、seed（种子兴趣）、user_confirmed（用户确认） |
| `interests[].confidence` | 可信度，从种子来的默认 Low，从记忆来的 Medium，用户确认过的 High |
| `interests[].last_matched_at` | 上次匹配到此兴趣的时间戳，用于衰减计算 |
| `interests[].match_count` | 累计匹配次数，辅助判断兴趣热度 |
| `keywords[].weight` | 关键词权重（3=高/2=中/1=低），用于初筛排序 |
| `dismissed_topics[].expires_at` | 屏蔽过期时间，到期自动恢复。默认永久（null），可设 30 天 |
| `feedback[].context_id` | 关联到具体的 judge 请求 ID，便于追溯 |
| `feedback[].raw_input` | 用户原始输入，用于后续分析 |
| `feedback[].scope` | 反馈作用域：global（全局降分）或 keyword_specific（仅对特定关键词生效） |

**衰减规则：**
- interests 超过 30 天未匹配，自动降一档置信度
- 降到底（Low）后仍 60 天未匹配，从快照中移除（Archived 归档）
- dismissed_topics 过期后自动恢复，不再屏蔽同类内容
- 以上衰减在每次更新快照时执行（2d 步骤中）
```

### Phase 3：相关性评分（推理层）

**输入：** `entities`（Phase 1）+ `context`（Phase 2）
**产出：** `score`（0-100）+ `dimension_scores` + `why_it_matters` + `confidence`

#### 3a. 等待汇合

Phase 1 和 Phase 2 两路必须都就绪才能进入评分。
- 先完成的路径等待另一路，最晚总耗时 45 秒
- 超时后未就绪的路径标记失败，走对应错误处理

#### 3b. 六维评分

基于实体 + 上下文，按以下维度评分（Agent 推理完成，非硬编码计算）：

| 维度 | 权重 | 评分标准 |
|------|------|---------|
| 项目影响 | 35% | 是否直接影响 active project |
| 兴趣匹配 | 20% | 是否匹配用户 hot/durable 兴趣 |
| 变化幅度 | 15% | release > SDK update > 观点讨论 |
| 可行动性 | 15% | 是否能触发具体行动 |
| 来源可信度 | 10% | 官方 > 一手 > 二手 |
| 时效性 | 5% | 24h > 一周 > 更早 |

**分桶：** top (80-100) / watch (60-79) / silent (30-59) / ignore (0-29)

#### 3c. Top 档位二次验证（评分 ≥ 80 时）

高相关度内容必须执行额外验证，防止过度匹配：

1. 从实体中提取与评分强相关的关键词（最多 3 个）
2. 验证这些关键词在内容中的上下文是否确实与项目/兴趣匹配
3. 例：内容中提到 "agent" → 确认是否真的是 AI Agent 而非 "travel agent"
4. 验证不通过时，下调至 watch 档位，置信度降一档

此步骤只做语义验证，不做额外召回，避免无限循环。

### Phase 4：输出（编排层）

**输入：** `result`（Phase 3 产出）
**产出：** 格式化后的用户消息

#### 4a. 组装响应信封

按接口规范组装响应：`api_version` + `success` + `data` + `processing_info`

#### 4b. 平台适配

根据配置的 `output_format` 选择输出格式（微信/Telegram/飞书/CLI）。

## 反馈闭环

用户对判断结果的反馈（confirm / dismiss）自动影响后续判断。

### 自适应存储

不绑定特定记忆工具。按优先级使用可用的存储工具：
1. 记忆系统的存储功能（如 hindsight_retain）— 附带 context 和 tags
2. Agent 原生记忆工具
3. 本地缓存文件（写入快照的 `feedback` 字段）

### 存储格式（通用）

无论用哪种存储后端，内容格式统一：

```
兴趣雷达反馈: [confirm|dismiss] — "内容标题" (score=82)
context_id: judge_20260517_001
scope: global|keyword_specific
```

### 反馈影响

- confirm：同类内容评分更自信
- dismiss：同类内容降分 10-20 分
- 多次 dismiss（≥ 2 次）：同类内容触发确认检查点，询问用户「这类内容似乎你不太感兴趣，要永久屏蔽吗？」。用户确认后降入 ignore。不确认则保持当前分数不变。
- 多次 confirm（≥ 3 次）：同类内容上调 5-10 分

Agent 通过 Step 3 的上下文召回自动带回反馈记录，在评分时自然调整。**不需要硬编码权重调整逻辑。**

### 触发词

**confirm（确认判断准确）：**
准 / 确实 / 对 / 是的 / 就是这个 / 说得对 / 看了 / 不错 / 有用 / 有帮助 / 说得好 / 👍 / 收藏 / 存一下

**dismiss（否认判断）：**
不准 / 不相关 / 不对 / 不是这样 / 别推这个 / 跟我没关系 / 不感兴趣 / 跳过 / 以后别推这个 / 没意思 / 👎

**不触发（模糊回应）：**
嗯 / 好 / 行 / 知道了 / 哦

### 注入/移除 cron job 触发词

**注入（把兴趣雷达加到推送里）：**
把兴趣雷达加到 XX / 给 XX 加上兴趣雷达 / 用兴趣雷达过滤 XX / 开启 XX 的雷达扫描 / XX 推送加上雷达

**移除（从推送里移除兴趣雷达）：**
从 XX 移除兴趣雷达 / 关闭 XX 的雷达扫描 / 取消 XX 的雷达过滤 / 去掉 XX 的雷达

### 主动扫描触发词

帮我扫描一下 / 雷达扫描一下 / 用兴趣雷达扫一下 / 看看最近有什么值得关注的 / 扫描最近的内容

### 状态查询触发词

兴趣雷达状态 / 当前配置 / 雷达设置 / 查看兴趣雷达 / 雷达开了哪些

### 参数调整触发词

调整兴趣 / 修改评分权重 / 添加兴趣 / 删除兴趣 / 更新快照 / 重置快照

## 平台适配参考

### 自适应上下文探测工具

Agent 在运行时按以下顺序探测可用的上下文/记忆工具（不预设）：

1. **hindsight_recall / hindsight_reflect** — 高阶语义记忆
2. **neuDrive MCP tools** — search_memory, read_profile, list_projects, list_skills
3. **memory（原生记忆）** — 简单键值记忆
4. **Obsidian 笔记扫描** — 本地笔记目录
5. **种子兴趣回退** — 以上全部不可用时

### 在 Hermes 上运行
- 上下文召回：hindsight_recall（主）+ neuDrive MCP（search_memory, read_profile, list_projects 辅助）+ Obsidian（补充）
  - **Cron 环境注意**：`memory` 工具在 cron session 中不可用，但 hindsight_recall 和 neuDrive MCP 都可用
- 反馈存储：hindsight_retain（主）+ 快照文件（回退）+ neuDrive save_memory（辅助）
- 内容获取：web_extract → browser fallback
- 快照操作：execute_code 或 terminal 读写 JSON

### 在 Claude Code 上运行
- 上下文召回：Project Knowledge + 本地文件搜索
- 反馈存储：本地 JSON 文件（快照）
- 内容获取：curl / 浏览器工具
- 快照操作：terminal 读写 JSON

### 在 Codex / Cursor 上运行
- 上下文召回：Workspace Index + 搜索工具
- 反馈存储：本地 JSON 文件
- 内容获取：curl / 浏览器工具
- 快照操作：terminal 读写 JSON

### 在 ChatGPT 上运行
- 上下文召回：用户手动提供的上下文 / Memory 功能
- 反馈存储：ChatGPT Memory
- 内容获取：浏览器工具
- 快照操作：不适用（无文件系统）

## 注入已有推送 Cron Job

当用户说「把兴趣雷达加到 XX 的推送里」或「从 XX 移除兴趣雷达」时，执行以下流程。

这是兴趣雷达提供的标准能力——用户一句话，Agent 自动操作 cron job。

### 注入流程（添加）

**Step 1：找到目标 cron job**

```
cronjob(action='list')
```

按名称匹配用户说的推送任务（如 follow-builders、aigc-weekly 等）。

**Step 2：构造注入段落**

在原有 prompt 末尾追加：

```
---
## 兴趣雷达扫描（必须执行）

在推送完成后，额外执行以下步骤：
1. 对本次推送的所有内容执行 batch_judge 相关性判断
   - 使用 SKILL.md 中定义的 batch_judge 流程
   - 输入：本次推送涉及的所有 title/url/content
2. 将判断结果格式化为「📡 兴趣雷达 · 今日扫描」
   - 列出 top 档位内容（score ≥ 80）
   - 列出 watch 档位内容（score 60-79）
   - 如果无新内容，写「今日无新内容」
3. 将雷达报告附加在推送消息末尾
```

**Step 3：更新 cron job**

```
cronjob(action='update', job_id=<目标 job>, prompt=<原 prompt + 注入段落>)
```

**Step 4：确认**

告知用户：
> ✅ 已将兴趣雷达注入 `<任务名>` 推送。
> 以后每次推送完成后，会额外附上一份雷达扫描报告。

### 移除流程（移除）

当用户说「从 XX 移除兴趣雷达」时：

1. 找到目标 cron job
2. 读取当前 prompt
3. 删除「--- ## 兴趣雷达扫描（必须执行）」到末尾之间的注入段落
4. 更新 cron job
5. 告知用户已移除

### 注意事项

- **只修改 cron job 的 prompt，绝对不修改被注入 Skill 的 SKILL.md 文件**
- 注入段落追加在 prompt 末尾，不影响原有推送流程
- 如果目标 cron job 已有兴趣雷达注入段落，告知用户"已注入，无需重复操作"
- 注入后，兴趣雷达扫描在原有推送完成后执行，两者互不阻塞
- 注入操作可逆，移除时只删除注入段落，恢复原始 prompt

---

## 错误处理

### 错误分类

| 类别 | 错误码 | 处理策略 |
|------|--------|---------|
| **可重试** | ERR_CONTENT_FETCH | 自动重试 1 次（换工具：web_extract → browser），仍失败则返回错误 |
| **可降级** | ERR_CONTEXT_FAILURE | 降级到种子兴趣，标记置信度 Low，不阻塞主流程 |
| **可截断** | ERR_CONTENT_TOO_LARGE | 截断到 50KB，在 processing_info 中标记 `truncated: true` |
| **可跳过** | 部分 item 内容获取失败 | 跳过该 item，其余正常评分，summary.scored_items 反映实际完成数 |
| **不可恢复** | ERR_PARAM_INVALID | 立即返回错误，不执行任何判断 |
| **不可恢复** | ERR_BATCH_EMPTY | 立即返回错误 |
| **不可恢复** | ERR_BATCH_TOO_LARGE | 立即返回错误，提示分批处理 |
| **内部异常** | ERR_INTERNAL | 返回错误，记录异常信息到 processing_info.error_detail |

### 重试策略

- 内容获取：最多重试 1 次，换工具（web_extract → browser）
- 上下文召回：每个工具独立超时（15 秒），超时自动跳过，不重试
- 不重试的场景：参数校验失败、批量超限、权限错误

### 错误响应示例

```json
{
  "api_version": "v1",
  "success": false,
  "error": {
    "code": "ERR_CONTENT_FETCH",
    "message": "无法获取内容：URL 不可达（超时 30s）",
    "detail": {
      "url": "https://example.com/article",
      "attempted": ["web_extract", "browser"],
      "last_error": "Connection timeout"
    }
  },
  "data": null,
  "processing_info": {
    "duration_ms": 31200,
    "retry_count": 1
  }
}
```

---

## 可观测性

### 日志

每次 judge/batch_judge 执行，Agent 应在处理过程中记录以下信息（输出到对话或日志）：

**必记：**
- 请求 ID（格式：`judge_YYYYMMDD_NNN` 或 `batch_YYYYMMDD_NNN`）
- 上下文来源（cache / memory / notes / seed）及具体工具名
- 最终分数 + 分桶 + 置信度
- 耗时（duration_ms）

**条件记录：**
- 发生重试：记录重试原因和重试次数
- 发生降级：记录降级原因（如 "hindsight_recall timeout, fallback to seed"）
- 发生截断：记录原始大小和截断后大小
- Top 档位二次验证：记录验证结果（通过/降级）

### 关键指标

Agent 应在处理过程中计算并暴露以下指标（通过 processing_info 或状态查询接口）：

| 指标 | 说明 | 暴露位置 |
|------|------|---------|
| `duration_ms` | 端到端耗时 | processing_info |
| `context_source` | 上下文来源 | processing_info |
| `retry_count` | 重试次数 | processing_info |
| `truncated` | 是否发生截断 | processing_info |
| `prescreened` | 批量是否执行初筛 | batch_judge summary |
| `scored_items` | 实际评分数量 | batch_judge summary |
| `cache_hit_ratio` | 快照缓存命中率（近 10 次） | 状态查询 |

### 状态查询

用户可通过以下触发词查询运行状态：

> 「兴趣雷达状态」

Agent 返回：
- 快照信息：schema_version、updated_at、source、interests 数量、keywords 数量
- 缓存状态：是否命中、TTL 剩余时间
- 反馈统计：近 7 天 confirm/dismiss 次数
- 衰减状态：有多少兴趣处于降级/归档边缘

---

## 边界

- ❌ 不做内容采集（不维护 sources、不 RSS scraping）
- ❌ 不负责推送（不发送消息、不维护 cronjob）
- ❌ 不存储事件历史
- ❌ 不管理订阅列表
- ✅ 只做判断：给内容 → 返回相关性
- ✅ 提供标准能力：注入/移除已有推送 cron job

## 仓库信息

- GitHub: https://github.com/Igloo302/interest-radar
- 发布内容：SKILL.md + references/
- 参考文件：scoring-patterns.md（评分模式详解 + 常见陷阱）

---

*最后更新：2026-05-17 — 接口规范化（v1）、架构分层重构、数据模型补全（schema_version/元数据/衰减）、错误处理分类、可观测性设计*