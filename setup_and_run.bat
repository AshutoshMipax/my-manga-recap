@echo off
setlocal enabledelayedexpansion

REM =======================================
REM  My Manga Recap - Local Model Setup
REM =======================================
echo.
echo =======================================
echo  My Manga Recap - Local Model Setup
echo =======================================
echo.

REM --- Configuration ---
set "PYTHON_VERSION=3.9"
set "VENV_NAME=.venv"
set "REQUIREMENTS_FILE=requirements.txt"

REM =======================================
REM  1. Check for Python
REM =======================================
echo --- Stage: Checking for Python ---
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: python.exe not found in your system's PATH.
    echo Please install Python %PYTHON_VERSION% or higher and ensure it's added to your PATH during installation.
    pause
    goto :error_exit
)
echo Python found.
echo.

REM =======================================
REM  2. Create and Activate Virtual Environment
REM =======================================
echo --- Stage: Virtual Environment Setup ---
REM Check if the activate script exists. If not, create the venv.
if not exist "%VENV_NAME%\Scripts\activate.bat" (
    echo Virtual environment not found. Creating it now in "%VENV_NAME%"...
    python -m venv "%VENV_NAME%"
    if !errorlevel! neq 0 (
        echo ERROR: Failed to create the virtual environment.
        echo Please check your Python installation (e.g., ensure the 'venv' module is available) and directory permissions.
        pause
        goto :error_exit
    )
    echo Virtual environment created successfully.
) else (
    echo Virtual environment already exists.
)

echo Activating virtual environment...
call "%VENV_NAME%\Scripts\activate.bat"
if !errorlevel! neq 0 (
    echo ERROR: Failed to activate the virtual environment.
    pause
    goto :error_exit
)
echo Virtual environment is active.
echo.
pause

REM =======================================
REM  3. Install Dependencies
REM =======================================
echo --- Stage: Installing Dependencies ---
echo Installing dependencies from %REQUIREMENTS_FILE%...
pip install -r "%REQUIREMENTS_FILE%"
if !errorlevel! neq 0 (
    echo ERROR: Failed to install dependencies from %REQUIREMENTS_FILE%.
    pause
    goto :error_exit
)
echo Dependencies from %REQUIREMENTS_FILE% installed successfully.
echo.

echo Installing additional dependencies for local AI models...
echo Note: For optimal GPU support, you might need to install a CUDA-specific version of PyTorch first.
echo See https://pytorch.org/get-started/locally/ for instructions.
pip install bitsandbytes accelerate sentencepiece protobuf
if !errorlevel! neq 0 (
    echo ERROR: Failed to install additional AI model dependencies (bitsandbytes, accelerate, etc.).
    pause
    goto :error_exit
)
echo Additional AI model dependencies installed successfully.
echo.
pause

REM =======================================
REM  4. Check for Tesseract OCR
REM =======================================
echo --- Stage: Checking for Tesseract OCR ---
where tesseract >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo ======================================================================
    echo  WARNING: Tesseract OCR not found in your system's PATH.
    echo ======================================================================
    echo  Tesseract is used as a fallback OCR engine if local/cloud AI providers fail.
    echo  To install it:
    echo    1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo    2. IMPORTANT: During installation, ensure you check the box to "Add Tesseract to your system PATH".
    echo    3. Also, add the language data for English ("eng") and Portuguese ("por").
    echo ======================================================================
    echo.
) else (
    echo Tesseract OCR found.
)
echo.
pause

REM =======================================
REM  5. Final Configuration Reminder
REM =======================================
echo.
echo ======================================================================
echo  ACTION REQUIRED: Configure Your Models
echo ======================================================================
echo  The final step is to tell the program which AI models to use.
echo  Open the file at:
echo.
echo    modules\config.py
echo.
echo  And edit the following variables with either a Hugging Face model ID
echo  (which will be downloaded automatically) or a path to a local model
echo  you've already downloaded.
echo.
echo  --- For Local Vision/OCR ---
echo  LLAVA_MODEL_ID = "llava-hf/llava-1.5-7b-hf"
echo  LLAVA_QUANTIZATION = "4bit"
echo.
echo  --- For Local Text Generation ---
echo  LOCAL_LLM_MODEL_ID = "NousResearch/Hermes-2-Pro-Llama-3-8B"
echo  LOCAL_LLM_PROMPT_FORMAT = "chatml"
echo  LOCAL_LLM_QUANTIZATION = "4bit"
echo.
echo  --- Preferred Provider ---
echo  PREFERRED_AI_PROVIDER = "local"
echo.
echo  You can also set QUANTIZATION to "8bit" or None (no quantization).
echo  If you want to use OpenAI, set PREFERRED_AI_PROVIDER = "openai"
echo  and make sure your OPENAI_API_KEY is set in 'modules/config.py' or an '.env' file.
echo ======================================================================
echo.
pause

REM =======================================
REM  6. Run Application
REM =======================================
:run_menu
echo.
echo --- Ready to Run ---
echo 1. Run Main Process (generates a video from start to finish)
echo 2. Run Interactive CLI (menu with more options)
echo 3. Test AI Providers (checks if models load correctly)
echo 4. Exit
echo.
choice /C 1234 /M "Enter your choice [1, 2, 3, 4]:"

if errorlevel 4 goto :eof
if errorlevel 3 goto :run_test_ai
if errorlevel 2 goto :run_interactive
if errorlevel 1 goto :run_main

:run_main
echo Running main.py...
echo To pass arguments, run from command line, e.g.: python main.py --chapters_dir manga --output video.mp4
python main.py %*
goto :run_complete

:run_interactive
echo Running interactive_cli.py...
python interactive_cli.py
goto :run_complete

:run_test_ai
echo Running test_openai.py...
python test_openai.py
goto :run_complete

:run_complete
echo.
echo Script finished.
pause
goto :eof

:error_exit
echo.
echo **************************************************
echo  An error occurred. Please check the messages above.
echo  The script will now exit.
echo **************************************************
pause
goto :eof
