# 反馈闭环参考

## 核心原则

反馈闭环不绑定任何特定的记忆工具或存储后端。Agent 在运行时自适应地使用当前环境可用的工具来存储和召回反馈。

## 自适应存储策略

| 优先级 | 存储方式 | 说明 |
|--------|---------|------|
| 1 | 记忆系统的存储功能（如 hindsight_retain） | 附带 context 和 tags |
| 2 | Agent 原生记忆工具 | Agent 内置的记忆/持久化功能 |
| 3 | 本地缓存文件 | 写入快照的 `feedback` 字段 |

## 存储格式

### 通用文本格式（用于记忆系统）

```
兴趣雷达反馈: [confirm|dismiss] — "内容标题" (score=82)
context_id: judge_20260517_001
scope: global|keyword_specific
```

附带 tags：
```
tags: [interest-radar, feedback, confirm|dismiss]
```

### 结构化格式（用于快照文件）

```json
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
```

## 用户反馈触发词

### confirm
准 / 确实 / 对 / 是的 / 就是这个 / 说得对 / 看了 / 不错 / 这个有用 / 有帮助 / 👍 / 收藏 / 存一下

### dismiss
不准 / 不相关 / 不对 / 不是这样 / 别推这个 / 跟我没关系 / 我不关心这个 / 判断错了 / 没意思 / 👎

### 不触发
嗯 / 好 / 行 / 知道了（模糊回应）

## 反馈影响

| 场景 | 影响 |
|------|------|
| 单条 confirm | 同类内容评分更自信，置信度可提一档 |
| 单条 dismiss | 同类内容降分 10-20 分 |
| 多次 dismiss（≥ 2 次） | 触发确认检查点，询问用户是否永久屏蔽 |
| 多次 dismiss 且用户确认 | 降入 ignore 档位，写入 dismissed_topics |
| 多次 confirm（≥ 3 次） | 同类内容上调 5-10 分 |

### 作用域说明

- **global**：反馈影响整个兴趣类别（如 dismiss 了所有"AI agents"相关内容）
- **keyword_specific**：反馈仅影响特定关键词组合（如 dismiss 了"奶茶AI"但不影响其他 AI 内容）

Agent 根据用户 raw_input 中的具体措辞判断作用域。如果用户说"别推奶茶相关的" → keyword_specific。如果用户说"别推 AI 了" → global。

Agent 通过上下文召回自动带回反馈记录，在评分时自然调整。

## 边界

- ❌ 不绑定特定记忆工具
- ❌ 不修改评分算法代码
- ❌ 不要求用户反馈（只对明确信号反应）
- ✅ 隐式生效