# 上下文系统动态适配

## 核心思路

兴趣雷达不维护 preset provider 列表。它在每次初始化时**动态探测**当前 Agent 环境中可用的上下文系统，然后**实时生成**获取代码。

这不是"if hindsight available → use HindsightProvider"这种硬编码，而是 Agent 根据实际环境决定：用什么工具、怎么调用、怎么合并结果。

## 探测步骤

Agent 在初始化时执行以下探测：

### 1. 工具级探测

检查以下工具是否可用（通过尝试调用或检查工具列表）：

| 工具 | 探测方式 | 对应上下文源 |
|------|---------|-------------|
| `hindsight_recall` / `hindsight_reflect` | 尝试调用，检查是否返回有效结果 | Hindsight 记忆系统 |
| `memory` | 尝试调用 memory(search) | Hermes 原生记忆 |
| `read_file` + `search_files` | 检查 Obsidian Vault 路径是否存在 | Obsidian 笔记 |

### 2. 环境级探测

检查环境中是否安装了其他记忆 SDK：

```python
# 伪代码：Agent 在运行时判断
try:
    import mem0
    # → 可用，生成 mem0 查询代码
except ImportError:
    pass

try:
    import some_future_memory_sdk
    # → 可用，生成对应查询代码
except ImportError:
    pass
```

### 3. 生成适配代码

根据探测结果，Agent 实时生成获取用户上下文的代码：

**场景 A：Hindsight 可用**
```python
# Agent 生成的适配代码
memories = hindsight_recall(query=entities, top_k=5)
reflection = hindsight_reflect(query=f"用户当前活跃项目和兴趣")
# 使用 memories + reflection 作为上下文
```

**场景 B：只有 Hermes memory**
```python
# Agent 生成的适配代码
memories = memory(search="用户项目 兴趣 决策")
# 使用 memories 作为上下文
```

**场景 C：只有 Obsidian**
```python
# Agent 生成的适配代码
projects = read_file("~/.../ObsidianVault/1-Projects/index.md")
active_notes = search_files(path="~/.../ObsidianVault/1-Projects", query="active")
# 解析笔记内容作为上下文
```

**场景 D：多个可用**
```python
# Agent 生成的组合代码
ctx_hindsight = hindsight_recall(query=entities)
ctx_memory = memory(search="活跃项目")
# 合并去重，Hindsight 结果优先
```

**场景 E：都没有**
→ 使用 SKILL.md 内置的最小种子兴趣
→ 建议用户配置上下文系统

## 告知用户

初始化完成后，Agent 简要告知：

- 成功：`"✅ 兴趣雷达已初始化，使用 [Hindsight] 作为上下文来源。"`
- 回退：`"⚠️ 未检测到个人上下文系统，使用最小种子兴趣（XR、AI、HomeLab）。建议：配置 Hindsight 或将 Obsidian Vault 置于标准路径。"`

## 与 preset provider 的区别

| 旧方案（preset） | 新方案（动态生成） |
|-----------------|-------------------|
| 写死 provider 类 | Agent 实时决定 |
| 预设检测顺序 | 根据实际环境决定 |
| 新增 provider 需改代码 | 新 SDK 自动探测 |
| 用户需配置 provider | 零配置 |
