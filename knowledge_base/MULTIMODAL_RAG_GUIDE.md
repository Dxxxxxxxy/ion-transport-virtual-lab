# Multimodal RAG System - User Guide

## Overview

The Ion Transport Knowledge Base now supports **full multimodal RAG** with three levels of functionality:

### ✅ Level 1: Vision LLM Figure Descriptions
- Extracts all figures/images from PDFs using PyMuPDF
- Analyzes each figure with GPT-4 Vision (GPT-4V)
- Generates detailed descriptions, identifies figure types
- Extracts key insights and approximate values

### ✅ Level 2: Plot Data Extraction
- Detects plot types (XY, bar, heatmap, scatter)
- Extracts numerical data points from graphs
- Stores structured data (axis info, data points, trends)
- Works for XY plots, line graphs, scatter plots

### ✅ Level 3: Multimodal Embeddings and Retrieval
- Generates semantic embeddings for figures
- Combines image analysis with text embeddings
- Enables hybrid search (text + figures)
- Stores images locally with metadata

## Architecture

```
PDF Paper
├── Text Extraction (PyMuPDF)
│   ├── Full text content
│   ├── Metadata (DOI, citation)
│   └── Text chunks (1000 tokens)
│
└── Figure Extraction (Multimodal)
    ├── Image files → saved to extracted_figures/{domain}/
    ├── GPT-4V Analysis
    │   ├── Figure type identification
    │   ├── Detailed description
    │   ├── Key insights extraction
    │   └── Approximate values
    ├── Plot Data Extraction (for graphs)
    │   ├── Axis information
    │   ├── Data points (x, y coordinates)
    │   └── Trends analysis
    └── Multimodal Embeddings
        ├── Text embedding (OpenAI)
        ├── Image-aware embedding
        └── Stored in ChromaDB
```

## Usage

### Basic Usage (Multimodal Enabled by Default)

```bash
# Ingest PDFs with full multimodal processing
python -m ion_transport.knowledge_base.ingest_papers
```

### Advanced Options

```bash
# Disable multimodal processing (text-only mode)
python -m ion_transport.knowledge_base.ingest_papers --no-multimodal

# Show statistics only
python -m ion_transport.knowledge_base.ingest_papers --stats

# Help
python -m ion_transport.knowledge_base.ingest_papers --help
```

## What Gets Extracted

### For Each Figure:

1. **Image File**
   - Saved to: `knowledge_base/extracted_figures/{domain}/{pdf_name}_page{N}_img{M}.{ext}`
   - Minimum size: 100x100 pixels
   - Formats: JPEG, PNG, etc.

2. **Vision Analysis** (GPT-4V)
   ```json
   {
     "figure_type": "XY plot",
     "description": "Capacitance vs pore size showing maximum at 0.7nm",
     "key_insights": ["Peak at 0.7nm", "Decreases for larger pores"],
     "approximate_values": "Peak ~200 F/g at 0.7nm",
     "variables": {
       "x_axis": "Pore size (nm)",
       "y_axis": "Capacitance (F/g)"
     },
     "data_extractable": true
   }
   ```

3. **Plot Data** (if applicable)
   ```json
   {
     "axis_info": {
       "x_axis": {"label": "Pore size", "unit": "nm", "range": [0.5, 3.0]},
       "y_axis": {"label": "Capacitance", "unit": "F/g", "range": [0, 250]}
     },
     "data_points": [
       [0.5, 120], [0.7, 200], [1.0, 180], ...
     ],
     "trends": "Increasing from 0.5-0.7nm, then decreasing"
   }
   ```

4. **ChromaDB Entry**
   - **Text**: Rich description combining caption + analysis + data
   - **Metadata**: PDF source, page number, figure type, image path
   - **Embedding**: Semantic vector for retrieval
   - **Content Type**: Marked as "figure" for filtering

## Querying Multimodal Content

When querying the knowledge base, figures are automatically included:

```python
# Example: Query will return both text chunks AND figure descriptions
query = "What is the optimal pore size for capacitance?"

# Results might include:
# 1. Text chunk: "...pore size of 0.7nm shows maximum capacitance..."
# 2. Figure chunk: "XY plot showing capacitance vs pore size. Peak at 0.7nm with 200 F/g..."
```

### Filtering by Content Type

```python
# Get only figures
results = collection.query(
    query_texts=["pore size capacitance"],
    where={"content_type": "figure"},
    n_results=10
)

# Get only text
results = collection.query(
    query_texts=["pore size capacitance"],
    where={"content_type": "text"},  # Default
    n_results=10
)

# Get specific figure types
results = collection.query(
    query_texts=["concentration profile"],
    where={"figure_type": "XY plot"},
    n_results=5
)
```

## Output Structure

After ingestion, you'll have:

```
ion_transport/
├── knowledge_base/
│   ├── extracted_figures/          # NEW: All extracted figures
│   │   ├── electrochemistry/
│   │   │   ├── Smith_2023_ACS_page3_img0.png
│   │   │   ├── Smith_2023_ACS_page5_img1.png
│   │   │   └── ...
│   │   ├── membrane_science/
│   │   ├── biology/
│   │   └── nanofluidics/
│   └── pdfs/
│       └── [your PDF files]
└── vector_db/
    └── chroma.sqlite3              # Contains text + figure embeddings
```

## Cost Estimates

### Multimodal Processing Costs (per PDF):

Assuming average scientific paper with:
- **Text**: 20-30 pages → ~$0.01-0.02 (text processing + embeddings)
- **Figures**: 5-10 figures → ~$0.05-0.15 (GPT-4V analysis)
  - Vision analysis: ~$0.01 per figure (GPT-4V input tokens)
  - Plot data extraction: ~$0.01 per plot (if applicable)
  - Embeddings: ~$0.0001 per figure (text-embedding-3-small)

**Total per PDF**: ~$0.06-0.17

**For 200 PDFs**: ~$12-34

Compare to text-only mode: ~$2-4 for 200 PDFs

## Performance

- **Text-only ingestion**: ~2-3 seconds/PDF
- **Multimodal ingestion**: ~10-15 seconds/PDF (due to GPT-4V calls)
  - Image extraction: ~1 sec
  - Vision analysis: ~5-10 sec (GPT-4V API calls)
  - Plot data extraction: ~3-5 sec (if applicable)
  - Embeddings: ~1 sec

## Limitations

1. **Plot Data Extraction Accuracy**
   - Vision LLM provides approximate values, not pixel-perfect
   - Best for clean, simple plots
   - Complex/overlapping plots: less accurate
   - Use original data files for high-precision needs

2. **Figure Recognition**
   - Minimum size: 100x100 pixels
   - Some small embedded graphics may be missed
   - Page decorations/logos may be extracted (usually filtered by size)

3. **Caption Matching**
   - Captions matched by page proximity (may not be perfect)
   - Some figures may not have captions extracted

## Best Practices

1. **First Run**: Start with a small test (5-10 PDFs) to verify everything works
2. **Cost Management**: Monitor OpenAI API usage during large ingestions
3. **Incremental Updates**: Use smart incremental ingestion to avoid reprocessing
4. **Quality Check**: Spot-check extracted figures in `extracted_figures/` folder
5. **Backup**: Keep original PDFs; extracted data can be regenerated

## Troubleshooting

### Issue: No figures extracted
**Solution**: Check if PDFs have actual embedded images (not scanned bitmap pages)

### Issue: GPT-4V API errors
**Solution**: Check OpenAI API key, rate limits, and account status

### Issue: Plot data extraction fails
**Solution**: This is normal for non-plot figures; extraction is attempted only for graphs

### Issue: High costs
**Solution**: Use `--no-multimodal` flag to disable figure processing temporarily

## Examples

### Example 1: Full Multimodal Ingestion
```bash
cd "/Users/xiaoyangdu/Library/Mobile Documents/com~apple~CloudDocs/HKUST/AI for system ionics/Virtual Lab for system ionics"
source ~/.zshrc
python -m ion_transport.knowledge_base.ingest_papers
```

Output:
```
🚀 ION TRANSPORT KNOWLEDGE BASE INGESTION
================================
Multimodal RAG: ✓ ENABLED (figures will be extracted & analyzed)

Processing domain: electrochemistry
  🖼️  Extracting multimodal content from: Smith_2023_ACS.pdf
    ✓ Extracted 8 images
    🔍 Analyzing Smith_2023_ACS_page3_img0.png with GPT-4V...
    📊 Extracting plot data...
    ✓ Created 8 searchable figure chunks
  ✓ Extracted 142 chunks from 25 pages
  ✓ Ingested 142 text chunks
  ✓ Ingested 8 figure chunks with multimodal analysis
```

### Example 2: Text-Only Mode
```bash
python -m ion_transport.knowledge_base.ingest_papers --no-multimodal
```

Output:
```
Multimodal RAG: ✗ Disabled (text-only mode)
```

## Future Enhancements

Possible improvements:
- [ ] True CLIP embeddings for better image-text alignment
- [ ] OCR for text within figures
- [ ] Chemical structure recognition
- [ ] Table extraction and structuring
- [ ] Equation recognition (LaTeX conversion)
- [ ] Video/animation support

## Support

For issues or questions:
1. Check this guide
2. Review error messages in console output
3. Verify OpenAI API key is set correctly
4. Check `extracted_figures/` folder for output

---

**Status**: ✅ Fully Implemented (Option C Complete)
**Version**: 1.0
**Last Updated**: 2026-01-05
