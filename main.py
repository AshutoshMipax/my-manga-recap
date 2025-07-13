import argparse
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any

from modules.ocr import extract_text_from_chapter
from modules.script_narrator import generate_scripts_from_ocr
from modules.audio_gen import text_to_speech
from modules.video_gen import create_video
from modules.config import (
    DEFAULT_TEMP_DIR,
    DEFAULT_LANG,
    DEFAULT_IMAGE_DURATION,
    DEFAULT_VIDEO_WIDTH,
    DEFAULT_VIDEO_HEIGHT,
)


def load_checkpoint(temp_dir: str) -> Dict[str, Any]:
    """Load checkpoint data if it exists."""
    checkpoint_file = os.path.join(temp_dir, "video_checkpoint.json")
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
            print(f"🔄 Checkpoint encontrado: continuando da etapa '{checkpoint.get('last_step', 'unknown')}'")
            return checkpoint
        except Exception as e:
            print(f"⚠️  Erro ao carregar checkpoint: {e}")
    return {}


def save_checkpoint(temp_dir: str, step: str, data: Dict[str, Any]) -> None:
    """Save checkpoint data."""
    checkpoint_file = os.path.join(temp_dir, "video_checkpoint.json")
    checkpoint_data = {
        "last_step": step,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": data
    }
    
    try:
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Checkpoint salvo: {step}")
    except Exception as e:
        print(f"⚠️  Erro ao salvar checkpoint: {e}")


def delete_checkpoint(temp_dir: str) -> None:
    """Delete checkpoint file after successful completion."""
    checkpoint_file = os.path.join(temp_dir, "video_checkpoint.json")
    try:
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)
            print("🗑️  Checkpoint removido após conclusão")
    except Exception as e:
        print(f"⚠️  Erro ao remover checkpoint: {e}")


def parse_args():
    parser = argparse.ArgumentParser(description="Generate video recap from manga chapters using AI providers")
    parser.add_argument("--chapters_dir", required=True, help="Directory containing chapter folders with images")
    parser.add_argument("--output", required=True, help="Output video file")
    parser.add_argument("--lang", default=DEFAULT_LANG, help="Language for narration")
    parser.add_argument("--temp", default=DEFAULT_TEMP_DIR, help="Temporary working directory")
    parser.add_argument("--image_duration", type=float, default=DEFAULT_IMAGE_DURATION, help="Duration for each image in seconds")
    parser.add_argument("--width", type=int, default=DEFAULT_VIDEO_WIDTH, help="Output video width")
    parser.add_argument("--height", type=int, default=DEFAULT_VIDEO_HEIGHT, help="Output video height")
    parser.add_argument("--force", action="store_true", help="Force restart from beginning (ignore checkpoint)")
    parser.add_argument("--max-chapters", type=int, help="Limit processing to first N chapters (useful for testing)")
    
    # Deprecated arguments for backward compatibility
    parser.add_argument("--model", help="[DEPRECATED] Model parameter - now handled by AI providers")
    parser.add_argument("--prompt", help="[DEPRECATED] Prompt parameter - now handled by AI providers") 
    parser.add_argument("--voice", help="[DEPRECATED] Voice parameter - now handled by AI providers")
    parser.add_argument("--use_tts", action="store_true", help="[DEPRECATED] TTS flag - now automatic")
    
    return parser.parse_args()


def main(args=None) -> None:
    if args is None:
        args = parse_args()

    os.makedirs(args.temp, exist_ok=True)
    
    # Warn about deprecated arguments
    deprecated_args = ['model', 'prompt', 'voice', 'use_tts']
    for arg in deprecated_args:
        if getattr(args, arg, None) is not None:
            print(f"⚠️  --{arg} é obsoleto - agora gerenciado pelos AI providers")
    
    start_time = time.time()
    print(f"🚀 Iniciando geração de vídeo recap com sistema de AI providers")
    print(f"📁 Diretório temporário: {args.temp}")
    print(f"🎬 Arquivo de saída: {args.output}")
    
    # Load checkpoint unless forced to restart
    checkpoint = {} if args.force else load_checkpoint(args.temp)
    
    # Discover chapter directories
    chapter_dirs = [os.path.join(args.chapters_dir, d)
                    for d in sorted(os.listdir(args.chapters_dir))
                    if os.path.isdir(os.path.join(args.chapters_dir, d))]
    if not chapter_dirs:
        raise ValueError("No chapter directories found")

    # Limit chapters if specified (useful for testing)
    if args.max_chapters:
        original_count = len(chapter_dirs)
        chapter_dirs = chapter_dirs[:args.max_chapters]
        if len(chapter_dirs) < original_count:
            print(f"🧪 MODO TESTE: Processando apenas {len(chapter_dirs)}/{original_count} capítulos")

    print(f"📚 Encontrados {len(chapter_dirs)} capítulos")

    # Step 1: OCR text extraction
    ocr_file = os.path.join(args.temp, "chapter_texts.json")
    if checkpoint.get("last_step") in ["ocr", "scripts", "audio", "video"] and os.path.exists(ocr_file):
        print("✅ OCR: Carregando textos salvos...")
        with open(ocr_file, "r", encoding="utf-8") as f:
            chapter_data = json.load(f)
    else:
        print("🔍 OCR: Extraindo texto das imagens...")
        step_start = time.time()
        
        # Extract text with metadata
        chapter_data = []
        for i, chapter_dir in enumerate(chapter_dirs, 1):
            print(f"📚 Capítulo {i}/{len(chapter_dirs)}: {os.path.basename(chapter_dir)}")
            chapter_result = extract_text_from_chapter(chapter_dir)
            chapter_data.append(chapter_result)
            
            # Show summary for each chapter
            total_pages = chapter_result["total_pages"]
            has_text = chapter_result["has_meaningful_content"]
            status = "✅ Texto encontrado" if has_text else "⚠️  Pouco/nenhum texto"
            print(f"   📄 {total_pages} páginas processadas - {status}")
        
        # Save complete OCR results with metadata
        with open(ocr_file, "w", encoding="utf-8") as f:
            json.dump(chapter_data, f, indent=2, ensure_ascii=False)
        
        save_checkpoint(args.temp, "ocr", {"chapter_texts_file": ocr_file})
        
        # Summary report
        total_pages = sum(ch["total_pages"] for ch in chapter_data)
        chapters_with_text = sum(1 for ch in chapter_data if ch["has_meaningful_content"])
        print(f"✅ OCR concluído em {time.time() - step_start:.2f}s")
        print(f"📊 Resumo: {total_pages} páginas em {len(chapter_data)} capítulos")
        print(f"📝 {chapters_with_text}/{len(chapter_data)} capítulos com texto detectado")

    # Step 2: Generate narration scripts using AI providers
    scripts_file = os.path.join(args.temp, "narration_scripts.json")
    if checkpoint.get("last_step") in ["scripts", "audio", "video"] and os.path.exists(scripts_file):
        print("✅ Roteiros: Carregando roteiros salvos...")
        with open(scripts_file, "r", encoding="utf-8") as f:
            scripts_data = json.load(f)
        script = scripts_data["full_script"]
    else:
        print("📝 Roteiros: Gerando com sistema de AI providers...")
        step_start = time.time()
        
        # Generate scripts using AI providers
        scripts_data = generate_scripts_from_ocr(chapter_data)
        script = scripts_data["full_script"]

        # Save scripts
        with open(scripts_file, "w", encoding="utf-8") as f:
            json.dump(scripts_data, f, indent=2, ensure_ascii=False)
        
        save_checkpoint(args.temp, "scripts", {"scripts_file": scripts_file})
        print(f"✅ Roteiros concluídos em {time.time() - step_start:.2f}s")
        print(f"📊 {scripts_data['total_chapters']} capítulos, {scripts_data['script_metadata']['word_count']} palavras")

    # Step 3: Generate audio narration using AI providers
    audio_path = os.path.join(args.temp, "narration.mp3")
    if checkpoint.get("last_step") in ["audio", "video"] and os.path.exists(audio_path):
        print("✅ Áudio: Carregando narração salva...")
    else:
        print("🎤 Áudio: Gerando com sistema de AI providers...")
        step_start = time.time()
        
        # Generate audio using AI providers
        text_to_speech(script, audio_path, lang=args.lang)

        save_checkpoint(args.temp, "audio", {"audio_file": audio_path})
        print(f"✅ Áudio concluído em {time.time() - step_start:.2f}s")

    # Step 4: Generate video
    if checkpoint.get("last_step") == "video" and os.path.exists(args.output):
        print("✅ Vídeo: Vídeo já existe!")
    else:
        print("🎬 Vídeo: Gerando vídeo final...")
        step_start = time.time()
        create_video(
            chapter_dirs,
            audio_path,
            args.output,
            script=script,
            image_duration=args.image_duration,
            width=args.width,
            height=args.height,
            temp_dir=args.temp,
        )
        
        save_checkpoint(args.temp, "video", {"output_file": args.output})
        print(f"✅ Vídeo concluído em {time.time() - step_start:.2f}s")

    # Final report
    total_time = time.time() - start_time
    print(f"\n🎉 Processo completo com sistema de AI providers!")
    print(f"⏱️  Tempo total: {total_time:.2f}s")
    print(f"🎬 Vídeo salvo em: {args.output}")
    print(f"📁 Arquivos temporários em: {args.temp}")
    print(f"\n💡 Dicas:")
    print(f"   • Use --force para recomeçar do zero")
    print(f"   • Configure OPENAI_API_KEY para qualidade premium")


if __name__ == "__main__":
    main()
