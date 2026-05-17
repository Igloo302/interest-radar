# batch_judge 接口参考

## 接口版本

API 版本 v1，与 SKILL.md 接口规范保持一致。

## 调用方 Skill 如何集成

在推送 Skill 的 SKILL.md 中，在推送步骤前添加批量过滤步骤。

### 标准集成模板

```markdown
## 推送前过滤（集成兴趣雷达）

推送前，对候选内容执行兴趣雷达的 batch_judge 流程：

1. 采集候选内容列表（通常 5-10 条）
2. 提取每条内容的 title、url、event_type
3. 按 batch_judge 输入格式组装 items 数组
4. 对 items 执行相关性判断（共享上下文召回）
5. 只推送 top 档位（80-100 分）的内容
6. watch 档位（60-79 分）内容记入 watchlist 备查
```

## 输入参数

```json
{
  "items": [
    {
      "title": string,           // 必填
      "url": string | null,      // 可选
      "content": string | null,  // 可选，最长 50KB/条
      "source": string | null,   // 可选
      "event_type": string | null
    }
  ],
  "top_k": 3,                    // 可选，默认 3，范围 1-10
  "page": 1,                     // 可选，默认 1
  "page_size": 10                // 可选，默认 10，最大 50
}
```

**限制：**
- items 长度：1-50 条
- items > 15 时自动执行初筛（基于 title 关键词匹配），取 top_k × 3 条进入完整评分
- 单条 content > 50KB 时截断

## 输出格式

```json
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

## 执行流程

### Step 1：准备 items

从调用方 Skill 的上下文提取候选内容，组装成 batch_judge 输入格式。校验必填字段（title），缺失则跳过该条。

### Step 2：上下文召回（共享）

只做一次，对所有 item 共享。

1. 快照缓存优先（TTL 6h）
2. 快照有效 → 直接使用，跳过实时召回
3. 快照过期/不存在 → 执行实时召回（使用 Agent 可用的记忆/搜索工具），完成后更新快照
4. 所有源不可用 → 回退种子兴趣

### Step 3：批量评分

逐条评分，共享 Step 2 的上下文。

- items ≤ 3：完整 judge
- items 4-10：共享上下文 + 逐条评分
- items 11-15：共享上下文 + 逐条评分（无需初筛）
- items > 15：title + event_type 快速初筛 → top_k × 3 条进入完整判断

### Step 4：汇总输出

生成 summary 和 pagination 信息。按分数降序排列。

### 错误处理

- 上下文召回全部失败：返回 error.code = ERR_CONTEXT_FAILURE，data 中 results 为空数组
- 部分 item 内容获取失败：跳过该条，其余正常评分，summary.scored_items 反映实际完成数
- 全部失败：返回空 results + error 信息
- 输入校验失败（items 为空或缺少 title）：返回 ERR_PARAM_INVALID

## 性能注意事项

- 上下文召回只做一次，不要对每条 item 单独召回
- 大量 items 时先基于 title 快速初筛
- 快照缓存能大幅减少实时召回次数