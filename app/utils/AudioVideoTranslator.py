
import librosa

from pydub import AudioSegment
from moviepy.editor import VideoFileClip, concatenate_audioclips 

import re
import requests

import numpy as np
from pyannote.audio import Pipeline


import logging.config

logger = logging.getLogger(__name__)  # This assumes the logger is defined in '__init__.py' and configured with 'logging.conf' or an 'logging.config.file' argument

formatter = logging.Formatter('%(asctime)s:%(levelname)s: %(message)s')

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)

class AudioVideoTranslator():
    def __init__(self, input_audio_path, input_video_path=None, num_segments=10, output_folder=None):
        self.input_audio_path = input_audio_path
        self.input_video_path = input_video_path
        self.output_folder = output_folder
        self.num_segments = num_segments                 # initialize it here with the value passed by user, or a default number.
        logger.debug("Input audio path : %s",self.input_audio_path)
        logger.debug("Input video path : %s",self.input_video_path)
        self.clip = VideoFileClip(self.input_video_path) if self.input_video_path else None
        logger.debug('Video Clip loaded? : %s',str(bool(self.clip)))
        print(self.clip)
        self.fps = self.clip.fps
        logger.debug('Video Clip fps : %s',str(self.fps))
        
        self._load_files()  # Move _load_files() to the constructor and update accordingly
        self.num_segments = num_segments
        
        self.pipeline = Pipeline.from_pretrained('pyannote/speaker-diarization',use_auth_token="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")  # Initialize the speaker diarization pipeline here
        
    def extract_segments(self):
        logger.debug("Extracting speech segments...")
        try:
            diarization_result = self._diarize_audio()  # Perform speaker diarization on audio clip

            self.segmentation_indices = np.array(list(diarization_result["tracks"]))
            logger.debug("Speech segments detection completed.")
            
            if not self.output_folder: raise ValueError("'output_folder' argument must be provided in order to save extracted speech segments.")

            self._save_segments()  # Save extracted speech segments to output_folder
            logger.info("Total extracted speech segments: {}".format(len(self.segmentation_indices)))
        except Exception as e:
            logger.error("Failed to extract speech segments, error message: '{}'" . format(e))


    def _diarize_audio(self):
        """Perform speaker diarization using pyannonte library on loaded input audio."""
        logger.info("Processing speech for diarization...")
        if not self.input_video_path:  # Only perform diarization if an input video file is provided
            self._perform_audio_diarization()
            return {"tracks": self.segmentation_indices}

    def _process_input_video(self):
        """Process input video (load clip with MoviePyEdit, get frames per second)"""
        if self.clip is not None:
            self.fps = self.clip.fps
        else:
            logger.warning("No input video provided.")

    def _process_input_audio(self):
        """Process input audio (load it with librosa, store loaded audio file)"""
        self.audio = librosa.load(self.input_audio_path)

    def _load_files(self):
        logger.info("Loading input files...")
        self._process_input_video()
        
        if self.input_audio_path:  # If audio file is provided
            logger.debug("Processing audio file...")
            self.audio = librosa.load(self.input_audio_path, sr=16000)

        else:
            logger.warning("No input audio file provided.")
        
        if self.input_video_path:
            self.clip = VideoFileClip(self.input_video_path)

    def _save_segments(self):
        logger.info("Saving extracted speech segments...")
        for segment_index in self.segmentation_indices:
            start = segment_index[0]
            end = segment_index[-1]

            # Extract segment from the input audio
            segmented_audio = self._extract_segment(self.input_audio, start, end)
            
            # Save the segment with proper naming and numbering
            output_file_name = f"segment{str(self.num_segments)[-3:]}_{int(start*1000/self.fps)}-{int((start + self._duration(end))*1000/self.fps)}"
            np.save(os.path.join(self.output_folder, output_file_name), segmented_audio)



    def merge_video_files(self, input_pattern):
        """
        Merge all saved video files with the specified naming pattern into a single output file using moviepy.
        """

        videos = list(filter(lambda x: re.search(r'{}[\w_\d]+\.mp4$'.format('.*'.join(input_pattern.split('.')[:-1])), x) for x in os.listdir(self.output_folder) if os.path.isfile(os.path.join(self.output_folder,x)) and x[-4:] == '.mp4'))
        merged_clip = VideoFileClip()
        clip_objects = [VideoFileClip(os.path.join(self.output_folder, x)) for x in videos]

        for clip in clip_objecs:
            merged_clip = merged_clip.concat(clip)
        merged_clip.write_videofile(os.path.join(self.output_folder,"merged_{}.mp4".format(".".join(input_pattern.split('.')[:-1]))), fps=30) # Replace fps with the appropriate frames per second (fps) value for your videos.


    def count_speakers(self):
        try:
            # Assuming speaker_diarization requires only the file path and the number of speakers.
            # This is a placeholder; you may need to adjust arguments according to the actual API.
            segments, speaker_labels = aS.speaker_diarization(self.audio_path,2)
            num_speakers = len(set(speaker_labels))
            logger.info(f"Estimated number of unique speakers: {num_speakers}")
            return num_speakers
        except Exception as e:
            logger.info(f"An error occurred during speaker diarization: {e}")



if __name__ == "__main__":    

    audio_file_path = "../downloads/Истинный Смысл Матрицы. Наука, Религия и Философия в Матрице.wav"
    
    video_file_path = "../downloads/Истинный Смысл Матрицы. Наука, Религия и Философия в Матрице.mp4"

    av = AudioVideoTranslator(audio_file_path,video_file_path)

    # Test your class implementation here - You may need to adjust the paths or add other test data based on your use case
    print("Input media:", audio_file_path, video_file_path)
    av.extract_segments()
    av._save_segments()

