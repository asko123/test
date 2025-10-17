"""Configuration for Document Chat Application"""

# Application Configuration
APP_ID = "trai"
ENV = "uat"  # Options: "uat", "prod"

# Model Configuration
AVAILABLE_MODELS = ["gemini-2.5-pro", "gemini-2.5-flash-lite"]
DEFAULT_MODEL = "gemini-2.5-flash-lite"
DEFAULT_TEMPERATURE = 0
LOG_LEVEL = "DEBUG"

# Application Settings
MAX_FILE_SIZE_MB = 50
SUPPORTED_FILE_TYPES = ["pdf", "json", "jsonl", "txt"]
MAX_DOCUMENTS = 10

# ReAct Agent Configuration
ENABLE_AGENT_MODE = True  # Enable/disable agent mode feature
AGENT_MAX_ITERATIONS = 10  # Maximum reasoning iterations for agent
AGENT_COMPLEXITY_THRESHOLD = 60  # Complexity score (0-100) to trigger agent mode
AGENT_TEMPERATURE = 0.2  # Temperature for agent (slightly higher for reasoning)
SHOW_AGENT_REASONING = True  # Show agent reasoning trace in UI
AGENT_DEFAULT_ENABLED = False  # Whether agent mode is enabled by default in UI

# Vespa Vector Store Configuration
ENABLE_VESPA_SEARCH = True  # Enable/disable Vespa DB search
VESPA_SCHEMA_ID = "tech_risk_ai"  # Vespa schema ID
VESPA_ENV = "uat"  # Vespa environment (dev, uat, or prod)
VESPA_TOP_K = 10  # Number of results to retrieve from Vespa
VESPA_AS_FALLBACK = True  # Use Vespa when no documents uploaded
VESPA_GSSSO = None  # Optional GSSO token (set if required)
VESPA_API_KEY = None  # Optional API key (set if required)

