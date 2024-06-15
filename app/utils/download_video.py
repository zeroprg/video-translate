# download.py
import os
from pytube import YouTube
from io import BytesIO as MemoryFile
import requests
import re
from fastapi import UploadFile

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) #Set log level if needed


def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)  # Removes problematic characters


def download_video_file(file: UploadFile, output_path='downloads'):
    # Ensure the output directory exists
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    filename = sanitize_filename(file.filename)
    # Construct the full path where the file will be saved
    file_path = os.path.join(output_path, filename)
    
    # Check if a file with the same name already exists
    if os.path.exists(file_path):
        print(f"File {filename} already exists. Skipping download.")
        return file_path  # or None, depending on how you want to handle this case
    
    # Save the uploaded file content to the new file
    try:
        with open(file_path, "wb") as out_file:
            # Read the file content in chunks and write to the output file
            while content := file.file.read(1024):  # Adjust chunk size as needed
                out_file.write(content)
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return None
    
    return file_path


def is_youtube_url(url):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    youtube_regex_match = re.match(youtube_regex, url)
    return youtube_regex_match is not None

def download_youtube_video(url, output_path='downloads'):
    logger.info(f"Downloading YouTube video from URL: {url}, output_path: {output_path} ")
    # Create a YouTube object
    youtube = YouTube(url)
    
    # Get the first available video stream
    video_stream = youtube.streams.first()
    
    # Sanitize the video title for use as a filename
    video_title = sanitize_filename(youtube.title)
    
    # Construct the full path where the video will be saved
    video_filename = f"{video_title}.mp4"
    video_path = os.path.join(output_path, video_filename)
    
    # Download the video if it does not exist already
    if not os.path.isfile(video_path):
        video_stream.download(output_path=output_path, filename=video_filename)
        return video_path
    else:
        logger.info(f"Video already exists: {video_path}")
        return video_path



def download_file(url, output_path='downloads'):
    try:
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        local_filename = url.split('/')[-1]
        local_filename = sanitize_filename(local_filename)
        video_path = os.path.join(output_path, f"{local_filename}.mp4")
        
        if os.path.isfile(video_path):
            return video_path  # File already exists
        
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(video_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
        return video_path
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return None

def download_video(url, output_path='downloads'):
    logger.info(f"Downloading video from URL: {url}, output_path: {output_path}")
    if is_youtube_url(url):
        return download_youtube_video(url, output_path = output_path)
    else:
        return download_file(url, output_path = output_path)

# Example usage
if __name__ == "__main__":
    url = "https://youtu.be/e9YP9xSWQh0?si=kx3rO-ZXyYviRpUm"  # Replace this with the actual video URL
    downloaded_video_path = download_video(url)
    if downloaded_video_path:
        print(f"Video successfully downloaded to: {downloaded_video_path}")
    else:
        print("Failed to download the video.")