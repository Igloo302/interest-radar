# 兴趣雷达输出格式参考

## 标准输出模板（judge 单条）

```
📡 兴趣雷达

🔗 [内容标题]
来源：[来源域名]

📊 相关度：[score]/100（[bucket中文]）
🎯 关联：[项目名/兴趣名]

💡 为什么相关：
[why_it_matters — 1-2句话，必须关联到具体的项目/兴趣/决策，指出具体影响点]

📋 建议行动：[read/watch/save/ignore]
   具体建议：[如"更新 PRD 技术风险部分"]

📎 判断依据：
• [依据1：来自上下文的具体内容]
• [依据2]

置信度：High/Medium/Low
上下文来源：[cache/memory/notes/seed]
```

## batch_judge 汇总模板

```
📡 兴趣雷达 · 批量过滤

📊 汇总：[total_items] 条候选 → [push_count] 条推送 🔥 | [watch_count] 条观察 👀
   已评分：[scored_items] 条 | 初筛：[是/否]
   最高分：[top_score] | 平均分：[avg_score]

🔥 推送（top 档位）：
1. [标题] [score]/100 — [why_it_matters]

👀 观察（watch 档位）：
2. [标题] [score]/100 — [why_it_matters]

💤 归档（silent + ignore，[数量] 条略）

上下文来源：[cache/memory/notes/seed]
命中兴趣：[兴趣1, 兴趣2, ...]
```

## 分桶中文对照

| 英文 | 中文 | 分数 |
|------|------|------|
| top | 🔥 强烈建议阅读 | 80-100 |
| watch | 👀 值得关注 | 60-79 |
| silent | 💤 有关联但不需要立即行动 | 30-59 |
| ignore | ❌ 不相关 | 0-29 |

## 置信度说明

- High：多源召回结果一致，上下文匹配度高
- Medium：单源召回，或上下文匹配度一般
- Low：内容过短/信息不足，或回退到种子兴趣

## 平台适配

不同平台需调整输出格式：
- 微信：不支持 markdown 表格，用列表格式
- Telegram：支持 markdown
- 飞书：支持富文本和卡片
- CLI：纯文本即可