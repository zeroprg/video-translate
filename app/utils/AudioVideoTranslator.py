from pyAudioAnalysis import audioSegmentation as aS
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, concatenate_audioclips
import requests

import time
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set log level if needed

class AudioVideoTranslator:
    def __init__(self, video_path):
        self.video_path = video_path
        self.audio_path = "../downloads/temp_audio.wav"
        self.video = VideoFileClip(video_path)
        self.video.audio.write_audiofile(self.audio_path)
        self.segments = []

    def count_speakers(self):
        try:
            # Assuming speaker_diarization requires only the file path and the number of speakers.
            # This is a placeholder; you may need to adjust arguments according to the actual API.
            segments, speaker_labels = aS.speaker_diarization(self.audio_path, numOfSpeakers=2)
            num_speakers = len(set(speaker_labels))
            logger.info(f"Estimated number of unique speakers: {num_speakers}")
            return num_speakers
        except Exception as e:
            logger.info(f"An error occurred during speaker diarization: {e}")


    def adjust_audio_duration_and_translate(self, target_language):
        for i, (start, end, _) in enumerate(self.segments):
            start_ms = start * 1000
            end_ms = end * 1000
            audio_chunk = AudioSegment.from_file(self.audio_path)[start_ms:end_ms]
            
            # Assuming you implement a function to handle speech-to-text, translation, and text-to-speech,
            # which outputs the translated audio file path.
            translated_audio_path = self.translate_audio_chunk(audio_chunk, target_language)
            
            # Update segment with translated audio path
            self.segments[i] = (start, end, translated_audio_path)

    def translate_audio_chunk(self, audio_chunk, target_language):
        # This method should implement speech-to-text, call translate_text_with_mixtral for translation,
        # and then use text-to-speech to generate the translated audio, returning the path to the audio file.
        pass

    def translate_text_with_mixtral(self, text_to_translate, target_language):
        """
        Translates a given text using the Mistral model from Ollama.

        Args:
            text_to_translate (str): The input text to be translated
            target_language (str): The target language for translation

        Returns:
            str: The translated text or None if an error occurs.
        """
        ollama_url = "http://localhost:11434/api/chat"  # Replace this URL with the actual Ollama instance's URL

        payload = {
            "model": "openhermes2.5-mistral",
            "messages": [{"role": "user", "content": f"Translate text to {target_language}: {text_to_translate}"}],
            "stream": False
        }

        try:
            start_time = time.time()
            response = requests.post(ollama_url, json=payload)  # Make the request

            elapsed_time = time.time() - start_time

            if response.status_code == 200:
                logger.debug(f"Received status code 200. Elapsed time for API call: {elapsed_time} seconds")

                response_data = response.json()
                print(response_data)
                translated_text = response_data['message']['content'] if len(response_data) > 0 else None

                if translated_text is not None:
                    logger.debug(f"Text translated successfully. Translation: {translated_text}")
                    return translated_text

            else:
                error_message = f"Failed to translate text. HTTP Status Code: {response.status_code}"
                logger.warning(error_message)

        except Exception as e:
            logger.critical(f"An error occurred while attempting to contact the Ollama service: {e}")

        return None

    def combine_audio_with_video(self):
        audio_clips = []
        for start, end, path in self.segments:
            if path:  # Ensure there's a translated path
                audio_clip = AudioFileClip(path).set_start(start)
                audio_clips.append(audio_clip)
        final_audio = concatenate_audioclips(audio_clips)
        
        final_video = self.video.set_audio(final_audio)
        final_video.write_videofile("translated_video.mp4", codec="libx264", audio_codec="aac")

# Example usage
if __name__ == "__main__":
    translator = AudioVideoTranslator("../downloads/Истинный Смысл Матрицы. Наука, Религия и Философия в Матрице.mp4")
    # translate text remove it after testing:
    result = translator.translate_text_with_mixtral("Hello world!!", "Russian")
    print(f"Translated : {result}")
    result = translator.count_speakers()
    print(f"Speakers counted : {result}")
    #translator.adjust_audio_duration_and_translate("French")
    #translator.combine_audio_with_video()