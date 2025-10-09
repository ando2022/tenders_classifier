import os
import pathlib

import dotenv

dotenv.load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MODEL = os.getenv('MODEL') or 'gpt-4o-mini'
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL') or 'text-embedding-3-small'



# data/
#   rag.json
#   docs/
#     ....

DATA_DIR = pathlib.Path('data')
DOCS_DIR = DATA_DIR / 'docs'
RAG_INDEX_PATH = DATA_DIR / 'rag.json'
RAG_TOP_K = 3
