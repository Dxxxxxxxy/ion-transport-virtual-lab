# RAG Knowledge Base User Guide

## Overview

The ion transport symposium uses a **RAG (Retrieval-Augmented Generation)** system to give each AI expert access to curated papers from their domain. This replaces PubMed search with your own selection of high-quality papers, including full text, figures, tables, and equations.

---

## Quick Start

### 1. Upload PDF Papers

Place your PDF files in the appropriate domain folders:

```
ion_transport/knowledge_base/pdfs/
├── electrochemistry/        # EDL capacitors, CDI, supercapacitors
├── membrane_science/        # Desalination, ion separation, element extraction
├── biology/                 # Ion channels (K+, Na+, Ca2+)
└── nanofluidics/           # Synthetic nanopores, nanochannels
```

**Important:**
- PDF file names don't matter for functionality
- However, recommended format: `FirstAuthor_Year_JournalAbbr.pdf` (e.g., `Smith_2023_EES.pdf`)
- Maximum ~1000 papers total across all domains

### 2. Run the Ingestion Script

From the virtual_lab directory, run:

```bash
python -m ion_transport.knowledge_base.ingest_papers
```

**What happens during ingestion:**
1. ✓ Extracts full PDF content (text, figures, tables, equations)
2. ✓ Automatically finds DOI in PDF
3. ✓ Queries CrossRef API for citation metadata
4. ✓ Formats citations as: "Journal Abbr (Year), Volume, Pages"
5. ✓ Chunks content into 1000-token segments with 200-token overlap
6. ✓ Generates OpenAI embeddings (text-embedding-3-small)
7. ✓ Stores in ChromaDB vector database (ion_transport/vector_db/)

**Expected output:**
```
================================================================================
🚀 ION TRANSPORT KNOWLEDGE BASE INGESTION
================================================================================
PDF Directory: ion_transport/knowledge_base/pdfs
Vector DB: ion_transport/vector_db
Chunk Size: 1000 tokens
Embedding Model: text-embedding-3-small

================================================================================
📚 Processing 15 PDFs from electrochemistry/
================================================================================
✓ Using existing collection: electrochemistry_papers

  Processing: smith_2023.pdf
      ✓ Found DOI: 10.1039/d3ee01234a
      ✓ Citation: Energy Environ. Sci. (2023), 16, 1234-1250
    ✓ Extracted 42 chunks from 127 elements

  Processing: jones_2024.pdf
      ⚠ No DOI found, extracting from PDF text
    ✓ Extracted 38 chunks from 105 elements

...

✓ Ingested 630 chunks from 15 papers

================================================================================
✅ INGESTION COMPLETE
================================================================================
Total chunks across all domains: 2450

You can now query the knowledge base using query_rag.py
```

### 3. Check Knowledge Base Status

To see statistics without re-ingesting:

```bash
python -m ion_transport.knowledge_base.ingest_papers --stats
```

**Output:**
```
================================================================================
📊 KNOWLEDGE BASE STATISTICS
================================================================================

ELECTROCHEMISTRY:
  Collection: electrochemistry_papers
  Documents: 630

MEMBRANE_SCIENCE:
  Collection: membrane_science_papers
  Documents: 825

BIOLOGY:
  Collection: biology_papers
  Documents: 512

NANOFLUIDICS:
  Collection: nanofluidics_papers
  Documents: 483
```

---

## How Agents Use the Knowledge Base

### During Symposium

When you run `run_full_symposium.py`, each expert automatically has access to their domain's knowledge base.

**Example agent query:**
```
Agent: "I need to find information about EDL capacitance in sub-nanometer pores"

Tool call: query_knowledge_base(
    query="EDL capacitance sub-nanometer pores carbon electrodes",
    top_k=5
)

Retrieved context:
[Source 1] Smith et al. (2023) - Electric Double-Layer Capacitance in Nanopores
Citation: Energy Environ. Sci. (2023), 16, 1234-1250

The specific capacitance increases dramatically when pore size approaches the
ion size due to desolvation effects. For sub-1nm pores, we measured 250 F/g
in aqueous KCl electrolyte...

[Source 2] Jones et al. (2024) - Ion Confinement Effects in Carbon Nanopores
Citation: Nano Lett. (2024), 24, 567-580

...
```

**Agent then cites in response:**
```
"Recent work has shown that EDL capacitance in sub-nanometer carbon pores
can exceed 250 F/g due to desolvation effects (Smith et al., Energy Environ.
Sci. (2023), 16, 1234-1250). This suggests..."
```

### Knowledge Base Usage Guidelines

The agent prompts instruct each expert to:
- ✓ Use `query_knowledge_base` tool when they need specific evidence
- ✓ Be specific in queries: "EDL capacitance in sub-nm pores" not just "capacitance"
- ✓ ALWAYS cite sources using the provided format
- ✓ Use retrieved information to support arguments with concrete evidence

---

## Testing the Knowledge Base

### Manual Query Test

You can manually test queries:

```bash
python -m ion_transport.knowledge_base.query_rag "ion selectivity mechanisms in nanopores" nanofluidics 5
```

**Arguments:**
1. Query string
2. Domain (electrochemistry, membrane_science, biology, nanofluidics, all)
3. Top K results (optional, default 5)

### Python API Test

```python
from ion_transport.knowledge_base import query_papers, get_context_for_agent

# Query a specific domain
results = query_papers(
    query="pore size effects on ion selectivity",
    domain="nanofluidics",
    top_k=5,
    format_for_llm=True  # Get formatted string for LLM
)
print(results)

# Get context formatted for agents (used internally by symposium)
context = get_context_for_agent(
    query="K+ selectivity filter structure",
    domain="biology",
    top_k=5
)
print(context)
```

---

## Citation Format Details

### Automatic Extraction

The system automatically extracts citations in this order:

1. **Find DOI** in PDF metadata or first 3 pages
2. **Query CrossRef API** using DOI to get:
   - Title
   - Authors (formatted as "FirstAuthor et al.")
   - Year
   - Journal name (abbreviated if available)
   - Volume and page numbers
3. **Format as:** `Journal Abbr (Year), Volume, Pages`
   - Example: `Energy Environ. Sci. (2023), 16, 1234-1250`

### Fallback for Papers Without DOI

If DOI is not found:
- Extracts title from PDF first page
- Uses filename for author/year if structured correctly
- Citation shows as "Citation unavailable"

---

## Best Practices

### Paper Selection

✓ **Do:** Select high-quality papers from top journals
✓ **Do:** Include recent reviews and seminal works
✓ **Do:** Organize by domain (electrochemistry, membrane_science, biology, nanofluidics)

✗ **Don't:** Upload papers outside the domain scope (e.g., battery papers in EDL folder)
✗ **Don't:** Upload excessively old papers unless seminal

### PDF Organization

**Recommended folder structure:**
```
electrochemistry/
├── Smith_2023_EES.pdf           # Recent EDL capacitance study
├── Jones_2024_NanoLett.pdf      # CDI mechanisms
├── Review_Wang_2023_ChemRev.pdf # Comprehensive review
└── ...

membrane_science/
├── Zhang_2024_JMembrSci.pdf     # Li+ selectivity in GO membranes
├── Kumar_2023_Desalination.pdf  # RO membrane performance
└── ...
```

### Ingestion Tips

- **Re-ingestion:** The system will skip duplicate files (based on content hash)
- **Incremental updates:** Just add new PDFs and re-run ingestion
- **Performance:** Ingesting 100 PDFs takes ~10-15 minutes (includes API calls to CrossRef)
- **Cost:** OpenAI embedding costs ~$0.01 per 1000 pages

---

## Troubleshooting

### "Vector database not found"

```
⚠️  Warning: Vector database not found. RAG will not work.
   Expected location: ion_transport/vector_db
   Run: python -m ion_transport.knowledge_base.ingest_papers
```

**Solution:** Run the ingestion script to create the vector database.

### "Collection not found"

If you see errors about missing collections, it means no PDFs have been ingested for that domain.

**Solution:**
1. Add PDFs to the domain folder
2. Re-run ingestion

### "DOI extraction failed"

Some PDFs may not have DOIs or have them in non-standard formats.

**Impact:** Citation will be incomplete but content is still indexed
**Solution:** Manually verify paper metadata or use filename format `Author_Year_Journal.pdf`

### "CrossRef API timeout"

The system includes rate limiting (0.5s between queries) to respect CrossRef API.

**Impact:** Slower ingestion but ensures all citations are retrieved
**Solution:** Be patient during ingestion of large batches

---

## System Architecture

### Components

1. **ingest_papers.py**
   - CitationExtractor: Extracts DOI and queries CrossRef
   - PDFIngester: Processes PDFs, chunks content, generates embeddings
   - Saves to ChromaDB in domain-specific collections

2. **query_rag.py**
   - RAGQueryEngine: Queries ChromaDB using embeddings
   - Retrieves top-k most relevant chunks
   - Formats results with citations for LLM consumption

3. **rag_tool.py**
   - RAGIntegration: Wraps RAG as an OpenAI function tool
   - Handles tool calls from agents during symposium
   - Maps agents to their domains automatically

### Data Flow

```
PDFs → Ingestion → CitationExtractor → CrossRef API → Metadata
                ↓
          UnstructuredPDFLoader → Full Content Extraction
                ↓
          RecursiveCharacterTextSplitter → 1000-token Chunks
                ↓
          OpenAI Embeddings → Vector Representations
                ↓
          ChromaDB → Persistent Storage

During Symposium:
Agent → query_knowledge_base tool → RAGQueryEngine → ChromaDB
      ← Formatted Context with Citations ← Top-K Retrieval
```

---

## Next Steps

1. ✓ Upload PDFs to domain folders
2. ✓ Run ingestion script
3. ✓ Check status with `--stats`
4. ✓ Test with manual queries
5. ✓ Run symposium with `run_full_symposium.py`
6. ✓ Review discussion outputs with citations

---

## Support

For issues or questions:
- Check ingestion logs for errors
- Test queries manually before running symposium
- Ensure OpenAI API key is set in environment
- Verify PDF files are readable (not scanned images without OCR)

**Happy researching!** 🚀
