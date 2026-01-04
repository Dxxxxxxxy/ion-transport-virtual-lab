# Ion Transport Virtual Lab

A multi-agent AI framework for conducting virtual research symposiums on ion transport phenomena across four scientific domains: Electrochemistry, Membrane Science, Biology, and Nanofluidics.

## Overview

This project enables AI-powered collaborative research discussions by bringing together domain-specific expert agents equipped with:
- **RAG (Retrieval-Augmented Generation)**: Each expert has access to curated research papers from their domain
- **Multi-round symposiums**: Structured 4-round discussions to develop unified theoretical frameworks
- **Scientific critique**: Built-in peer review and rigorous evaluation of ideas
- **Citation support**: Automatic extraction and formatting of academic citations

## Features

- **4 Domain Expert Agents**:
  - Electrochemistry Expert (EDL capacitors, CDI, supercapacitors)
  - Membrane Science Expert (Desalination, ion separation)
  - Biology Expert (Ion channels: K+, Na+, Ca2+)
  - Nanofluidics Expert (Synthetic nanopores, nanochannels)

- **Knowledge Base with RAG**:
  - PDF ingestion and processing
  - Automatic DOI extraction and citation formatting
  - Vector database using ChromaDB
  - OpenAI embeddings for semantic search

- **Symposium System**:
  - 4-round structured discussions
  - Symposium Chair (PI) for facilitation
  - Scientific Critic for rigorous feedback
  - Automatic summary generation

## Installation

### Prerequisites
- Python 3.8+
- OpenAI API key
- Virtual Lab framework (parent project)

### Setup

1. **Clone the repository**:
```bash
git clone https://github.com/Dxxxxxxxy/ion-transport-virtual-lab.git
cd ion-transport-virtual-lab
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up OpenAI API key**:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

4. **Install Virtual Lab framework**:
```bash
# Navigate to parent directory and install virtual_lab
cd ../virtual_lab
pip install -e .
```

## Usage

### 1. Prepare Knowledge Base

Create domain-specific PDF collections:

```
ion_transport/knowledge_base/pdfs/
├── electrochemistry/        # Place electrochemistry papers here
├── membrane_science/        # Place membrane science papers here
├── biology/                 # Place biology papers here
└── nanofluidics/           # Place nanofluidics papers here
```

### 2. Ingest Papers into Vector Database

```bash
python -m ion_transport.knowledge_base.ingest_papers
```

This will:
- Extract content from PDFs
- Find DOIs and fetch citation metadata
- Generate embeddings
- Store in ChromaDB vector database

### 3. Run Full Symposium

```bash
python -m ion_transport.run_full_symposium
```

The symposium consists of 4 rounds:
1. **Round 1**: Map the Landscape - Understanding current paradigms
2. **Round 2**: Identify Unifying Principles - Test analogies
3. **Round 3**: Build Unified Framework - Define common core
4. **Round 4**: Applications & Future Directions - Cross-pollination

### 4. Review Results

Discussion transcripts are saved in:
```
ion_transport/results/full_symposium/
├── round_1_landscape/
├── round_2_principles/
├── round_3_framework/
└── round_4_applications/
```

## Project Structure

```
ion_transport/
├── agents/
│   └── detailed_agents.py       # Domain expert agent definitions
├── prompts/
│   └── detailed_prompts.py      # Symposium agendas and questions
├── knowledge_base/
│   ├── ingest_papers.py         # PDF ingestion and processing
│   ├── query_rag.py             # RAG query engine
│   └── pdfs/                    # PDF storage by domain
├── rag_tool.py                  # RAG tool integration
├── run_full_symposium.py        # Main symposium orchestrator
├── RAG_USER_GUIDE.md            # Detailed RAG documentation
└── requirements.txt             # Python dependencies
```

## Configuration

### Cost Estimates
- **Full 4-round symposium**: $2.50-4.00
- **Processing time**: 15-25 minutes

### Customization

Edit `agents/detailed_agents.py` to:
- Modify expert personas and expertise
- Add new domain experts
- Adjust research focus

Edit `prompts/detailed_prompts.py` to:
- Customize symposium agendas
- Change discussion questions
- Modify discussion rules

## Documentation

See [RAG_USER_GUIDE.md](RAG_USER_GUIDE.md) for detailed information about:
- Knowledge base setup
- PDF ingestion process
- Citation extraction
- Query system
- Troubleshooting

## Requirements

- chromadb >= 0.4.0
- langchain >= 0.1.0
- langchain-openai >= 0.0.5
- langchain-community >= 0.0.20
- pymupdf >= 1.23.0
- requests >= 2.31.0
- tqdm >= 4.66.0
- Virtual Lab framework

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Xiaoyang Du**
- GitHub: [@Dxxxxxxxy](https://github.com/Dxxxxxxxy)
- Email: dxy602127858@gmail.com
- Affiliation: HKUST (Hong Kong University of Science and Technology)

## Citation

If you use this framework in your research, please cite:

```bibtex
@software{du2026_ion_transport_virtual_lab,
  author = {Du, Xiaoyang},
  title = {Ion Transport Virtual Lab: Multi-Agent Framework for Research Symposiums},
  year = {2026},
  url = {https://github.com/Dxxxxxxxy/ion-transport-virtual-lab}
}
```

## Acknowledgments

Built with the Virtual Lab framework for multi-agent AI research collaboration.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For questions or issues, please open an issue on GitHub or contact the author.
