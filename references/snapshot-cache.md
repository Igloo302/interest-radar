# 兴趣快照缓存方案

## 文件位置
缓存文件：`~/.hermes/cache/interest-snapshot.json`（默认，可配置）

## 使用方式

Agent 直接用文件读写工具操作 JSON，不需要 Python 脚本。

### 读取快照
```
读文件 → 解析 JSON → 取 updated_at 字段 → 计算是否超过 TTL（默认 6h）
```

### 写入快照
```
组装 JSON dict → 写入 updated_at 时间戳 → 覆盖写入文件
```

### 首次初始化
没有快照时，直接用种子兴趣生成一份写入。

## 快照结构

```json
{
  "interests": [{"label": "AI agents", "keywords": ["Claude Code", "Codex", "MCP"]}],
  "active_projects": [{"name": "项目名", "status": "active"}],
  "keywords": ["OpenXR", "MCP", "agent"],
  "dismissed_topics": [
    {"keywords": ["奶茶AI"], "reason": "user_dismissed", "count": 1}
  ],
  "updated_at": 1715760000
}
```

## TTL 策略
- 默认 6 小时（可配置）
- 触发 judge 时检查，过期才重新召回
- 首次使用自动用种子兴趣生成
- 实时召回后更新

## 种子兴趣（首次初始化用）

```json
{
  "interests": [
    {"label": "AI agents", "keywords": ["Claude Code", "Codex", "MCP", "agent"]},
    {"label": "XR / spatial computing", "keywords": ["OpenXR", "Android XR", "Vision Pro"]},
    {"label": "Personal context / memory", "keywords": ["knowledge graph", "personal knowledge"]},
    {"label": "HomeLab / local inference", "keywords": ["Ollama", "llama.cpp", "Docker", "GPU"]}
  ],
  "active_projects": [],
  "keywords": ["OpenXR", "MCP", "agent"],
  "dismissed_topics": [],
  "updated_at": 1715760000
}
```