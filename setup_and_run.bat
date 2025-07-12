@echo off
setlocal

REM Project Title
echo =======================================
echo  My Manga Recap - Local Model Setup
echo =======================================
echo.

REM --- Configuration ---
set PYTHON_VERSION=3.9
set VENV_NAME=.venv
set REQUIREMENTS_FILE=requirements.txt

REM --- Helper Functions ---
:check_command
    echo Checking for %1...
    where %1 >nul 2>nul
    if %errorlevel% neq 0 (
        echo   %1 not found. Please install it and add to PATH.
        exit /b 1
    )
    echo   %1 found.
    exit /b 0

REM --- 1. Check for Python ---
call :check_command python
if %errorlevel% neq 0 (
    echo Python is required to run this application.
    echo Please install Python %PYTHON_VERSION% or higher and ensure it's in your PATH.
    goto :eof
)
echo.

REM --- 2. Create/Activate Virtual Environment ---
if not exist "%VENV_NAME%\Scripts\activate.bat" (
    echo Creating Python virtual environment (%VENV_NAME%)...
    python -m venv %VENV_NAME%
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment. Please check your Python installation.
        goto :eof
    )
    echo Virtual environment created.
) else (
    echo Virtual environment (%VENV_NAME%) already exists.
)

echo Activating virtual environment...
call "%VENV_NAME%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment.
    goto :eof
)
echo.

REM --- 3. Install Dependencies ---
echo Installing dependencies from %REQUIREMENTS_FILE%...
pip install -r %REQUIREMENTS_FILE%
if %errorlevel% neq 0 (
    echo Failed to install dependencies from %REQUIREMENTS_FILE%.
    goto :error_exit
)
echo Dependencies from %REQUIREMENTS_FILE% installed successfully.
echo.

echo Installing additional dependencies for local AI models...
REM - torch, torchvision, torchaudio: Often best installed separately with specific CUDA version if needed.
REM   The versions in requirements.txt might be CPU-only or a generic CUDA.
REM   For optimal performance with GPUs, users might need to install PyTorch from https://pytorch.org/get-started/locally/
echo   Note: For GPU support with PyTorch, you might need to install a CUDA-specific version.
echo   See https://pytorch.org/ for instructions. The 'torch' in requirements.txt might be CPU-only.
pip install bitsandbytes accelerate sentencepiece protobuf
REM sentencepiece is often a dependency for tokenizers
REM protobuf is sometimes needed by transformers or underlying libraries
if %errorlevel% neq 0 (
    echo Failed to install additional AI model dependencies.
    goto :error_exit
)
echo Additional AI model dependencies installed successfully.
echo.

REM --- 4. Tesseract OCR (if not installed) ---
where tesseract >nul 2>nul
if %errorlevel% neq 0 (
    echo ======================================================================
    echo  WARNING: Tesseract OCR not found in PATH.
    echo ======================================================================
    echo  Tesseract is used as a fallback OCR engine.
    echo  If you haven't installed it, please download and install it from:
    echo    https://github.com/UB-Mannheim/tesseract/wiki
    echo  During installation, make sure to:
    echo    1. Add Tesseract to your system PATH.
    echo    2. Install the language data for English ("eng") and Portuguese ("por").
    echo  After installation, you might need to restart this script or your terminal.
    echo ======================================================================
    echo.
) else (
    echo Tesseract OCR found.
)
echo.

REM --- 5. Model Downloading (Instructions/Placeholders) ---
echo ======================================================================
echo  ACTION REQUIRED: Download Local AI Models
echo ======================================================================
echo  This script does not automatically download the large AI model files.
echo  You need to download them manually and update 'modules/config.py'.
echo.
echo  Instructions:
echo  1. LLaVA Model (for Vision/OCR):
echo     - Recommended model: e.g., 'bakLLaVA-1' (llava-hf/bakLlava-v1-hf) or other LLaVA 1.5/Next variants.
echo     - Download from Hugging Face Hub: https://huggingface.co/models?search=llava
echo     - Update 'LLAVA_MODEL_ID' in 'modules/config.py' to the path of your downloaded model
echo       or its Hugging Face identifier (e.g., "llava-hf/bakLlava-v1-hf").
echo     - You can also set 'LLAVA_QUANTIZATION = "4bit"' or '"8bit"' in config.py for smaller memory footprint (requires bitsandbytes).
echo.
echo  2. LLaMA-style LLM (for Text Generation):
echo     - Recommended models: e.g., Llama-2-7b-chat-hf, Mistral-7B-Instruct-v0.1, etc.
echo     - Download from Hugging Face Hub: https://huggingface.co/models
echo     - Update 'LOCAL_LLM_MODEL_ID' in 'modules/config.py' to the path of your downloaded model
echo       or its Hugging Face identifier (e.g., "meta-llama/Llama-2-7b-chat-hf").
echo     - Update 'LOCAL_LLM_PROMPT_FORMAT' in 'modules/config.py' (e.g., "llama2", "chatml", "alpaca").
echo     - You can also set 'LOCAL_LLM_QUANTIZATION = "4bit"' or '"8bit"' in config.py.
echo.
echo  Example for config.py:
echo  ----------------------------------------------------------------------
echo  # modules/config.py
echo  # ... other settings ...
echo  LLAVA_MODEL_ID = "llava-hf/bakLlava-v1-hf"  # Or path like "C:/models/bakLlava-v1-hf"
echo  LLAVA_QUANTIZATION = "4bit"  # Options: "4bit", "8bit", or None
echo.
echo  LOCAL_LLM_MODEL_ID = "meta-llama/Llama-2-7b-chat-hf" # Or path
echo  LOCAL_LLM_PROMPT_FORMAT = "llama2" # or "chatml", "alpaca", "generic"
echo  LOCAL_LLM_QUANTIZATION = "4bit" # Options: "4bit", "8bit", or None
echo  # ... other settings ...
echo  ----------------------------------------------------------------------
echo.
echo  IMPORTANT: Ensure the paths in config.py are correct if you download models locally.
echo  If using Hugging Face identifiers, an internet connection will be needed
echo  the first time the models are run to download them to the Hugging Face cache.
echo  Default cache location is usually C:/Users/YourUser/.cache/huggingface/hub
echo ======================================================================
echo.
pause

REM --- 6. Update config.py (Reminder) ---
echo ======================================================================
echo  REMINDER: Ensure 'modules/config.py' is correctly set up!
echo ======================================================================
echo  - Set 'OPENAI_API_KEY' if you plan to use OpenAI providers.
echo  - Verify 'LLAVA_MODEL_ID', 'LLAVA_QUANTIZATION'.
echo  - Verify 'LOCAL_LLM_MODEL_ID', 'LOCAL_LLM_PROMPT_FORMAT', 'LOCAL_LLM_QUANTIZATION'.
echo  - Check 'DEFAULT_LANG' and other settings.
echo.
echo  The application will attempt to use local models if the respective
echo  '..._MODEL_ID' variables are set in 'modules/config.py'.
echo ======================================================================
echo.
pause
echo.

REM --- 7. Run Application ---
:run_menu
echo Choose how to run the application:
echo 1. Run Main Process (main.py - for full video generation)
echo 2. Run Interactive CLI (interactive_cli.py - for menu options)
echo 3. Test AI Providers (test_openai.py)
echo 4. Exit
echo.
choice /C 1234 /M "Enter your choice [1, 2, 3, 4]:"

if errorlevel 4 goto :eof
if errorlevel 3 goto :run_test_ai
if errorlevel 2 goto :run_interactive
if errorlevel 1 goto :run_main

:run_main
echo Running main.py...
echo Example: python main.py --chapters_dir manga_chapters --output manga_recap.mp4 --temp temp_files
echo You will be prompted for arguments if none are provided to main.py or use --help.
python main.py %*
goto :run_complete

:run_interactive
echo Running interactive_cli.py...
python interactive_cli.py
goto :run_complete

:run_test_ai
echo Running test_openai.py (tests AI provider setup)...
python test_openai.py
goto :run_complete

:run_complete
echo.
echo Script finished.
goto :eof

:error_exit
echo.
echo **************************************************
echo  An error occurred. Please check the messages above.
echo **************************************************
goto :eof

endlocal
