---
name: interest-radar
description: "通用相关性判断引擎（兴趣雷达/Interest Radar/Personal Radar）：接收外部内容，利用用户的个人上下文判断内容与用户的相关程度。平台无关，可在各种 Agent 平台上运行。触发场景：(1) 用户转发/粘贴链接/消息并询问相关性；(2) 用户要求分析某条内容与项目的关联；(3) 用户提到\"兴趣雷达\"、\"personal radar\"、\"相关性判断\"；(4) 其他推送 Skill 调用 batch_judge 增强推送质量。"
---

# 兴趣雷达 / Interest Radar

## 一句话

**给内容，还判断。** 兴趣雷达不采集、不推送、不存储，只做一件事：告诉你一段外部内容和你有多相关、为什么、该不该看。

## 设计原则

### 平台无关

兴趣雷达不绑定任何特定 Agent 平台。它通过 SKILL.md 描述工作流，任何能执行该流程的 Agent（Claude Code、Codex、Cursor、OpenClaw、ChatGPT、Hermes 等）都可以使用。

**Agent 不预设任何工具。** 运行时自适应探测当前环境可用的工具，选择最优方案执行。

### 零代码依赖

兴趣雷达是纯 SKILL.md 定义的工作流，不依赖任何 Python 脚本或外部运行时。快照缓存直接通过读写 JSON 文件实现。

### 判断引擎，不是采集器

兴趣雷达只做中间层，不碰两端。不采集内容，不负责推送，不存数据。

```
已有的内容推送来源（用户转发 / 推送 Skill / RSSHub / 微信群 等）
    ↓
    兴趣雷达（相关性判断引擎）
    ├── 自适应上下文召回
    ├── 实体抽取
    ├── 兴趣匹配
    ├── 项目关联
    ├── 综合评分 + why_it_matters
    └── 反馈闭环（越用越准）
    ↓
增强后结果（分数 + 原因 + 关联 + 建议 + 置信度）
```

### 自适应上下文召回

Agent 按以下优先级顺序探测可用的上下文工具，**不预设使用哪个**：

| 优先级 | 上下文源 | 探测方式 |
|--------|---------|---------|
| 1 | 快照缓存文件 | 检查本地缓存文件是否存在、是否过期（TTL 6h） |
| 2 | 记忆系统召回 | 尝试调用 Agent 可用的记忆/搜索工具 |
| 3 | 项目笔记扫描 | 检查本地笔记目录是否存在（如 Obsidian Vault） |
| 4 | 最小种子兴趣 | 以上全部不可用时回退 |

### Skill 只定义接口，不绑定实现

SKILL.md 只定义 `judge()` 和 `batch_judge()` 两个接口的行为流程。配置驱动运行，不内置任何平台/工具假设。

## 配置

兴趣雷达通过配置文件驱动（默认路径 `~/.hermes/config.yaml` 或同级 `interest-radar.json`），不内置任何平台假设。

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| snapshot_path | 快照缓存文件路径 | `~/.hermes/cache/interest-snapshot.json` |
| snapshot_ttl_hours | 快照缓存有效期 | 6 |
| seed_interests | 回退用种子兴趣 | 内置 |
| output_format | 输出格式（weixin / telegram / feishu / plain） | plain |

用户在 onboarding 时配置，Agent 运行时读配置。

## 接口

### judge（单条）

输入：title, summary, url?, source?
输出：relevance_score (0-100), bucket (top|watch|silent|ignore), why_it_matters, confidence (High|Medium|Low), action (read|watch|save|ignore)

### batch_judge（批量）

输入：items[{title, url, content, source, event_type}], top_k (默认3)
输出：results[{index, score, bucket, why_it_matters, confidence, action}], summary{push_count, watch_count, top_score, avg_score}, context{source, interests_hit}

## 判断流程

### Step 1：获取内容

由 Agent 自身能力处理。对 URL 先用网页提取工具，失败则用浏览器工具回退。

与 Step 3 并行执行。

### Step 2：实体抽取

从内容中识别：技术词、产品/项目名、公司/组织、事件类型（release / breaking change / SDK update / paper 等）。

### Step 3：自适应上下文召回

#### 3a. 快照缓存（优先使用）

检查本地缓存文件（配置项 `snapshot_path`，默认 `~/.hermes/cache/interest-snapshot.json`）。

**操作方式：** Agent 直接用文件读写工具操作 JSON，不需要 Python 脚本。

```
读文件 → 解析 JSON → 取 updated_at 字段 → 计算是否超过 TTL（默认 6h）
```

- 文件存在且未过期 → 使用快照内容作为上下文，**跳过 3b/3c/3d**
- 文件不存在或过期 → 执行实时召回，完成后写入更新后的快照
- **首次使用**：没有快照 → 自动用种子兴趣生成初始快照并写入

快照结构：
```json
{
  "interests": [{"label": "AI agents", "keywords": ["Claude Code", "Codex", "MCP"]}],
  "active_projects": [{"name": "项目名", "status": "active"}],
  "keywords": ["OpenXR", "MCP", "agent"],
  "dismissed_topics": [],
  "updated_at": 1715760000
}
```

#### 3b. 实时召回（快照过期时）

用 Agent 可用的记忆/搜索工具召回上下文。不预设具体工具，按以下优先级尝试：

1. 尝试 Agent 的高阶记忆工具（如有）
2. 尝试 Agent 的原生记忆/搜索工具（如有）
3. 扫描本地项目笔记目录（如有）

#### 3c. 回退到种子兴趣

全部不可用时使用以下最小种子兴趣：
- XR / spatial computing
- AI agents / Agent 产品
- Personal context / memory systems
- HomeLab / local inference

#### 3d. Top 档位强制多源（评分 ≥ 80 时）

高相关度内容必须执行额外召回：不同关键词再次搜索 + 深度思考（如有此能力）+ 项目笔记扫描。失败则跳过，不阻塞。

#### 3e. 更新快照

实时召回完成后，将最新上下文写入快照文件（Agent 直接写 JSON）：

```json
{
  "interests": [从召回结果提取的兴趣列表],
  "active_projects": [从召回结果提取的项目列表],
  "keywords": [从实体抽取 + 召回结果提取的关键词],
  "dismissed_topics": [保留已有，追加新的],
  "updated_at": [当前时间戳]
}
```

写入方式：Agent 直接用文件写入工具覆盖写入。

### Step 4：相关性评分

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

### Step 5：生成 why_it_matters

1-2 句话，必须关联到具体项目/兴趣/决策，指出具体影响点。避免"因为你对 XR 感兴趣"这种废话。

### Step 6：输出结果

平台适配格式（如微信用列表，Telegram 用 markdown，飞书用富文本）。

## 反馈闭环

用户对判断结果的反馈（confirm / dismiss）自动影响后续判断。

### 自适应存储

不绑定特定记忆工具。按优先级使用可用的存储工具：
1. 记忆系统的存储功能（如 hindsight_retain）
2. Agent 原生记忆工具
3. 本地缓存文件（写入快照的 `feedback` 字段）

### 反馈影响

- confirm：同类内容评分更自信
- dismiss：同类内容降分 10-20 分
- 多次 dismiss（≥ 3 次）：同类内容降入 ignore
- 多次 confirm（≥ 3 次）：同类内容上调 5-10 分

Agent 通过 Step 3 的上下文召回自动带回反馈记录，在评分时自然调整。**不需要硬编码权重调整逻辑。**

### 触发词

confirm：准 / 确实 / 对 / 看了 / 这个有用
dismiss：不准 / 不相关 / 别推这个 / 跟我没关系

模糊回应（嗯 / 好 / 行）不触发。

## 平台适配参考

### 在 Hermes 上运行
- 上下文召回：hindsight_recall（主）+ Obsidian（补充）
- 反馈存储：hindsight_retain（主）+ 快照文件（回退）
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

*最后更新：2026-05-16 — 去掉 Python 脚本依赖，纯 SKILL.md 定义的工作流*