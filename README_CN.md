# Ion Transport Virtual Lab

**离子传输虚拟实验室** - 基于AI的多代理科学研讨系统

An AI-powered multi-agent symposium system for collaborative research on ion transport mechanisms across multiple scientific domains.

---

## 🎯 项目概述 | Overview

本项目实现了一个由6个AI代理组成的虚拟科学研讨会，通过4轮深入讨论探索离子传输的跨学科统一理论：

- **4个领域专家**: 电化学、膜科学、生物学、纳米流体学
- **1个研讨会主席** (PI): 引导讨论方向
- **1个科学评论家**: 提供批判性反馈

This project implements a virtual scientific symposium with 6 AI agents conducting 4 rounds of in-depth discussions to explore unified theories of ion transport across disciplines:

- **4 Domain Experts**: Electrochemistry, Membrane Science, Biology, Nanofluidics
- **1 Symposium Chair** (PI): Guides discussion direction
- **1 Scientific Critic**: Provides critical feedback

---

## ✨ 核心特性 | Key Features

### 🤖 Validated Agentic RAG (验证式代理RAG)
- 代理通过推理自主决定何时检索知识库
- 实质性科学声明自动验证是否有证据支持
- 17,763篇研究论文支持的领域隔离知识库

### 🧠 增强型代理能力
- ✅ **ReAct推理**: 明确的思考→行动→观察→回答流程
- ✅ **持久记忆**: 跨研讨会轮次的学习和记忆
- ✅ **战略规划**: 每轮讨论前的策略制定
- ✅ **Phase 4工具**: 方程求解、绘图、概念图、网络搜索
- ✅ **RAG验证**: 确保证据支持的回复

### 🔬 科学严谨性
- 领域隔离的知识库（防止跨领域污染）
- 强制引用来源
- 智能成本优化（简单回复跳过验证）

---

## 📋 系统要求 | Requirements

### 环境依赖
- Python 3.8+
- OpenAI API key (gpt-4o model access)
- 至少2GB可用内存 (向量数据库177MB)

### 主要依赖包
```
openai >= 2.0.0
chromadb >= 1.4.0
langchain >= 1.2.0
langchain-openai
langchain-community
pymupdf
matplotlib
networkx
sympy
```

---

## 🚀 快速开始 | Quick Start

### 1. 安装依赖

```bash
# 克隆项目
cd ion_transport

# 安装依赖
pip install -r requirements.txt

# 安装项目（可编辑模式）
pip install -e .
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入你的OpenAI API密钥
# OPENAI_API_KEY=sk-proj-your-actual-key-here
```

或直接在终端设置：
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### 3. 运行研讨会

```bash
# 设置Python路径
export PYTHONPATH="$(pwd):$PYTHONPATH"

# 运行完整4轮研讨会
python run_full_symposium.py --yes
```

### 4. 查看结果

研讨会结果保存在 `results/full_symposium/` 目录：
```
results/full_symposium/
├── round_1_landscape/
│   ├── round1_discussion.md          # 讨论记录
│   ├── round1_discussion.json        # JSON格式
│   └── round1_discussion_summary.txt # 摘要
├── round_2_principles/
├── round_3_framework/
├── round_4_applications/
└── agent_data/                        # 代理数据（计划、统计）
```

---

## 💰 成本估算 | Cost Estimates

运行一次完整4轮研讨会的预计成本：

- **LLM调用** (gpt-4o): ~$2.50
- **RAG查询**: ~$0.50
- **战略规划** (gpt-4o-mini): ~$0.10
- **记忆整合**: ~$0.05
- **工具使用**: $0.00 (本地计算)

**总计**: **$3.20 - $4.00** / 每次研讨会

**预计时间**: 15-25分钟

---

## 📁 项目架构 | Architecture

```
ion_transport/
├── agents/                    # 代理系统
│   ├── base_agent.py         # 基础代理类
│   ├── constants.py          # 配置常量
│   ├── agent_definitions.py  # 6个代理定义
│   ├── prompts.py            # 讨论议程
│   └── enhancements/         # 增强功能
│       ├── unified_agent.py  # 统一代理封装
│       ├── memory_system.py  # 记忆系统
│       ├── planning_system.py # 规划系统
│       ├── tool_manager.py   # 工具管理
│       └── rag_validator.py  # RAG验证
│
├── tools/                     # 工具系统
│   ├── rag_tool.py           # RAG集成
│   ├── web_search_tool.py    # 网络搜索
│   ├── equation_solver_tool.py # 方程求解
│   ├── plotting_tool.py      # 数据可视化
│   └── concept_mapper_tool.py # 概念映射
│
├── knowledge_base/            # 知识库系统
│   ├── ingest_papers.py      # 论文导入
│   ├── query_rag.py          # RAG查询
│   └── multimodal_*.py       # 多模态提取
│
├── data/
│   └── vector_db/            # ChromaDB向量数据库 (177MB)
│       └── 17,763 documents from 200+ papers
│
├── orchestrator.py           # 研讨会协调器
└── run_full_symposium.py     # 主程序入口
```

### 详细架构说明

- 📖 **[完整架构文档](PROJECT_ARCHITECTURE_CN.md)** - 500+行详细说明（中文）
- 📊 **[系统状态报告](SYSTEM_STATUS.md)** - 运行指南和故障排除

---

## 🎓 研讨会流程 | Symposium Workflow

### Round 1: 地图绘制 (2轮发言)
- 各领域专家介绍本领域的离子传输现象
- 识别关键机制和挑战

### Round 2: 统一原理 (3轮发言)
- 寻找跨领域的共同原理
- 比较不同系统的选择性机制

### Round 3: 统一框架 (4轮发言)
- 构建整合多领域见解的理论框架
- 开发预测模型

### Round 4: 应用与未来 (3轮发言)
- 讨论实际应用
- 确定未来研究方向

---

## 📊 知识库 | Knowledge Base

### 向量数据库统计
- **总文档数**: 17,763个文档片段
- **数据库大小**: 176.80 MB
- **来源**: 200+篇高质量研究论文

### 领域分布
- **电化学**: 6,478 documents
- **膜科学**: 4,026 documents
- **生物学**: 534 documents
- **纳米流体学**: 6,725 documents

---

## 🔧 高级使用 | Advanced Usage

### 创建自定义代理

```python
from agents import Agent, UnifiedAgent

# 定义基础代理
custom_agent = Agent(
    title="Custom Expert",
    expertise="Your expertise description",
    goal="Your goal",
    role="Your role instructions",
    model="gpt-4o"
)

# 封装为增强型代理
enhanced_agent = UnifiedAgent(
    base_agent=custom_agent,
    domain="your_domain",
    symposium_id="custom_symposium"
)
```

### 自定义讨论议程

```python
from orchestrator import run_meeting
from agents import CUSTOM_AGENT

# 运行自定义讨论
summary = run_meeting(
    team_lead=PI,
    team_members=(CUSTOM_AGENT,),
    agenda="Your custom agenda",
    num_rounds=3,
    save_dir="results/custom_meeting"
)
```

---

## 🐛 故障排除 | Troubleshooting

### 导入错误
```bash
# 确保PYTHONPATH正确设置
export PYTHONPATH="$(pwd):$PYTHONPATH"

# 重新安装包
pip install -e .
```

### API认证失败
```bash
# 检查API密钥是否设置
echo $OPENAI_API_KEY

# 测试API密钥有效性
python -c "import openai; client = openai.OpenAI(); print('API key valid')"
```

### 内存不足
- 向量数据库较大(177MB)，确保至少2GB可用内存
- 可以考虑减少每次RAG查询的top_k值（默认5）

---

## 📄 许可证 | License

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 📚 引用 | Citation

如果您在研究中使用本项目，请引用：

```bibtex
@software{ion_transport_virtual_lab,
  title = {Ion Transport Virtual Lab: AI-Powered Multi-Agent Symposium System},
  author = {Your Name},
  year = {2026},
  url = {https://github.com/yourusername/ion_transport}
}
```

---

## 🤝 贡献 | Contributing

欢迎贡献！请遵循以下步骤：

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 📞 联系方式 | Contact

- **项目维护者**: Dr. Xiaoyang Du
- **邮箱**: kexiaoyangdu@ust.hk
- **机构**: Prof. Dan Li's Group at HKUST (香港科技大学)

---

## 🙏 致谢 | Acknowledgments

- OpenAI for GPT-4o model
- ChromaDB for vector database
- LangChain for RAG framework
- 所有贡献的研究论文作者

---

**Last Updated**: January 10, 2026
**Version**: 0.4.0 - Unified Agent with Validated Agentic RAG
