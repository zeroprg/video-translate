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

def replace_original_audio_intime_range(video_clip, audio, start_time, end_time, output_file = "./translations/temp.mp4"):
    """
    Replace the audio of the video clip with the audio from the given path
    for the specified time range and save the result to the output path.
    """
    try:
        logger.info(f"Replacing audio in video: {video_clip.filename} ")
        logger.info(f"Audio path or audio clip: {audio}")
        video_clip_duration = end_time - start_time
        logger.info(f"Time range: {start_time}-{end_time}. Time range is in seconds: {video_clip_duration}")
        logger.info(f"Video_clip.duration: {video_clip.duration}")
        
        # Load the audio clip
        if not isinstance(audio, AudioFileClip):
            audio = AudioFileClip(audio)
        logger.info(f"audio.clip.duration: {audio.duration}")

        # Golden ratio and its reciprocal
        golden_ratio = 1.29
        golden_ratio_reciprocal = 1 / golden_ratio

        # Calculate the ratio of the shorter duration to the longer duration
        duration_ratio = min(audio.duration, video_clip_duration) / max(audio.duration, video_clip_duration)

        # Determine if adjustment is needed based on the golden ratio thresholds
        if golden_ratio_reciprocal <= duration_ratio <= golden_ratio:
            if audio.duration > video_clip_duration:
                # Audio is longer than video, and difference is significant
                speed_change_factor = video_clip_duration / audio.duration
            else:
                # Audio is shorter than video, and difference is significant
                speed_change_factor = audio.duration / video_clip_duration

            # Apply the speed change
            audio = audio.fx(vfx.speedx, speed_change_factor)


        new_subclip = video_clip.subclip(t_start=start_time, t_end=end_time).set_audio(audio)

        # Save the video with the new audio
        new_subclip.write_videofile(output_file, codec="libx264", audio_codec="aac")  
        
        logger.info(f"Video with new audio saved to: {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Error replacing audio: {e}")
        return None

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