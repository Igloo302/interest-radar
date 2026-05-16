# batch_judge 接口参考

## 调用方 Skill 如何集成

在推送 Skill 的 SKILL.md 中，在推送步骤前添加批量过滤步骤。

### 标准集成模板

```markdown
## 推送前过滤（集成兴趣雷达）

推送前，对候选内容执行兴趣雷达的 batch_judge 流程：

1. 采集候选内容列表（通常 5-10 条）
2. 提取每条内容的 title、url、event_type
3. 按 batch_judge 格式组装 items 数组
4. 对 items 执行相关性判断（共享上下文召回）
5. 只推送 top 档位（80-100 分）的内容
6. watch 档位（60-79 分）内容记入 watchlist 备查
```

### 执行流程

#### Step 1：准备 items

从调用方 Skill 的上下文提取候选内容，组装成 batch_judge 输入格式。

#### Step 2：上下文召回（共享）

只做一次，对所有 item 共享。

1. 快照缓存优先（TTL 6h）
2. 快照有效 → 直接使用，跳过实时召回
3. 快照过期/不存在 → 执行实时召回（使用 Agent 可用的记忆/搜索工具），完成后更新快照
4. 所有源不可用 → 回退种子兴趣

#### Step 3：批量评分

逐条评分，共享 Step 2 的上下文。

- items ≤ 3：完整 judge
- items 4-10：共享上下文 + 逐条评分
- items > 10：title + event_type 快速初筛 → top_k × 3 条进入完整判断

#### Step 4：汇总输出

生成 summary：push_count、watch_count、top_score、avg_score。按分数降序排列。

### 性能注意事项

- 上下文召回只做一次，不要对每条 item 单独召回
- 大量 items 时先基于 title 快速初筛
- 快照缓存能大幅减少实时召回次数

### 错误处理

- 上下文召回失败：使用种子兴趣 + 标记 Low 置信度
- 部分 item 内容获取失败：基于 title 继续评分，标注 Low 置信度
- 全部失败：返回空 results + error 信息