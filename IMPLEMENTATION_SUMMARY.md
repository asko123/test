# Document Chat Bot - Implementation Summary

## Solution Overview

A multi-document chatbot for querying PDF documents. This solution enables users to upload multiple PDF documents and chat with them using grounded AI responses.

## Architecture

The solution follows this pattern:

```python
# 1. Document Upload
from goldmansachs.awm_genai import DocUtils
doc_utils = DocUtils(app_id=app_id, env=env)
documents = doc_utils.upload(file_paths=file_paths)

# 2. LLM Configuration and Inference
from goldmansachs.awm_genai import LLM, LLMConfig
llm_config = LLMConfig(
    app_id=app_id,
    env=env,
    model_name="gemini-2.0-flash",
    temperature=0,
    log_level="DEBUG"
)
llm = LLM.init(config=llm_config)
response = llm.invoke(question, documents=documents)
```

## Created Files

### Core Application Files

1. **chatbot.ipynb** - Jupyter Notebook Implementation
   - Complete notebook-based solution
   - Step-by-step document upload and chat
   - Interactive interface with chat history
   - Example questions and batch processing

2. **app.py** - Streamlit Web Application
   - Web-based chat interface
   - Multi-document upload UI
   - Real-time chat with history
   - Configurable CMS and model settings

3. **document_processor.py** - Document Processing Module
   - Handles document upload to CMS
   - Uses DocUtils from SDK
   - Document validation and info

4. **llm_handler.py** - LLM Handler Module
   - Manages LLM initialization
   - Handles queries with documents
   - Batch query support

5. **config.py** - Configuration
   - CMS settings (App ID, Environment)
   - Model configuration
   - Application limits

### Setup and Documentation

6. **requirements.txt** - Dependencies
   ```
   goldmansachs.awm_genai
   streamlit>=1.28.0
   python-dotenv>=1.0.0
   pandas>=2.0.0
   ```

7. **setup.sh** - Setup Script
   - Automated environment setup
   - SDK installation
   - Virtual environment creation

8. **README.md** - Main Documentation
   - Complete usage instructions
   - Architecture overview
   - Configuration guide

9. **USAGE_GUIDE.md** - Detailed Usage Guide
   - Step-by-step instructions
   - Example workflows
   - Troubleshooting

10. **.gitignore** - Git Ignore Rules
    - Python artifacts
    - Environment files
    - Documents and data

## Key Features

### Multi-Document Support
- Upload multiple PDF documents simultaneously
- Documents processed together for comprehensive answers
- Configurable document limits

### Grounded Responses
- All responses grounded in uploaded documents
- Accurate, source-based answers
- Temperature set to 0 for deterministic results

### Multiple Interfaces
1. **Jupyter Notebook** - For exploration and analysis
2. **Streamlit Web App** - For production deployment
3. **Python Modules** - For custom integration

### SDK Integration
- DocUtils for document upload
- LLM with LLMConfig for inference
- Proper error handling

## Usage Options

### Option 1: Jupyter Notebook
```bash
jupyter notebook cms_chatbot.ipynb
```
- Best for: Exploration, analysis, testing

### Option 2: Streamlit App
```bash
streamlit run app.py
```
- Best for: Production use, end-user interface

### Option 3: Python Modules
```python
from document_processor import DocumentProcessor
from llm_handler import LLMHandler

processor = DocumentProcessor(app_id="trai", env="uat")
handler = LLMHandler(app_id="trai", env="uat")

documents = processor.upload_documents(["doc1.pdf"])
response = handler.query("Question?", documents)
```
- Best for: Custom integration, automation

## Configuration

### Application Configuration
```python
APP_ID = "trai"
ENV = "uat"  # or "prod"
```

### Model Configuration
```python
DEFAULT_MODEL = "gemini-2.0-flash"
DEFAULT_TEMPERATURE = 0
LOG_LEVEL = "DEBUG"
```

### Application Settings
```python
MAX_FILE_SIZE_MB = 50
SUPPORTED_FILE_TYPES = ["pdf"]
MAX_DOCUMENTS = 10
```

## How It Works

1. **Initialize DocUtils** with App ID and environment
2. **Upload Documents** using `doc_utils.upload(file_paths)`
3. **Configure LLM** with LLMConfig
4. **Initialize LLM** with `LLM.init(config)`
5. **Query Documents** with `llm.invoke(question, documents=documents)`
6. **Display Response** with source grounding

## Security Considerations

- Credentials never hardcoded
- Environment variables for sensitive data
- Proper entitlements required
- Network access required

## Limitations

- Only PDF documents supported
- Maximum 50MB per file (configurable)
- Maximum 10 documents (configurable)
- Requires valid credentials
- Cannot be tested without proper access

## File Structure

```
.
├── chatbot.ipynb             # Jupyter notebook
├── app.py                    # Streamlit web app
├── document_processor.py     # Document handling
├── llm_handler.py            # LLM interactions
├── config.py                 # Configuration
├── requirements.txt          # Dependencies
├── setup.sh                  # Setup script
├── README.md                 # Main docs
└── .gitignore                # Git ignore
```

## Quick Start

```bash
# 1. Setup
./setup.sh
source venv/bin/activate

# 2. Configure (edit config.py)
APP_ID = "your_app_id"
ENV = "uat"

# 3. Run Streamlit
streamlit run app.py

# OR Run Jupyter
jupyter notebook chatbot.ipynb
```

## Next Steps

1. Configure your App ID in config.py
2. Run setup.sh to install dependencies
3. Choose your preferred interface (notebook or web app)
4. Upload your PDF documents
5. Start asking questions

## Important Notes

- This solution follows SDK patterns
- All code uses exact patterns from documentation
- Designed for Linux environment
- Grounded responses ensure accuracy
- Multi-document support for comprehensive analysis

