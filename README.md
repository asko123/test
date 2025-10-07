# Document Chat Bot

A multi-document chatbot for querying PDF documents.

## Quick Start

### Prerequisites
- Python 3.8+
- Valid App ID and credentials

### Installation

1. Run setup script:
```bash
./setup.sh
source venv/bin/activate
```

2. Configure credentials in `config.py`:
```python
APP_ID = "your_app_id"
ENV = "uat"  # or "prod"
```

## Running the Application

### Option 1: Streamlit Web App

```bash
streamlit run app.py
```

Then:
1. Configure App ID and Environment in sidebar
2. Upload PDF documents
3. Click "Process Documents"
4. Start chatting

### Option 2: Jupyter Notebook

```bash
jupyter notebook chatbot.ipynb
```

Follow the cells step by step to upload documents and chat.

### Option 3: Python Script

```python
from document_processor import DocumentProcessor
from llm_handler import LLMHandler

# Initialize
doc_processor = DocumentProcessor(app_id="trai", env="uat")
llm_handler = LLMHandler(app_id="trai", env="uat", model_name="gemini-2.0-flash")

# Upload documents
documents = doc_processor.upload_documents(["doc1.pdf", "doc2.pdf"])

# Query
response = llm_handler.query("What are the key findings?", documents=documents)
print(response)
```

## Configuration

Edit `config.py`:

```python
APP_ID = "trai"
ENV = "uat"
DEFAULT_MODEL = "gemini-2.0-flash"
DEFAULT_TEMPERATURE = 0
```

## Files

- `chatbot.ipynb` - Jupyter notebook
- `app.py` - Streamlit web app
- `document_processor.py` - Document handling
- `llm_handler.py` - LLM interactions
- `config.py` - Configuration

