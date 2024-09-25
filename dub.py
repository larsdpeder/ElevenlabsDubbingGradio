import gradio as gr
import os
import time
import json
from typing import Optional, Dict
from elevenlabs import ElevenLabs
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize ElevenLabs client
eleven = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# Define language options with codes
languages: Dict[str, str] = {
    "English": "en", "Hindi": "hi", "Portuguese": "pt", "Chinese": "zh", "Spanish": "es",
    "French": "fr", "German": "de", "Japanese": "ja", "Arabic": "ar", "Russian": "ru",
    "Korean": "ko", "Indonesian": "id", "Italian": "it", "Dutch": "nl", "Turkish": "tr",
    "Polish": "pl", "Swedish": "sv", "Filipino": "fil", "Malay": "ms", "Romanian": "ro",
    "Ukrainian": "uk", "Greek": "el", "Czech": "cs", "Danish": "da", "Finnish": "fi",
    "Bulgarian": "bg", "Croatian": "hr", "Slovak": "sk", "Tamil": "ta"
}

def wait_for_dubbing_completion(dubbing_id: str, progress: Optional[gr.Progress] = None) -> bool:
    MAX_ATTEMPTS = 360  # Increased to allow for up to 1 hour of processing
    CHECK_INTERVAL = 10  # In seconds

    for attempt in range(MAX_ATTEMPTS):
        try:
            metadata = eleven.dubbing.get_dubbing_project_metadata(dubbing_id)
            if metadata.status == "dubbed":
                if progress:
                    progress(1, desc="Dubbing completed successfully.")
                return True
            elif metadata.status == "dubbing":
                if progress:
                    progress((attempt + 1) / MAX_ATTEMPTS, desc=f"Dubbing in progress... Time elapsed: {attempt * CHECK_INTERVAL} seconds")
                time.sleep(CHECK_INTERVAL)
            else:
                if progress:
                    progress(1, desc=f"Dubbing failed: {metadata.error_message}")
                return False
        except Exception as e:
            print(f"Error in wait_for_dubbing_completion: {str(e)}")
            if progress:
                progress(1, desc=f"Error checking dubbing status: {str(e)}")
            return False

    if progress:
        progress(1, desc="Dubbing timed out after 1 hour")
    return False

def download_dubbed_file(dubbing_id: str, language_code: str, output_dir: str, progress: Optional[gr.Progress] = None) -> Optional[str]:
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, f"{dubbing_id}_{language_code}.mp4")
    try:
        with open(file_path, "wb") as file:
            for chunk in eleven.dubbing.get_dubbed_file(dubbing_id, language_code):
                file.write(chunk)
        if progress:
            progress(1, desc=f"File downloaded successfully: {file_path}")
        return file_path
    except Exception as e:
        print(f"Error in download_dubbed_file: {str(e)}")
        if progress:
            progress(1, desc=f"Error downloading dubbed file: {str(e)}")
        return None

def create_dub(input_type: str, input_data, source_language: str, target_language: str, output_dir: str, progress: Optional[gr.Progress] = None) -> str:
    try:
        if progress:
            progress(0.1, desc="Initiating dubbing process")
        
        if input_type == "file":
            if not input_data:
                return "No file uploaded."
            file_path = input_data.name
            with open(file_path, "rb") as audio_file:
                response = eleven.dubbing.dub_a_video_or_an_audio_file(
                    file=(os.path.basename(file_path), audio_file, "video/mp4"),
                    target_lang=languages[target_language],
                    source_lang=languages[source_language],
                )
        else:  # URL
            response = eleven.dubbing.dub_a_video_or_an_audio_file(
                source_url=input_data,
                target_lang=languages[target_language],
                source_lang=languages[source_language],
            )

        dubbing_id = response.dubbing_id
        if progress:
            progress(0.2, desc="Dubbing initiated, waiting for completion")

        if wait_for_dubbing_completion(dubbing_id, progress):
            if progress:
                progress(0.9, desc="Dubbing completed, downloading file")
            output_file_path = download_dubbed_file(dubbing_id, languages[target_language], output_dir, progress)
            if output_file_path:
                return f"Dubbing was successful! File saved at: {output_file_path}"
            else:
                return "Dubbing completed but file download failed."
        else:
            return "Dubbing failed or timed out."
    except Exception as e:
        print(f"Error in create_dub: {str(e)}")
        error_message = str(e)
        if hasattr(e, 'status_code') and hasattr(e, 'body'):
            try:
                error_body = json.loads(e.body)
                if 'detail' in error_body:
                    error_message = f"Error {e.status_code}: {error_body['detail']['message']}"
            except json.JSONDecodeError:
                error_message = f"Error {e.status_code}: {e.body}"
        return f"An error occurred: {error_message}"

# Create Gradio interface
with gr.Blocks() as iface:
    gr.Markdown("# ElevenLabs Video Dubbing Interface")
    
    with gr.Tab("File Upload"):
        file_input = gr.File(label="Upload Video File")
        file_source_lang = gr.Dropdown(list(languages.keys()), label="Source Language", value="English")
        file_target_lang = gr.Dropdown(list(languages.keys()), label="Target Language", value="Spanish")
        file_output_dir = gr.Textbox(label="Output Directory", value="output", placeholder="Enter the output directory path")
        file_submit = gr.Button("Dub Video File")
        file_output = gr.Textbox(label="Result")

    with gr.Tab("URL Input"):
        url_input = gr.Textbox(label="Enter Video URL (YouTube, TikTok, Twitter, or Vimeo)")
        url_source_lang = gr.Dropdown(list(languages.keys()), label="Source Language", value="English")
        url_target_lang = gr.Dropdown(list(languages.keys()), label="Target Language", value="Spanish")
        url_output_dir = gr.Textbox(label="Output Directory", value="output", placeholder="Enter the output directory path")
        url_submit = gr.Button("Dub Video from URL")
        url_output = gr.Textbox(label="Result")

    file_submit.click(
        create_dub,
        inputs=[
            gr.Textbox(value="file", visible=False),
            file_input,
            file_source_lang,
            file_target_lang,
            file_output_dir
        ],
        outputs=file_output
    )

    url_submit.click(
        create_dub,
        inputs=[
            gr.Textbox(value="url", visible=False),
            url_input,
            url_source_lang,
            url_target_lang,
            url_output_dir
        ],
        outputs=url_output
    )

iface.launch()
