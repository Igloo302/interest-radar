# MVP 1 实现参考

## 架构

MVP 1 是"转发即用"——用户在聊天中发链接，Agent 自动触发 judge 流程。

**不是** cron 驱动的批量采集，**不是** Python 脚本定时运行。

```
用户发链接 + 询问意图
  ↓
Agent 识别触发条件（SKILL.md 定义）
  ↓
Step 1: 获取内容（web_extract → fallback browser）
  ↓
Step 2: 实体抽取（技术词、产品名、组织、事件类型）
  ↓
Step 3: 上下文召回（Hindsight → Memory → Obsidian → 种子兴趣）
  ↓
Step 4: 相关性评分（6 维度加权）
  ↓
Step 5: 生成 why_it_matters
  ↓
Step 6: 输出结果（微信友好格式）
```

## 内容获取

```
优先级 1: web_extract(url)
  → 失败 → fallback: browser_navigate(url) + browser_snapshot
优先级 2: 用户直接提供的文字
优先级 3: URL + 用户补充描述 → 合并
```

**关键：** web_extract 可能因 Nous 订阅限制失败。必须 fallback 到 browser，不要因为获取失败就跳过判断。

## 上下文探测

每次 judge 初始化时探测（不是 preset provider）：

1. 尝试 `hindsight_recall(query, limit=5)` → 成功则用
2. 尝试 `memory` 搜索 → 成功则用
3. 检查 Obsidian Vault 路径 → 存在则扫描
4. 都没有 → 回退种子兴趣 + 告知用户

## 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| 项目影响 | 35% | 是否直接影响 active project |
| 兴趣匹配 | 20% | 是否匹配 hot/durable 兴趣 |
| 变化幅度 | 15% | release > SDK update > 观点讨论 |
| 可行动性 | 15% | 是否能触发具体行动 |
| 来源可信度 | 10% | 官方 > 一手 > 二手 |
| 时效性 | 5% | 24h > 一周 > 更早 |

分桶：top(80-100) / watch(60-79) / silent(30-59) / ignore(0-29)

## 输出格式（微信）

```
📡 兴趣雷达

🔗 [标题]
来源：[域名]

📊 相关度：[score]/100（[档位]）
🎯 关联：[项目/兴趣]

💡 为什么相关：
[why_it_matters]

📋 建议行动：[read/watch/save/ignore]
   具体建议：[...]

📎 判断依据：
• [依据1]
• [依据2]

置信度：High/Medium/Low
```

## 质量检查

好的输出必须包含：
- 具体的影响点（不是"因为你对 XR 感兴趣"）
- 关联到具体的项目/兴趣/决策
- 可执行的建议
- 判断依据来源

如果输出只是摘要新闻，judge 失败了。

## 项目文档

- Skill: `~/.hermes/skills/research/personal-radar/SKILL.md`
- 项目文档: Obsidian `1-Projects/兴趣雷达/兴趣雷达.md`
- 每次架构变更后同步更新两个文件
