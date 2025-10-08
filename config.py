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
SUPPORTED_FILE_TYPES = ["pdf", "json", "jsonl"]
MAX_DOCUMENTS = 10

