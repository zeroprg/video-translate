import os
import tempfile
from moviepy.editor import VideoFileClip, AudioFileClip, vfx
from pydub import AudioSegment
import logging 

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Set log level if needed
from moviepy.editor import VideoFileClip, AudioFileClip
from pydub import AudioSegment
import os
import tempfile

from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
import os

def split_audio_into_chunks(audio_clip, chunk_duration):
    """
    Split the audio clip into chunks of specified duration.
    """
    audio_duration = audio_clip.duration
    num_chunks = int(audio_duration // chunk_duration)
    chunks = []
    for i in range(num_chunks):
        start_time = i * chunk_duration
        end_time = min((i + 1) * chunk_duration, audio_duration)
        chunk = audio_clip.subclip(start_time, end_time)
        chunks.append(chunk)
    return chunks
    
def replace_original_audio(video_path, translated_audio_path, chunk_duration=30, translations="translations"):
    try:
        logger.info(f"Replacing audio in video: {video_path}")
        logger.info(f"Translated audio path: {translated_audio_path}")

        # Load the video
        video_clip = VideoFileClip(video_path)

        # Load the translated audio
        translated_audio = AudioFileClip(translated_audio_path)

        # Split the translated audio into chunks
        audio_chunks = split_audio_into_chunks(translated_audio, chunk_duration)

        video_duration = video_clip.duration
        # Ensure we do not create a video segment beyond the video's duration
        num_segments = min(len(audio_chunks), int(video_duration // chunk_duration) + (1 if video_duration % chunk_duration else 0))

        # Adjust video segments creation to not exceed video duration
        video_segments = []
        for i in range(num_segments):
            start_time = i * chunk_duration
            end_time = min((i + 1) * chunk_duration, video_duration)
            video_segment = video_clip.subclip(start_time, end_time)
            video_segments.append(video_segment)

        # Ensure each audio chunk does not exceed its corresponding video segment's duration
        final_video_with_audio = []
        for video_segment, audio_chunk in zip(video_segments, audio_chunks):
            # Adjust audio chunk if necessary to fit video segment
            if audio_chunk.duration > video_segment.duration:
                audio_chunk = audio_chunk.subclip(0, video_segment.duration)
            final_video_with_audio.append(video_segment.set_audio(audio_chunk))

        # Concatenate all video segments with adjusted audio
        video_with_audio = concatenate_videoclips(final_video_with_audio)

        # Save the video with the new audio
        output_filename = os.path.splitext(os.path.basename(video_path))[0] + "_translated.mp4"
        output_path = os.path.join(translations, output_filename)
        video_with_audio.write_videofile(output_path, codec="libx264", audio_codec="aac")

        logger.info(f"Video with translated audio saved to: {output_path}")

        return output_path
    except Exception as e:
        logger.error(f"Error replacing audio: {e}")
        return None
