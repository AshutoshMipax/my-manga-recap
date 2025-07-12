"""Configuration settings for My Manga Recap - Centralized config with .env support."""

import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, continue without it
    pass

# Directory settings
DEFAULT_TEMP_DIR = "temp"

# Language and video settings
DEFAULT_LANG = os.getenv("MMR_LANG", "pt")
DEFAULT_IMAGE_DURATION = None  # Auto-calculated based on audio
DEFAULT_VIDEO_WIDTH = 1280
DEFAULT_VIDEO_HEIGHT = 720

# OpenAI Configuration (loaded from .env or environment)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_ID = os.getenv("OPENAI_MODEL_ID", "gpt-4o-mini") # Renamed from OPENAI_MODEL for clarity
OPENAI_TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "tts-1")
OPENAI_TTS_VOICE = os.getenv("OPENAI_TTS_VOICE", "alloy")
OPENAI_VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4o") # Used by OpenAIVisionProvider for OCR

# --- Local AI Model Configuration ---
# LLaVA Model (for local OCR and image understanding)
# Replace with your downloaded model path or Hugging Face identifier
LLAVA_MODEL_ID = os.getenv("LLAVA_MODEL_ID", "llava-hf/llava-1.5-7b-hf") # Example, user should change
LLAVA_QUANTIZATION = os.getenv("LLAVA_QUANTIZATION", None) # Options: "4bit", "8bit", or None

# Local LLM (for local text/script generation)
# Replace with your downloaded model path or Hugging Face identifier
LOCAL_LLM_MODEL_ID = os.getenv("LOCAL_LLM_MODEL_ID", "NousResearch/Hermes-2-Pro-Llama-3-8B") # Example, user should change
LOCAL_LLM_PROMPT_FORMAT = os.getenv("LOCAL_LLM_PROMPT_FORMAT", "chatml") # Options: "chatml", "llama2", "alpaca", "generic"
LOCAL_LLM_QUANTIZATION = os.getenv("LOCAL_LLM_QUANTIZATION", None) # Options: "4bit", "8bit", or None

# Preferred AI Provider for script generation (text-to-text)
# Options: "local", "openai", "silent". If None or invalid, AIManager defaults to "local" > "openai" > "silent".
PREFERRED_AI_PROVIDER = os.getenv("PREFERRED_AI_PROVIDER", "local")


# Configuration validation and info
def get_openai_config():
    """Get OpenAI configuration as a dictionary"""
    return {
        "api_key": OPENAI_API_KEY,
        "model_id": OPENAI_MODEL_ID, # Updated name
        "tts_model": OPENAI_TTS_MODEL,
        "tts_voice": OPENAI_TTS_VOICE,
        "vision_model": OPENAI_VISION_MODEL,
    }

def is_openai_configured():
    """Check if OpenAI is properly configured"""
    return OPENAI_API_KEY is not None and OPENAI_API_KEY.strip() != ""

def get_local_models_config():
    """Get local models configuration as a dictionary"""
    return {
        "llava_model_id": LLAVA_MODEL_ID,
        "llava_quantization": LLAVA_QUANTIZATION,
        "local_llm_model_id": LOCAL_LLM_MODEL_ID,
        "local_llm_prompt_format": LOCAL_LLM_PROMPT_FORMAT,
        "local_llm_quantization": LOCAL_LLM_QUANTIZATION,
    }

def print_config_status():
    """Print current configuration status"""
    print("⚙️  Configuração Atual:")
    print("--- OpenAI ---")
    print(f"  OPENAI_API_KEY: {'✅ Configurada' if is_openai_configured() else '❌ Não encontrada'}")
    print(f"  OPENAI_MODEL_ID (for text): {OPENAI_MODEL_ID}")
    print(f"  OPENAI_TTS_MODEL: {OPENAI_TTS_MODEL}")
    print(f"  OPENAI_TTS_VOICE: {OPENAI_TTS_VOICE}")
    print(f"  OPENAI_VISION_MODEL (for OCR): {OPENAI_VISION_MODEL}")
    if not is_openai_configured():
        print("  💡 Dica OpenAI: Copie env.example para .env e configure sua OPENAI_API_KEY.")

    print("\n--- Modelos Locais ---")
    print(f"  LLAVA_MODEL_ID (Vision/OCR): {LLAVA_MODEL_ID or '❌ Não configurado'}")
    print(f"  LLAVA_QUANTIZATION: {LLAVA_QUANTIZATION or 'Nenhuma'}")
    print(f"  LOCAL_LLM_MODEL_ID (Text Gen): {LOCAL_LLM_MODEL_ID or '❌ Não configurado'}")
    print(f"  LOCAL_LLM_PROMPT_FORMAT: {LOCAL_LLM_PROMPT_FORMAT or 'Nenhum (usará genérico)'}")
    print(f"  LOCAL_LLM_QUANTIZATION: {LOCAL_LLM_QUANTIZATION or 'Nenhuma'}")

    if not LLAVA_MODEL_ID or not LOCAL_LLM_MODEL_ID:
        print("  💡 Dica Modelos Locais: Configure os IDs/caminhos dos modelos em 'modules/config.py' ou via variáveis de ambiente (e.g., LLAVA_MODEL_ID, LOCAL_LLM_MODEL_ID).")
        print("     Consulte setup_and_run.bat para mais detalhes sobre download e configuração dos modelos.")

    print("\n--- Geral ---")
    print(f"  DEFAULT_LANG: {DEFAULT_LANG}")
    print(f"  DEFAULT_TEMP_DIR: {DEFAULT_TEMP_DIR}")
