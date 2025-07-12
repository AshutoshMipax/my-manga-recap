"""OCR provider system with fallback between Tesseract, TrOCR, and LLaVA."""

from abc import ABC, abstractmethod
from typing import Optional, List

import base64
import io

from PIL import Image
import pytesseract

# Attempt to import transformers and torch for LLaVA and TrOCR
try:
    from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration, BitsAndBytesConfig
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    LlavaNextProcessor = None
    LlavaNextForConditionalGeneration = None
    BitsAndBytesConfig = None
    torch = None

try:
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    TROCR_TRANSFORMERS_AVAILABLE = True
except ImportError:
    TROCR_TRANSFORMERS_AVAILABLE = False
    TrOCRProcessor = None
    VisionEncoderDecoderModel = None


from .config import OPENAI_API_KEY, OPENAI_VISION_MODEL, DEFAULT_LANG, LLAVA_MODEL_ID, LLAVA_QUANTIZATION


class OCRProvider(ABC):
    """Base class for OCR providers."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if provider can be used."""

    @abstractmethod
    def extract_text(self, image: Image.Image) -> str:
        """Extract text from a PIL image."""


class TesseractProvider(OCRProvider):
    """Default OCR provider using pytesseract."""

    def is_available(self) -> bool:
        return True

    def extract_text(self, image: Image.Image) -> str:
        return pytesseract.image_to_string(image, lang="eng+por")


class TrOCRProvider(OCRProvider):
    """OCR using HuggingFace TrOCR (transformers)."""

    def __init__(self) -> None:
        self._available = False
        self._error = "TrOCR dependencies (transformers, torch) not found."
        if TROCR_TRANSFORMERS_AVAILABLE and torch:
            try:
                self.processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-printed")
                self.model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-printed")
                self.model.eval() # Set to evaluation mode
                if torch.cuda.is_available():
                    self.model = self.model.to("cuda")
                self._available = True
            except Exception as exc:  # pragma: no cover - optional dependency
                self._error = f"Error initializing TrOCR: {exc}"
        else: # pragma: no cover
            print(f"⚠️ TrOCR not available: {self._error}")


    def is_available(self) -> bool:
        return getattr(self, "_available", False)

    def extract_text(self, image: Image.Image) -> str:
        if not self.is_available():
            raise RuntimeError(getattr(self, "_error", "TrOCR not available or not initialized correctly."))

        # Ensure image is RGB
        if image.mode != "RGB":
            image = image.convert("RGB")

        pixel_values = self.processor(images=image, return_tensors="pt").pixel_values
        if torch.cuda.is_available():
            pixel_values = pixel_values.to("cuda")

        with torch.no_grad():
            generated_ids = self.model.generate(pixel_values)
        text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return text.strip()


class OpenAIVisionProvider(OCRProvider):
    """OCR provider using OpenAI vision models with contextual extraction."""

    def __init__(self, model: Optional[str] = None, lang: str = DEFAULT_LANG) -> None:
        self.model = model or OPENAI_VISION_MODEL
        self.lang = lang

    def is_available(self) -> bool:
        if not OPENAI_API_KEY:
            return False
        try:
            import openai  # type: ignore
        except Exception:
            return False
        return True

    def extract_text(self, image: Image.Image) -> str:
        if not self.is_available():
            raise RuntimeError("OpenAI not configured")

        import openai  # type: ignore

        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        prompt = (
            "Read the text from this manga page and identify any characters and "
            "context. Reply in {lang}."
        ).format(lang=self.lang)

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                ],
            }
        ]

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
        )

        return response.choices[0].message.get("content", "").strip()


class LlavaProvider(OCRProvider):
    """OCR provider using local LLaVA model."""

    def __init__(self, model_id: str = LLAVA_MODEL_ID, quantization: Optional[str] = LLAVA_QUANTIZATION, lang: str = DEFAULT_LANG) -> None:
        self.model_id = model_id
        self.quantization = quantization
        self.lang = lang
        self._available = False
        self._error = "LLaVA dependencies (transformers, torch) not found or model failed to load."

        if not TRANSFORMERS_AVAILABLE or not LlavaNextProcessor or not LlavaNextForConditionalGeneration or not torch:
            print(f"⚠️ LLaVA not available: Missing core dependencies (transformers/torch).")
            return

        try:
            print(f"⏳ Initializing LLaVA provider with model: {self.model_id}")
            quantization_config = None
            if self.quantization == "4bit":
                if not BitsAndBytesConfig: # Should be caught by TRANSFORMERS_AVAILABLE but good to double check
                    raise ImportError("BitsAndBytesConfig not found for 4-bit quantization.")
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16
                )
                print("   Using 4-bit quantization (BitsAndBytesConfig)")
            elif self.quantization == "8bit":
                if not BitsAndBytesConfig:
                    raise ImportError("BitsAndBytesConfig not found for 8-bit quantization.")
                quantization_config = BitsAndBytesConfig(load_in_8bit=True)
                print("   Using 8-bit quantization (BitsAndBytesConfig)")

            self.processor = LlavaNextProcessor.from_pretrained(self.model_id)
            self.model = LlavaNextForConditionalGeneration.from_pretrained(
                self.model_id,
                quantization_config=quantization_config,
                torch_dtype=torch.float16 if torch.cuda.is_available() and self.quantization else torch.float32, # float16 for GPU if quantized, else float32
                low_cpu_mem_usage=True, # Try to reduce CPU RAM usage during model loading
            )

            if torch.cuda.is_available():
                # Model is moved to GPU by from_pretrained if quantization_config is used and CUDA is available.
                # If not using quantization, manually move it.
                if not quantization_config:
                    self.model = self.model.to("cuda")
                print("   LLaVA model loaded on GPU.")
            else:
                print("   LLaVA model loaded on CPU. This might be slow.")

            self.model.eval() # Set to evaluation mode
            self._available = True
            print("✅ LLaVA provider initialized successfully.")

        except ImportError as e: # Specifically catch import errors for BitsAndBytes
            self._error = f"LLaVA initialization failed due to missing dependency for quantization: {e}. Try pip install bitsandbytes."
            print(f" condemning LLaVA provider: {self._error}")
        except Exception as exc:
            self._error = f"Error initializing LLaVA model {self.model_id}: {exc}"
            print(f" condemning LLaVA provider: {self._error}")

    def is_available(self) -> bool:
        return self._available

    def extract_text(self, image: Image.Image) -> str:
        if not self.is_available():
            raise RuntimeError(self._error)

        if image.mode != "RGB":
            image = image.convert("RGB")

        # LLaVA specific prompt for OCR-like text extraction
        # The prompt might need adjustment based on the specific LLaVA model fine-tuning.
        # For a general LLaVA model, a direct instruction is usually best.
        prompt = f"<image>\nUSER: Read all text from this manga page. Focus on extracting the dialogue and narration text accurately. Respond in {self.lang}.\nASSISTANT:"

        try:
            inputs = self.processor(text=prompt, images=image, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            with torch.no_grad():
                generated_ids = self.model.generate(**inputs, max_new_tokens=768) # Increased max_new_tokens

            # Decode the full output and then try to extract the assistant's response
            full_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]

            # Extract content after "ASSISTANT:"
            # This logic might need to be robust if the model doesn't strictly follow the prompt format.
            assistant_marker = "ASSISTANT:"
            if assistant_marker in full_text:
                extracted_text = full_text.split(assistant_marker, 1)[-1].strip()
            else:
                # Fallback if the marker is not found (e.g. some models might just output the text directly)
                # This might happen if the model is specifically fine-tuned for OCR and doesn't need the full chat structure.
                # Or, if the prompt structure itself was consumed/modified by the model.
                # We take the last part of the prompt and hope the model's answer follows.
                prompt_user_part = prompt.split("USER:")[-1].split("ASSISTANT:")[0].strip()
                if full_text.startswith(prompt_user_part): # if the model output includes the prompt
                    extracted_text = full_text[len(prompt_user_part):].strip()
                else:
                    extracted_text = full_text # Best guess

            return extracted_text

        except Exception as e:
            print(f"⚠️ Error during LLaVA text extraction: {e}")
            # Consider re-raising or returning a specific error string
            return f"[LLaVA Error: {e}]"


class OCRManager:
    """Manages multiple OCR providers with fallback."""

    def __init__(self, provider_name: Optional[str] = None, llava_model_id: str = LLAVA_MODEL_ID, llava_quantization: Optional[str] = LLAVA_QUANTIZATION) -> None:
        self.providers: List[OCRProvider] = []

        # Order of providers determines priority (first successful one is used)

        # 1. LLaVA Provider (if specified or default)
        if provider_name in (None, "llava", "local"): # "local" can also map to LLaVA for OCR
            try:
                print("Attempting to initialize LLaVAProvider...")
                llava_provider = LlavaProvider(model_id=llava_model_id, quantization=llava_quantization, lang=DEFAULT_LANG)
                if llava_provider.is_available():
                    self.providers.append(llava_provider)
                    print("✅ LLaVAProvider added to OCRManager.")
                else:
                    print(f"⚠️ LLaVA OCR provider unavailable: {getattr(llava_provider, '_error', 'Unknown error')}")
            except Exception as exc:  # pragma: no cover - safety
                print(f"⚠️ Error initializing LLaVA OCR provider: {exc}")

        # 2. OpenAI Vision Provider (if specified or default and LLaVA not chosen/failed)
        if provider_name in (None, "openai"):
            # Only add OpenAI if LLaVA wasn't successfully added or if OpenAI is explicitly requested
            if not any(isinstance(p, LlavaProvider) for p in self.providers) or provider_name == "openai":
                try:
                    openai_provider = OpenAIVisionProvider(lang=DEFAULT_LANG)
                    if openai_provider.is_available():
                        self.providers.append(openai_provider)
                        print("✅ OpenAI Vision provider added to OCRManager.")
                    else:
                        print("⚠️ OpenAI Vision provider unavailable.")
                except Exception as exc:  # pragma: no cover - safety
                    print(f"⚠️ Error initializing OpenAI Vision provider: {exc}")

        # 3. TrOCR Provider (if specified or default and others not chosen/failed)
        if provider_name in (None, "trocr"):
            if not any(isinstance(p, (LlavaProvider, OpenAIVisionProvider)) for p in self.providers) or provider_name == "trocr":
                try:
                    trocr = TrOCRProvider()
                    if trocr.is_available():
                        self.providers.append(trocr)
                        print("✅ TrOCR provider added to OCRManager.")
                    else:
                        print(f"⚠️ TrOCR provider unavailable: {getattr(trocr, '_error', 'Unknown error')}")
                except Exception as exc:  # pragma: no cover - safety
                    print(f"⚠️ Error initializing TrOCR provider: {exc}")

        # 4. Tesseract (Always added as a final fallback if no other providers were added or if explicitly requested)
        if not self.providers or provider_name == "tesseract":
            if not any(isinstance(p, TesseractProvider) for p in self.providers): # Avoid duplicates
                self.providers.append(TesseractProvider())
                print("✅ Tesseract provider added as fallback to OCRManager.")

        if not self.providers: # Should not happen due to Tesseract fallback, but as a safeguard
             print("🚨 OCRManager: No OCR providers were successfully initialized! Defaulting to Tesseract.")
             self.providers.append(TesseractProvider())


    def extract_text(self, image_path: str) -> str:
        try:
            with Image.open(image_path) as img:
                # Ensure image is in a compatible mode if necessary, e.g. RGB
                if img.mode not in ['RGB', 'L']:
                    img = img.convert('RGB')

                # This loop MUST be inside the 'with' block
                for provider in self.providers:
                    try:
                        print(f"Attempting OCR with {provider.__class__.__name__}...")
                        text = provider.extract_text(img)
                        if text and text.strip() and not text.startswith("["):
                            print(f"✅ Success with {provider.__class__.__name__}.")
                            return text.strip()
                        else:
                            print(f"⚠️ {provider.__class__.__name__} returned empty or error-like text.")
                    except Exception as exc:
                        print(f"❌ {provider.__class__.__name__} failed: {exc}")

        except FileNotFoundError:
            print(f"❌ OCR Error: File not found at {image_path}")
            return f"[Erro: Arquivo não encontrado - {os.path.basename(image_path)}]"
        except Exception as exc:
            print(f"❌ OCR Error: Could not process image {image_path}. Reason: {exc}")
            return f"[Erro ao processar imagem: {exc}]"

        return "[Página vazia]"
