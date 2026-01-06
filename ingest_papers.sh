#!/bin/bash
# Wrapper script to ingest papers into RAG system with correct Python environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PARENT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Set Python path to include parent directory
export PYTHONPATH="$PARENT_DIR:$PYTHONPATH"

# Use conda Python
PYTHON="/Users/xiaoyangdu/miniconda3/bin/python"

# Run the ingestion script
cd "$SCRIPT_DIR"
exec "$PYTHON" knowledge_base/ingest_papers.py "$@"
