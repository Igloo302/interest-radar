# 兴趣快照缓存方案

## 文件位置
缓存文件：`~/.hermes/cache/interest-snapshot.json`（默认，可配置）

## 使用方式

Agent 直接用文件读写工具操作 JSON，不需要 Python 脚本。

### 读取快照
```
读文件 → 解析 JSON → 校验 schema_version → 取 updated_at → 判断是否超过 TTL（默认 6h）
```

### 写入快照
```
组装 JSON dict（含 schema_version） → 写入 updated_at 时间戳 → 覆盖写入文件
```

### Cron 环境行为

在 Hermes cron session 中运行时：
- `memory` 工具不可用，但 `hindsight_recall` 和 `neuDrive MCP`（search_memory, read_profile）都可用
- 快照过期时，优先尝试 hindsight_recall（查询 recent interests/projects/activities）+ neuDrive read_profile
- neuDrive list_projects 也可用，能补充 active projects 列表
- 如果实时召回成功但 neuDrive 不可用（跨平台场景），直接退回到种子兴趣并标记 Low 置信度

## 首次初始化
没有快照时，直接用种子兴趣生成一份写入。标记 `source: seed`，置信度 Low。

## 快照结构

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

## 字段说明

| 字段 | 说明 |
|------|------|
| `schema_version` | 快照结构版本号，用于未来迁移兼容。当前 v1 |
| `interests[].source` | 来源标记：memory（从记忆系统召回）、seed（种子兴趣）、user_confirmed（用户确认） |
| `interests[].confidence` | 可信度，从种子来的默认 Low，从记忆来的 Medium，用户确认过的 High |
| `interests[].last_matched_at` | 上次匹配到此兴趣的时间戳，用于衰减计算 |
| `interests[].match_count` | 累计匹配次数，辅助判断兴趣热度 |
| `keywords[].weight` | 关键词权重（3=高/2=中/1=低），用于初筛排序 |
| `dismissed_topics[].expires_at` | 屏蔽过期时间，到期自动恢复。默认永久（null），可设 30 天 |
| `feedback[].context_id` | 关联到具体的 judge 请求 ID，便于追溯 |
| `feedback[].raw_input` | 用户原始输入，用于后续分析 |
| `feedback[].scope` | 反馈作用域：global（全局降分）或 keyword_specific（仅对特定关键词生效） |

## 衰减规则

在每次更新快照时执行：

- interests 超过 30 天未匹配，自动降一档置信度
- 降到底（Low）后仍 60 天未匹配，从快照中移除（标记 archived）
- dismissed_topics 过期后自动恢复，不再屏蔽同类内容
- keywords 的 weight 超过 90 天未匹配，降一档

## TTL 策略

- 快照自身 TTL：默认 6 小时（可配置），过期后重新召回
- 触发 judge 时检查，过期才重新召回
- 首次使用自动用种子兴趣生成
- 实时召回后更新

## 种子兴趣（首次初始化用）

```json
{
  "interests": [
    {
      "label": "AI agents",
      "keywords": ["Claude Code", "Codex", "MCP", "agent"],
      "source": "seed",
      "confidence": "Low",
      "last_matched_at": null,
      "match_count": 0
    },
    {
      "label": "XR / spatial computing",
      "keywords": ["OpenXR", "Android XR", "Vision Pro"],
      "source": "seed",
      "confidence": "Low",
      "last_matched_at": null,
      "match_count": 0
    },
    {
      "label": "Personal context / memory",
      "keywords": ["knowledge graph", "personal knowledge", "memory system"],
      "source": "seed",
      "confidence": "Low",
      "last_matched_at": null,
      "match_count": 0
    },
    {
      "label": "HomeLab / local inference",
      "keywords": ["Ollama", "llama.cpp", "Docker", "GPU"],
      "source": "seed",
      "confidence": "Low",
      "last_matched_at": null,
      "match_count": 0
    }
  ],
  "active_projects": [],
  "keywords": [
    {"word": "OpenXR", "weight": 3},
    {"word": "MCP", "weight": 3},
    {"word": "agent", "weight": 2},
    {"word": "Ollama", "weight": 3},
    {"word": "llama.cpp", "weight": 2}
  ],
  "dismissed_topics": [],
  "feedback": [],
  "schema_version": "v1",
  "updated_at": 1715760000,
  "source": "seed"
}
```