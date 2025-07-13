import gradio as gr
import os
import time
from main import main as generate_video_recap
from modules.manga_scraper import fetch_chapter_links, download_chapters

def get_available_mangas():
    manga_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and d != 'env' and d != 'modules' and not d.startswith('.')]
    return manga_dirs

def scrape_manga(series_url, output_json):
    if not series_url:
        return "Please enter a series URL.", "", ""

    if not output_json:
        manga_name = series_url.split("/")[-2].replace("-", " ").title()
        output_json = f"{manga_name.replace(' ', '_')}_chapters.json"

    fetch_chapter_links(series_url, output_json)

    download_chapters(output_json)

    return f"Manga scraped successfully! JSON file created at {output_json}", output_json, gr.update(choices=get_available_mangas())

def generate_recap(manga_dir, output_filename, lang, image_duration, width, height, force_restart):
    if not manga_dir:
        return "Please select a manga directory.", None

    if not output_filename:
        output_filename = f"{manga_dir}_recap.mp4"

    class Args:
        def __init__(self):
            self.chapters_dir = manga_dir
            self.output = output_filename
            self.lang = lang
            self.temp = "temp"
            self.image_duration = image_duration if image_duration else None
            self.width = width
            self.height = height
            self.force = force_restart
            self.max_chapters = None
            self.model = None
            self.prompt = None
            self.voice = None
            self.use_tts = False

    args = Args()

    try:
        generate_video_recap(args)

        video_path = os.path.join(os.getcwd(), output_filename)
        if os.path.exists(video_path):
            return f"Video generated successfully! You can find it at {video_path}", video_path
        else:
            return "Video generation failed. Check the console for logs.", None

    except Exception as e:
        return f"An error occurred: {e}", None


with gr.Blocks() as demo:
    gr.Markdown("# My Manga Recap Generator")

    with gr.Tab("Scrape Manga"):
        series_url_input = gr.Textbox(label="Manga Series URL")
        json_output_input = gr.Textbox(label="Output JSON Filename (optional)")
        scrape_button = gr.Button("Scrape and Download")
        scrape_output_text = gr.Textbox(label="Scraping Status", interactive=False)

    with gr.Tab("Generate Recap"):
        manga_dropdown = gr.Dropdown(label="Select Manga", choices=get_available_mangas())
        output_filename_input = gr.Textbox(label="Output Video Filename (e.g., recap.mp4)")

        with gr.Row():
            lang_input = gr.Textbox(label="Language", value="pt")
            image_duration_input = gr.Number(label="Image Duration (seconds, optional)")

        with gr.Row():
            width_input = gr.Number(label="Video Width", value=1280)
            height_input = gr.Number(label="Video Height", value=720)

        force_restart_checkbox = gr.Checkbox(label="Force Restart (ignore checkpoint)")

        generate_button = gr.Button("Generate Recap Video")

        recap_output_text = gr.Textbox(label="Generation Status", interactive=False)
        recap_output_video = gr.Video(label="Generated Recap")

    scrape_button.click(
        scrape_manga,
        inputs=[series_url_input, json_output_input],
        outputs=[scrape_output_text, json_output_input, manga_dropdown]
    )

    generate_button.click(
        generate_recap,
        inputs=[manga_dropdown, output_filename_input, lang_input, image_duration_input, width_input, height_input, force_restart_checkbox],
        outputs=[recap_output_text, recap_output_video]
    )

if __name__ == "__main__":
    demo.launch()
