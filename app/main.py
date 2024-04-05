# main.py
import os
import shutil
#import gradio as gr
import requests
import urllib

from fastapi import FastAPI, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json

from typing import Dict
import uuid
import re

from utils.download_video import download_video
from utils.extract_audio import extract_audio
from utils.transcribe_audio import transcribe_audio
from utils.translate_text import translate_text
from utils.synthesize_audio import synthesize_audio, synthesize_audio_openai
from utils.replace_original_audio import replace_original_audio
from utils.AudioVideoTranslator import AudioVideoTranslator

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) #Set log level if needed

app = FastAPI()
# Define empty sessions dictionary
sessions = {}
api_keys: Dict[str, Dict[str, str]] = {}


import concurrent
from concurrent.futures import ThreadPoolExecutor

# Get the path to the downloads folder from the environment variable
download_folder = os.environ.get("DOWNLOAD_FOLDER", "./downloads")
# Get the path to the translations folder from the environment variable
translations_folder = os.environ.get("TRANSLATIONS_FOLDER", "./translations")



# Pass the pattern to executor like this : r"_(\d+)-(\d+)_(\d+)\.wav$"
def execute_files(file_paths, execution_function, pattern, max_workers=2):
    # Pattern to extract start time from filename
    pattern = re.compile(pattern)

    # Filter file_paths to include only those that match the pattern
    filtered_paths = [path for path in file_paths if pattern.search(path)]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit only the filtered paths to the executor
        future_to_file = {executor.submit(execution_function, path): path for path in filtered_paths}
        results = {}
        for future in concurrent.futures.as_completed(future_to_file):
            path = future_to_file[future]
            try:
                result = future.result()
                file_name_without_extension = os.path.splitext(os.path.basename(path))[0]
                results[file_name_without_extension] = result
            except Exception as exc:
                print(f"{path} generated an exception: {exc}")
        return results

class APIKeys(BaseModel):
    openai_key: str
    mistralai_key: str

def get_session(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        session = sessions.get(session_id, {})
    else:
        session_id = str(uuid.uuid4())
        session = {}
        sessions[session_id] = session

    def set_session(response: Response):
        response.set_cookie(key="session_id", value=session_id)
        return response

    return session, set_session

@app.post("/add_api_keys/")
async def add_api_keys(request: Request):
    api_key_json = await request.json()  # parse JSON data from incoming POST request

    session, set_session = get_session(request)
    user_id = session.get("user_id", str(uuid.uuid4()))
    session["user_id"] = user_id

    api_keys = APIKeys(**api_key_json)  # parse JSON data into a pydantic APIKeys model

    if all([api_key for api_key in [api_keys.openai_key, api_keys.mistralai_key]]):
        session[user_id] = {
            "openai_key": api_keys.openai_key,
            "mistralai_key": api_keys.mistralai_key,
        }
        response = {"message": "API keys added successfully!"}
        return set_session(Response(content=json.dumps(response), media_type="application/json"))
    else:
        raise HTTPException(status_code=400, detail="Invalid API key data")

@app.post("/translate_video_url/")
async def translate_video_url(url: str, target_languages: str, request: Request):
    logger.info(f"/translate_video_url/ endpoint ,url: {url} target_languages: {target_languages}")
    session,_ = get_session(request)
       # Get JSON data from the request
    json_data = await request.json()
    
    # Extract values from JSON body
    openAIkey = json_data.get("openAIkey", None)
    mistralAIkey = json_data.get("mistralAIkey", None)
    genders = json_data.get("genders", "male")  # Default value "male" if not provided
    
    logger.info(f"openAIkey: {openAIkey} , mistralAIkey: {mistralAIkey} ,  genders: {genders}")
    speakers = genders.split(',')  # Splitting the input string into a list
    logger.info(f"genders: {genders}")
    user_id = session.get("user_id", str(uuid.uuid4()))

    translated_videos = []

    translators = {
        "OpenAI": {"name": "openai", "available": True, "function": "openai_translate_text", "api_key": openAIkey, "model_name": "davinci"},
        "Ollama": {"name": "ollama", "available": True, "function": "translate_text_with_ollama", "api_key": None, "model_name": "llama2"},
        "Mistralai": {"name": "mistrali", "available": True, "function": "mistralai_translate_text", "api_key": mistralAIkey}
    }
    
    # Translate target_languages to English
    prompt = f"Please extract only the language names from the following text and provide them in English, separated by commas: {target_languages}"
    translated_target_languages = target_languages #translate_text(target_languages, "English", openai_key, mistralai_key, prompt = prompt)
    #translated_text = re.sub(r'[^\w\s]', '', translated_text)
    logger.info(f"translated_target_languages: {translated_target_languages}")
    # Clean the translated text and extract meaningful languages
    cleaned_languages = [lang.strip() for lang in translated_target_languages.split(",") if lang.strip()]

    if not cleaned_languages:
        raise HTTPException(status_code=400, detail="No meaningful target languages found.")

    video_path = download_video(url, output_path=download_folder)
    audio_path = extract_audio(video_path, output_path=download_folder)
    av = AudioVideoTranslator(audio_path, video_path, output_folder=translations_folder, lang = cleaned_languages[0], translators=translators, speakers = speakers)   
    print("Input media:", audio_path, video_path)
    av._perform_audio_diarization()
    filename_no_extention = os.path.splitext(os.path.basename(video_path))[0]
        # Translate the filename text
    filename_no_extention_trans = translate_text(filename_no_extention, cleaned_languages[0], translators, prompt = "consider translation no longer then original text")
    # Merge files and Rename the output file with the translated filename 
    translated_video_path = av.merge_video_files(output_filename = f"{filename_no_extention_trans}.mp4")
    # translated_videos.append(translated_video_path)

    # transcribe_audio(audio_path) where audio_path is the path to the audio file follw this pattern r"_(\d+)-(\d+)_(\d+)\.wav$"
    # results will keep 
    #results = execute_files(download_folder, transcribe_audio , r"_(\d+)-(\d+)_(\d+)\.wav$")
    #transcription = transcribe_audio(audio_path)

    """
    for lang in cleaned_languages:
      for filename,transcription in results.items():
        translated_text = translate_text(transcription, lang, translators, prompt = None, audio_path = f"{filename}.txt")
        translated_audio_path = synthesize_audio_openai(translated_text, lang, translations="translations",api_key=None , simulate_male_voice=True, speaker=0)
       
        translated_video_path = replace_original_audio(video_path, translated_audio_path)
        translated_videos.append(translated_video_path)

    #shutil.rmtree(translations_folder, ignore_errors=True)
    #os.makedirs(translations_folder, exist_ok=True)
    """
        # Return both file and message
    return {
        "message": "Translation completed successfully! To get the translated video, click the link below (temporary not accessable send eMail to zeroprg@gmail.com).",
        "file": FileResponse(translated_video_path, media_type='application/octet-stream')
    }
    return {"message": "Translation completed successfully.", "translated_videos": translated_videos}

@app.post("/translate_video_file/")
async def translate_video_file(file: UploadFile, target_languages: str, request: Request):
    logger.info(f"/translate_video_file/ endpoint ,UploadFile: {UploadFile} target_languages: {target_languages}")
    session,_ = get_session(request)
    user_id = session.get("user_id", str(uuid.uuid4()))    
    
    if user_id not in api_keys:
        raise HTTPException(status_code=400, detail="User not found or API keys not configured.")

    openai_key = api_keys[user_id]["openai_key"]
    mistralai_key = api_keys[user_id]["mistralai_key"]

    # Translate target_languages to English
    prompt = f"Please extract only the language names from the following text and provide them in English, separated by commas: {target_languages}"
    translated_target_languages = translate_text(target_languages, "English", openai_key, mistralai_key, prompt)

    # Clean the translated text and extract meaningful languages
    cleaned_languages = [lang.strip() for lang in translated_target_languages.split(",") if lang.strip()]

    if not cleaned_languages:
        raise HTTPException(status_code=400, detail="No meaningful target languages found.")

    video_path = download_video(file)
    audio_path = extract_audio(video_path)

    av = AudioVideoTranslator(audio_path, video_path, output_folder= download_folder)
   
    print("Input media:", audio_path, video_path)
    av._perform_audio_diarization()
    # transcribe_audio(audio_path) where audio_path is the path to the audio file follw this pattern r"_(\d+)-(\d+)_(\d+)\.wav$"
    # results will keep 
    results = execute_files(download_folder, r"_(\d+)-(\d+)_(\d+)\.wav$", transcribe_audio)
    #transcription = transcribe_audio(audio_path)

    translated_videos = []

    for lang in cleaned_languages:
        translated_text = translate_text(transcription, lang, openai_key, mistralai_key, prompt = None, audio_path = translations)
        translated_audio_path = synthesize_audio(translated_text, lang)
        translated_video_path = replace_original_audio(video_path, translated_audio_path)
        translated_videos.append(translated_video_path)

    # shutil.rmtree(translations_folder, ignore_errors=True)
    # os.makedirs(translations_folder, exist_ok=True)

    return {"message": "Translation completed successfully.", "translated_videos": translated_videos}

    # Launch the Gradio app

""" Gradio definitions """


def translate_video(url, target_languages, openAIkey, mistralAIkey, genders):
     # Encode URL parameters
    encoded_url = urllib.parse.quote(url, safe='')
    encoded_target_languages = urllib.parse.quote(target_languages, safe='')
        # Endpoint URL with URL parameters
    endpoint = f"http://localhost:8081/translate_video_url/?url={encoded_url}&target_languages={encoded_target_languages}"
    

    # JSON body
    json_body = {
        "openAIkey": openAIkey,
        "mistralAIkey": mistralAIkey,
        "genders": genders
    }

       # Make the POST request
    response = requests.post(endpoint, json=json_body) 

    # Assuming the response is JSON and contains a message
    return response

  
"""
# Define the Gradio interface
iface = gr.Interface(fn=translate_video,
                     inputs=[
                         gr.Textbox(label="Video URL"),
                         gr.Textbox(label="Target Languages (comma-separated)"),                        
                         gr.Textbox(label="OpenAI Key"),
                         gr.Textbox(label="MistralAI Key"),
                         gr.Textbox(label="Speaker Genders (comma-separated, e.g., male,female,male)")
                         ],
                     outputs="text",
                     title="Video Translator",
                     description="Translate videos by providing the video URL and target languages.")
"""

if __name__ == "__main__":    
    files = os.listdir(download_folder)
    print("Files in downloads folder:", files)
    #iface.launch(share=False)