
import openai
import whisper
import logging

import os

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def generate_srt(segments):
    srt_content = ""
    segment_number = 1

    for segment in segments:
        start_time = segment["start"]
        end_time = segment["end"]
        text = segment["text"]
        
        # Format the timing in HH:MM:SS,mmm format (milliseconds)
        start_time_formatted = "{:02d}:{:02d}:{:02d},{:03d}".format(
            int(start_time // 3600),
            int((start_time % 3600) // 60),
            int(start_time % 60),
            int((start_time * 1000) % 1000)  # Correct milliseconds calculation
        )
        end_time_formatted = "{:02d}:{:02d}:{:02d},{:03d}".format(
            int(end_time // 3600),
            int((end_time % 3600) // 60),
            int(end_time % 60),
            int((end_time * 1000) % 1000)  # Correct milliseconds calculation
        )

        # Add the segment number, timing, and text to the SRT content
        srt_content += f"{segment_number}\n"
        srt_content += f"{start_time_formatted} --> {end_time_formatted}\n"
        srt_content += f"{text.strip()}\n\n"  # Ensure text is stripped of leading/trailing spaces

        segment_number += 1

    return srt_content



def transcribe_audio(audio_path):
    # Convert to absolute path
    absolute_audio_path = os.path.abspath(audio_path)
    
    if not os.path.exists(absolute_audio_path):
        logger.error(f"Audio file does not exist: {absolute_audio_path}")
        return None

    try:
        # Check if a corresponding TXT file already exists
        text_filename = os.path.splitext(absolute_audio_path)[0] + ".txt"
        if os.path.exists(text_filename):
            # If the TXT file exists, return its content without transcribing
            with open(text_filename, "r", encoding="utf-8") as text_file:
                transcribed_text = text_file.read()
            logger.info(f"Text already transcribed, loaded from: {text_filename}")
            return transcribed_text
        
        # Check if a corresponding SRT file already exists
        srt_filename = os.path.splitext(absolute_audio_path)[0] + ".srt"
        if os.path.exists(srt_filename):
            # If the SRT file exists, return its content without transcribing
            with open(srt_filename, "r", encoding="utf-8") as srt_file:
                transcribed_text = srt_file.read()
            logger.info(f"SRT file already exists, loaded from: {srt_filename}")
            return transcribed_text

        # Load the Whisper model
        model = whisper.load_model("base",device='cuda')

        logger.info(f"Transcribing audio file: {absolute_audio_path}")

        # Transcribe the audio with automatic language detection
        result = model.transcribe(absolute_audio_path, language=None)  # Enable automatic language detection

        # Extracting the transcribed text
        transcribed_text = result["text"]

        # Extracting the timing segments
        timing_segments =  result["segments"]

        # Generate SRT content
        srt_content = generate_srt(timing_segments)

        # Writing the transcribed text to a file
        with open(text_filename, "w", encoding="utf-8") as text_file:
            text_file.write(transcribed_text)

        logger.info(f"Transcribed text saved to: {text_filename}")

        # Writing the transcribed srt text to a file
        with open(srt_filename, "w", encoding="utf-8") as text_file:
            text_file.write(srt_content)    

        logger.info(f"Transcribed srt text saved to: {srt_filename}")
        
        return transcribed_text
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return None

# Example usage
if __name__ == "__main__":    

    from download_video import download_youtube_video

    youtube_url = "https://youtu.be/CEC9XRw_C_8?si=IC3F_AE02V78Df5U"
    audio_path = download_youtube_video(youtube_url, output_path="../downloads")
    if audio_path:
        transcribed_text = transcribe_audio(audio_path)
        if transcribed_text:
            print(f"Transcription completed and saved to text file.")
        else:
            logger.info("Transcription could not be completed.")
    else:
        logger.info("Audio download failed.")