import torch
import librosa
import torchaudio
from pyannote.audio import Pipeline
import soundfile as sf
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, concatenate_audioclips 

import re
import os
import requests
import logging.config

from transcribe_audio import transcribe_audio
from synthesize_audio import synthesize_audio_openai
from translate_text import translate_text
from replace_original_audio import replace_original_audio_intime_range

# Create or get the logger
logger = logging.getLogger(__name__)  # This assumes the logger is defined in '__init__.py' and configured with 'logging.conf' or a 'logging.config.file' argument


from pyannote.core import Segment

translators = {
    "Ollama": {"name": "ollama", "available": True, "function": "translate_text_with_ollama", "api_key": None, "model_name": "llama2"},
    "OpenAI": {"name": "openai", "available": True, "function": "openai_translate_text", "api_key": 'sk-***', "model_name": "davinci"},
    "Mistralai": {"name": "mistrali", "available": True, "function": "mistralai_translate_text", "api_key": 'BCI4GMNwnbZaEKcxjeEflPs5RamS1157'}
}


def merge_segments(diarization_results, gap_threshold=1.5):
    merged_segments = []
    current_segment = None

    for turn, _, speaker in diarization_results:
        # Adjust the start of the first segment to 0 if it's the initial one
        if current_segment is None:
            start_time = 0 if turn.start > 0 else turn.start
            current_segment = (Segment(start=start_time, end=turn.end), speaker)
        else:
            last_turn, last_speaker = current_segment
            # If the current segment is for the same speaker and within the gap threshold,
            # extend the end of the last segment; otherwise, append and start a new segment
            if speaker == last_speaker or turn.start - last_turn.end <= gap_threshold:
                # Merge this segment with the current one by extending the end time
                current_segment = (Segment(start=last_turn.start, end=turn.end), speaker)
            else:
                # Save the current segment and start a new one for the current turn
                merged_segments.append(current_segment)
                
                current_segment = (turn, speaker)
                print(f"{turn.start}-{turn.end}: {speaker} ")

    # Don't forget to add the last processed segment
    if current_segment is not None:
        merged_segments.append(current_segment)
   
    return merged_segments


class AudioVideoTranslator():
    def __init__(self, input_audio_path, input_video_path=None, output_folder="../translations" , lang = "English"):
        self.input_audio_path = input_audio_path
        self.input_video_path = input_video_path
        self.output_folder = output_folder
        self.lang = lang

        logger.debug("Input audio path : %s",self.input_audio_path)
        logger.debug("Input video path : %s",self.input_video_path)
                        
        pipeline = Pipeline.from_pretrained('pyannote/speaker-diarization-3.1',use_auth_token="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")  # Initialize the speaker diarization pipeline here
              # if GPU is available, use it
        if torch.cuda.is_available():
            pipeline.to(torch.device("cuda"))
        self.pipeline = pipeline
        self._process_input_video() 

    def _extract_and_save_audio_segment(self, speaker, start_sec, end_sec):
        """
        Extracts a segment from the loaded audio data and saves it to a file.
        Args:
        - start_sec: Start of the segment in seconds.
        - end_sec: End of the segment in seconds.
        """

        # Corrected use of soundfile for efficient reading
        # Note: Ensure 'path' variable is defined or use 'self.input_audio_path'
        with sf.SoundFile(self.input_audio_path) as sound_file:
            # Calculate start and end samples
            samplerate = sound_file.samplerate
            start_sample = int(start_sec * samplerate)
            end_sample = int(end_sec * samplerate)

            sound_file.seek(start_sample)
            segment = sound_file.read(frames=end_sample - start_sample)
        
        filename_no_extention = f"{os.path.splitext(os.path.basename(self.input_audio_path))[0]}_{start_sec}-{end_sec}_{speaker}"


        # Generate a readable filename
        filename = f"{filename_no_extention}.wav"
        output_path = os.path.join(self.output_folder, filename)

        # Save the segment using the soundfile module
        sf.write(output_path, segment, samplerate)
        print(f"Saved segment to {output_path}")  
        #Do not translate videos less then 2 seconds
        if end_sec - start_sec < 1.7:
            print(f"Segment duration is less than 1.7 seconds, skipping translation.")
            self._extract_and_save_video_segment(speaker, start_sec, end_sec)
            return

        transcribed_text = transcribe_audio(output_path)
        print(f"Transcribed text: {transcribed_text}")

        translated_text = translate_text(transcribed_text, self.lang, translators, prompt = None)
        print(f"Translated text: {translated_text}")

        # Synthesize audio for the transcribed text
        translated_audio_path = synthesize_audio_openai(translated_text, self.lang, output_file_path=filename ,api_key=None , simulate_male_voice=True)
              
        # Replace the audio in the video with the translated audio
        replace_original_audio_intime_range(self.clip, translated_audio_path, start_sample, end_sample, output_path = "../translations")

    def _extract_and_save_video_segment(self, speaker, start_sec, end_sec):
        """
        Extracts a segment from the loaded video data and saves it to a file.
        Args:
        - start_sec: Start of the segment in seconds.
        - end_sec: End of the segment in seconds.
        """
        clip = self.clip.subclip(start_sec, end_sec)
        #clip.set_audio(self.audio_clip) if you have an audio clip to add to the video
          # Generate a readable filename
        filename = f"{os.path.splitext(os.path.basename(self.input_audio_path))[0]}_{start_sec}-{end_sec}_{speaker}.mp4"
        output_path = os.path.join(self.output_folder, filename)

        clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        return filename


    def _perform_audio_diarization(self):
        """Perform speaker diarization on the input audio using the pyannote library."""
        logger.info("Performing speaker diarization...")
        # run the pipeline on an audio file
        diarization = self.pipeline(self.input_audio_path)

        waveform, sample_rate = torchaudio.load(self.input_audio_path)
        diarization = self.pipeline({"waveform": waveform, "sample_rate": sample_rate})
        segmentation_indices = diarization.itertracks(yield_label=True)
        # Merge the segments to avoid short pauses between speakers
        self._save_segments(segmentation_indices)
        

    def _process_input_video(self):
        """Process input video (load clip with MoviePyEdit, get frames per second)"""
        if not self.input_video_path:
            raise ValueError("No input video provided.")
        self.clip = VideoFileClip(self.input_video_path)
        self.fps = self.clip.fps
        logger.debug('Video Clip fps : %s',str(self.fps))
        return self.clip



    def _save_segments(self, merged_segments):
        logger.info("Saving extracted speech segments...") 
        merged_segments = merge_segments(merged_segments)
        for (turn, speaker) in merged_segments:

            print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")

            # Extract segment from the input audio and video
            self._extract_and_save_audio_segment(speaker,turn.start, turn.end)            



    def merge_video_files(self, input_pattern):
        # Pattern to extract start time from filename
        pattern = re.compile(r"_(\d+)-(\d+)_(\d+)\.mp4$")

        files = glob.glob(os.path.join(self.output_folder, input_pattern))
        
        # Filter and sort files based on the timestamps in their filenames
        sorted_files = sorted(files, key=lambda x: (int(pattern.search(x).group(1)), int(pattern.search(x).group(2))))

        clips = [VideoFileClip(filename) for filename in sorted_files]
        final_clip = concatenate_videoclips(clips)

        # Define output filename and save the concatenated clip
        output_filename = f"{os.path.splitext(os.path.basename(self.input_video_path))[0]}(trans).mp4"
        final_clip.write_videofile(os.path.join(self.output_folder, output_filename))



if __name__ == "__main__":    

    audio_file_path = "../downloads/Истинный Смысл Матрицы. Наука, Религия и Философия в Матрице.wav"
    
    video_file_path = "../downloads/Истинный Смысл Матрицы. Наука, Религия и Философия в Матрице.mp4"

    av = AudioVideoTranslator(audio_file_path,video_file_path)

    # Test your class implementation here - You may need to adjust the paths or add other test data based on your use case
    print("Input media:", audio_file_path, video_file_path)
    av._perform_audio_diarization()
    av.merge_video_files("*.mp4")

