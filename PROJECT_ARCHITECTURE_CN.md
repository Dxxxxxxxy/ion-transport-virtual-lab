# 离子传输虚拟实验室 - 完整项目架构说明

**创建日期**: 2026年1月10日
**项目版本**: 0.4.0
**代码语言**: Python
**AI模型**: GPT-4o

---

## 📋 目录

1. [项目概述](#项目概述)
2. [整体架构](#整体架构)
3. [核心模块详解](#核心模块详解)
4. [文件夹结构](#文件夹结构)
5. [数据流程](#数据流程)
6. [运行机制](#运行机制)

---

## 项目概述

### 项目目标
建立一个**多智能体科学讨论系统**，让4个不同领域的AI专家（电化学、膜科学、生物学、纳米流体）通过4轮深入讨论，共同建立**离子传输的统一理论框架**。

### 核心特点
- **多智能体协作**: 6个AI智能体（4专家 + 1主席 + 1评论家）
- **知识库隔离**: 每个专家有独立的RAG知识库（17,763篇论文）
- **增强能力**: ReAct推理、记忆系统、规划系统、工具调用、RAG验证
- **自包含**: 不依赖外部virtual_lab框架
- **成本优化**: 全程约$3-4，耗时15-25分钟

### 技术栈
- **LLM**: OpenAI GPT-4o (主模型), GPT-4o-mini (规划/总结)
- **向量数据库**: ChromaDB (177 MB, 17,763文档)
- **知识库**: LangChain + OpenAI Embeddings
- **工具**: SymPy, Matplotlib, NetworkX, Semantic Scholar API

---

## 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Ion Transport Symposium                      │
│                    (run_full_symposium.py)                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼────┐            ┌────▼────────┐
    │ 主席PI  │            │ 4个专家智能体 │
    │ (协调) │            │ (UnifiedAgent)│
    └─────────┘            └────┬─────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
            ┌───────▼──┐  ┌────▼────┐  ┌──▼──────┐
            │ 基础智能体│  │增强层   │  │工具系统 │
            │ (Agent) │  │(Memory, │  │(Tools)  │
            │         │  │Planning,│  │         │
            │         │  │ReAct)   │  │         │
            └─────────┘  └────┬────┘  └──┬──────┘
                              │           │
                        ┌─────▼───────────▼─────┐
                        │  知识库 (ChromaDB)    │
                        │  17,763 研究文档      │
                        └───────────────────────┘
```

---

## 核心模块详解

### 🎯 模块1: 根目录核心文件 (37 KB)

#### `base_agent.py` (3,530 bytes)
**作用**: 定义基础Agent类，是所有智能体的核心基类

**功能**:
```python
class Agent:
    - __init__: 初始化智能体（title, expertise, goal, role, model）
    - prompt: 返回完整提示词（expertise + goal + role）
    - message: 返回OpenAI API格式的系统消息
    - __hash__/__eq__: 支持智能体去重和比较
```

**为什么需要它**:
- 替代了外部`virtual_lab.agent.Agent`依赖
- 为6个智能体提供统一接口
- 每个智能体都是Agent的实例

**被谁调用**:
- `agents/detailed_agents.py` - 创建6个专家智能体
- `enhanced_agents/react_layer.py` - ReAct增强层
- `enhanced_agents/unified_agent.py` - 统一智能体包装器

---

#### `constants.py` (1,109 bytes)
**作用**: 全局配置常量

**内容**:
```python
DEFAULT_MODEL = "gpt-4o"  # 所有智能体使用的默认模型
SCIENTIFIC_CRITIC = "..." # 科学评论家提示模板（参考）
```

**为什么需要它**:
- **中心化配置**: 一处修改，全局生效
- 想切换到`o1-preview`? 只需改这一行！
- 所有6个智能体共用同一个模型设置

**被谁调用**:
- `agents/detailed_agents.py` - 导入DEFAULT_MODEL为所有智能体设置模型

---

#### `orchestrator.py` (9,971 bytes)
**作用**: 多智能体讨论的**核心编排器**

**功能**:
```python
def run_meeting(
    team_lead,        # 主席
    team_members,     # 专家们
    agenda,           # 讨论议程
    num_rounds,       # 讨论轮数
    ...
):
    # 1. 构建讨论上下文（议程、问题、规则、历史总结）
    # 2. 每轮让每个智能体依次发言
    # 3. 调用OpenAI API，支持工具调用
    # 4. 处理工具调用（RAG查询、方程求解等）
    # 5. 保存讨论记录（markdown + JSON）
    # 6. 生成总结（使用gpt-4o-mini节省成本）
```

**为什么需要它**:
- 替代了外部`virtual_lab.run_meeting`
- **是整个symposium的心脏** - 控制讨论流程
- 处理智能体轮流发言、工具调用、记录保存

**核心逻辑**:
1. 初始化OpenAI客户端
2. 为每个智能体准备消息历史
3. 每轮讨论：
   - 遍历每个专家
   - 调用OpenAI API（带工具）
   - 如果有工具调用 → 执行工具 → 获取结果
   - 记录到对话历史
4. 保存完整记录
5. 返回总结

**被谁调用**:
- `run_full_symposium.py` - 调用4次（4轮讨论）

---

#### `rag_tool.py` (7,437 bytes)
**作用**: RAG（检索增强生成）工具接口

**功能**:
```python
class RAGIntegration:
    - run_rag_query(query, domain, top_k): 查询知识库
    - format_rag_results(results): 格式化检索结果
    - to_openai_schema(): 转换为OpenAI工具格式

def get_rag_integration(): 获取全局RAG实例
```

**工作流程**:
1. 接收查询（例如："EDL capacitance in nanopores"）
2. 指定领域（例如："electrochemistry"）
3. 调用`knowledge_base/query_rag.py`查询向量数据库
4. 返回相关文献片段（含引用）

**为什么需要它**:
- 将RAG功能包装成**工具**，可被智能体调用
- 支持OpenAI Function Calling格式
- 连接智能体和知识库的**桥梁**

**被谁调用**:
- `enhanced_agents/tool_manager.py` - 注册为工具
- `enhanced_agents/rag_validator.py` - RAG验证

---

#### `run_full_symposium.py` (13,917 bytes)
**作用**: **主程序入口** - 运行完整的4轮symposium

**功能**:
```python
def create_unified_agents():
    # 创建4个UnifiedAgent（电化学、膜科学、生物、纳米流体）

def main():
    # 1. 初始化4个专家智能体
    # 2. Round 1: 绘制理论全景图（2轮讨论）
    # 3. Round 2: 识别统一原则（3轮讨论）
    # 4. Round 3: 构建统一框架（4轮讨论）
    # 5. Round 4: 应用与未来方向（3轮讨论）
    # 6. 导出数据（计划、统计、记忆）
    # 7. 提升记忆为长期存储
```

**4轮讨论流程**:
```
Round 1 (2轮) → 理解各领域当前范式
    ↓
Round 2 (3轮) → 测试类比、找共同数学框架
    ↓
Round 3 (4轮) → 合成为统一理论框架
    ↓
Round 4 (3轮) → 跨领域应用、借鉴技术
```

**每轮的步骤**:
1. **准备阶段**: 每个智能体调用`prepare_for_round()`
   - 生成战略计划（使用gpt-4o-mini）
   - 检索相关记忆
2. **讨论阶段**: 调用`run_meeting()`
   - 智能体轮流发言
   - 使用工具（RAG、方程、绘图等）
3. **巩固阶段**: 每个智能体调用`consolidate_round()`
   - 提取关键见解存入记忆

**输出结果**:
```
results/full_symposium/
├── round_1_landscape/
│   ├── round1_discussion.md        # 讨论记录
│   ├── round1_discussion.json      # 结构化数据
│   └── round1_discussion_summary.txt
├── round_2_principles/
├── round_3_framework/
├── round_4_applications/
└── agent_data/
    ├── electrochemistry_plans.json
    ├── electrochemistry_stats.json
    └── ... (其他专家数据)
```

**被谁调用**:
- 用户直接运行: `python run_full_symposium.py --yes`

---

#### `setup.py` (1,283 bytes)
**作用**: Python包安装配置

**功能**:
- 定义包名: `ion_transport`
- 定义版本: `0.4.0`
- 列出依赖: 从`requirements.txt`读取
- 配置包元数据

**为什么需要它**:
- 使项目可以通过`pip install -e .`安装
- 解决导入路径问题（`from agents.xxx import yyy`）
- 自动安装所有依赖

---

### 🤖 模块2: agents/ - 智能体定义 (21 KB)

#### `agents/__init__.py` (38 bytes)
**作用**: 包初始化文件

```python
"""Agent definitions for the symposium."""
```

---

#### `agents/detailed_agents.py` (20,848 bytes)
**作用**: **定义6个专家智能体** - 项目的核心角色

**包含的智能体**:

**1. ELECTROCHEMISTRY_EXPERT** (电化学科学家)
```python
Agent(
    title="Electrochemistry Scientist",
    expertise="电双层(EDL)电容器、超级电容器、电容去离子化(CDI)...",
    goal="解释水系统中的离子传输和EDL形成...",
    role="你是电化学研究员，专注于电容系统...",
    model=DEFAULT_MODEL  # "gpt-4o"
)
```
- **知识领域**: EDL电容、CDI、多孔碳电极、水溶液电解质
- **知识库**: `electrochemistry_papers` (6,478篇文献)
- **限制**: 不熟悉电池、有机电解质、生物蛋白结构

**2. MEMBRANE_SCIENCE_EXPERT** (膜科学专家)
```python
Agent(
    title="Membrane Science Expert",
    expertise="离子交换膜、纳滤、反渗透、膜选择性...",
    goal="解释膜中的离子传输机制...",
    model=DEFAULT_MODEL
)
```
- **知识领域**: 离子交换膜、Donnan排斥、膜电位、离子选择性
- **知识库**: `membrane_science_papers` (4,026篇文献)

**3. BIOLOGY_EXPERT** (生物离子传输科学家)
```python
Agent(
    title="Biological Ion Transport Scientist",
    expertise="离子通道、水孔蛋白、Na+/K+ ATPase...",
    goal="解释生物系统中的离子传输...",
    model=DEFAULT_MODEL
)
```
- **知识领域**: 离子通道、门控机制、选择性过滤器、跨膜电位
- **知识库**: `biology_papers` (534篇文献)

**4. NANOFLUIDICS_EXPERT** (纳米流体科学家)
```python
Agent(
    title="Nanofluidics Scientist",
    expertise="纳米通道、纳米孔、离子整流、浓差极化...",
    goal="解释纳米尺度的离子传输...",
    model=DEFAULT_MODEL
)
```
- **知识领域**: 纳米通道、离子整流、表面电荷效应、浓差极化
- **知识库**: `nanofluidics_papers` (6,725篇文献)

**5. SYMPOSIUM_PI** (研讨会主席/PI)
```python
Agent(
    title="Symposium Chair and PI",
    expertise="跨学科研究、理论综合...",
    goal="引导专家们找到统一框架",
    model=DEFAULT_MODEL
)
```
- **角色**: 主持人、协调者
- **职责**:
  - 提出引导性问题
  - 识别共同模式
  - 推动深入讨论
  - 确保所有声音被听到

**6. CUSTOM_SCIENTIFIC_CRITIC** (科学评论家)
```python
Agent(
    title="Scientific Critic",
    expertise="批判性分析、逻辑谬误识别...",
    goal="评估论证质量，识别不支持的主张",
    model=DEFAULT_MODEL
)
```
- **角色**: 质量把关者
- **职责**:
  - 评估论证质量
  - 识别逻辑谬误
  - 检查证据是否支持结论
  - 确保科学严谨性

**被谁调用**:
- `run_full_symposium.py` - 导入所有6个智能体
- `enhanced_agents/unified_agent.py` - 包装EXPERT智能体

---

### 🚀 模块3: enhanced_agents/ - 增强能力系统 (101 KB)

这个模块是**项目的核心创新**，实现了所有高级功能。

#### `enhanced_agents/__init__.py` (2,555 bytes)
**作用**: 导出所有增强组件

```python
from enhanced_agents.react_layer import ReActAgent
from enhanced_agents.memory_system import AgentMemory
from enhanced_agents.planning_system import AgentPlanner
from enhanced_agents.tool_manager import ToolManager
from enhanced_agents.rag_validator import RAGValidator
from enhanced_agents.unified_agent import UnifiedAgent  # ⭐ 核心
```

---

#### `enhanced_agents/unified_agent.py` (13,854 bytes)
**作用**: **统一智能体包装器** - 集成所有增强功能的核心类

**架构**:
```python
class UnifiedAgent:
    def __init__(self, base_agent, domain, ...):
        self.base_agent = base_agent        # 基础Agent
        self.domain = domain                # 领域（electrochemistry等）
        self.memory = AgentMemory(...)      # 记忆系统
        self.planner = AgentPlanner(...)    # 规划系统
        self.tool_manager = ToolManager(...) # 工具管理
        self.rag_validator = RAGValidator(...) # RAG验证
```

**核心方法**:

**1. 属性委托** (Delegation Pattern)
```python
@property
def title(self): return self.base_agent.title
@property
def model(self): return self.base_agent.model
@property
def enhanced_role(self):
    # 组合: 基础role + ReAct指令 + RAG强制 + 工具说明
```

**2. prepare_for_round()** - 回合准备
```python
def prepare_for_round(self, round_number, agenda, questions, previous_summary):
    # 1. 从记忆中检索相关过去见解
    memories = self.memory.recall_relevant(...)

    # 2. 生成战略计划（使用gpt-4o-mini节省成本）
    plan = self.planner.create_contribution_plan(
        round_number, agenda, questions, memories, previous_summary
    )

    # 3. 返回增强议程（含计划和记忆）
    return enhanced_agenda
```

**3. consolidate_round()** - 回合巩固
```python
def consolidate_round(self, round_number, round_summary):
    # 1. 提取关键见解（使用LLM总结）
    insights = self.memory.consolidate_memories(
        round_number, round_summary
    )

    # 2. 存入记忆数据库
    # 3. 更新统计信息
```

**4. openai_tools** - 工具列表
```python
@property
def openai_tools(self):
    # 返回所有可用工具的OpenAI格式schema
    return self.tool_manager.get_all_openai_tools()
    # 包括: RAG查询、方程求解、绘图、概念图、文献搜索
```

**5. respond()** - 响应生成（占位符）
```python
def respond(self, messages, **kwargs):
    # 注意：实际的OpenAI调用在orchestrator.py中
    # 这个方法展示了预期的验证和重试逻辑
```

**为什么这是核心**:
- ✅ **一站式包装**: 所有增强功能都集成在这里
- ✅ **简化使用**: 用户只需创建UnifiedAgent，所有功能自动启用
- ✅ **接口兼容**: 保持与基础Agent相同的接口
- ✅ **领域隔离**: 每个智能体有独立的知识库和记忆

**被谁调用**:
- `run_full_symposium.py` - 创建4个UnifiedAgent实例

---

#### `enhanced_agents/memory_system.py` (17,929 bytes)
**作用**: **持久化记忆系统** - 智能体跨回合学习

**核心类**:
```python
class AgentMemory:
    def __init__(self, domain, config, symposium_id):
        self.domain = domain
        self.collection = chroma_client.get_or_create_collection(
            name=f"{domain}_agent_memory"
        )
        self.short_term = []      # 当前回合
        self.working_memory = []  # 当前symposium
        self.long_term = []       # 永久存储
```

**核心方法**:

**1. recall_relevant()** - 检索相关记忆
```python
def recall_relevant(self, query, top_k=5):
    # 语义搜索：找到与当前议程最相关的过去见解
    results = self.collection.query(
        query_texts=[query],
        n_results=top_k
    )
    return formatted_memories
```

**2. consolidate_memories()** - 巩固记忆
```python
def consolidate_memories(self, round_number, round_summary):
    # 1. 使用LLM从讨论总结中提取关键见解
    prompt = f"从这次讨论中提取3-5个关键见解..."
    insights = llm.generate(prompt)

    # 2. 存入ChromaDB
    self.collection.add(
        documents=insights,
        metadatas=[{"round": round_number, ...}],
        ids=[...]
    )

    # 3. 清空短期记忆，移入工作记忆
```

**3. promote_to_long_term_memory()** - 提升为长期记忆
```python
def promote_to_long_term_memory(self):
    # Symposium结束后，将工作记忆标记为长期
    # 下次symposium可以检索
```

**记忆层级**:
```
短期记忆 (Short-term)
    ↓ (每回合结束后consolidate)
工作记忆 (Working)
    ↓ (symposium结束后promote)
长期记忆 (Long-term)
```

**存储位置**: `data/memory_db/{domain}_agent_memory/`

**为什么需要它**:
- ✅ 智能体可以**记住**过去的讨论
- ✅ 避免重复相同的论点
- ✅ 建立**累积性知识**
- ✅ 跨symposium学习

---

#### `enhanced_agents/planning_system.py` (12,193 bytes)
**作用**: **战略规划系统** - 每回合前制定贡献计划

**核心类**:
```python
class AgentPlanner:
    def __init__(self, agent_title, domain, model="gpt-4o-mini"):
        self.agent_title = agent_title
        self.domain = domain
        self.model = model  # 使用mini节省成本
```

**核心方法**:
```python
def create_contribution_plan(self, round_number, agenda, questions,
                             memory_context, previous_summary):
    # 1. 构建规划提示
    prompt = f"""
    作为{self.agent_title}，为Round {round_number}制定战略计划。

    议程: {agenda}
    关键问题: {questions}
    过去记忆: {memory_context}
    上轮总结: {previous_summary}

    请制定计划：
    1. 要提出的主要观点
    2. 需要的证据（查询知识库）
    3. 要提的问题
    """

    # 2. 使用gpt-4o-mini生成计划（成本优化）
    plan = llm.generate(prompt, model="gpt-4o-mini")

    # 3. 保存计划
    self.plans[round_number] = plan

    return plan
```

**计划结构**:
```json
{
  "round": 1,
  "main_points": [
    "强调EDL的非法拉第本质",
    "解释孔径如何控制离子可及性"
  ],
  "evidence_needed": [
    "sub-nm孔中的EDL电容数据",
    "孔径分布对性能的影响"
  ],
  "questions_to_ask": [
    "膜领域如何处理孔径效应？",
    "生物通道的选择性机制是否类似？"
  ]
}
```

**为什么需要它**:
- ✅ 智能体**有备而来** - 不是盲目发言
- ✅ 确保**聚焦讨论**
- ✅ 提前识别需要的证据
- ✅ 促进**跨领域提问**

**成本优化**:
- 使用`gpt-4o-mini`而非`gpt-4o`
- 规划任务相对简单，mini足够
- 每个计划约$0.006，全symposium约$0.10

---

#### `enhanced_agents/react_layer.py` (10,296 bytes)
**作用**: **ReAct推理模式** - 让智能体展示思考过程

**ReAct = Reasoning (推理) + Acting (行动)**

**模式**:
```
Thought: [智能体解释推理过程]
Action: [使用工具，例如 query_knowledge_base("query")]
Observation: [工具结果出现在这里]
... (根据需要重复)
Thought: [最终综合推理]
Answer: [最终贡献]
```

**核心内容**:
```python
REACT_INSTRUCTION_TEMPLATE = """
重要 - 推理格式：

响应时使用ReAct模式：

**Thought**: 解释你的推理...
**Action**: query_knowledge_base("sub-nm孔中的EDL电容")
**Observation**: [检索结果...]
**Thought**: 现在我有证据了...
**Answer**: 实际贡献内容...
"""

class ReActAgent:
    # 包装基础Agent，添加ReAct指令到role中
```

**示例**:
```
Thought: 我需要找到纳米孔中离子选择性机制的具体数据来支持我的论点。

Action: query_knowledge_base("ion selectivity mechanisms nanopore size exclusion")

Observation: [检索到："研究表明sub-5nm纳米孔表现出强烈的尺寸选择性，K+渗透性是Na+的10倍..."]

Thought: 这个证据支持我的主张。现在我应该检查是否有关于电荷选择性的信息来比较机制。

Action: query_knowledge_base("charge-based selectivity surface charge nanopores")

Observation: [检索到："表面电荷密度通过静电相互作用控制离子选择性，单价/二价离子的选择性比可达100:1..."]

Thought: 完美。我现在有了尺寸和电荷选择性的证据。我可以综合这些来解释互补机制。

Answer: 纳米孔中的离子选择性通过两种互补机制运作。首先，尺寸排阻：sub-5nm孔可以实现10:1的K+/Na+选择性...
```

**为什么需要它**:
- ✅ **透明推理** - 可以看到智能体如何思考
- ✅ **更好的调试** - 理解决策过程
- ✅ **改进科学严谨性** - 明确逻辑流程
- ✅ **促进信任** - 展示如何得出结论

---

#### `enhanced_agents/tool_manager.py` (7,128 bytes)
**作用**: **工具编排器** - 管理所有工具调用

**核心类**:
```python
class ToolManager:
    def __init__(self, domain):
        self.domain = domain
        self.tool_registry = get_global_registry()  # 获取全局工具注册表
        self.rag_integration = get_rag_integration()  # RAG工具
```

**核心方法**:

**1. get_all_openai_tools()** - 获取工具列表
```python
def get_all_openai_tools(self):
    tools = []

    # 1. RAG工具（必须包含）
    tools.append(self.rag_integration.to_openai_schema())

    # 2. Phase 4工具（领域特定）
    domain_tools = self.tool_registry.get_openai_schemas(self.domain)
    tools.extend(domain_tools)

    return tools  # 返回5个工具的OpenAI格式schema
```

**2. execute_tool_calls()** - 执行工具调用
```python
def execute_tool_calls(self, tool_calls, conversation_context):
    outputs = []
    tool_messages = []

    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        # 路由到正确的工具
        if tool_name == "query_knowledge_base":
            result = self.rag_integration.run_rag_query(
                args["query"], self.domain, args.get("top_k", 5)
            )
        else:
            # Phase 4工具
            result = self.tool_registry.execute_tool(
                tool_name, self.domain, **args
            )

        outputs.append(result)
        tool_messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        })

    return outputs, tool_messages
```

**管理的工具**:
1. **query_knowledge_base** (RAG) - 查询领域知识库
2. **solve_equation** - SymPy方程求解
3. **create_plot** - Matplotlib绘图
4. **create_concept_map** - NetworkX概念图
5. **search_recent_papers** - Semantic Scholar文献搜索

**为什么需要它**:
- ✅ **统一接口** - 所有工具通过一个管理器
- ✅ **领域隔离** - RAG查询限制在智能体的领域
- ✅ **自动路由** - 根据工具名称调用正确的实现
- ✅ **使用跟踪** - 记录工具使用统计

---

#### `enhanced_agents/rag_validator.py` (10,518 bytes)
**作用**: **RAG验证器** - 确保实质性主张有证据支持

**核心概念**: RAG-First验证
- 简单响应（致谢、同意）→ 跳过验证
- 实质性主张（数据、机制）→ 必须使用RAG

**核心类**:

**1. ResponseClassifier** - 响应分类器
```python
class ResponseClassifier:
    SIMPLE_PATTERNS = [
        r"^I agree",
        r"^Thank you",
        r"^Yes,",
        # ... 简单响应模式
    ]

    NUMERICAL_PATTERN = r'\d+\.?\d*\s*[a-zA-Z/°µ]+'  # "280 F/g"
    MECHANISM_KEYWORDS = ["because", "due to", "mechanism", ...]

    def is_simple(self, response):
        # 检查：< 50词 或 匹配简单模式

    def is_substantive(self, response):
        # 检查：> 100词 或 有数字+单位 或 机制关键词
```

**2. RAGValidator** - 验证器
```python
class RAGValidator:
    def validate_response(self, response, tool_calls_made, context):
        # 1. 分类响应
        if self.classifier.is_simple(response):
            return (True, None)  # 简单响应，无需RAG

        # 2. 检查是否实质性
        if self.classifier.is_substantive(response):
            # 检查是否使用了query_knowledge_base工具
            rag_used = any(
                tc.function.name == "query_knowledge_base"
                for tc in tool_calls_made
            )

            if not rag_used:
                # 未使用RAG，生成重试指导
                guidance = self.force_rag_retrieval(response, context)
                return (False, guidance)

        return (True, None)
```

**验证流程**:
```
响应生成
    ↓
分类: 简单 or 实质性？
    ↓
简单 → ✅ 通过
    ↓
实质性 → 检查tool_calls
    ↓
使用了RAG → ✅ 通过
    ↓
未使用RAG → ❌ 拒绝，生成重试指导
```

**为什么需要它**:
- ✅ **确保证据** - 实质性主张必须有文献支持
- ✅ **避免幻觉** - 强制智能体查询知识库
- ✅ **成本优化** - 简单响应跳过验证
- ✅ **提高质量** - 所有重要主张都有引用

**注意**: 当前验证逻辑在`unified_agent.respond()`中，但实际OpenAI调用在`orchestrator.py`，需要集成。

---

#### `enhanced_agents/memory_config.py` (5,225 bytes)
**作用**: 记忆系统配置

```python
@dataclass
class MemoryConfig:
    max_short_term: int = 10      # 短期记忆容量
    max_working_memory: int = 50  # 工作记忆容量
    embedding_model: str = "text-embedding-3-small"
    similarity_threshold: float = 0.7
    ...

DEFAULT_MEMORY_CONFIG = MemoryConfig()
MEMORY_COLLECTION_NAMES = {...}  # 集合名称映射
```

---

#### `enhanced_agents/plan_templates.py` (9,435 bytes)
**作用**: 规划提示模板

包含针对不同回合的规划提示模板，指导智能体如何制定计划。

---

#### `enhanced_agents/react_parser.py` (11,612 bytes)
**作用**: 解析ReAct格式响应

从智能体响应中提取Thought、Action、Observation、Answer组件。

---

### 🧰 模块4: tools/ - 工具系统 (46 KB)

#### `tools/tool_registry.py` (7,160 bytes)
**作用**: **工具注册中心** - 管理所有Phase 4工具

**核心类**:
```python
class Tool(ABC):
    """工具基类"""
    def __init__(self, metadata: ToolMetadata):
        self.metadata = metadata

    @abstractmethod
    def execute(self, domain: str, **kwargs) -> str:
        """执行工具"""

    @abstractmethod
    def to_openai_schema(self) -> Dict:
        """转换为OpenAI Function Calling格式"""

class ToolRegistry:
    """工具注册表"""
    def __init__(self):
        self.tools = {}
        self.domain_tools = defaultdict(set)

    def register(self, tool: Tool, domains: List[str]):
        """注册工具到特定领域"""

    def get_tools_for_domain(self, domain: str) -> List[Tool]:
        """获取领域的所有工具"""

    def get_openai_schemas(self, domain: str) -> List[Dict]:
        """获取OpenAI格式的工具schema"""

    def execute_tool(self, tool_name: str, domain: str, **kwargs) -> str:
        """执行工具调用"""
```

**全局注册函数**:
```python
def register_default_tools() -> ToolRegistry:
    """注册所有Phase 4工具到所有领域"""
    registry = ToolRegistry()

    all_domains = ["electrochemistry", "membrane_science",
                   "biology", "nanofluidics"]

    # 注册工具
    registry.register(WebSearchTool(), all_domains)
    registry.register(EquationSolverTool(), all_domains)
    registry.register(PlottingTool(), all_domains)
    registry.register(ConceptMapperTool(), all_domains)

    return registry
```

---

#### `tools/web_search_tool.py` (7,794 bytes)
**作用**: Semantic Scholar学术搜索

**功能**:
```python
class WebSearchTool(Tool):
    def execute(self, domain, query, year_range="2020-", max_results=5):
        # 1. 调用Semantic Scholar API
        # 2. 搜索最新论文
        # 3. 返回格式化结果（标题、作者、年份、引用数、摘要）

    def to_openai_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "search_recent_papers",
                "description": "Search recent scientific papers using Semantic Scholar",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "year_range": {"type": "string", "default": "2020-"},
                        "max_results": {"type": "integer", "default": 5}
                    },
                    "required": ["query"]
                }
            }
        }
```

**使用场景**: 查找最新研究进展

---

#### `tools/equation_solver_tool.py` (8,801 bytes)
**作用**: SymPy方程求解器

**功能**:
```python
class EquationSolverTool(Tool):
    def execute(self, domain, operation, expression, variable=None, **kwargs):
        # 支持的操作:
        # - solve: 求解方程
        # - differentiate: 求导
        # - integrate: 积分
        # - simplify: 化简
        # - expand: 展开
        # - factor: 因式分解

        # 使用SymPy执行符号数学运算
```

**使用场景**: 推导数学关系、验证方程

---

#### `tools/plotting_tool.py` (10,596 bytes)
**作用**: Matplotlib数据可视化

**功能**:
```python
class PlottingTool(Tool):
    def execute(self, domain, plot_type, data, title, xlabel, ylabel, **kwargs):
        # 支持的图表类型:
        # - line: 折线图
        # - bar: 柱状图
        # - scatter: 散点图
        # - histogram: 直方图

        # 1. 生成图表
        # 2. 保存到results/plots/
        # 3. 返回文件路径
```

**使用场景**: 可视化数据趋势、比较不同系统

---

#### `tools/concept_mapper_tool.py` (10,410 bytes)
**作用**: NetworkX概念关系图

**功能**:
```python
class ConceptMapperTool(Tool):
    def execute(self, domain, concepts, relationships, layout="spring", **kwargs):
        # 1. 创建NetworkX图
        # 2. 添加节点（concepts）
        # 3. 添加边（relationships）
        # 4. 使用指定布局算法
        # 5. 保存图像
        # 6. 返回文件路径
```

**使用场景**: 绘制概念关系、理论框架结构

---

#### `tools/__init__.py` (839 bytes)
**作用**: 导出工具

```python
from tools.tool_registry import ToolRegistry, Tool, get_global_registry, register_default_tools
from tools.web_search_tool import WebSearchTool
from tools.equation_solver_tool import EquationSolverTool
from tools.plotting_tool import PlottingTool
from tools.concept_mapper_tool import ConceptMapperTool
```

---

### 📚 模块5: knowledge_base/ - 知识库系统 (96 KB)

#### `knowledge_base/query_rag.py` (9,573 bytes)
**作用**: **RAG查询引擎** - 核心检索功能

**核心类**:
```python
class MultiDomainRAGEngine:
    def __init__(self, persist_directory="data/vector_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        # 领域到集合的映射
        self.domain_collections = {
            "electrochemistry": "electrochemistry_papers",
            "membrane_science": "membrane_science_papers",
            "biology": "biology_papers",
            "nanofluidics": "nanofluidics_papers"
        }

    def query_domain(self, query, domain, top_k=5):
        """查询特定领域的知识库"""
        collection_name = self.domain_collections[domain]
        return self.query_collection(query, collection_name, top_k)

    def query_collection(self, query, collection_name, top_k=5):
        """查询ChromaDB集合"""
        # 1. 生成查询embedding
        query_embedding = self.embeddings.embed_query(query)

        # 2. 向量相似度搜索
        collection = self.client.get_collection(collection_name)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        # 3. 格式化结果（含引用）
        return self._format_results(results)
```

**辅助函数**:
```python
def get_context_for_agent(query, domain, top_k=5):
    """便捷函数：获取智能体的上下文"""
    engine = MultiDomainRAGEngine()
    return engine.query_domain(query, domain, top_k)
```

**检索流程**:
```
查询: "EDL capacitance in sub-nm pores"
    ↓
生成embedding (OpenAI text-embedding-3-small)
    ↓
在electrochemistry_papers集合中搜索
    ↓
返回top-5最相关文档片段
    ↓
格式化: [Doc 1] ... [Citation: Author et al., Journal, Year]
```

**被谁调用**:
- `rag_tool.py` - RAG工具接口
- `enhanced_agents/rag_validator.py` - 强制RAG检索

---

#### `knowledge_base/ingest_papers.py` (33,829 bytes)
**作用**: **文献摄取管道** - 将PDF转为向量数据库

**功能**:
1. **PDF解析**: PyMuPDF提取文本和图像
2. **多模态处理**:
   - 文本分块（LangChain RecursiveCharacterTextSplitter）
   - 图像提取和分析
   - 方程识别
3. **Embedding生成**: OpenAI text-embedding-3-small
4. **存储**: ChromaDB持久化

**关键流程**:
```python
def ingest_papers_for_domain(domain, papers_dir, vector_db_dir):
    # 1. 扫描papers_dir中的PDF
    # 2. 对每个PDF:
    #    - 提取文本
    #    - 分块（chunk_size=1000, overlap=200）
    #    - 生成embedding
    #    - 存入domain对应的collection
    # 3. 显示进度条
```

**数据来源**: `data/papers/{domain}/` 中的PDF文件

**被谁调用**:
- 手动运行（初始化或更新知识库时）
- `ingest_papers.sh` - bash脚本

---

#### `knowledge_base/multimodal_extractor.py` (19,822 bytes)
**作用**: 多模态内容提取（文本+图像+方程）

**功能**:
- 提取论文中的图表
- 识别和提取方程
- 分析图像内容

---

#### `knowledge_base/equation_extractor.py` (13,488 bytes)
**作用**: LaTeX方程提取和解析

---

#### `knowledge_base/panel_segmentation.py` (11,816 bytes)
**作用**: 分割和分析论文中的多面板图

---

#### `knowledge_base/multimodal_embeddings.py` (6,162 bytes)
**作用**: 多模态内容的embedding生成

---

#### `knowledge_base/__init__.py` (937 bytes)
**作用**: 导出知识库函数

```python
from knowledge_base.query_rag import (
    MultiDomainRAGEngine,
    query_papers,
    get_context_for_agent
)
```

---

### 💬 模块6: prompts/ - 讨论提示 (10 KB)

#### `prompts/detailed_prompts.py` (10,306 bytes)
**作用**: **定义4轮讨论的议程和问题**

**内容**:

**Round 1: 绘制理论全景图**
```python
ROUND_1_DETAILED_AGENDA = """
每个专家介绍其领域的离子传输理论方法。
识别核心概念、数学框架和实验方法。
"""

ROUND_1_QUESTIONS = [
    "你的领域如何定量描述离子传输？",
    "关键控制参数是什么？",
    "主要挑战在哪里？",
    ...
]
```

**Round 2: 识别统一原则**
```python
ROUND_2_DETAILED_AGENDA = """
测试跨领域类比。
寻找共同数学框架。
识别可能的桥梁概念。
"""

ROUND_2_QUESTIONS = [
    "EDL和Donnan势之间的类比有多深？",
    "选择性的共同原则是什么？",
    ...
]
```

**Round 3: 构建统一框架**
```python
ROUND_3_DETAILED_AGENDA = """
定义核心理论框架。
明确共同核心和领域特定扩展。
建立跨领域术语映射。
"""

ROUND_3_QUESTIONS = [
    "统一框架的最小核心是什么？",
    "如何处理边界条件差异？",
    ...
]
```

**Round 4: 应用与未来方向**
```python
ROUND_4_DETAILED_AGENDA = """
讨论跨领域应用。
识别可借鉴的技术。
规划未来研究方向。
"""

ROUND_4_QUESTIONS = [
    "你的领域可以从其他领域借鉴什么技术？",
    "统一框架如何指导新材料设计？",
    ...
]
```

**讨论规则**:
```python
RIGOROUS_DISCUSSION_RULES = """
1. 所有定量主张必须有文献支持
2. 明确说明假设和限制
3. 识别知识空白
4. 尊重但批判性地评估他人论点
...
"""
```

**被谁调用**:
- `run_full_symposium.py` - 为每轮提供议程

---

### 📊 模块7: 数据存储

#### `data/vector_db/` (177 MB)
**作用**: ChromaDB向量数据库

**结构**:
```
data/vector_db/
├── chroma.sqlite3 (177 MB)  # SQLite数据库
└── [ChromaDB内部文件]
```

**包含的集合**:
- `electrochemistry_papers`: 6,478 documents
- `membrane_science_papers`: 4,026 documents
- `biology_papers`: 534 documents
- `nanofluidics_papers`: 6,725 documents

**总计**: 17,763 研究论文片段

---

#### `data/memory_db/` (动态生成)
**作用**: 智能体记忆存储

每个智能体有独立的ChromaDB集合：
```
{domain}_agent_memory/
```

存储内容：
- 每轮讨论的关键见解
- 元数据（回合编号、symposium_id、时间戳）

---

#### `data/papers/` (原始PDF)
**作用**: 源论文PDF文件

```
data/papers/
├── electrochemistry/
├── membrane_science/
├── biology/
└── nanofluidics/
```

---

#### `results/` (输出结果)
**作用**: Symposium讨论记录和导出数据

```
results/full_symposium/
├── round_1_landscape/
│   ├── round1_discussion.md        # Markdown格式讨论记录
│   ├── round1_discussion.json      # JSON格式结构化数据
│   └── round1_discussion_summary.txt  # AI生成的总结
├── round_2_principles/
├── round_3_framework/
├── round_4_applications/
└── agent_data/
    ├── electrochemistry_plans.json    # 智能体的所有计划
    ├── electrochemistry_stats.json    # 工具使用统计
    ├── membrane_science_plans.json
    └── ... (其他专家)
```

---

## 数据流程

### 完整Symposium执行流程

```
1. 初始化阶段
   用户运行: python run_full_symposium.py --yes
       ↓
   create_unified_agents() 创建4个UnifiedAgent
       ↓
   每个UnifiedAgent初始化:
       - 加载base_agent (从detailed_agents.py)
       - 创建AgentMemory (连接ChromaDB)
       - 创建AgentPlanner (使用gpt-4o-mini)
       - 创建ToolManager (注册5个工具)
       - 创建RAGValidator

2. Round 1 开始
   ↓
   准备阶段:
   for each agent in unified_agents:
       agent.prepare_for_round(1, ROUND_1_AGENDA, ROUND_1_QUESTIONS, None)
           ↓
           memory.recall_relevant(ROUND_1_AGENDA, top_k=3)
               → 查询memory_db (首次为空)
           ↓
           planner.create_contribution_plan(...)
               → 调用gpt-4o-mini生成计划
               → 保存计划
           ↓
           返回enhanced_agenda (含计划和记忆)
   ↓
   讨论阶段:
   run_meeting(
       team_lead=SYMPOSIUM_PI,
       team_members=(4个UnifiedAgent + CRITIC),
       agenda=ROUND_1_AGENDA,
       num_rounds=2
   )
       ↓
       for round in range(2):  # 2轮讨论
           for agent in team_members:
               1. 准备消息: [agent.message] + conversation_history
               2. 调用OpenAI API:
                  - model: agent.model (gpt-4o)
                  - tools: agent.openai_tools (5个工具)
               3. 获取响应
               4. 如果有tool_calls:
                  - agent.tool_manager.execute_tool_calls(tool_calls)
                  - 例如: query_knowledge_base("EDL capacitance")
                      → rag_tool.run_rag_query(...)
                      → knowledge_base.query_rag.get_context_for_agent(...)
                      → ChromaDB.query(electrochemistry_papers)
                      → 返回top-5相关文档
                  - 将工具结果添加到对话
                  - 再次调用OpenAI获取最终响应
               5. 记录到conversation_history
       ↓
       保存讨论记录:
       - round_1_landscape/round1_discussion.md
       - round_1_landscape/round1_discussion.json
       ↓
       生成总结 (使用gpt-4o-mini):
       - round_1_landscape/round1_discussion_summary.txt
       ↓
       返回round1_summary
   ↓
   巩固阶段:
   for each agent in unified_agents:
       agent.consolidate_round(1, round1_summary)
           ↓
           memory.consolidate_memories(1, round1_summary)
               → 调用gpt-4o-mini提取3-5个关键见解
               → 存入memory_db/{domain}_agent_memory
               → 元数据: {round: 1, symposium_id: "xxx"}

3. Round 2-4
   重复类似流程，但有累积效应:
       ↓
   prepare_for_round():
       - memory.recall_relevant() 现在能找到Round 1的见解
       - planner使用previous_summary和memories制定计划
       ↓
   讨论中智能体可以引用:
       - 过去的讨论 (从记忆中)
       - 知识库文献 (从RAG)
       - 工具结果 (方程、图表)

4. Symposium结束
   ↓
   导出数据:
   for each agent in unified_agents:
       agent.export_agent_data("results/agent_data/")
           → 保存所有计划: {domain}_plans.json
           → 保存统计信息: {domain}_stats.json
   ↓
   提升记忆:
   for each agent in unified_agents:
       agent.promote_to_long_term_memory()
           → 标记memory_db中的记忆为long_term
           → 下次symposium可以检索
   ↓
   完成！
```

### RAG查询详细流程

```
智能体决定: "我需要查询EDL电容的数据"
    ↓
生成tool_call:
{
  "function": "query_knowledge_base",
  "arguments": {
    "query": "EDL capacitance in sub-nm pores",
    "top_k": 5
  }
}
    ↓
orchestrator.py 检测到tool_call
    ↓
调用: agent.tool_manager.execute_tool_calls([tool_call])
    ↓
tool_manager识别: tool_name == "query_knowledge_base"
    ↓
调用: rag_integration.run_rag_query(
    query="EDL capacitance in sub-nm pores",
    domain=agent.domain,  # "electrochemistry"
    top_k=5
)
    ↓
rag_tool.py → knowledge_base/query_rag.py
    ↓
MultiDomainRAGEngine.query_domain("...", "electrochemistry", 5)
    ↓
1. embeddings.embed_query("EDL capacitance in sub-nm pores")
   → 调用OpenAI API (text-embedding-3-small)
   → 返回768维向量
    ↓
2. collection = chroma_client.get_collection("electrochemistry_papers")
    ↓
3. results = collection.query(
    query_embeddings=[embedding_vector],
    n_results=5
)
   → ChromaDB执行向量相似度搜索
   → 在6,478个文档中找到最相似的5个
    ↓
4. 格式化结果:
"""
[Document 1]
研究表明，在sub-nanometer孔中，EDL电容可达280 F/g...
[Citation: Chmiola et al., Science, 2006, 引用: 2847次]

[Document 2]
...

[Document 3]
...
"""
    ↓
返回给tool_manager
    ↓
tool_manager构建tool_message:
{
  "role": "tool",
  "tool_call_id": "call_xxx",
  "content": "[检索到的文档...]"
}
    ↓
添加到conversation_history
    ↓
orchestrator再次调用OpenAI API (带tool_message)
    ↓
智能体看到检索结果，生成响应:
"基于文献，sub-nm孔中的EDL电容可达280 F/g (Chmiola et al., 2006)..."
```

---

## 运行机制

### 启动Symposium

**步骤1: 设置环境**
```bash
cd "/path/to/ion_transport"
export PYTHONPATH="$(pwd):$PYTHONPATH"
export OPENAI_API_KEY="your-key"
```

**步骤2: 运行**
```bash
python run_full_symposium.py --yes
```

**步骤3: 发生了什么**
```
1. 加载配置
   - constants.py: DEFAULT_MODEL = "gpt-4o"
   - 所有模块

2. 创建智能体
   create_unified_agents() 创建4个UnifiedAgent:
   - electrochemistry (ELECTROCHEMISTRY_EXPERT + 增强层)
   - membrane_science (MEMBRANE_SCIENCE_EXPERT + 增强层)
   - biology (BIOLOGY_EXPERT + 增强层)
   - nanofluidics (NANOFLUIDICS_EXPERT + 增强层)

3. Round 1 (预计5-8分钟)
   - 准备: 4个智能体各生成计划 (4 × gpt-4o-mini调用)
   - 讨论: 2轮 × 5个智能体 = 10次OpenAI调用
     - 每次可能触发1-3次工具调用
     - RAG查询: 约10-15次
   - 巩固: 4个智能体提取见解 (4 × gpt-4o-mini调用)
   - 总结: 1次gpt-4o-mini调用

   成本: 约$0.80

4. Round 2 (预计6-10分钟)
   - 3轮讨论
   - 更多工具使用（因为有记忆和计划）

   成本: 约$1.00

5. Round 3 (预计7-12分钟)
   - 4轮讨论
   - 最复杂的综合阶段

   成本: 约$1.20

6. Round 4 (预计4-7分钟)
   - 3轮讨论
   - 应用和未来方向

   成本: 约$0.80

7. 导出和保存
   - 保存所有讨论记录
   - 导出智能体数据
   - 提升记忆为长期存储

总耗时: 15-25分钟
总成本: $3.20-$4.00
```

### 成本分解

```
OpenAI API调用成本估算:

1. 主要讨论 (gpt-4o):
   - Round 1: 2轮 × 5智能体 = 10次调用
   - Round 2: 3轮 × 5智能体 = 15次调用
   - Round 3: 4轮 × 5智能体 = 20次调用
   - Round 4: 3轮 × 5智能体 = 15次调用
   总计: 60次主调用

   平均每次:
   - 输入: ~2000 tokens (上下文)
   - 输出: ~500 tokens (响应)

   成本: 60 × (2000×$0.0025 + 500×$0.01) / 1M
        ≈ $0.60 输入 + $0.30 输出 = $0.90

   但考虑工具调用后的follow-up:
   实际成本: ~$2.50

2. RAG查询 (text-embedding-3-small):
   - 约40-60次RAG查询
   - 每次embedding: ~20 tokens
   成本: 60 × 20 × $0.00002 / 1K ≈ $0.024

   但embedding在knowledge_base查询中:
   实际成本: ~$0.50 (含多次查询)

3. 规划 (gpt-4o-mini):
   - 4轮 × 4智能体 = 16次计划生成
   - 平均每次: 输入1000, 输出300 tokens
   成本: 16 × (1000×$0.00015 + 300×$0.0006) / 1K
        ≈ $0.002 + $0.003 = $0.005
   实际: ~$0.10 (含其他mini调用)

4. 记忆巩固 (gpt-4o-mini):
   - 4轮 × 4智能体 = 16次巩固
   成本: ~$0.05

5. 总结生成 (gpt-4o-mini):
   - 4轮总结
   成本: ~$0.05

总计: $2.50 + $0.50 + $0.10 + $0.05 + $0.05 = $3.20
加上额外工具调用和重试: $3.20 - $4.00
```

---

## 总结

### 核心文件优先级

**必须理解的核心文件** (8个):
1. `base_agent.py` - Agent基类
2. `constants.py` - 配置
3. `orchestrator.py` - 讨论编排
4. `agents/detailed_agents.py` - 6个智能体定义
5. `enhanced_agents/unified_agent.py` - 统一包装器
6. `enhanced_agents/memory_system.py` - 记忆系统
7. `knowledge_base/query_rag.py` - RAG查询
8. `run_full_symposium.py` - 主程序

**重要的增强文件** (4个):
9. `enhanced_agents/planning_system.py` - 规划
10. `enhanced_agents/tool_manager.py` - 工具管理
11. `enhanced_agents/rag_validator.py` - RAG验证
12. `prompts/detailed_prompts.py` - 讨论议程

**辅助文件** (其余):
- ReAct层、工具实现、知识库摄取等

---

### 设计理念

**1. 模块化**
- 每个功能独立模块
- 清晰的接口
- 易于测试和维护

**2. 增强层次**
```
基础Agent
    ↓ 包装
ReActAgent (推理)
    ↓ 包装
+ AgentMemory (记忆)
    ↓ 包装
+ AgentPlanner (规划)
    ↓ 包装
+ ToolManager (工具)
    ↓ 集成
UnifiedAgent (all-in-one)
```

**3. 领域隔离**
- 每个专家有独立知识库
- 防止知识交叉污染
- 保持专业性

**4. 成本优化**
- 主讨论: gpt-4o (质量)
- 规划/总结: gpt-4o-mini (成本)
- RAG: 减少LLM调用

**5. 可扩展性**
- 新工具: 实现Tool接口 → 注册
- 新智能体: 创建Agent → 包装为UnifiedAgent
- 新领域: 添加知识库 → 更新映射

---

### 项目统计

**代码规模**:
- Python文件: 34个
- 代码量: ~303 KB
- 行数: ~10,000行

**知识库**:
- 论文数量: 17,763篇
- 数据库大小: 177 MB
- 4个领域集合

**功能**:
- 6个AI智能体
- 5个工具（RAG + 4个Phase 4）
- 4层记忆系统
- 4轮渐进式讨论

**性能**:
- 运行时间: 15-25分钟
- 成本: $3.20-$4.00
- API调用: ~100次

---

**这就是完整的项目架构！** 🎉

每个文件都有其明确的职责，协同工作构建一个强大的多智能体科学讨论系统。
