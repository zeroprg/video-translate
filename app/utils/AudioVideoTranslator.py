import torch
#import librosa
import torchaudio
from pyannote.audio import Pipeline
#import soundfile as sf
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips, concatenate_videoclips

import re
import os
import glob 
import requests
import logging.config
import threading
import concurrent.futures


from .transcribe_audio import transcribe_audio
from .synthesize_audio import synthesize_audio_openai
from .translate_text import translate_text
from .replace_original_audio import replace_original_audio_intime_range

# Create or get the logger
logger = logging.getLogger(__name__)  # This assumes the logger is defined in '__init__.py' and configured with 'logging.conf' or a 'logging.config.file' argument


from pyannote.core import Segment

# Get the path to the translations folder from the environment variable
translations_folder = os.environ.get("TRANSLATIONS_FOLDER", "./translations")

#Example of default translators
translators = {
    "OpenAI": {"name": "openai", "available": True, "function": "openai_translate_text", "api_key": None, "model_name": "davinci"},
    "Ollama": {"name": "ollama", "available": True, "function": "translate_text_with_ollama", "api_key": None, "model_name": "llama2"},
    "Mistralai": {"name": "mistrali", "available": True, "function": "mistralai_translate_text", "api_key": '***'}
}

def extract_speaker_index(speaker):
    match = re.match(r'SPEAKER_(\d+)', speaker)
    return int(match.group(1)) if match else 0


def merge_segments(diarization_results, gap_threshold=0.92):
    print("Merging segments...")
    merged_segments = []
    current_segment = None
    for turn, _, speaker_str in diarization_results:

        speaker = extract_speaker_index(speaker_str)
        print(f"Speaker: {speaker}")
        # Adjust the start of the first segment to 0 if it's the initial one
        if current_segment is None:            
            current_segment = (Segment(start=0, end=turn.end), speaker)
        else:
            last_turn, last_speaker = current_segment
            # If the current segment is for the same speaker and within the gap threshold,
            # extend the end of the last segment; otherwise, append and start a new segment
            if  turn.start - last_turn.end <= gap_threshold: #speaker == last_speaker and
                # Merge this segment with the current one by extending the end time
                current_segment = (Segment(start=last_turn.start, end=turn.end), speaker)
                last_speaker = speaker # Update the speaker for the merged segment
            else:
                # Save the current segment and start a new one for the current turn
                merged_segments.append(current_segment)
                
                current_segment = (turn, speaker)
        print(f"{turn.start} - {turn.end}: {speaker} ")

    # Don't forget to add the last processed segment
    if current_segment is not None:
        merged_segments.append(current_segment)
   
    return merged_segments


class AudioVideoTranslator():
    def __init__(self, input_audio_path, input_video_path=None, output_folder=translations_folder , lang = "English", speakers = ["male","male"], translators = translators): #default 2 male speakers
        self.threads = threading.Semaphore(1)
        self.speakers = speakers
        self.translators = translators
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
        self._process_input_audio() 

    def _extract_and_save_audio_segment(self, speaker, start_sec, end_sec , speakers = None):
        """
        Extracts a segment from the loaded audio data and saves it to a file.
        Args:
        - start_sec: Start of the segment in seconds.
        - end_sec: End of the segment in seconds.
        """
        gender = "male"
        if speakers is not None:
           speaker = speaker % len(speakers)
           gender = speakers[speaker]
          


        filename_no_extention = f"{os.path.splitext(os.path.basename(self.input_audio_path))[0]}_{start_sec}-{end_sec}_{speaker}"


        # Generate a readable filename
        filename = f"{filename_no_extention}.wav"
        output_path = os.path.join(self.output_folder, filename)

        # Save the segment using the soundfile module
        #sf.write(output_path, segment, samplerate)
        #print(f"Saved segment to {output_path}")  
        #Do not translate videos less then 2 seconds
        if end_sec - start_sec < 1.0:
            print(f"Segment duration is less than 1.7 seconds, skipping translation.")
            self._extract_and_save_video_segment(speaker, start_sec, end_sec)
            return

        audio_subclip = self.audio_clip.subclip(t_start=start_sec, t_end=end_sec)
        audio_subclip.write_audiofile(output_path)
        # Transcribe the audio segment        
        transcribed_text = transcribe_audio(output_path)
        # Translate the transcribed text
        translated_text = translate_text(transcribed_text, self.lang, self.translators, prompt = None, audio_path = output_path )

        # Synthesize audio for the transcribed text
        translated_audio_path = synthesize_audio_openai(translated_text, self.lang, output_file_path=filename , api_key = self.translators["OpenAI"]["api_key"] ,
             simulate_male_voice = True if gender == "male" else False , speaker = speaker)
              
        # Replace the audio in the video with the translated audio
        output_file = os.path.join(self.output_folder, f"{filename_no_extention}.mp4")

        replace_original_audio_intime_range(self.clip, translated_audio_path, start_sec, end_sec, output_file = output_file)

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
        print("Performing speaker diarization...")
        if len(self.speakers) > 1 :
            waveform, sample_rate = torchaudio.load(self.input_audio_path)
            diarization = self.pipeline({"waveform": waveform, "sample_rate": sample_rate})
            segmentation_indices = diarization.itertracks(yield_label=True)
        else: 
            segmentation_indices = None



        
        # Note: Printing the generator directly won't give meaningful output
        #for segment in segmentation_indices:
        #    print(f"Segment: {segment}")
        
        # Assuming _save_segments is correctly implemented to handle segmentation_indices
        self._save_segments(segmentation_indices)


    def _process_input_video(self):
        """Process input video (load clip with MoviePyEdit, get frames per second)"""
        if not self.input_video_path:
            raise ValueError("No input video provided.")
        self.clip = VideoFileClip(self.input_video_path)
        self.fps = self.clip.fps
        print('Video Clip fps : %s',str(self.fps))
        return self.clip

    def _process_input_audio(self):
        """Process input video (load clip with MoviePyEdit, get frames per second)"""
        if not self.input_audio_path:
            raise ValueError("No input audio provided.")
        self.audio_clip = AudioFileClip(self.input_audio_path)        
        print(f"Audio Clip duration : {self.audio_clip.duration}")
        return self.audio_clip    


    def _save_segments(self, segmentation_indices):
        print("Saving extracted speech segments...") 
        if segmentation_indices is None:
            print("No speaker diarization results found. Only one segment ")
            self._extract_and_save_audio_segment(0, 0.0, self.audio_clip.duration, speakers = self.speakers) 
            return
        merged_segments = merge_segments(segmentation_indices)
        for (turn, speaker) in merged_segments:
            print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker:{speaker}")
            # Extract segment from the input audio and video
            
            self._extract_and_save_audio_segment(speaker,turn.start, turn.end, speakers = self.speakers)            

    """

    def _save_segments(self, merged_segments):
        logger.info("Saving extracted speech segments...")
        merged_segments = merge_segments(merged_segments)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:            
            futures = {executor.submit(self._extract_and_save_video_segment, speaker, turn.start, turn.end) for (turn, speaker) in merged_segments}
            for future in concurrent.futures.as_completed(futures):
                #print(f"Processing segment for turn {future[0].args[0].start:.1f}s - {future[0].args[0].end:.1f}s completed by thread: {threading.current_thread().ident}")
                print(f"Processing segment for turn {future.result()[0].start:.1f}s - {future.result()[0].end:.1f}s completed by thread: {threading.current_thread().ident}")

    """


    def merge_video_files(self , output_filename = None):
        print(f"Merging video files in self.output_folder: {self.output_folder} / output_filename: {output_filename}...")

        print(f"Merging video files in {self.output_folder} / {output_filename}...")
        video_pattern = re.compile(r"(\d+\.\d+|\d+)_(\d+)\.mp4$")
        audio_pattern = re.compile(r"(\d+\.\d+|\d+)_(\d+)\.wav$")
        #text_pattern =  re.compile(r"(\d+\.\d+|\d+)_(\d+)\.txt$")

        # Get all .mp4 files in the output folder
        all_files = glob.glob(os.path.join(self.output_folder, "*.mp4"))
        #print(f"all_files files : {all_files}")
        # Filter files using the video_pattern
        filtered_files = [file for file in all_files if video_pattern.search(os.path.basename(file))]
        #print(f"Filtered files : {filtered_files}")

        if output_filename is None: 
            output_filename = f"{os.path.splitext(os.path.basename(self.input_video_path))[0]}(trans).mp4"
        else:
            output_filename = output_filename.replace("..mp4", ".mp4")
        if not filtered_files:
            print("No matching video files were found.")
        elif len(filtered_files) == 1:
            # If only one file is found, rename it
            file_path = filtered_files[0]            
            os.rename(file_path, os.path.join(self.output_folder, output_filename))
            #print(f"File renamed to: {output_filename}")
        else:
            # Sort and merge if more than one file is found
            filtered_files.sort(key=lambda x: [float(num) if '.' in num else int(num) 
                                            for num in video_pattern.search(os.path.basename(x)).groups()])
            clips = [VideoFileClip(file) for file in filtered_files]
            final_clip = concatenate_videoclips(clips)
               
            final_clip.write_videofile(os.path.join(self.output_folder, output_filename))
            print("File saved to {output_filename}") 
           
        try:
            # Delete all files matching the video and audio patterns for cleanup
            for pattern in [video_pattern, audio_pattern]:
                for file in glob.glob(os.path.join(self.output_folder, "*")):
                    if pattern.search(os.path.basename(file)):
                        os.remove(file)
                        print(f"Deleted {file}")
        except Exception as e:          
            print(f"Error deleting files: {e}")
                
        return  output_filename           
 


if __name__ == "__main__":    

    audio_file_path = "./app/downloads/Самый секретный прием Умной Молитвы.wav"
    
    video_file_path = "./app/downloads/Самый секретный прием Умной Молитвы.mp4"

    av = AudioVideoTranslator(audio_file_path,video_file_path, output_folder="app/translations")

    # Test your class implementation here - You may need to adjust the paths or add other test data based on your use case
    print("Input media:", audio_file_path, video_file_path)
    #av._perform_audio_diarization()
    av.merge_video_files()

