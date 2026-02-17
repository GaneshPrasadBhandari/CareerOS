import httpx
from loguru import logger

def check_ollama():
    """Verify Ollama is running and reachable on this MacBook."""
    url = "http://127.0.0.1:11434/api/tags"
    try:
        response = httpx.get(url, timeout=5.0)
        if response.status_code == 200:
            logger.info("✅ Ollama is Online and responding.")
            return True
    except Exception as e:
        logger.error(f"❌ Ollama Offline: Ensure 'ollama serve' is running. Error: {e}")
        return False

if __name__ == "__main__":
    check_ollama()