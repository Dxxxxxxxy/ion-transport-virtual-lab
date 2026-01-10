# Ion Transport Virtual Lab

**AI-Powered Multi-Agent Symposium System for Collaborative Research**

An advanced multi-agent framework enabling collaborative scientific research on ion transport mechanisms across electrochemistry, membrane science, biology, and nanofluidics domains.

[中文版](README_CN.md) | English

---

## 🎯 Overview

This project implements a virtual scientific symposium with 6 AI agents conducting 4 rounds of in-depth discussions to explore unified theories of ion transport across multiple disciplines:

- **4 Domain Experts**: Electrochemistry, Membrane Science, Biology, Nanofluidics
- **1 Symposium Chair** (PI): Guides discussion direction
- **1 Scientific Critic**: Provides critical feedback

---

## ✨ Key Features

### 🤖 Validated Agentic RAG
- Agents autonomously decide when to retrieve from knowledge bases through reasoning
- Automatic validation that substantive scientific claims are evidence-backed
- Domain-isolated knowledge bases with 17,763 research paper chunks
- Mandatory citations with source attribution

### 🧠 Enhanced Agent Capabilities
- ✅ **ReAct Reasoning**: Explicit Thought → Action → Observation → Answer flow
- ✅ **Persistent Memory**: Cross-round learning and retention
- ✅ **Strategic Planning**: Pre-discussion strategy formulation
- ✅ **Phase 4 Tools**: Equation solving, plotting, concept mapping, web search
- ✅ **RAG Validation**: Ensures evidence-supported responses

### 🔬 Scientific Rigor
- Domain-isolated knowledge bases (prevents cross-field contamination)
- Mandatory source citations
- Intelligent cost optimization (skips validation for simple responses)

---

## 📋 Requirements

### Environment
- Python 3.8+
- OpenAI API key (gpt-4o model access)
- At least 2GB available memory (vector database: 177MB)

### Dependencies
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

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Navigate to project directory
cd ion_transport

# Install dependencies
pip install -r requirements.txt

# Install package in editable mode
pip install -e .
```

### 2. Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env file and add your OpenAI API key
# OPENAI_API_KEY=sk-proj-your-actual-key-here
```

Or set directly in terminal:
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### 3. Run Symposium

```bash
# Set Python path
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Run full 4-round symposium
python run_full_symposium.py --yes
```

### 4. View Results

Symposium results are saved in `results/full_symposium/`:
```
results/full_symposium/
├── round_1_landscape/
│   ├── round1_discussion.md          # Discussion transcript
│   ├── round1_discussion.json        # JSON format
│   └── round1_discussion_summary.txt # Summary
├── round_2_principles/
├── round_3_framework/
├── round_4_applications/
└── agent_data/                        # Agent data (plans, statistics)
```

---

## 💰 Cost Estimates

Estimated cost for one complete 4-round symposium:

- **LLM Calls** (gpt-4o): ~$2.50
- **RAG Queries**: ~$0.50
- **Strategic Planning** (gpt-4o-mini): ~$0.10
- **Memory Integration**: ~$0.05
- **Tool Usage**: $0.00 (local computation)

**Total**: **$3.20 - $4.00** per symposium

**Estimated Time**: 15-25 minutes

---

## 📁 Project Architecture

```
ion_transport/
├── agents/                    # Agent system
│   ├── base_agent.py         # Base agent class
│   ├── constants.py          # Configuration constants
│   ├── agent_definitions.py  # 6 agent definitions
│   ├── prompts.py            # Discussion agendas
│   └── enhancements/         # Enhancement features
│       ├── unified_agent.py  # Unified agent wrapper
│       ├── memory_system.py  # Memory system
│       ├── planning_system.py # Planning system
│       ├── tool_manager.py   # Tool management
│       └── rag_validator.py  # RAG validation
│
├── tools/                     # Tool system
│   ├── rag_tool.py           # RAG integration
│   ├── web_search_tool.py    # Web search
│   ├── equation_solver_tool.py # Equation solving
│   ├── plotting_tool.py      # Data visualization
│   └── concept_mapper_tool.py # Concept mapping
│
├── knowledge_base/            # Knowledge base system
│   ├── ingest_papers.py      # Paper ingestion
│   ├── query_rag.py          # RAG queries
│   └── multimodal_*.py       # Multimodal extraction
│
├── data/
│   └── vector_db/            # ChromaDB vector database (177MB)
│       └── 17,763 documents from 200+ papers
│
├── orchestrator.py           # Symposium coordinator
└── run_full_symposium.py     # Main program entry
```

### Detailed Documentation

- 📖 **[Full Architecture Guide](PROJECT_ARCHITECTURE_CN.md)** - 500+ lines detailed documentation (Chinese)
- 📊 **[System Status Report](SYSTEM_STATUS.md)** - Running guide and troubleshooting

---

## 🎓 Symposium Workflow

### Round 1: Landscape Mapping (2 speaking rounds)
- Domain experts introduce ion transport phenomena in their fields
- Identify key mechanisms and challenges

### Round 2: Unifying Principles (3 speaking rounds)
- Search for common principles across domains
- Compare selectivity mechanisms across different systems

### Round 3: Unified Framework (4 speaking rounds)
- Build theoretical framework integrating multi-domain insights
- Develop predictive models

### Round 4: Applications & Future Directions (3 speaking rounds)
- Discuss practical applications
- Identify future research directions

---

## 📊 Knowledge Base

### Vector Database Statistics
- **Total Documents**: 17,763 document chunks
- **Database Size**: 176.80 MB
- **Source**: 200+ high-quality research papers

### Domain Distribution
- **Electrochemistry**: 6,478 documents
- **Membrane Science**: 4,026 documents
- **Biology**: 534 documents
- **Nanofluidics**: 6,725 documents

---

## 🔧 Advanced Usage

### Create Custom Agents

```python
from agents import Agent, UnifiedAgent

# Define base agent
custom_agent = Agent(
    title="Custom Expert",
    expertise="Your expertise description",
    goal="Your goal",
    role="Your role instructions",
    model="gpt-4o"
)

# Wrap as enhanced agent
enhanced_agent = UnifiedAgent(
    base_agent=custom_agent,
    domain="your_domain",
    symposium_id="custom_symposium"
)
```

### Custom Discussion Agenda

```python
from orchestrator import run_meeting
from agents import CUSTOM_AGENT

# Run custom discussion
summary = run_meeting(
    team_lead=PI,
    team_members=(CUSTOM_AGENT,),
    agenda="Your custom agenda",
    num_rounds=3,
    save_dir="results/custom_meeting"
)
```

---

## 🐛 Troubleshooting

### Import Errors
```bash
# Ensure PYTHONPATH is set correctly
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Reinstall package
pip install -e .
```

### API Authentication Failure
```bash
# Check if API key is set
echo $OPENAI_API_KEY

# Test API key validity
python -c "import openai; client = openai.OpenAI(); print('API key valid')"
```

### Out of Memory
- Vector database is large (177MB), ensure at least 2GB available memory
- Consider reducing top_k value in RAG queries (default: 5)

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 📚 Citation

If you use this project in your research, please cite:

```bibtex
@software{ion_transport_virtual_lab,
  title = {Ion Transport Virtual Lab: AI-Powered Multi-Agent Symposium System},
  author = {Your Name},
  year = {2026},
  url = {https://github.com/yourusername/ion_transport}
}
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📞 Contact

- **Project Maintainer**: Dr. Xiaoyang Du
- **Email**: kexiaoyangdu@ust.hk
- **Institution**: Prof. Dan Li's Group at HKUST (Hong Kong University of Science and Technology)

---

## 🙏 Acknowledgments

- OpenAI for GPT-4o model
- ChromaDB for vector database
- LangChain for RAG framework
- All contributing research paper authors

---

**Last Updated**: January 10, 2026
**Version**: 0.4.0 - Unified Agent with Validated Agentic RAG
