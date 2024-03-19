import os
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, vfx
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set log level if needed

def split_audio_into_chunks(audio_clip, chunk_duration, video_duration):
    """
    Split the audio clip into chunks of specified duration.
    Adjust the speed of the audio if its total duration is longer than the video's duration.
    """
    audio_duration = audio_clip.duration
    if audio_duration > video_duration:
        # Calculate the speed change required to match the video duration
        speed_change_factor = audio_duration / video_duration
        # Apply the speed change
        audio_clip = audio_clip.fx(vfx.speedx, speed_change_factor)
        # Update the audio duration after the speed change
        audio_duration = video_duration

    num_chunks = int(audio_duration // chunk_duration) + (1 if audio_duration % chunk_duration else 0)
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
        video_duration = video_clip.duration

        # Load the translated audio
        translated_audio = AudioFileClip(translated_audio_path)

        # Split the translated audio into chunks, adjusting speed if necessary
        audio_chunks = split_audio_into_chunks(translated_audio, chunk_duration, video_duration)

        # Create video segments to match the audio chunks
        video_segments = [video_clip.subclip(max(i * chunk_duration, 0), min((i + 1) * chunk_duration, video_duration)) for i in range(len(audio_chunks))]

        # Combine the video segments with their corresponding adjusted audio chunks
        final_video_with_audio = [video_segment.set_audio(audio_chunk) for video_segment, audio_chunk in zip(video_segments, audio_chunks)]

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