# extract.py
import os
import logging
from moviepy.editor import VideoFileClip

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def extract_audio(video_path, output_path='downloads'):
    try:
        # Ensure the output directory exists
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        # Construct the audio file path
        audio_filename = os.path.splitext(os.path.basename(video_path))[0] + ".wav"
        audio_path = os.path.join(output_path, audio_filename)

        # Check if the audio file already exists
        if os.path.exists(audio_path):
            logger.info(f"Audio file already exists: {audio_path}")
            return audio_path

        # Extract the audio
        video_clip = VideoFileClip(video_path)
        audio_clip = video_clip.audio
        audio_clip.write_audiofile(audio_path)

        # Close the clips to free up resources
        audio_clip.close()
        video_clip.close()

        return audio_path
    except Exception as e:
        logger.error(f"Error extracting audio: {e}")
        return None
