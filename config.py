"""
Configurações centrais do projeto RAG VendeFácil.

Nenhuma credencial real deve ser armazenada neste arquivo.
As chaves são obtidas por variável de ambiente.
"""

import os

# ============================================================
# LLM
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = "openai/gpt-oss-20b"

# ============================================================
# EMBEDDINGS
# ============================================================

EMBEDDING_MODEL = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

# ============================================================
# RECUPERAÇÃO
# ============================================================

TOP_K = 5
FETCH_K = 500
RRF_K = 60

# ============================================================
# CAMINHOS
# ============================================================

DATA_DIR = "data"
INDEX_DIR = "index/faiss_index"

# ============================================================
# SEGURANÇA
# ============================================================

SENSITIVITY_LEVELS = (
    "publico",
    "interno",
    "restrito",
)
