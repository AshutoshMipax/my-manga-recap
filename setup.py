import os
import sys
import subprocess
import shutil
import venv

# --- Configuration ---
VENV_NAME = ".venv"
REQUIREMENTS_FILE = "requirements.txt"
EXTRA_DEPS = ["bitsandbytes", "accelerate", "sentencepiece", "protobuf"]

# --- Helper Functions ---
def print_header(title):
    """Prints a formatted header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_error(message):
    """Prints an error message."""
    print(f"\n[ERROR] {message}")

def print_warning(message):
    """Prints a warning message."""
    print(f"\n[WARNING] {message}")

def print_info(message):
    """Prints an informational message."""
    print(f"\n[INFO] {message}")

def get_executable(name):
    """Cross-platform way to get the path to an executable in the venv."""
    if sys.platform == "win32":
        return os.path.join(VENV_NAME, "Scripts", name)
    else:
        return os.path.join(VENV_NAME, "bin", name)

def run_command(command, description):
    """Runs a command and handles errors."""
    print_info(f"Running: {description}")
    try:
        # Use list format for command to avoid shell injection issues
        process = subprocess.run(command, check=True, text=True, capture_output=True)
        if process.stdout:
            print(process.stdout)
        if process.stderr:
            print(process.stderr)
        return True
    except FileNotFoundError:
        print_error(f"Command not found: {command[0]}. Is it installed and in your PATH?")
        return False
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {' '.join(command)}")
        print("--- stdout ---")
        print(e.stdout)
        print("--- stderr ---")
        print(e.stderr)
        return False
    except Exception as e:
        print_error(f"An unexpected error occurred: {e}")
        return False

# --- Main Setup Logic ---
def main():
    """Main setup function."""
    print_header("My Manga Recap - Python Setup Script")

    # 1. Check if we are running inside a virtual environment
    if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
        print_warning("This script is not running in a virtual environment.")
        print("It's highly recommended to use a virtual environment to manage dependencies.")
        print(f"\nTo create and activate one before running this script:")
        print(f"  1. python -m venv {VENV_NAME}")
        if sys.platform == "win32":
            print(f"  2. {VENV_NAME}\\Scripts\\activate")
        else:
            print(f"  2. source {VENV_NAME}/bin/activate")
        print(f"  3. python {os.path.basename(__file__)}")

        # Ask user if they want to continue anyway
        choice = input("\nDo you want to continue and install packages globally? (y/N): ").lower()
        if choice != 'y':
            print_info("Setup aborted by user.")
            sys.exit(0)

    # 2. Install dependencies
    print_header("Installing Dependencies")
    pip_executable = get_executable("pip")

    # Install from requirements.txt
    if os.path.exists(REQUIREMENTS_FILE):
        if not run_command([pip_executable, "install", "-r", REQUIREMENTS_FILE], f"Installing dependencies from {REQUIREMENTS_FILE}"):
            print_error("Could not install dependencies from requirements.txt. Aborting.")
            sys.exit(1)
    else:
        print_warning(f"{REQUIREMENTS_FILE} not found. Skipping.")

    # Install extra dependencies
    if EXTRA_DEPS:
        if not run_command([pip_executable, "install"] + EXTRA_DEPS, f"Installing additional libraries: {', '.join(EXTRA_DEPS)}"):
            print_error("Could not install additional dependencies. Your setup might be incomplete.")
        else:
            print_info("All dependencies installed successfully.")

    # 3. Check for Tesseract
    print_header("Checking for External Tools (Tesseract OCR)")
    if shutil.which("tesseract"):
        print_info("Tesseract OCR found in PATH.")
    else:
        print_warning("Tesseract OCR not found in your system's PATH.")
        print("Tesseract is used as a fallback OCR engine if AI providers fail.")
        print("If you need it, please install it from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("IMPORTANT: During installation, ensure you check the box to 'Add Tesseract to your system PATH'.")

    # 4. Check model configuration
    print_header("Checking Model Configuration")
    try:
        # Dynamically import the config to check it
        from modules.config import LLAVA_MODEL_ID, LOCAL_LLM_MODEL_ID, PREFERRED_AI_PROVIDER, OPENAI_API_KEY

        print(f"Preferred AI Provider for text generation: '{PREFERRED_AI_PROVIDER}'")

        if PREFERRED_AI_PROVIDER == "local":
            print_info("Local provider is preferred. Checking local model configurations...")
            # Check if default placeholder models are still being used
            if "llava-hf/llava-1.5-7b-hf" in LLAVA_MODEL_ID:
                print_warning("LLaVA model is set to the default example ('llava-hf/llava-1.5-7b-hf').")
            else:
                print_info(f"LLaVA model configured: {LLAVA_MODEL_ID}")

            if "NousResearch/Hermes-2-Pro-Llama-3-8B" in LOCAL_LLM_MODEL_ID:
                print_warning("Local LLM is set to the default example ('NousResearch/Hermes-2-Pro-Llama-3-8B').")
            else:
                print_info(f"Local LLM configured: {LOCAL_LLM_MODEL_ID}")

            print("\nTo use your own models, please edit the file at 'modules/config.py'.")
            print("The first time you run the app with a Hugging Face model ID, it will be downloaded automatically.")

        elif PREFERRED_AI_PROVIDER == "openai":
            print_info("OpenAI provider is preferred.")
            if not OPENAI_API_KEY:
                print_warning("OpenAI is preferred, but OPENAI_API_KEY is not set in your config or .env file.")
            else:
                print_info("OPENAI_API_KEY is configured.")

    except (ImportError, AttributeError) as e:
        print_error(f"Could not check 'modules/config.py'. Ensure it exists and is correctly formatted. Error: {e}")

    # 5. Final instructions and run menu
    print_header("Setup Complete - Ready to Run")
    while True:
        print("\nChoose an option:")
        print("  1. Run Main Process (generates a video from start to finish)")
        print("  2. Run Interactive CLI (menu with more options)")
        print("  3. Test AI Providers (checks if models load correctly)")
        print("  4. Exit")

        choice = input("\nEnter your choice [1-4]: ").strip()

        if choice == '1':
            print_info("Starting main process...")
            subprocess.run([get_executable("python"), "main.py"])
        elif choice == '2':
            print_info("Starting interactive CLI...")
            subprocess.run([get_executable("python"), "interactive_cli.py"])
        elif choice == '3':
            print_info("Starting AI provider test...")
            subprocess.run([get_executable("python"), "test_openai.py"])
        elif choice == '4':
            print_info("Exiting.")
            break
        else:
            print_error("Invalid choice. Please enter a number from 1 to 4.")

if __name__ == "__main__":
    main()
