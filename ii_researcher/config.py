import os

SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "serpapi")
SCRAPER_PROVIDER = os.getenv("SCRAPER_PROVIDER", "firecrawl")
STEP_SLEEP = int(os.getenv("STEP_SLEEP", "100"))

COMPRESS_MAX_OUTPUT_WORDS = int(os.getenv("COMPRESS_MAX_OUTPUT_WORDS", "6500"))
COMPRESS_MAX_INPUT_WORDS = int(os.getenv("COMPRESS_MAX_INPUT_WORDS", "32000"))
COMPRESS_SIMILARITY_THRESHOLD = float(
    os.getenv("COMPRESS_SIMILARITY_THRESHOLD", "0.30")
)
COMPRESS_EMBEDDING_MODEL = os.getenv(
    "COMPRESS_EMBEDDING_MODEL", "BAAI/bge-m3"
)

SEARCH_QUERY_TIMEOUT = int(os.getenv("SEARCH_QUERY_TIMEOUT", "20"))
SCRAPE_URL_TIMEOUT = int(os.getenv("SCRAPE_URL_TIMEOUT", "30"))
SEARCH_PROCESS_TIMEOUT = int(os.getenv("SEARCH_PROCESS_TIMEOUT", "300"))

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:4000")
# Separate embedding server URL (defaults to same as OPENAI_BASE_URL if not set)
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", os.getenv("OPENAI_BASE_URL", "http://localhost:4000"))
USE_LLM_COMPRESSOR = os.getenv("USE_LLM_COMPRESSOR", "false").lower() == "true"

# Deep research timeout in seconds (default: 600 = 10 minutes)
DEEP_RESEARCH_TIMEOUT = int(os.getenv("DEEP_RESEARCH_TIMEOUT", "600"))

# Maximum concurrent browser scrape operations (default: 5)
MAX_CONCURRENT_BROWSER_SCRAPES = int(os.getenv("MAX_CONCURRENT_BROWSER_SCRAPES", "5"))
